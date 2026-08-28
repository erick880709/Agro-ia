"""Motor de reglas agronómicas (Sistema Experto).

Evalúa variables de suelo contra reglas UPRA/Cenicafé/AGROSAVIA.
Determinístico, trazable y versionado. Las reglas se cachean en Redis.
"""

from dataclasses import dataclass

from agroia.logging import get_logger

logger = get_logger(__name__)

# ── Mapeo VariableSuelo (valor de la regla) → clave en SoilData.to_dict() ──
VARIABLE_KEY_MAP = {
    "pH": "ph",
    "N": "nitrogeno",
    "P": "fosforo",
    "K": "potasio",
    "Ca": "calcio",
    "Mg": "magnesio",
    "S": "azufre",
    "Fe": "hierro",
    "Mn": "manganeso",
    "Zn": "zinc",
    "Cu": "cobre",
    "B": "boro",
    "MO": "materia_organica",
    "CIC": "cic",
    "textura": "textura",
    "humedad": "humedad",
    "temperatura_suelo": "temperatura_suelo",
    "CE": "conductividad_electrica",
}


@dataclass
class RuleViolation:
    """Una violación detectada por el motor de reglas."""
    variable: str
    valor_actual: float | None
    umbral_min: float | None
    umbral_max: float | None
    accion: str
    prioridad: str
    fuente: str
    regla_id: str


@dataclass
class RulesResult:
    """Resultado de la evaluación del motor de reglas."""
    status: str  # "OK", "WARNING", "FORBIDDEN"
    violations: list[RuleViolation]
    warnings: list[RuleViolation]
    applied_rules: int
    total_rules: int

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def is_blocked(self) -> bool:
        return self.status == "FORBIDDEN"


