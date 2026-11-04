"""Calibración local del sensor (Épica E4, RF-015/016/018/019).

- Regresión lineal por dispositivo, variable y unidad de suelo, con n, R²,
  RMSE y sesgo (sustituye el factor único).
- Capa de equivalencia sensor ↔ laboratorio: las reglas se evalúan en la
  unidad del laboratorio; sin calibración vigente, la variable queda en
  **grado C** (indicativa) y no alimenta clasificaciones definitivas.
"""

from __future__ import annotations

from datetime import date
from statistics import fmean

# Variables que requieren calibración para interpretarse en unidad de laboratorio.
VARIABLES_EQUIVALENCIA = {
    "nitrogeno": "N (desde MO, Kjeldahl)",
    "fosforo": "P (Bray II)",
    "potasio": "K intercambiable (cmol(+)/kg)",
    "humedad": "Humedad gravimétrica × densidad aparente",
    "conductividad_electrica": "CE 1:5 / CEe",
}

# Suelos excluidos de la calibración de fábrica de humedad (H-05 / RF-023).
SUELOS_HUMEDAD_NO_APLICABLE = {"arenoso", "salino"}


def regresion_lineal(xs: list[float], ys: list[float]) -> dict | None:
    """Regresión lineal simple y = a·x + b, con n, R², RMSE y sesgo.

    Devuelve None si no hay suficientes puntos (n < 2) o varianza nula en x.
    """
    pares = [(float(x), float(y)) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pares)
    if n < 2:
        return None

    xm = fmean(p[0] for p in pares)
    ym = fmean(p[1] for p in pares)
    sxx = sum((x - xm) ** 2 for x, _ in pares)
    if sxx == 0:
        return None

    sxy = sum((x - xm) * (y - ym) for x, y in pares)
    pendiente = sxy / sxx
    intercepto = ym - pendiente * xm

    # R²
    sst = sum((y - ym) ** 2 for _, y in pares)
    sse = sum((y - (pendiente * x + intercepto)) ** 2 for x, y in pares)
    r2 = 1.0 - (sse / sst) if sst > 0 else None

    # RMSE (error típico de la regresión)
    rmse = (sse / n) ** 0.5

    # Sesgo medio (laboratorio - predicho)
    sesgo = fmean((y - (pendiente * x + intercepto)) for x, y in pares)

    return {
        "pendiente": round(pendiente, 6),
        "intercepto": round(intercepto, 6),
        "n": n,
        "r2": round(r2, 6) if r2 is not None else None,
        "rmse": round(rmse, 6),
        "sesgo": round(sesgo, 6),
    }


def aplicar_calibracion_lineal(valor: float, pendiente: float, intercepto: float) -> float:
    """Convierte un valor del sensor a la unidad de laboratorio (RF-016)."""
    return round(valor * pendiente + intercepto, 4)


def calibracion_vigente(calibraciones: list[dict], hoy: date | None = None) -> dict | None:
    """Devuelve la calibración activa y vigente más reciente (o None)."""
    hoy = hoy or date.today()
    vigentes = [
        c for c in calibraciones
        if c.get("activa", True)
        and (c.get("vigencia") is None or c["vigencia"] >= hoy)
    ]
    if not vigentes:
        return None
    return max(vigentes, key=lambda c: c.get("created_at") or date.min)


def equivalente_laboratorio(
    variable: str,
    valor: float | None,
    calibraciones: list[dict],
    hoy: date | None = None,
) -> dict:
    """Aplica la capa de equivalencia sensor↔laboratorio (TT-09 / RF-016).

    Devuelve:
      {variable, valor_sensor, valor_laboratorio, grado, calibracion}
    donde `grado` es "B" (calibrada vigente) o "C" (sin calibración, indicativa)
    y `valor_laboratorio` es None si no hay calibración.
    """
    base = {
        "variable": variable,
        "valor_sensor": valor,
        "valor_laboratorio": None,
        "grado": "C",
        "calibracion": None,
    }
    if valor is None:
        return base

    cal = calibracion_vigente(
        [c for c in calibraciones if c.get("variable") == variable], hoy
    )
    if cal is None:
        return base

    base["valor_laboratorio"] = aplicar_calibracion_lineal(
        valor, cal["pendiente"], cal["intercepto"]
    )
    base["grado"] = "B"
    base["calibracion"] = {
        "id": cal.get("id"),
        "n": cal.get("n"),
        "r2": cal.get("r2"),
        "rmse": cal.get("rmse"),
        "sesgo": cal.get("sesgo"),
    }
    return base


def humedad_aplicable(textura: str | None, ce_dsm: float | None) -> bool:
    """TT-10 / RF-023: la humedad del sensor es aplicable para este suelo.

    False en suelos arenosos o salinos (CE alta) sin calibración propia.
    """
    if textura and textura.strip().lower() in SUELOS_HUMEDAD_NO_APLICABLE:
        return False
    if ce_dsm is not None and ce_dsm >= 4.0:  # CE alta: suelo salino
        return False
    return True
