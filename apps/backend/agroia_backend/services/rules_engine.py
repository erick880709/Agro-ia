"""Motor de reglas agronómicas (Sistema Experto).

Evalúa variables de suelo contra reglas UPRA/Cenicafé/AGROSAVIA.
Determinístico, trazable y versionado. Las reglas se cachean en Redis.
"""

from dataclasses import dataclass
from typing import Optional

from agroia.logging import get_logger
from agroia_backend.models.regla_agronomica import PrioridadRegla, VariableSuelo

logger = get_logger(__name__)


@dataclass
class RuleViolation:
    """Una violación detectada por el motor de reglas."""
    variable: str
    valor_actual: Optional[float]
    umbral_min: Optional[float]
    umbral_max: Optional[float]
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

    async def load_rules(self, cultivo_id: Optional[str] = None) -> list[dict]:
        """Carga reglas activas desde BD, filtrando por cultivo si se especifica."""
        from sqlalchemy import select

        from agroia_backend.models.regla_agronomica import ReglaAgronomica

        stmt = select(ReglaAgronomica).where(ReglaAgronomica.activa == True)
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
        self, soil_data: dict, cultivo_id: Optional[str] = None
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
            value = soil_data.get(var_name)

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
