"""Muestreo inteligente: ¿dónde tomar la muestra de laboratorio?

Usa las posiciones del mapa de calor (`pos_x/pos_y` de `sensor_readings`)
y elige los puntos de **máxima incertidumbre espacial** con *Farthest
Point Sampling* (FPS): el primer punto es el más alejado del centroide
de la nube de muestras y cada punto siguiente es el más distante de los
ya elegidos. Así se cubren las zonas menos representadas por el sensor.

La salida alimenta la sección «P» del reporte: se marcan los puntos con
cruces rojas y se ofrece el GeoJSON descargable para que el agrónomo
tome las muestras compuestas de laboratorio.
"""

import math

from agroia.logging import get_logger

logger = get_logger(__name__)


def puntos_muestreo_optimos(
    muestras: list[dict] | None,
    n: int = 3,
) -> list[dict]:
    """Elige hasta `n` puntos de muestreo con Farthest Point Sampling.

    Args:
        muestras: lecturas con `pos_x`/`pos_y` (del mapa de calor).
        n: número de puntos sugeridos.

    Returns:
        Lista de dicts con `pos_x`, `pos_y` y la referencia de la muestra.
    """
    puntos: list[dict] = []
    for m in muestras or []:
        try:
            x = float(m.get("pos_x"))
            y = float(m.get("pos_y"))
        except (TypeError, ValueError):
            continue
        if x is None or y is None or (x == 0 and y == 0):
            continue
        puntos.append({"pos_x": x, "pos_y": y, **{k: m.get(k) for k in ("ts", "sensor_id")}})

    n_puntos = len(puntos)
    if n_puntos == 0:
        return []
    if n_puntos <= n:
        return puntos

    cx = sum(p["pos_x"] for p in puntos) / n_puntos
    cy = sum(p["pos_y"] for p in puntos) / n_puntos

    disponibles = puntos[:]
    seleccionados: list[dict] = []

    # Punto 1: el más alejado del centroide de la nube de muestras
    primero = max(
        disponibles,
        key=lambda p: math.hypot(p["pos_x"] - cx, p["pos_y"] - cy),
    )
    seleccionados.append(primero)
    disponibles.remove(primero)

    def _distancia_min(p: dict) -> float:
        return min(
            math.hypot(p["pos_x"] - s["pos_x"], p["pos_y"] - s["pos_y"])
            for s in seleccionados
        )

    while len(seleccionados) < n and disponibles:
        mejor = max(disponibles, key=_distancia_min)
        seleccionados.append(mejor)
        disponibles.remove(mejor)

    logger.info(
        "muestreo_optimo",
        puntos_disponibles=n_puntos,
        sugeridos=len(seleccionados),
    )
    return seleccionados