class RulesEngine:
    """Motor de reglas agronómicas determinístico."""

    def __init__(self, db_session, redis_client=None):
        self.db = db_session
        self.redis = redis_client
        self._rules_cache: list[dict] = []
        self._cache_version: int = 0

    async def load_rules(self, cultivo_id: str | None = None) -> list[dict]:
        """Carga reglas activas desde BD, filtrando por cultivo si se especifica."""
        from sqlalchemy import select

        from agroia_backend.models.regla_agronomica import ReglaAgronomica

        stmt = select(ReglaAgronomica).where(
            ReglaAgronomica.activa.is_(True),
            ReglaAgronomica.tipo == "primaria",
        )
        if cultivo_id:
            stmt = stmt.where(
                (ReglaAgronomica.cultivo_id == cultivo_id)
                | (ReglaAgronomica.cultivo_id.is_(None))
            )

        result = await self.db.execute(stmt)
        rules = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "variable": r.variable.value,
                "umbral_min": r.umbral_min,
                "umbral_max": r.umbral_max,
                "accion": r.accion,
                "prioridad": r.prioridad.value,
                "fuente": r.fuente,
                "version": r.version,
                "cultivo_id": str(r.cultivo_id) if r.cultivo_id else None,
            }
            for r in rules
        ]

    async def evaluate(
        self, soil_data: dict, cultivo_id: str | None = None
    ) -> RulesResult:
        """Evalúa datos de suelo contra las reglas activas.

        Args:
            soil_data: diccionario {variable: valor} con las 18 variables
            cultivo_id: ID del cultivo objetivo (opcional, para filtrar reglas)

        Returns:
            RulesResult con status, violations y warnings
        """
        rules = await self.load_rules(cultivo_id)
        violations: list[RuleViolation] = []
        warnings: list[RuleViolation] = []
        total_applied = 0

        for rule in rules:
            var_name = rule["variable"]
            # Las reglas usan valores del enum VariableSuelo (ej. "pH", "N");
            # SoilData.to_dict() usa claves en español (ej. "ph", "nitrogeno").
            key = VARIABLE_KEY_MAP.get(var_name, var_name)
            value = soil_data.get(key)

            # Si no hay dato para esta variable, omitir la regla
            if value is None:
                continue

            total_applied += 1

            # Evaluar umbral
            violated = False
            if rule["umbral_min"] is not None and value < rule["umbral_min"]:
                violated = True
            if rule["umbral_max"] is not None and value > rule["umbral_max"]:
                violated = True

            if violated:
                v = RuleViolation(
                    variable=var_name,
                    valor_actual=value,
                    umbral_min=rule["umbral_min"],
                    umbral_max=rule["umbral_max"],
                    accion=rule["accion"],
                    prioridad=rule["prioridad"],
                    fuente=rule["fuente"],
                    regla_id=rule["id"],
                )
                if rule["prioridad"] in ("Critica", "Alta"):
                    violations.append(v)
                else:
                    warnings.append(v)

        # ── Determinar status ──
        if any(v.prioridad == "Critica" for v in violations):
            status = "FORBIDDEN"
        elif violations:
            status = "WARNING"
        else:
            status = "OK"

        logger.info(
            "rules_evaluation_complete",
            status=status,
            violations=len(violations),
            warnings=len(warnings),
            total_rules=len(rules),
            applied=total_applied,
        )

        return RulesResult(
            status=status,
            violations=violations,
            warnings=warnings,
            applied_rules=total_applied,
            total_rules=len(rules),
        )

    async def _estado_variable(
        self, soil_dict: dict, var_enum: str
    ) -> tuple[float | None, str | None]:
        """Devuelve (valor, estado) de una variable según las reglas primarias.

        estado: "exceso" | "deficit" | None (sin dato o sin regla aplicable).
        """
        rules = await self.load_rules(None)
        key = VARIABLE_KEY_MAP.get(var_enum, var_enum)
        value = soil_dict.get(key)
        if value is None:
            return None, None
        estados = []
        for rule in rules:
            if rule["variable"] != var_enum:
                continue
            if rule["umbral_min"] is not None and value < rule["umbral_min"]:
                estados.append("deficit")
            if rule["umbral_max"] is not None and value > rule["umbral_max"]:
                estados.append("exceso")
        if not estados:
            return float(value), None
        return float(value), "exceso" if "exceso" in estados else "deficit"

    async def evaluar_antagonismos(
        self, soil_dict: dict, etapa_fenologica: str | None = None
    ) -> list[dict]:
        """Reglas de segundo orden (antagonismo/sinergia nutricional).

        Devuelve filas tipo {variable, estado, accion, prioridad, fuente} con
        estado 'INTERACCION' listas para inyectarse como ajustes nutricionales.
        """
        from sqlalchemy import select

        from agroia_backend.models.regla_agronomica import ReglaAgronomica

        resultado = (
            await self.db.execute(
                select(ReglaAgronomica).where(
                    ReglaAgronomica.activa.is_(True),
                    ReglaAgronomica.tipo == "antagonismo",
                )
            )
        ).scalars().all()
        if not resultado:
            return []

        def regla_para(var_enum: str):
            for r in resultado:
                if getattr(r.variable, "value", r.variable) == var_enum:
                    return r
            return None

        filas: list[dict] = []

        def _agregar(variable: str, accion: str, prioridad: str, fuente: str) -> None:
            filas.append({
                "variable": variable,
                "estado": "INTERACCION",
                "valor_actual": None,
                "accion": accion,
                "prioridad": prioridad,
                "fuente": fuente,
            })

        k_val, k_estado = await self._estado_variable(soil_dict, "K")
        ca_val, ca_estado = await self._estado_variable(soil_dict, "Ca")
        mg_val, mg_estado = await self._estado_variable(soil_dict, "Mg")
        p_val, p_estado = await self._estado_variable(soil_dict, "P")
        zn_val, zn_estado = await self._estado_variable(soil_dict, "Zn")
        n_val, n_estado = await self._estado_variable(soil_dict, "N")
        ph = soil_dict.get("ph")

        # 1. K en exceso reduce absorción de Ca/Mg
        if k_estado == "exceso" and (ca_estado == "deficit" or mg_estado == "deficit"):
            r = regla_para("K")
            if r:
                _agregar("K-Ca-Mg", r.accion, r.prioridad.value, r.fuente)
        # 2. P en exceso fija Zn
        if p_estado == "exceso" and zn_estado == "deficit":
            r = regla_para("P")
            if r:
                _agregar("P-Zn", r.accion, r.prioridad.value, r.fuente)
        # 3. N en exceso en fructificación retrasa maduración
        etapa = (etapa_fenologica or "").lower()
        if n_estado == "exceso" and "ructificaci" in etapa:
            r = regla_para("N")
            if r:
                _agregar("N-maduracion", r.accion, r.prioridad.value, r.fuente)
        # 4. pH < 5.5 y Mg bajo → cal dolomítica
        if ph is not None and float(ph) < 5.5 and mg_estado == "deficit":
            r = regla_para("pH")
            if r:
                _agregar("pH-Ca-Mg", r.accion, r.prioridad.value, r.fuente)

        if filas:
            logger.info(
                "antagonismos_evaluados", total=len(filas),
                variables=[f["variable"] for f in filas],
            )
        return filas
