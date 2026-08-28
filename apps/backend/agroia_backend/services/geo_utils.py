"""Utilidades geográficas — conversión de GPS absoluto a metros relativos.

El mapa de calor y el plano del lote usan `pos_x`/`pos_y` en **metros**
relativos al origen/centroide de la finca. Cuando la trama llega con
`latitude`/`longitude` (grados decimales), este módulo los convierte a
desplazamientos Este/Norte (m) desde el centroide de la finca.
"""

import math

R_TIERRA_M = 6371000.0  # radio medio terrestre (WGS84)


def haversine_relativa(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float]:
    """Distancia en metros hacia el Este (X) y Norte (Y) entre dos puntos GPS.

    Equirectangular de radio local: suficiente para distancias de lote
    (< 100 km) con precisión centimétrica a métrica.
    """
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    x = R_TIERRA_M * dlon * math.cos(math.radians((lat1 + lat2) / 2.0))
    y = R_TIERRA_M * dlat
    return round(x, 2), round(y, 2)


def centroide_finca(finca) -> tuple[float, float] | None:
    """(lat, lon) del centroide de la finca: campo lat/lon o polígono GeoJSON."""
    lat = getattr(finca, "latitud", None)
    lon = getattr(finca, "longitud", None)
    if lat is not None and lon is not None:
        return (float(lat), float(lon))

    geom = getattr(finca, "geometria", None) or {}
    coords = None
    if isinstance(geom, dict):
        g = geom.get("geometry") or {}
        if isinstance(g, dict):
            coords = g.get("coordinates")
    if not coords:
        return None
    try:
        ring = coords[0] if isinstance(coords, list) and coords and isinstance(coords[0], list) else coords
        puntos = [p for p in ring if isinstance(p, (list, tuple)) and len(p) >= 2]
        if not puntos:
            return None
        lons = [float(p[0]) for p in puntos]
        lats = [float(p[1]) for p in puntos]
        return (sum(lats) / len(lats), sum(lons) / len(lons))
    except (TypeError, ValueError, IndexError):
        return None
