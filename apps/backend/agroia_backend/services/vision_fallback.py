"""Fallback de visión tradicional (sección 14 de la especificación AgroVision).

Implementa las reglas del fallback OpenCV sobre numpy puro (usa cv2/Pillow
solo para decodificar si están disponibles):
  - Segmentación HSV del follaje y separación de fondo.
  - Clorosis: proporción de píxeles amarillos sobre área verde.
  - Necrosis/manchas: regiones marrón/oscuro con máscaras morfológicas.
  - Textura: desviación estándar local del gris.
  - Área afectada: porcentaje del órgano con lesión.
  - Score: combinación de rasgos con reglas parametrizadas.

NUNCA presenta el resultado como diagnóstico definitivo: todo resultado
lleva `requires_review=True` y `status="preliminary"`; ante foto inválida
o sin hoja devuelve `status="abstain"` con motivo (abstención explicada).
"""

from __future__ import annotations

import io
import json
import os
from typing import Any

import numpy as np

FUENTE_FALLBACK = "agrovision_opencv_v1"
MODELO_VERSION = "agrovision-fallback-1.0.0"

_DEFAULT_CONFIG: dict[str, Any] = {
    "quality_gate": {
        "min_size_px": 64,
        "blur_variance_min": 40.0,
        "min_brightness": 30,
        "max_brightness": 245,
    },
    "fallback": {
        "abstain_confidence": 0.6,
        "severity_thresholds": {
            "none": 0.01,
            "mild": 0.05,
            "moderate": 0.15,
            "severe": 0.35,
            "critical": 0.55,
        },
    },
}

# Reglas de compatibilidad de síntomas por cultivo (parametrizables).
_DIAGNOSIS_RULES = [
    ("coffee", "coffee_rust", {"necrosis": 0.02}),
    ("coffee", "coffee_cercospora", {"necrosis": 0.05}),
    ("cacao", "cocoa_black_pod", {"necrosis": 0.05}),
    ("cacao", "cocoa_monilia_m1", {"necrosis": 0.01}),
]


def _config() -> dict[str, Any]:
    config = json.loads(json.dumps(_DEFAULT_CONFIG))
    path = os.environ.get("AGROIA_VISION_CONFIG")
    if path and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                superpuesto = json.load(fh)
            config["quality_gate"].update(superpuesto.get("quality_gate", {}))
            config["fallback"].update(superpuesto.get("fallback", {}))
        except Exception:  # noqa: BLE001
            pass
    return config


def decodificar(contenido: bytes) -> np.ndarray | None:
    """Decodifica bytes a RGB uint8. cv2 > Pillow > None."""
    try:
        import cv2  # type: ignore

        img = cv2.imdecode(np.frombuffer(contenido, np.uint8), cv2.IMREAD_COLOR)
        if img is not None and img.size:
            return img[:, :, ::-1]  # BGR → RGB
    except Exception:  # noqa: BLE001
        pass
    try:
        from PIL import Image  # type: ignore

        with Image.open(io.BytesIO(contenido)) as im:
            return np.asarray(im.convert("RGB"))
    except Exception:  # noqa: BLE001
        return None


