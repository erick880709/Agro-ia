"""Servicio de aptitud de cultivos — sistema experto (UC1).

Puntúa cada cultivo del catálogo contra los datos de suelo medidos por los
sensores IoT usando las reglas agronómicas (UPRA/Cenicafé/AGROSAVIA).
Metodología de aptitud por rangos, similar a la zonificación UPRA.

Determinístico, trazable y versionado — cumple RNF-010 (actualización del
conocimiento sin reentrenamiento: basta editar reglas en BD).
"""

from agroia.logging import get_logger

logger = get_logger(__name__)

# Peso de cada prioridad de regla al calcular la penalización de aptitud
PESOS_PRIORIDAD = {
    "Critica": 30,
    "Alta": 20,
    "Media": 10,
    "Baja": 5,
}

MAX_PENALIZACION = 100.0
TOTAL_VARIABLES_SENSOR = 18  # ALL_SOIL_VARIABLES en data_adapters.py

# Cultivos de raíz profunda: no prosperan en suelos someros (< 30 cm)
CULTIVOS_RAIZ_PROFUNDA = {
    "aguacate", "mango", "naranja", "limón", "mandarina", "palma de aceite",
}

# Cultivos tolerantes a sequía (priorizados en fincas de secano)
CULTIVOS_RESISTENTES_SEQUIA = {
    "sorgo", "yuca", "mango", "maracuyá", "uva", "tabaco", "higuerilla",
}


def clasificar_aptitud(score: float) -> str:
    """Clasifica un score de aptitud en categoría UPRA-style."""
    if score >= 80:
        return "Apta"
    if score >= 60:
        return "Moderadamente apta"
    if score >= 40:
        return "Marginalmente apta"
    return "No apta"


