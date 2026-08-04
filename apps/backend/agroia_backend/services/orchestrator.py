"""Orquestador híbrido de recomendaciones — ML + Reglas.

Coordina el pipeline completo: recibe solicitud → consulta datos →
invoca modelos ML → aplica reglas → detecta discordancia → ensambla respuesta.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from agroia.errors import InsufficientDataError
from agroia.logging import get_logger

logger = get_logger(__name__)

# ── Días hábiles para SLA de discordancia ──
SLA_DISCORDANCIA_DIAS = 10


@dataclass
class RecommendationRequest:
    """Solicitud de análisis de aptitud."""
    finca_id: str
    cultivo_id: Optional[str] = None
    tenant_id: Optional[str] = None


@dataclass
class RecommendationResult:
    """Resultado completo del pipeline de recomendación."""
    cultivo: str
    clasificacion_upra: str
    confianza: float
    recomendaciones: list[dict] = field(default_factory=list)
    justificacion: dict = field(default_factory=dict)
    advertencia: Optional[str] = None
    discordancia: Optional[dict] = None
    tiempo_respuesta_ms: float = 0.0


class RecommendationOrchestrator:
    """Orquesta el pipeline completo de recomendación."""

    def __init__(
        self,
        db_session,
        soil_adapter=None,
        ml_service=None,
        rules_engine=None,
        justification_service=None,
    ):
        self.db = db_session
        self.soil = soil_adapter
        self.ml = ml_service
        self.rules = rules_engine
        self.justification = justification_service

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

        # ── Paso 2: ML Inference (modo sombra/fallback según disponibilidad) ──
        ml_result = None
        if self.ml:
            try:
                ml_result = await self.ml.predict(soil_dict, request.cultivo_id)
                logger.info("ml_prediction", cultivo=ml_result.get("cultivo"), confianza=ml_result.get("confianza"))
            except Exception as e:
                logger.error("ml_inference_failed", error=str(e))

        # ── Paso 3: Reglas agronómicas ──
        rules_result = await self.rules.evaluate(soil_dict, request.cultivo_id)
        logger.info(
            "rules_result",
            status=rules_result.status,
            violations=len(rules_result.violations),
        )

        # ── Paso 4: Detección de discordancia ──
        discordancia = None
        if ml_result and rules_result.is_blocked:
            cultivo_ml = ml_result.get("cultivo", "desconocido")
            discordancia = {
                "tipo": "ml_vs_reglas",
                "cultivo_ml": cultivo_ml,
                "confianza_ml": ml_result.get("confianza", 0),
                "regla_bloqueante": rules_result.violations[0].accion if rules_result.violations else "N/A",
                "sla_vencimiento": (datetime.utcnow() + timedelta(days=SLA_DISCORDANCIA_DIAS)).isoformat(),
            }
            logger.warning("discordance_detected", **discordancia)

        # ── Paso 5: Ensamblar respuesta ──
        cultivo = ml_result.get("cultivo", "No determinado") if ml_result else "No determinado"
        clasificacion = "Media"  # default; se refina con UPRA en TT-04
        confianza = ml_result.get("confianza", 0.5) if ml_result else 0.5
        advertencia = None
        if confianza < 0.80:
            advertencia = "⚠️ Esta recomendación tiene baja confianza y será revisada por un técnico agrónomo."

        # Generar recomendaciones desde violaciones de reglas
        recomendaciones = []
        for v in rules_result.violations + rules_result.warnings:
            rec = {
                "variable": v.variable,
                "valor_actual": v.valor_actual,
                "rango_ideal": f"[{v.umbral_min} - {v.umbral_max}]",
                "accion": v.accion,
                "prioridad": v.prioridad,
                "fuente": v.fuente,
            }
            recomendaciones.append(rec)

        # Justificación
        justificacion = {
            "resumen": f"Análisis de aptitud para {cultivo}: clasificación {clasificacion}.",
            "variables_analizadas": len(soil_dict),
            "confianza": confianza,
        }

        t_end = datetime.utcnow()
        elapsed_ms = (t_end - t_start).total_seconds() * 1000

        return RecommendationResult(
            cultivo=cultivo,
            clasificacion_upra=clasificacion,
            confianza=confianza,
            recomendaciones=recomendaciones,
            justificacion=justificacion,
            advertencia=advertencia,
            discordancia=discordancia,
            tiempo_respuesta_ms=elapsed_ms,
        )