def rgb_a_hsv(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convierte RGB uint8 a (H 0-360, S 0-1, V 0-1) sin OpenCV."""
    f = rgb.astype(np.float64) / 255.0
    mx = f.max(axis=2)
    mn = f.min(axis=2)
    df = mx - mn
    eps = 1e-9
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    h = np.zeros_like(mx)
    seg = df > eps
    rojo = seg & (mx == r)
    verde = seg & (mx == g)
    azul = seg & (mx == b)
    h[rojo] = 60.0 * ((g[rojo] - b[rojo]) / np.maximum(df[rojo], eps)) % 360.0
    h[verde] = 60.0 * ((b[verde] - r[verde]) / np.maximum(df[verde], eps)) + 120.0
    h[azul] = 60.0 * ((r[azul] - g[azul]) / np.maximum(df[azul], eps)) + 240.0
    h[h < 0] += 360.0
    s = np.where(mx > eps, df / np.maximum(mx, eps), 0.0)
    return h, s, mx


def _laplaciano_var(gris: np.ndarray) -> float:
    """Varianza del Laplaciano (nitidez) con numpy puro."""
    g = gris.astype(np.float64)
    if g.ndim == 3:
        g = g.mean(axis=2)
    if g.shape[0] < 3 or g.shape[1] < 3:
        return 0.0
    lap = (
        4 * g[1:-1, 1:-1]
        - g[:-2, 1:-1]
        - g[2:, 1:-1]
        - g[1:-1, :-2]
        - g[1:-1, 2:]
    )
    return float(lap.var())


def quality_gate(rgb: np.ndarray) -> dict[str, Any]:
    """Quality gate (sección 13): tamaño, nitidez, exposición, presencia de hoja."""
    config = _config()["quality_gate"]
    alto, ancho = rgb.shape[:2]
    brillo = float(rgb.mean())
    nitidez = _laplaciano_var(rgb)
    h, s, v = rgb_a_hsv(rgb)
    verde = (h >= 35) & (h <= 170) & (s >= 0.20) & (v >= 0.08)
    ratio_hoja = float(verde.mean())
    motivos: list[str] = []
    if min(alto, ancho) < config["min_size_px"]:
        motivos.append("tamano_insuficiente")
    if nitidez < config["blur_variance_min"]:
        motivos.append("imagen_borrosa")
    if brillo < config["min_brightness"]:
        motivos.append("imagen_oscura")
    if brillo > config["max_brightness"]:
        motivos.append("sobreexpuesta")
    if ratio_hoja < 0.03:
        motivos.append("hoja_no_detectada")
    return {
        "ok": not motivos,
        "motivos": motivos,
        "tamano": [int(alto), int(ancho)],
        "brillo": round(brillo, 1),
        "nitidez": round(nitidez, 1),
        "ratio_hoja": round(ratio_hoja, 3),
    }


def _severidad(afectada: float) -> str:
    umbrales = _config()["fallback"]["severity_thresholds"]
    if afectada < umbrales["none"]:
        return "none"
    if afectada < umbrales["mild"]:
        return "mild"
    if afectada < umbrales["moderate"]:
        return "moderate"
    if afectada < umbrales["severe"]:
        return "severe"
    if afectada < umbrales["critical"]:
        return "critical"
    return "critical"


# ── Explicación en lenguaje humano (para el agricultor) ──

_SEVERIDAD_PALABRAS = {
    "none": "sin daño aparente",
    "mild": "un daño leve",
    "moderate": "un daño moderado",
    "severe": "un daño fuerte",
    "critical": "un daño muy severo",
}

_MOTIVOS_PALABRAS = {
    "tamano_insuficiente": "la foto es muy pequeña",
    "imagen_borrosa": "la foto salió movida o desenfocada",
    "imagen_oscura": "la foto está muy oscura",
    "sobreexpuesta": "la foto está muy clara (quemada por la luz)",
    "hoja_no_detectada": "no se alcanza a ver la hoja o el fruto",
    "confianza_bajo_umbral": "los síntomas detectados son muy débiles",
    "imagen_no_decodificable": "el archivo no se pudo leer como imagen",
}

_CAUSAS_POR_DIAGNOSTICO = {
    "sin_sintomas_visibles": (
        "La hoja o fruto se ve sano: no se detectaron manchas importantes. "
        "El cultivo podría estar bien, o el síntoma apenas está comenzando. "
        "Vuelva a revisar la planta en unos días."
    ),
    "clorosis_compatible": (
        "La coloración amarillenta (clorosis) suele aparecer por falta de "
        "nutrientes como nitrógeno, hierro o magnesio, por exceso o escasez "
        "de riego, por daño en las raíces, o por el inicio de una enfermedad. "
        "Compare con el análisis de suelo y las fertilizaciones recientes "
        "para acotar la causa."
    ),
    "necrosis_compatible": (
        "Las manchas oscuras o secas suelen deberse a hongos o bacterias, a "
        "quemaduras por sol o por productos mal aplicados, o a una falta de "
        "agua prolongada. Revise el historial de aplicaciones y el riego de "
        "los últimos días."
    ),
    "coffee_rust_compatible": (
        "En café, manchas con necrosis en la hoja son compatibles con roya. "
        "La roya avanza en ambientes húmedos y con poca ventilación; revise "
        "el manejo preventivo y el sombrío del cultivo."
    ),
    "coffee_cercospora_compatible": (
        "En café, manchas redondeadas con necrosis pueden ser cercospora "
        "(ojo de gallo), favorecida por la humedad y el exceso de sombra. "
        "Mejore la aireación y consulte el plan sanitario."
    ),
    "cocoa_black_pod_compatible": (
        "En cacao, manchas oscuras sobre la mazorca son compatibles con "
        "pudrición (monilia o phytophthora). Retire los frutos enfermos, "
        "evite la humedad estancada y no deje mazorcas en el suelo."
    ),
    "cocoa_monilia_m1_compatible": (
        "En cacao, los abultamientos o bultos en la mazorca son compatibles "
        "con monilia en etapa temprana. Retire y entierre las mazorcas "
        "afectadas para que el hongo no se propague."
    ),
}


def _explicacion_preliminar(metricas: dict[str, Any], diagnostico: str) -> str:
    """Describe en palabras sencillas lo que vio el análisis y qué pudo causarlo."""
    porc_hoja = round(metricas.get("ratio_hoja", 0.0) * 100, 1)
    porc_clorosis = round(metricas.get("clorosis", 0.0) * 100, 1)
    porc_necrosis = round(metricas.get("necrosis", 0.0) * 100, 1)
    porc_afectada = round(metricas.get("area_afectada", 0.0) * 100, 1)
    textura = metricas.get("textura", 0.0)
    superficie = (
        "lisa"
        if textura < 15
        else "algo rugosa"
        if textura < 30
        else "muy rugosa"
    )
    severidad_palabras = _SEVERIDAD_PALABRAS.get(
        metricas.get("severidad", "none"), "un daño leve"
    )
    causas = _CAUSAS_POR_DIAGNOSTICO.get(
        diagnostico,
        "Las señales pueden venir de una enfermedad, de plagas, de falta de "
        "nutrientes o de estrés por agua o clima. Revise la planta completa "
        "y las condiciones del lote para identificar el origen.",
    )
    return (
        f"En la foto, la hoja o fruto ocupa el {porc_hoja}% de la imagen. "
        f"El análisis encontró que el {porc_clorosis}% de esa superficie está "
        f"amarillenta (clorosis), el {porc_necrosis}% tiene manchas oscuras o "
        f"secas (necrosis) y en total el {porc_afectada}% del área presenta "
        f"algún daño; la textura de la superficie se ve {superficie}. Esto "
        f"corresponde a {severidad_palabras}. "
        f"¿Qué pudo llevar la mata a ese estado? {causas} "
        f"Este es un análisis visual preliminar hecho con reglas de visión: "
        f"no reemplaza el dictamen de un agrónomo ni los análisis de suelo o "
        f"de laboratorio."
    )


def explicacion_abstencion(motivo: str) -> str:
    """Explicación humana de por qué el análisis se abstuvo y qué hacer."""
    razones = ";".join(
        _MOTIVOS_PALABRAS.get(m.strip(), m.strip()) for m in (motivo or "").split(";") if m.strip()
    ) or "la imagen no es apta para el análisis"
    return (
        f"El análisis no se pudo hacer porque {razones}. Tome la foto de "
        f"cerca, con buena luz, sin mover la cámara y con la hoja o el fruto "
        f"bien enfocado, y vuelva a intentarlo."
    )


def analizar_sintomas(rgb: np.ndarray, crop_hint: str | None = None) -> dict[str, Any]:
    """Análisis HSV de clorosis, necrosis, textura y área afectada."""
    h, s, v = rgb_a_hsv(rgb)
    verde = (h >= 35) & (h <= 170) & (s >= 0.20) & (v >= 0.08)
    hoja = verde
    if hoja.sum() == 0:
        hoja = np.ones(h.shape, dtype=bool)
    clorosis = hoja & (h >= 15) & (h <= 70) & (s >= 0.30) & (v >= 0.30)
    necrosis = hoja & (
        ((v < 0.35) & (s < 0.85)) | ((h < 35) & (s >= 0.40) & (v < 0.65))
    )
    area = float(hoja.sum())
    ratio_clorosis = float(clorosis.sum()) / max(area, 1)
    ratio_necrosis = float(necrosis.sum()) / max(area, 1)
    afectada = min(1.0, ratio_clorosis + ratio_necrosis)
    gris = rgb.mean(axis=2)
    textura = float(gris[hoja].std()) if hoja.sum() else 0.0
    return {
        "ratio_hoja": float(verde.mean()),
        "clorosis": round(ratio_clorosis, 4),
        "necrosis": round(ratio_necrosis, 4),
        "area_afectada": round(afectada, 4),
        "textura": round(textura, 2),
        "severidad": _severidad(afectada),
    }


def _diagnostico(metricas: dict[str, Any], crop_hint: str | None) -> str:
    necrosis = metricas["necrosis"]
    afectada = metricas["area_afectada"]
    if afectada < 0.01:
        return "sin_sintomas_visibles"
    if crop_hint:
        crop_n = crop_hint.strip().lower()
        for crop, clase, requisitos in _DIAGNOSIS_RULES:
            if crop_n == crop and necrosis >= requisitos.get("necrosis", 1.0):
                return f"{clase}_compatible"
    if metricas["clorosis"] >= necrosis:
        return "clorosis_compatible"
    return "necrosis_compatible"


def _confianza(metricas: dict[str, Any], nitidez: float, brillo: float) -> float:
    config = _config()
    conf = 0.80
    conf += min(0.10, max(0.0, metricas["ratio_hoja"] - 0.10) * 0.5)
    if nitidez < config["quality_gate"]["blur_variance_min"] * 2:
        conf -= 0.15
    if brillo < config["quality_gate"]["min_brightness"] + 10:
        conf -= 0.05
    if metricas["area_afectada"] < 0.01:
        conf -= 0.10
    return round(min(0.95, max(0.05, conf)), 2)


def diagnosticar(
    contenido: bytes, crop_hint: str | None = None
) -> dict[str, Any]:
    """Contrato de salida del fallback (sección 14)."""
    rgb = decodificar(contenido)
    if rgb is None:
        motivo = "imagen_no_decodificable"
        return {
            "status": "abstain",
            "motivo": motivo,
            "confidence": 0.0,
            "evidence": [],
            "explicacion": explicacion_abstencion(motivo),
            "requires_review": True,
            "fuente": FUENTE_FALLBACK,
        }
    puerta = quality_gate(rgb)
    if not puerta["ok"]:
        motivo = ";".join(puerta["motivos"])
        return {
            "status": "abstain",
            "motivo": motivo,
            "confidence": 0.0,
            "quality_gate": puerta,
            "evidence": [
                f"tamano {puerta['tamano'][0]}x{puerta['tamano'][1]}px",
                f"nitidez {puerta['nitidez']}",
                f"brillo {puerta['brillo']}",
            ],
            "explicacion": explicacion_abstencion(motivo),
            "requires_review": True,
            "fuente": FUENTE_FALLBACK,
        }
    metricas = analizar_sintomas(rgb, crop_hint)
    diagnostico = _diagnostico(metricas, crop_hint)
    confianza = _confianza(metricas, puerta["nitidez"], puerta["brillo"])
    evidencia = [
        f"hoja segmentada {round(metricas['ratio_hoja'] * 100, 1)}% de la imagen",
        f"clorosis {round(metricas['clorosis'] * 100, 1)}%",
        f"necrosis {round(metricas['necrosis'] * 100, 1)}%",
        f"area_afectada {round(metricas['area_afectada'] * 100, 1)}%",
        f"textura {metricas['textura']}",
    ]
    return {
        "status": "preliminary",
        "diagnosis": diagnostico,
        "confidence": confianza,
        "severity": {"label": metricas["severidad"], "confidence": 0.7},
        "evidence": evidencia,
        "explicacion": _explicacion_preliminar(metricas, diagnostico),
        "requires_review": True,
        "fuente": FUENTE_FALLBACK,
    }
