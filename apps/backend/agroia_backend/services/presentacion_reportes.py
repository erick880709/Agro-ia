"""Presentación de calidad y evidencia en reportes (Épica E7, HU-10).

Insignias de calidad, insignias de grado de evidencia, leyenda metodológica y
resumen de una línea ("confiable / indicativo / sin datos") para no sobrecargar
al usuario final.
"""

from __future__ import annotations

from agroia_backend.services.grados_evidencia import (
    GRADO_A,
    GRADO_B,
    GRADO_C,
    GRADO_D,
)

# Insignia visual por grado de evidencia.
INSIGNIA_GRADO = {
    GRADO_A: {"etiqueta": "Laboratorio", "icono": "🧪", "color": "verde"},
    GRADO_B: {"etiqueta": "Sensor calibrado", "icono": "📡", "color": "azul"},
    GRADO_C: {"etiqueta": "Sensor indicativo", "icono": "📡", "color": "amarillo"},
    GRADO_D: {"etiqueta": "Estimado (SIG/modelo)", "icono": "🗺️", "color": "gris"},
}

# Insignia por estado de calidad.
INSIGNIA_CALIDAD = {
    "valida": {"etiqueta": "Válida", "icono": "✅", "color": "verde"},
    "valida_con_advertencia": {"etiqueta": "Válida con advertencia", "icono": "⚠️", "color": "amarillo"},
    "bajo_limite_deteccion": {"etiqueta": "Bajo límite de detección", "icono": "🔽", "color": "gris"},
    "saturada": {"etiqueta": "Saturada", "icono": "🔴", "color": "rojo"},
    "fuera_de_rango": {"etiqueta": "Fuera de rango", "icono": "🔴", "color": "rojo"},
    "sonda_fuera_de_suelo": {"etiqueta": "Sonda fuera del suelo", "icono": "🔴", "color": "rojo"},
    "humedad_insuficiente": {"etiqueta": "Humedad insuficiente", "icono": "💧", "color": "rojo"},
    "no_calibrada": {"etiqueta": "Sin calibrar", "icono": "⚙️", "color": "amarillo"},
    "estimado_sig": {"etiqueta": "Estimado SIG", "icono": "🗺️", "color": "gris"},
    "invalidada": {"etiqueta": "Invalidada", "icono": "🚫", "color": "rojo"},
}

LEYENDA_METODOLOGICA = (
    "El sensor JXBS-3001-NPK-RS mide 7 variables (pH, humedad VWC, temperatura, "
    "CE, N, P y K) con calibración de fábrica. NO mide materia orgánica, CIC, "
    "textura, Ca, Mg, Al, S ni micronutrientes. El pH y la CE son confiables con "
    "suelo húmedo; N, P y K son indicativos (exactitud ±40 mg/kg) hasta calibrar "
    "contra laboratorio. Sin análisis de suelo no se emiten dosis de fertilización."
)


def insignia_grado(grado: str | None) -> dict | None:
    if grado is None:
        return None
    return INSIGNIA_GRADO.get(grado)


def insignia_calidad(estado: str | None) -> dict:
    if estado is None:
        return {"etiqueta": "Previa a la regla de calidad", "icono": "❔", "color": "gris"}
    return INSIGNIA_CALIDAD.get(estado, {"etiqueta": estado, "icono": "❔", "color": "gris"})


def resumen_una_linea(grados: dict[str, dict] | None, estados: list[str] | None = None) -> dict:
    """Resumen de una línea: 'confiable / indicativo / sin datos' (HU-10)."""
    if not grados:
        return {"resumen": "sin datos", "icono": "⚪", "detalle": "No hay datos de suelo."}
    estados = estados or []
    if any(e in ("saturada", "fuera_de_rango", "sonda_fuera_de_suelo", "invalidada")
           for e in estados):
        return {"resumen": "sin datos confiables", "icono": "🔴",
                "detalle": "Hay lecturas excluidas por calidad."}

    grados_presentes = {info["grado"] for info in grados.values() if isinstance(info, dict)}
    if grados_presentes & {GRADO_A, GRADO_B}:
        return {"resumen": "confiable", "icono": "🟢",
                "detalle": "Datos de laboratorio o sensor calibrado."}
    if grados_presentes & {GRADO_C, GRADO_D}:
        return {"resumen": "indicativo", "icono": "🟡",
                "detalle": "Datos indicativos; priorizar muestreo de laboratorio."}
    return {"resumen": "sin datos", "icono": "⚪", "detalle": "Sin grados de evidencia."}


def serie_con_incertidumbre(lecturas: list[dict], eventos: list[dict] | None = None) -> dict:
    """Serie de tiempo con banda de incertidumbre (HU-11).

    Devuelve puntos con valor, incertidumbre y excluidos en gris, y marcadores
    de eventos (riego, fertilización, lluvia).
    """
    puntos = []
    for r in lecturas:
        excluida = r.get("calidad") in (
            "saturada", "fuera_de_rango", "sonda_fuera_de_suelo",
            "humedad_insuficiente", "invalidada",
        )
        puntos.append({
            "ts": r.get("ts"),
            "valor": r.get("valor"),
            "incertidumbre": r.get("incertidumbre"),
            "calidad": r.get("calidad"),
            "excluida": excluida,
        })
    return {
        "puntos": puntos,
        "eventos": eventos or [],
        "banda_incertidumbre": True,
    }
