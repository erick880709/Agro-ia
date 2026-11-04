"""Incertidumbre por variable del sensor (Épica E3, RF-011 / Anexo A).

Cada variable del JXBS-3001-NPK-RS tiene una exactitud declarada (±). La
incertidumbre estándar se calcula con criterio de distribución rectangular:
`exactitud / √3`. Para la humedad se usa la exactitud por tramo (±3 % hasta
53 %, ±5 % por encima). La CE no tiene exactitud declarada por el fabricante.

Los valores son los iniciales del Anexo A y son parametrizables (RF-087).
"""

from __future__ import annotations

from math import sqrt

# Exactitud (±) por variable (clave canónica de SensorReading).
EXACTITUDES: dict[str, float | None] = {
    "ph": 0.3,
    "temperatura_suelo": 0.5,
    "nitrogeno": 40.0,   # 2 % del fondo de escala (1999 mg/kg)
    "fosforo": 40.0,
    "potasio": 40.0,
    "conductividad_electrica": None,  # no especificada por el fabricante
    "humedad": None,  # por tramo (ver exactitud_humedad)
}

# Humedad: exactitud por tramo (Anexo A).
HUMEDAD_TRAMOS: tuple[tuple[float, float], ...] = (
    (53.0, 3.0),   # ≤ 53 % → ±3 %
    (float("inf"), 5.0),  # > 53 % → ±5 %
)

# Variables NPK (redondeo a decenas de mg/kg en la presentación, RF-013).
VARIABLES_NPK = ("nitrogeno", "fosforo", "potasio")


def exactitud_humedad(valor: float | None) -> float | None:
    """Exactitud de humedad según el tramo del valor medido."""
    if valor is None:
        return None
    for limite, exact in HUMEDAD_TRAMOS:
        if valor <= limite:
            return exact
    return None


def exactitud(variable: str, valor: float | None = None) -> float | None:
    """Exactitud (±) de una variable; para humedad depende del valor."""
    if variable == "humedad":
        return exactitud_humedad(valor)
    return EXACTITUDES.get(variable)


def incertidumbre_estandar(variable: str, valor: float | None = None) -> float | None:
    """Incertidumbre estándar con distribución rectangular: exactitud / √3."""
    ex = exactitud(variable, valor)
    if ex is None:
        return None
    return round(ex / sqrt(3), 4)


def incertidumbres_lectura(payload: dict) -> dict | None:
    """Mapa variable → incertidumbre estándar para las variables medidas.

    Solo incluye las variables del sensor con exactitud declarada; ignora
    claves no numéricas (textura, valor_crudo) y telemetría.
    """
    salida: dict = {}
    for variable in EXACTITUDES:
        valor = payload.get(variable)
        if valor is None:
            continue
        try:
            numerico = float(valor)
        except (TypeError, ValueError):
            continue
        u = incertidumbre_estandar(variable, numerico)
        if u is not None:
            salida[variable] = u
    return salida or None


def redondeo_presentacion(variable: str) -> tuple[int, float | None]:
    """Precisión de presentación (RF-013): (decimales, paso).

    - pH a 0,1; CE a 0,01 dS/m; humedad a 1 %; N/P/K a decenas de mg/kg.
    - Devuelve (decimales, paso_de_redondeo) donde paso None = redondear
      con `round(valor, decimales)`.
    """
    if variable == "ph":
        return (1, None)
    if variable == "conductividad_electrica":
        return (2, None)
    if variable == "humedad":
        return (0, None)
    if variable in VARIABLES_NPK:
        return (0, 10.0)
    if variable == "temperatura_suelo":
        return (1, None)
    return (2, None)


def formatear_valor(variable: str, valor: float) -> dict:
    """Presenta un valor con su incertidumbre y redondeo (HU-03 / RF-013).

    Devuelve {variable, valor, redondeado, unidad, incertidumbre}. El usuario
    final ve siempre el intervalo, no solo el valor puntual.
    """
    decimales, paso = redondeo_presentacion(variable)
    if paso is not None:
        redondeado = round(valor / paso) * paso
    else:
        redondeado = round(valor, decimales)
    return {
        "variable": variable,
        "valor": valor,
        "redondeado": redondeado,
        "unidad": _UNIDADES.get(variable, ""),
        "incertidumbre": incertidumbre_estandar(variable, valor),
    }


_UNIDADES = {
    "ph": "",
    "temperatura_suelo": "°C",
    "humedad": "%",
    "nitrogeno": "mg/kg",
    "fosforo": "mg/kg",
    "potasio": "mg/kg",
    "conductividad_electrica": "dS/m",
}
