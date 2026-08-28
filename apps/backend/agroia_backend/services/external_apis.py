"""Conectores para APIs externas: IDEAM, Google Maps GIS, IGAC, Copernicus.

Cada conector es modular e independiente. Siguen el patrón Adapter
con graceful degradation: si una API falla, el sistema sigue funcionando
con los datos disponibles.
"""

from datetime import datetime, timedelta

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

# ── Datos climáticos de referencia por región de Colombia (fallback offline) ──
# Fuente: IDEAM - Atlas Climatológico de Colombia (promedios 1981-2010)
CLIMATE_ZONES_COLOMBIA = {
    # Región Andina
    "cundinamarca": {"temp_min": 8, "temp_max": 20, "temp_avg": 14, "precip_anual": 900, "humedad": 75, "altitud_min": 2500, "altitud_max": 3000},
    "boyaca": {"temp_min": 7, "temp_max": 19, "temp_avg": 13, "precip_anual": 800, "humedad": 72, "altitud_min": 2400, "altitud_max": 2900},
    "antioquia": {"temp_min": 16, "temp_max": 28, "temp_avg": 22, "precip_anual": 2000, "humedad": 80, "altitud_min": 500, "altitud_max": 2500},
    "santander": {"temp_min": 18, "temp_max": 30, "temp_avg": 24, "precip_anual": 1500, "humedad": 78, "altitud_min": 200, "altitud_max": 2500},
    "eje_cafetero": {"temp_min": 16, "temp_max": 26, "temp_avg": 21, "precip_anual": 2200, "humedad": 82, "altitud_min": 1000, "altitud_max": 1800},
    "tolima": {"temp_min": 20, "temp_max": 33, "temp_avg": 26, "precip_anual": 1200, "humedad": 70, "altitud_min": 300, "altitud_max": 1500},
    "narino": {"temp_min": 10, "temp_max": 20, "temp_avg": 15, "precip_anual": 1000, "humedad": 78, "altitud_min": 2500, "altitud_max": 3000},
    # Región Caribe
    "costa_atlantica": {"temp_min": 24, "temp_max": 34, "temp_avg": 28, "precip_anual": 800, "humedad": 80, "altitud_min": 0, "altitud_max": 200},
    # Región Pacífica
    "costa_pacifica": {"temp_min": 22, "temp_max": 32, "temp_avg": 26, "precip_anual": 4000, "humedad": 88, "altitud_min": 0, "altitud_max": 200},
    # Región Orinoquía
    "llanos": {"temp_min": 22, "temp_max": 35, "temp_avg": 27, "precip_anual": 2500, "humedad": 75, "altitud_min": 100, "altitud_max": 500},
    # Región Amazónica
    "amazonia": {"temp_min": 22, "temp_max": 32, "temp_avg": 26, "precip_anual": 3500, "humedad": 87, "altitud_min": 100, "altitud_max": 400},
    # Default
    "default": {"temp_min": 18, "temp_max": 28, "temp_avg": 23, "precip_anual": 1500, "humedad": 78, "altitud_min": 0, "altitud_max": 3000},
}


def _estimate_region_from_coords(lat: float, lon: float) -> str:
    """Estima la región climática de Colombia a partir de coordenadas.

    Las regiones más específicas se evalúan PRIMERO; las costas amplias van
    al final para no capturar puntos del interior (ej. la Sabana de Bogotá
    caía en la caja Caribe).
    """
    # Regiones aproximadas por bounding box (orden: más específico primero)
    if 0.5 <= lat <= 2.5 and -78.5 <= lon <= -77.0:
        return "narino"
    # Tolima: valle del Magdalena (Ibagué/Melgar) + norte (Honda/Mariquita)
    if (3.0 <= lat <= 4.45 and -76.0 <= lon <= -74.4) or (
        5.0 <= lat <= 5.4 and -75.2 <= lon <= -74.4
    ):
        return "tolima"
    if 4.45 <= lat <= 5.7 and -76.0 <= lon <= -75.35:
        return "eje_cafetero"
    if 4.3 <= lat <= 5.3 and -74.5 <= lon <= -73.2:
        return "cundinamarca"  # Sabana de Bogotá
    if 5.3 <= lat <= 6.5 and -73.8 <= lon <= -72.6:
        return "boyaca"
    if 6.5 <= lat <= 8.3 and -74.5 <= lon <= -72.5:
        return "santander"
    if 5.5 <= lat <= 8.5 and -77.0 <= lon <= -74.0:
        return "antioquia"
    if 1.5 <= lat <= 5.0 and -78.5 <= lon <= -77.0:
        return "costa_pacifica"
    if 2.5 <= lat <= 6.5 and -74.0 <= lon <= -67.0:
        return "llanos"
    if -5.0 <= lat <= 2.0 and -74.0 <= lon <= -69.0:
        return "amazonia"
    if 7.0 <= lat <= 12.5 and -77.5 <= lon <= -72.0:
        return "costa_atlantica"
    return "default"