class AptitudService:
    """Recomienda los cultivos más aptos para un suelo sin siembra previa."""

    def __init__(self, db_session, rules_engine):
        self.db = db_session
        self.rules = rules_engine

    async def _cultivos_evaluables(self) -> list[tuple]:
        """Cultivos activos que tienen al menos una regla agronómica específica."""
        from sqlalchemy import func, select

        from agroia_backend.models.cultivo import Cultivo
        from agroia_backend.models.regla_agronomica import ReglaAgronomica

        stmt = (
            select(Cultivo, func.count(ReglaAgronomica.id))
            .join(ReglaAgronomica, ReglaAgronomica.cultivo_id == Cultivo.id)
            .where(Cultivo.activo.is_(True), ReglaAgronomica.activa.is_(True))
            .group_by(Cultivo.id)
        )
        result = await self.db.execute(stmt)
        return [(cultivo, n) for cultivo, n in result.all() if n > 0]

    async def recommend_crops(
        self,
        soil_dict: dict,
        top_n: int = 5,
        min_score: float = 40.0,
        lote: dict | None = None,
    ) -> list[dict]:
        """UC1: recomienda los cultivos más aptos para el suelo medido.

        Args:
            soil_dict: variables de suelo medidas por los sensores
                (claves de SoilData.to_dict(): ph, nitrogeno, ...).
            top_n: número máximo de sugerencias a devolver.
            min_score: score mínimo (0-100) para incluir un cultivo.
            lote: características físicas del lote (profundidad_suelo_cm,
                pedregosidad) — penalizan cultivos con requerimientos
                específicos (p. ej. aguacate de raíz pivotante).

        Returns:
            Lista ordenada desc por score con cultivo, score, confianza,
            clasificación UPRA y ajustes requeridos para sembrar.
        """
        cultivos = await self._cultivos_evaluables()
        if not cultivos:
            logger.warning("aptitud_no_cultivos_evaluables")
            return []

        cobertura = len(soil_dict) / TOTAL_VARIABLES_SENSOR
        lote = lote or {}
        profundidad = lote.get("profundidad_suelo_cm")
        pedregosidad = (lote.get("pedregosidad") or "").lower()

        sugerencias: list[dict] = []
        for cultivo, n_reglas in cultivos:
            rules_result = await self.rules.evaluate(soil_dict, str(cultivo.id))

            penalizacion = 0.0
            ajustes: list[dict] = []
            for v in rules_result.violations + rules_result.warnings:
                penalizacion += PESOS_PRIORIDAD.get(v.prioridad, 10)
                estado = self._clasificar_estado(v)
                ajustes.append({
                    "variable": v.variable,
                    "estado": estado,
                    "valor_actual": v.valor_actual,
                    "rango_ideal": self._formatear_rango(v),
                    "accion": v.accion,
                    "prioridad": v.prioridad,
                    "fuente": v.fuente,
                })

            # ── Profundidad efectiva del suelo (limitante física) ──
            # El cultivo declara su profundidad radicular mínima (fisiología).
            # Si el lote es más somero, se penaliza proporcional al déficit
            # (fallback: raíces profundas conocidas si la columna es NULL).
            nombre_l = cultivo.nombre.lower()
            req_prof = cultivo.profundidad_radicular_min_cm
            if req_prof is None and nombre_l in CULTIVOS_RAIZ_PROFUNDA:
                req_prof = 60  # fallback agronómico histórico
            if req_prof is not None and profundidad is not None and profundidad < req_prof:
                deficit = req_prof - profundidad
                pen = round(min(40.0, 10.0 + deficit * 0.5), 1)
                penalizacion += pen
                ajustes.append({
                    "variable": "profundidad_suelo",
                    "estado": "DEFICIT",
                    "valor_actual": profundidad,
                    "rango_ideal": f"≥ {req_prof} cm para {cultivo.nombre}",
                    "accion": (
                        f"Profundidad efectiva del suelo ({profundidad} cm) por debajo "
                        f"de lo requerido para {cultivo.nombre} (raíz de {req_prof} cm). "
                        "Considere otro cultivo o mejore el perfil con camellones/"
                        "enmiendas profundas."
                    ),
                    "prioridad": "Critica" if deficit >= 15 else "Alta",
                    "fuente": "AGROSAVIA — fisiología del cultivo",
                })

            # ── Pedregosidad alta: advertencia de limitante física ──
            if pedregosidad == "alta":
                ajustes.append({
                    "variable": "pedregosidad",
                    "estado": "ADVERTENCIA",
                    "valor_actual": "Alta",
                    "rango_ideal": "Ninguna – Moderada",
                    "accion": (
                        "Limitante física: alta pedregosidad restringe el desarrollo "
                        "radicular y la retención de agua. Valore despedrado del hoyo "
                        "de siembra o cultivos tolerantes."
                    ),
                    "prioridad": "Media",
                    "fuente": "AGROSAVIA",
                })
                penalizacion += PESOS_PRIORIDAD.get("Media", 10)

            score = round(max(0.0, 100.0 - min(penalizacion, MAX_PENALIZACION)), 1)
            # Confianza: calidad de cumplimiento de reglas + cobertura de datos
            confianza = round(
                min(0.99, max(0.05, (100.0 - min(penalizacion, MAX_PENALIZACION)) / 100.0)
                    * (0.75 + 0.25 * cobertura)),
                3,
            )

            sugerencias.append({
                "cultivo_id": str(cultivo.id),
                "cultivo": cultivo.nombre,
                "icono": cultivo.icono,
                "score": score,
                "confianza": confianza,
                "clasificacion": clasificar_aptitud(score),
                "reglas_especificas": n_reglas,
                "ajustes": ajustes[:5],
            })

        sugerencias.sort(
            key=lambda s: (s["score"], s["reglas_especificas"]),
            reverse=True,
        )
        resultado = [s for s in sugerencias if s["score"] >= min_score][:top_n]
        # Si ningún cultivo alcanza el umbral, devolver el mejor disponible
        # (marcado como No apta) para que la respuesta siempre sea accionable.
        if not resultado and sugerencias:
            resultado = sugerencias[:1]
        logger.info(
            "aptitud_recomendacion",
            evaluados=len(sugerencias),
            sugeridos=len(resultado),
            top=sugerencias[0]["cultivo"] if sugerencias else None,
        )
        return resultado

    @staticmethod
    def _clasificar_estado(v) -> str:
        """Clasifica una violación como DEFICIT, EXCESO o DESCONOCIDO."""
        if v.valor_actual is None:
            return "DESCONOCIDO"
        if v.umbral_min is not None and v.valor_actual < v.umbral_min:
            return "DEFICIT"
        if v.umbral_max is not None and v.valor_actual > v.umbral_max:
            return "EXCESO"
        return "DESCONOCIDO"

    @staticmethod
    def _formatear_rango(v) -> str:
        if v.umbral_min is not None and v.umbral_max is not None:
            return f"[{v.umbral_min} - {v.umbral_max}]"
        if v.umbral_min is not None:
            return f"≥ {v.umbral_min}"
        if v.umbral_max is not None:
            return f"≤ {v.umbral_max}"
        return "—"
