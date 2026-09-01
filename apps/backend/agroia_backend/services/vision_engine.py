"""Motor de visión AgroVision — orquestación de inferencia (sección 18).

Jerarquía (sección 13): modelo empaquetado → fallback OpenCV → abstención.
- Si existe un modelo versionado en el registry (AGROIA_VISION_MODEL_DIR) y
  su confianza supera el umbral, responde `estado="model"`.
- Si no hay modelo aplicable o la confianza es baja, responde el fallback
  OpenCV con `estado="preliminary"` (nunca presentado como definitivo).
- Si la imagen no es válida (quality gate) o el motor no puede analizarla,
  responde `estado="abstain"` con motivo (abstención explicada, sección 24).

El resultado siempre incluye la versión exacta del modelo/motor usado.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from agroia.logging import get_logger

from agroia_backend.services.vision_fallback import (
    FUENTE_FALLBACK,
    MODELO_VERSION,
    diagnosticar,
    explicacion_abstencion,
)

logger = get_logger(__name__)

UMBRAL_ABSTENCION = 0.6  # RF-13 / sección 24

_RECOMENDACION_PRELIMINAR = (
    "Diagnóstico visual PRELIMINAR generado por reglas de visión "
    "tradicional (no confirmatorio). Confirma el dictamen con un agrónomo."
)
_RECOMENDACION_ABSTAIN = (
    "No fue posible emitir un diagnóstico visual preliminar con esta foto. "
    "Toma una imagen más nítida, bien iluminada y con la hoja/fruto en foco."
)


def _buscar_modelo(crop_hint: str | None) -> dict | None:
    """Busca un modelo empaquetado aplicable en el registry local.

    Estructura lista para el MLOps de la sección 19; devuelve None mientras
    no exista artefacto publicado."""
    raiz = Path(os.environ.get("AGROIA_VISION_MODEL_DIR", ""))
    if not raiz.is_dir():
        return None
    candidatos = sorted(raiz.glob("*/manifest.json"))
    for manifest_path in candidatos:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if crop_hint and manifest.get("crops") and crop_hint not in manifest.get("crops", []):
            continue
        return manifest
    return None


def _mapear_contrato(resultado: dict[str, Any], crop_hint: str | None) -> dict[str, Any]:
    """Traduce la salida del fallback al contrato público de inferencia."""
    estado = resultado["status"]
    if estado == "abstain":
        plaga = "No determinada"
        confianza = 0.0
        severidad = "desconocida"
        recomendacion = (
            f"{resultado.get('motivo', 'sin_evidencia_suficiente')}. "
            f"{_RECOMENDACION_ABSTAIN}"
        )
        diagnosis = {"label": "unknown", "confidence": 0.0}
    else:
        plaga = resultado.get("diagnosis", "sintomas_compatibles")
        confianza = float(resultado.get("confidence", 0.0))
        severidad = resultado.get("severity", {}).get("label", "unknown")
        recomendacion = _RECOMENDACION_PRELIMINAR
        diagnosis = {"label": plaga, "confidence": confianza}
    return {
        "modelo_version": MODELO_VERSION,
        "estado": estado,
        "crop": {"label": crop_hint or "unknown", "confidence": 1.0 if crop_hint else 0.0},
        "diagnosis": diagnosis,
        "severity": {"label": severidad, "confidence": resultado.get("severity", {}).get("confidence", 0.0)},
        "evidence": resultado.get("evidence", []),
        "explicacion": resultado.get("explicacion")
        or explicacion_abstencion(resultado.get("motivo", "sin_evidencia_suficiente"))
        if estado == "abstain"
        else resultado.get("explicacion", ""),
        "requiere_revision": bool(resultado.get("requires_review", True)),
        # Campos legados del endpoint /analizar-plaga (compatibilidad v3.0).
        "plaga": plaga,
        "confianza": confianza,
        "severidad": severidad,
        "recomendacion": recomendacion,
        "fuente": resultado.get("fuente", FUENTE_FALLBACK),
    }


def diagnosticar_imagen(contenido: bytes, crop_hint: str | None = None) -> dict[str, Any]:
    """Punto de entrada único del motor de visión."""
    manifest = _buscar_modelo(crop_hint)
    if manifest is not None:
        # Punto de integración del modelo empaquetado (sección 19). Mientras
        # no exista artefacto entrenado se delega al fallback.
        logger.info(
            "vision_modelo_no_ejecutable",
            extra_fields={"manifest": manifest.get("model_name")},
        )
    resultado = diagnosticar(contenido, crop_hint)
    if resultado["status"] == "preliminary" and resultado.get("confidence", 0.0) < UMBRAL_ABSTENCION:
        resultado = {
            "status": "abstain",
            "motivo": "confianza_bajo_umbral",
            "confidence": resultado.get("confidence", 0.0),
            "evidence": resultado.get("evidence", []),
            "explicacion": explicacion_abstencion("confianza_bajo_umbral"),
            "requires_review": True,
            "fuente": resultado.get("fuente", FUENTE_FALLBACK),
        }
    contrato = _mapear_contrato(resultado, crop_hint)
    logger.info(
        "vision_diagnostico_generado",
        extra_fields={"estado": contrato["estado"], "crop_hint": crop_hint},
    )
    return contrato
