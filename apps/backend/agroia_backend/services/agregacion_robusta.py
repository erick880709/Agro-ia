"""Agregación robusta de lecturas (Épica E3, RF-014).

- Valor por punto = mediana de réplicas (robusta a valores atípicos).
- Valor por lote = mediana de puntos con intervalo (IQR).
- El mapa de calor solo se genera con un mínimo parametrizable de puntos.
"""

from __future__ import annotations

from statistics import median


def mediana_robusta(valores: list[float]) -> float | None:
    """Mediana de una lista de réplicas (ignora None/no numéricos)."""
    limpios = [float(v) for v in valores if v is not None]
    if not limpios:
        return None
    return round(median(limpios), 4)


def agregar_punto(valores: list[float]) -> dict:
    """Agrega las réplicas de un punto: mediana y número de réplicas."""
    limpios = [float(v) for v in valores if v is not None]
    return {
        "mediana": mediana_robusta(limpios),
        "replicas": len(limpios),
    }


def _cuartiles(valores: list[float]) -> tuple[float, float] | None:
    if not valores:
        return None
    ordenados = sorted(valores)
    n = len(ordenados)

    def cuantil(p: float) -> float:
        idx = p * (n - 1)
        lo = int(idx)
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        return ordenados[lo] * (1 - frac) + ordenados[hi] * frac

    return cuantil(0.25), cuantil(0.75)


def agregar_lote(puntos: list[float]) -> dict:
    """Agrega los valores por punto de un lote: mediana con intervalo (IQR).

    Devuelve {mediana, n_puntos, q1, q3, iqr, minimo_puntos_requeridos}.
    """
    limpios = [float(v) for v in puntos if v is not None]
    cuartiles = _cuartiles(limpios)
    if cuartiles is None:
        return {"mediana": None, "n_puntos": 0, "q1": None, "q3": None,
                "iqr": None, "minimo_puntos_requeridos": MINIMO_PUNTOS_MAPA}
    q1, q3 = cuartiles
    return {
        "mediana": mediana_robusta(limpios),
        "n_puntos": len(limpios),
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(q3 - q1, 4),
        "minimo_puntos_requeridos": MINIMO_PUNTOS_MAPA,
    }


def puede_generar_mapa(n_puntos_validos: int) -> bool:
    """True si hay suficientes puntos para interpolar el mapa de calor."""
    return n_puntos_validos >= MINIMO_PUNTOS_MAPA


# Mínimo parametrizable de puntos válidos para generar el mapa de calor.
MINIMO_PUNTOS_MAPA = 3
