"""Conectores para APIs externas: IDEAM, Google Maps GIS, IGAC, Copernicus.

Cada conector es modular e independiente. Siguen el patrón Adapter
con graceful degradation: si una API falla, el sistema sigue funcionando
con los datos disponibles.
"""

from datetime import datetime, timedelta
from typing import Optional

import httpx

from agroia.config import get_settings
from agroia.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ── Timeouts por servicio ──
TIMEOUT_IDEAM = 15.0  # segundos
TIMEOUT_GIS = 5.0
TIMEOUT_IGAC = 30.0  # shapefiles pueden ser pesados
TIMEOUT_COPERNICUS = 20.0


# ═══════════════════════════════════════════════════════════════
# IDEAM — Datos climáticos (diario, 24h)
# ═══════════════════════════════════════════════════════════════

async def fetch_ideam_climate(
    lat: float, lon: float, dataset_id: str | None = None
) -> Optional[dict]:
    """Obtiene datos climáticos del IDEAM para una ubicación.

    Args:
        lat, lon: Coordenadas de la finca
        dataset_id: ID del dataset en Socrata (ej. 'uext-mhny')

    Returns:
        Dict con temperatura, precipitación, humedad o None si falla
    """
    if not settings.ideam_api_url:
        logger.warning("ideam_api_not_configured")
        return None

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_IDEAM) as client:
            # SODA API: consulta por ubicación
            params = {
                "$where": f"within_circle(location, {lat}, {lon}, 50000)",
                "$limit": 1,
                "$order": "fecha DESC",
            }
            url = f"{settings.ideam_api_url}/resource/{dataset_id or 'uext-mhny'}.json"
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data:
                record = data[0]
                return {
                    "fuente": "IDEAM",
                    "fecha": record.get("fecha"),
                    "temperatura": record.get("temperatura"),
                    "precipitacion": record.get("precipitacion"),
                    "humedad": record.get("humedad"),
                    "estacion": record.get("estacion"),
                }
            logger.info("ideam_no_data", lat=lat, lon=lon)
            return None
    except Exception as e:
        logger.error("ideam_api_error", error=str(e))
        return None


# ═══════════════════════════════════════════════════════════════
# Google Maps GIS — Geolocalización (on-demand)
# ═══════════════════════════════════════════════════════════════

async def fetch_gis_location(address: str) -> Optional[dict]:
    """Geocodifica una dirección usando Google Maps Geocoding API.

    Args:
        address: Dirección o nombre del lugar

    Returns:
        Dict con lat, lon, altitud, formatted_address o None si falla
    """
    if not settings.google_maps_api_key:
        logger.warning("gis_api_not_configured")
        return None

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_GIS) as client:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            resp = await client.get(url, params={
                "address": address,
                "key": settings.google_maps_api_key,
            })
            resp.raise_for_status()
            data = resp.json()
            if data.get("results"):
                result = data["results"][0]
                loc = result["geometry"]["location"]
                return {
                    "fuente": "Google Maps",
                    "lat": loc["lat"],
                    "lon": loc["lng"],
                    "altitud": None,  # Google Maps no devuelve altitud en geocoding
                    "formatted_address": result.get("formatted_address"),
                }
            return None
    except Exception as e:
        logger.error("gis_api_error", error=str(e))
        return None


async def fetch_gis_elevation(lat: float, lon: float) -> Optional[dict]:
    """Obtiene altitud para coordenadas usando Google Maps Elevation API."""
    if not settings.google_maps_api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_GIS) as client:
            url = "https://maps.googleapis.com/maps/api/elevation/json"
            resp = await client.get(url, params={
                "locations": f"{lat},{lon}",
                "key": settings.google_maps_api_key,
            })
            resp.raise_for_status()
            data = resp.json()
            if data.get("results"):
                return {
                    "fuente": "Google Maps Elevation",
                    "lat": lat,
                    "lon": lon,
                    "altitud": data["results"][0]["elevation"],
                }
            return None
    except Exception as e:
        logger.error("gis_elevation_error", error=str(e))
        return None


# ═══════════════════════════════════════════════════════════════
# IGAC — Datos edafológicos (bajo demanda, shapefiles)
# ═══════════════════════════════════════════════════════════════

async def fetch_igac_soil_data(lat: float, lon: float) -> Optional[dict]:
    """Obtiene datos edafológicos del IGAC para una coordenada.

    Nota: IGAC expone shapefiles vía WFS/Geoserver. Este conector
    es un placeholder que devuelve la estructura esperada.
    En producción, se integrará con el Geoportal IGAC.
    """
    logger.info("igac_connector_placeholder", lat=lat, lon=lon,
                note="Requiere integración con WFS del Geoportal IGAC")
    # Placeholder — el IGAC expone datos vía WFS (Web Feature Service)
    # La integración real requiere consultar el endpoint WFS del departamento
    return {
        "fuente": "IGAC",
        "lat": lat,
        "lon": lon,
        "estado": "placeholder",
        "nota": "Integración con WFS del Geoportal IGAC pendiente de implementación",
    }


# ═══════════════════════════════════════════════════════════════
# Copernicus / Sentinel-2 — NDVI (cada 5 días)
# ═══════════════════════════════════════════════════════════════

async def fetch_copernicus_ndvi(lat: float, lon: float) -> Optional[dict]:
    """Obtiene el índice NDVI más reciente de Copernicus/Sentinel-2.

    Nota: Copernicus requiere autenticación OAuth2. Para desarrollo
    local se usa Sentinel Hub / EO Browser como alternativa gratuita.
    La integración productiva usa Google Earth Engine API.
    """
    logger.info("copernicus_connector_placeholder", lat=lat, lon=lon,
                note="Requiere cuenta Copernicus Data Space o Google Earth Engine")
    # Placeholder — en producción:
    # 1. Autenticar con Copernicus Data Space Ecosystem (OAuth2)
    # 2. Consultar Sentinel Hub API para NDVI más reciente (máx 5 días)
    # 3. Alternativa: Google Earth Engine API (gratuita, más escalable)
    return {
        "fuente": "Copernicus/Sentinel-2",
        "lat": lat,
        "lon": lon,
        "ndvi": None,
        "fecha": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        "estado": "placeholder",
        "nota": "Integración con Copernicus Data Space o Google Earth Engine pendiente",
    }


# ═══════════════════════════════════════════════════════════════
# Servicio unificado
# ═══════════════════════════════════════════════════════════════

async def enrich_location_data(lat: float, lon: float, address: str | None = None) -> dict:
    """Enriquece una ubicación con datos de todas las APIs externas.

    Ejecuta los conectores en paralelo. Si alguno falla, continúa
    con los demás (graceful degradation).

    Returns:
        Dict con clima, gis, suelo, ndvi (cada uno puede ser None)
    """
    results = {}

    # Ejecutar en paralelo
    import asyncio
    tasks = {
        "clima": fetch_ideam_climate(lat, lon),
        "gis": fetch_gis_location(address) if address else fetch_gis_elevation(lat, lon),
        "suelo": fetch_igac_soil_data(lat, lon),
        "ndvi": fetch_copernicus_ndvi(lat, lon),
    }
    gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)

    for key, result in zip(tasks.keys(), gathered):
        if isinstance(result, Exception):
            logger.warning("external_api_failed", api=key, error=str(result))
            results[key] = None
        else:
            results[key] = result

    return results
