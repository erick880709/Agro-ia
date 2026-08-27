"""Orquestador híbrido de recomendaciones — ML + Reglas.

Coordina el pipeline completo: recibe solicitud → consulta datos →
invoca modelos ML → aplica reglas → detecta discordancia → ensambla respuesta.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from agroia.errors import InsufficientDataError
from agroia.logging import get_logger

logger = get_logger(__name__)

# ── Días hábiles para SLA de discordancia ──
SLA_DISCORDANCIA_DIAS = 10


@dataclass
class RecommendationRequest:
    """Solicitud de análisis de aptitud."""
    finca_id: str
    cultivo_id: str | None = None
    tenant_id: str | None = None


@dataclass
class RecommendationResult:
    """Resultado completo del pipeline de recomendación."""
    cultivo: str
    clasificacion_upra: str
    confianza: float
    recomendaciones: list[dict] = field(default_factory=list)
    justificacion: dict = field(default_factory=dict)
    advertencia: str | None = None
    discordancia: dict | None = None
    tiempo_respuesta_ms: float = 0.0
    sugerencias_cultivos: list[dict] = field(default_factory=list)
    modo: str = "analizar_cultivo"


class RecommendationOrchestrator:
    """Orquesta el pipeline completo de recomendación."""

    def __init__(
        self,
        db_session,
        soil_adapter=None,
        ml_service=None,
        rules_engine=None,
        justification_service=None,
        aptitud_service=None,
    ):
        self.db = db_session
        self.soil = soil_adapter
        self.ml = ml_service
        self.rules = rules_engine
        self.justification = justification_service
        self.aptitud = aptitud_service

    async def analyze(self, request: RecommendationRequest) -> RecommendationResult:
        """Ejecuta el pipeline completo de recomendación.

        Args:
            request: Solicitud con finca_id y cultivo_id opcional

        Returns:
            RecommendationResult con la recomendación completa

        Raises:
            InsufficientDataError: si faltan variables bloqueantes
        """
        t_start = datetime.utcnow()

        # ── Paso 1: Obtener datos de suelo ──
        soil_data = await self.soil.get_latest(request.finca_id)
        if soil_data is None or not soil_data.has_sufficient_data:
            missing = soil_data.missing_blocking if soil_data else ["ph", "nitrogeno", "fosforo", "potasio"]
            logger.warning("insufficient_data", finca_id=request.finca_id, missing=missing)
            raise InsufficientDataError(missing)

        soil_dict = soil_data.to_dict()
        logger.info("soil_data_loaded", finca_id=request.finca_id, vars=len(soil_dict))

        # ── Advertencias de calidad de datos (brechas G3/G4) ──
        advertencias_datos = []
        if soil_data.calidad == "npk_no_calibrado":
            advertencias_datos.append(
                "⚠️ Lecturas NPK sin calibrar: valide con análisis de laboratorio "
                "antes de aplicar fertilizantes."
            )
        if soil_data.missing_non_blocking:
            advertencias_datos.append(
                "⚠️ Recomendación parcial: faltan variables ("
                + ", ".join(soil_data.missing_non_blocking) + ")."
            )
        advertencia_datos = " ".join(advertencias_datos) or None

        # ── Paso 2: Ramificación por caso de uso ──
        if request.cultivo_id is None:
            # UC1: no hay cultivo sembrado → recomendar qué sembrar
            return await self._recomendar_cultivos(soil_dict, t_start, advertencia_datos)

        # UC2: hay cultivo sembrado → diagnosticar qué falta/sobra
        return await self._analizar_cultivo(request, soil_dict, t_start, advertencia_datos)

    async def _recomendar_cultivos(
        self, soil_dict: dict, t_start: datetime, advertencia_datos: str | None = None
    ) -> "RecommendationResult":
        """UC1: puntúa todos los cultivos y recomienda los más aptos."""
        if self.aptitud is None:
            raise RuntimeError("AptitudService no configurado en el orquestador")

        sugerencias = await self.aptitud.recommend_crops(soil_dict, top_n=5)
        top = sugerencias[0] if sugerencias else None

        cultivo = top["cultivo"] if top else "No determinado"
        clasificacion = top["clasificacion"] if top else "No apta"
        confianza = top["confianza"] if top else 0.0
        recomendaciones = top.get("ajustes", []) if top else []

        advertencia = None
        if not sugerencias:
            advertencia = (
                "⚠️ No hay cultivos evaluables: verifique que las reglas agronómicas "
                "estén cargadas (python load_seeds.py)."
            )
        elif confianza < 0.80:
            advertencia = (
                "⚠️ Esta recomendación tiene baja confianza y será revisada por un "
                "técnico agrónomo."
            )
        advertencia = self._combinar_advertencias(advertencia, advertencia_datos)

        justificacion = {
            "resumen": f"Recomendación sin siembra previa: {cultivo} ({clasificacion}).",
            "variables_analizadas": len(soil_dict),
            "cultivos_evaluados": len(sugerencias),
            "confianza": confianza,
        }

        elapsed_ms = (datetime.utcnow() - t_start).total_seconds() * 1000
        return RecommendationResult(
            cultivo=cultivo,
            clasificacion_upra=clasificacion,
            confianza=confianza,
            recomendaciones=recomendaciones,
            justificacion=justificacion,
            advertencia=advertencia,
            discordancia=None,
            tiempo_respuesta_ms=elapsed_ms,
            sugerencias_cultivos=sugerencias,
            modo="recomendar_cultivos",
        )

    async def _analizar_cultivo(
        self,
        request: RecommendationRequest,
        soil_dict: dict,
        t_start: datetime,
        advertencia_datos: str | None = None,
    ) -> "RecommendationResult":
        """UC2: evalúa el suelo contra las reglas del cultivo sembrado."""
        from sqlalchemy import select

        from agroia_backend.models.cultivo import Cultivo

        # ── Nombre del cultivo objetivo ──
        nombre_cultivo = request.cultivo_id
        try:
            cultivo_uuid = uuid.UUID(str(request.cultivo_id))
            cultivo_obj = (
                await self.db.execute(
                    select(Cultivo).where(Cultivo.id == cultivo_uuid)
                )
            ).scalar_one_or_none()
            if cultivo_obj is not None:
                nombre_cultivo = cultivo_obj.nombre
        except ValueError:
            pass  # cultivo_id no es UUID válido; se usa tal cual

        # ── ML Inference (modo sombra; no afecta la respuesta si falla) ──
        ml_result = None
        if self.ml:
            try:
                ml_result = await self.ml.predict(soil_dict, request.cultivo_id)
                logger.info(
                    "ml_prediction",
                    cultivo=ml_result.get("cultivo"),
                    confianza=ml_result.get("confianza"),
                )
            except Exception as e:
                logger.error("ml_inference_failed", error=str(e))

        # ── Reglas agronómicas ──
        rules_result = await self.rules.evaluate(soil_dict, request.cultivo_id)
        logger.info(
            "rules_result",
            status=rules_result.status,
            violations=len(rules_result.violations),
            warnings=len(rules_result.warnings),
        )

        # ── Detección de discordancia ML vs reglas (solo si ML activo) ──
        discordancia = None
        if ml_result and rules_result.is_blocked:
            cultivo_ml = ml_result.get("cultivo", "desconocido")
            discordancia = {
                "tipo": "ml_vs_reglas",
                "cultivo_ml": cultivo_ml,
                "confianza_ml": ml_result.get("confianza", 0),
                "regla_bloqueante": (
                    rules_result.violations[0].accion
                    if rules_result.violations else "N/A"
                ),
                "sla_vencimiento": (
                    datetime.utcnow() + timedelta(days=SLA_DISCORDANCIA_DIAS)
                ).isoformat(),
            }
            logger.warning("discordance_detected", **discordancia)

        # ── Clasificación UPRA a partir del resultado de reglas ──
        if rules_result.is_blocked:
            clasificacion = "No apta"
        elif rules_result.has_violations:
            clasificacion = "Moderadamente apta"
        else:
            clasificacion = "Apta"

        # ── Recomendaciones de qué falta / qué sobra ──
        recomendaciones = []
        for v in rules_result.violations + rules_result.warnings:
            recomendaciones.append({
                "variable": v.variable,
                "estado": self._clasificar_estado(v),
                "valor_actual": v.valor_actual,
                "rango_ideal": self._formatear_rango(v),
                "accion": v.accion,
                "prioridad": v.prioridad,
                "fuente": v.fuente,
            })

        # ── Confianza en función del cumplimiento de reglas ──
        penalizacion = len(rules_result.violations) * 0.20 + len(rules_result.warnings) * 0.05
        confianza = round(max(0.05, min(0.99, 1.0 - penalizacion)), 3)

        advertencia = None
        if rules_result.applied_rules == 0:
            advertencia = (
                "⚠️ No hay reglas agronómicas configuradas para este cultivo. "
                "Ejecute python load_seeds.py."
            )
        elif confianza < 0.80:
            advertencia = (
                "⚠️ Esta recomendación tiene baja confianza y será revisada por un "
                "técnico agrónomo."
            )
        advertencia = self._combinar_advertencias(advertencia, advertencia_datos)

        faltantes = [r for r in recomendaciones if r["estado"] == "DEFICIT"]
        excesos = [r for r in recomendaciones if r["estado"] == "EXCESO"]
        justificacion = {
            "resumen": (
                f"Análisis de aptitud para {nombre_cultivo}: clasificación {clasificacion}."
            ),
            "variables_analizadas": len(soil_dict),
            "reglas_aplicadas": rules_result.applied_rules,
            "faltantes": len(faltantes),
            "excesos": len(excesos),
            "confianza": confianza,
        }

        elapsed_ms = (datetime.utcnow() - t_start).total_seconds() * 1000
        return RecommendationResult(
            cultivo=nombre_cultivo,
            clasificacion_upra=clasificacion,
            confianza=confianza,
            recomendaciones=recomendaciones,
            justificacion=justificacion,
            advertencia=advertencia,
            discordancia=discordancia,
            tiempo_respuesta_ms=elapsed_ms,
            sugerencias_cultivos=[],
            modo="analizar_cultivo",
        )

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
    def _combinar_advertencias(
        principal: str | None, datos: str | None
    ) -> str | None:
        """Combina la advertencia del análisis con las de calidad de datos."""
        if principal and datos:
            return f"{principal} {datos}"
        return principal or datos

    @staticmethod
    def _formatear_rango(v) -> str:
        if v.umbral_min is not None and v.umbral_max is not None:
            return f"[{v.umbral_min} - {v.umbral_max}]"
        if v.umbral_min is not None:
            return f"≥ {v.umbral_min}"
        if v.umbral_max is not None:
            return f"≤ {v.umbral_max}"
        return "—"