async def fetch_ideam_climate_offline(lat: float, lon: float) -> dict:
    """Obtiene datos climáticos de referencia para una ubicación en Colombia.
    
    Usa datos climatológicos del IDEAM (Atlas Climatológico 1981-2010)
    como fallback offline cuando la API no está disponible.
    """
    region = _estimate_region_from_coords(lat, lon)
    zone = CLIMATE_ZONES_COLOMBIA.get(region, CLIMATE_ZONES_COLOMBIA["default"])
    
    # Variación estacional simple (±15% basado en mes actual)
    import random
    random.seed(int(lat * 100 + lon * 100))  # Determinístico por ubicación
    month = datetime.utcnow().month
    seasonal_factor = 1.0 + 0.15 * (1 if month in [12, 1, 2] else -1 if month in [6, 7, 8] else 0)
    
    return {
        "fuente": "IDEAM (Atlas Climatológico 1981-2010, offline)",
        "region": region,
        "temperatura_promedio": round(zone["temp_avg"] * seasonal_factor, 1),
        "temperatura_min": round(zone["temp_min"] * seasonal_factor, 0),
        "temperatura_max": round(zone["temp_max"] * seasonal_factor, 0),
        "precipitacion_anual_mm": zone["precip_anual"],
        "precipitacion_mensual_estimada": round(zone["precip_anual"] / 12 * seasonal_factor, 0),
        "humedad_relativa": zone["humedad"],
        "altitud_estimada_msnm": (zone["altitud_min"] + zone["altitud_max"]) // 2,
        "fecha_consulta": datetime.utcnow().isoformat(),
        "nota": "Datos climatológicos de referencia. Para datos en tiempo real configure IDEAM_API_KEY.",
    }


async def fetch_ideam_historical(lat: float, lon: float, months: int = 12) -> dict:
    """Obtiene serie histórica de clima para una ubicación.
    
    Combina datos de la API IDEAM (si está disponible) con datos
    climatológicos de referencia como fallback.
    """
    # Intentar API real primero
    api_data = await fetch_ideam_climate(lat, lon)
    
    # Obtener datos de referencia
    offline_data = await fetch_ideam_climate_offline(lat, lon)
    
    # Construir serie histórica simulada basada en patrones climáticos colombianos
    historical = []
    for m in range(months):
        month_offset = (datetime.utcnow().month - m - 1) % 12 + 1
        month_name = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                      "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][month_offset - 1]
        # Colombia tiene 2 temporadas de lluvia (abr-may y oct-nov) y 2 secas
        rain_factor = 1.5 if month_offset in [4, 5, 10, 11] else 0.5 if month_offset in [1, 2, 7, 8] else 1.0
        historical.append({
            "mes": month_name,
            "mes_num": month_offset,
            "temperatura_promedio": round(offline_data["temperatura_promedio"] + (1 if month_offset > 6 else -1), 1),
            "precipitacion_estimada": round(offline_data["precipitacion_mensual_estimada"] * rain_factor, 0),
        })
    
    return {
        "ubicacion": {"lat": lat, "lon": lon},
        "region_climatica": offline_data["region"],
        "datos_referencia": offline_data,
        "serie_historica_12m": historical,
        "datos_tiempo_real": api_data,
        "api_disponible": api_data is not None,
    }

async def fetch_ideam_climate(
    lat: float, lon: float, dataset_id: str | None = None
) -> dict | None:
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


