"""Clasificación con banda de frontera (Épica E3, RF-012).

Cuando un valor está a una distancia ≤ exactitud del umbral, no se clasifica
de forma determinista: se informa "indeterminada (frontera)" con la
probabilidad estimada de cada clase (asumiendo distribución rectangular de la
incertidumbre). El motor de reglas y el orquestador consumen esta salida.
"""

from __future__ import annotations

CLASE_CUMPLE = "cumple"
CLASE_NO_CUMPLE = "no_cumple"
CLASE_FRONTERA = "indeterminada (frontera)"


def clasificar_frente_a_umbral(
    valor: float | None,
    umbral: float | None,
    *,
    exactitud_var: float | None,
    direccion: str,
) -> dict:
    """Clasifica un valor contra un umbral con banda de frontera.

    Args:
        valor: valor medido.
        umbral: umbral de la regla.
        exactitud_var: exactitud (±) de la variable; None o ≤0 → determinista.
        direccion: "max" (el valor debe ser ≤ umbral) o "min" (≥ umbral).

    Returns:
        {"clase": "cumple"|"no_cumple"|"indeterminada (frontera)"|None,
         "probabilidad_cumple": float|None, "margen": float|None}
    """
    if valor is None or umbral is None:
        return {"clase": None, "probabilidad_cumple": None, "margen": None}

    d = valor - umbral  # margen con signo respecto al umbral

    if exactitud_var is None or exactitud_var <= 0:
        cumple = d <= 0 if direccion == "max" else d >= 0
        return {
            "clase": CLASE_CUMPLE if cumple else CLASE_NO_CUMPLE,
            "probabilidad_cumple": 1.0 if cumple else 0.0,
            "margen": round(d, 4),
        }

    if abs(d) <= exactitud_var:
        # Banda de frontera: distribución rectangular en [valor-u, valor+u].
        if direccion == "max":
            p = (exactitud_var - d) / (2 * exactitud_var)
        else:
            p = (exactitud_var + d) / (2 * exactitud_var)
        p = max(0.0, min(1.0, p))
        return {
            "clase": CLASE_FRONTERA,
            "probabilidad_cumple": round(p, 4),
            "margen": round(d, 4),
        }

    cumple = d <= 0 if direccion == "max" else d >= 0
    return {
        "clase": CLASE_CUMPLE if cumple else CLASE_NO_CUMPLE,
        "probabilidad_cumple": 1.0 if cumple else 0.0,
        "margen": round(d, 4),
    }


def combinar_umbrales(resultados: list[dict]) -> dict:
    """Combina la clasificación de umbral inferior y superior de una regla.

    La regla se cumple solo si TODOS los umbrales se cumplen; si alguno está
    en frontera (y ninguno es no_cumple), la regla queda en frontera.
    """
    if not resultados:
        return {"clase": None, "probabilidad_cumple": None, "margen": None}
    clases = [r["clase"] for r in resultados if r["clase"] is not None]
    if CLASE_NO_CUMPLE in clases:
        return {"clase": CLASE_NO_CUMPLE, "probabilidad_cumple": 0.0, "margen": None}
    if CLASE_FRONTERA in clases:
        # Probabilidad conjunta: producto de las probabilidades por umbral.
        probs = [r["probabilidad_cumple"] for r in resultados
                 if r["probabilidad_cumple"] is not None]
        p = 1.0
        for q in probs:
            p *= q
        return {"clase": CLASE_FRONTERA, "probabilidad_cumple": round(p, 4), "margen": None}
    return {"clase": CLASE_CUMPLE, "probabilidad_cumple": 1.0, "margen": None}