async def fetch_ideam_clima_fecha(lat: float, lon: float, fecha: str) -> dict:
    """Clima del día de la muestra (fecha en formato ISO o YYYY-MM-DD).

    1) API IDEAM (estación cercana) si está configurada y responde.
    2) Fallback: climatología de referencia del IDEAM (Atlas 1981-2010)
       ajustada al mes de la fecha de la muestra.
    """
    api = await fetch_ideam_climate(lat, lon)
    if api and (api.get("temperatura") is not None or api.get("precipitacion") is not None):
        api["fuente"] = "IDEAM (estación cercana)"
        api["fecha"] = fecha
        return api

    offline = await fetch_ideam_climate_offline(lat, lon)
    try:
        d = datetime.fromisoformat(str(fecha).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        d = datetime.utcnow()
    mes = d.month
    # Dos temporadas de lluvia (abr-may, oct-nov) y dos secas (ene-feb, jul-ago)
    rain_factor = 1.5 if mes in (4, 5, 10, 11) else 0.5 if mes in (1, 2, 7, 8) else 1.0
    estacional = 1.0 + (0.10 if mes in (12, 1, 2) else -0.08 if mes in (6, 7, 8) else 0.0)
    return {
        "fuente": "IDEAM — Atlas Climatológico 1981-2010 (referencia del mes)",
        "region": offline.get("region"),
        "fecha": fecha,
        "temperatura_min": round(offline["temperatura_min"] * estacional, 0),
        "temperatura_max": round(offline["temperatura_max"] * estacional, 0),
        "temperatura_promedio": round(offline["temperatura_promedio"] * estacional, 1),
        "precipitacion_estimada_mm": round(offline["precipitacion_mensual_estimada"] * rain_factor, 0),
        "humedad_relativa": offline["humedad_relativa"],
        "nota": (
            "Referencia climatológica del mes de la muestra; "
            "configure IDEAM_API_KEY para datos observados del día."
        ),
    }


async def resolver_enlace_google(enlace: str) -> str:
    """Resuelve un enlace corto de Google Maps (goo.gl/maps.app.goo.gl)
    siguiendo los redireccionamientos y retorna la URL final (que suele
    contener las coordenadas). Si no se puede resolver, retorna el enlace.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_GIS, follow_redirects=True) as client:
            try:
                resp = await client.head(enlace)
            except httpx.HTTPError:
                resp = await client.get(enlace)
            final = str(resp.url)
            return final if final and final != enlace else enlace
    except Exception as e:  # noqa: BLE001
        logger.warning("enlace_google_no_resuelto", error=str(e))
        return enlace


# ═══════════════════════════════════════════════════════════════
# Google Maps GIS — Geolocalización (on-demand)
# ═══════════════════════════════════════════════════════════════

async def fetch_gis_location(address: str) -> dict | None:
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


async def fetch_gis_elevation(lat: float, lon: float) -> dict | None:
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

async def fetch_igac_soil_data(lat: float, lon: float) -> dict | None:
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

async def fetch_copernicus_ndvi(lat: float, lon: float) -> dict | None:
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
# Pronóstico extendido (Open-Meteo, sin API key) — alertas proactivas
# ═══════════════════════════════════════════════════════════════

TIMEOUT_PRONOSTICO = 12.0

# Modelos seleccionables de Open-Meteo. `ecmwf` = ECMWF IFS 0.25° (open data,
# CC BY 4.0, https://data.ecmwf.int/forecasts); `auto` = mejor modelo disponible.
MODELOS_PRONOSTICO = {
    "auto": None,
    "ecmwf": "ecmwf_ifs025",
}


async def fetch_pronostico_open_meteo(
    lat: float, lon: float, dias: int = 7, modelo: str = "auto"
) -> list[dict] | None:
    """Pronóstico diario (lluvia y temperaturas) para los próximos `dias` días.

    Usa la API pública de Open-Meteo (sin clave). Con `modelo="ecmwf"` la
    respuesta proviene del modelo internacional ECMWF (IFS 0.25°). Si falla,
    devuelve None para que el llamador degrade con gracia. Formato por día:
    {fecha, precipitacion_mm, temp_min_c, temp_max_c}.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": f"{lat:.4f}",
        "longitude": f"{lon:.4f}",
        "daily": "precipitation_sum,temperature_2m_min,temperature_2m_max",
        "timezone": "America/Bogota",
        "forecast_days": str(int(dias)),
    }
    modelo_openmeteo = MODELOS_PRONOSTICO.get((modelo or "auto").lower())
    if modelo_openmeteo:
        params["models"] = modelo_openmeteo
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_PRONOSTICO) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            datos = r.json()
        daily = datos.get("daily") or {}
        fechas = daily.get("time") or []
        lluvias = daily.get("precipitation_sum") or []
        tmin = daily.get("temperature_2m_min") or []
        tmax = daily.get("temperature_2m_max") or []
        pronostico = [
            {
                "fecha": fechas[i],
                "precipitacion_mm": float(lluvias[i]) if i < len(lluvias) and lluvias[i] is not None else 0.0,
                "temp_min_c": float(tmin[i]) if i < len(tmin) and tmin[i] is not None else 20.0,
                "temp_max_c": float(tmax[i]) if i < len(tmax) and tmax[i] is not None else 26.0,
            }
            for i in range(len(fechas))
        ]
        return pronostico or None
    except Exception as e:  # noqa: BLE001 — graceful degradation
        logger.warning("pronostico_no_disponible", error=str(e), lat=lat, lon=lon)
        return None


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
