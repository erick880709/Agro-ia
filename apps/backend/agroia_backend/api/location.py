"""API endpoints de geolocalización, clima IDEAM y mapas."""

from agroia.logging import get_logger
from fastapi import APIRouter, HTTPException, Query

from agroia_backend.services.external_apis import (
    enrich_location_data,
    fetch_gis_elevation,
    fetch_gis_location,
    fetch_ideam_climate_offline,
    fetch_ideam_historical,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/location", tags=["geolocalización"])


@router.get("/resolver-enlace")
async def resolver_enlace(
    url: str = Query(..., min_length=10, description="Enlace de Google Maps (corto o completo)"),
):
    """Resuelve un enlace de Google Maps (p. ej. maps.app.goo.gl) y extrae
    las coordenadas de la URL final, sin necesidad de API key."""
    from agroia_backend.api.fincas import _extraer_coordenadas
    from agroia_backend.services.external_apis import resolver_enlace_google

    final = await resolver_enlace_google(url)
    lat, lng = _extraer_coordenadas(final)
    if lat is None or lng is None:
        lat, lng = _extraer_coordenadas(url)
    if lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        raise HTTPException(status_code=422, detail={
            "code": "ENLACE_SIN_COORDENADAS",
            "message": (
                "No se pudieron extraer coordenadas del enlace. "
                "Use un enlace de Google Maps con ubicación o el formato 'lat, lng'."
            ),
        })
    return {"status": "ok", "latitud": lat, "longitud": lng, "enlace_final": final}


@router.get("/catalogo")
async def catalogo_geografico():
    """Catálogo departamento → municipios usado por la validación de fincas."""
    from agroia_backend.services.geografia import CATALOGO, CENTROIDES

    return {
        "departamentos": [
            {
                "nombre": dep,
                "municipios": [
                    {
                        "nombre": mun,
                        "centroide": (
                            {"latitud": CENTROIDES[mun][0], "longitud": CENTROIDES[mun][1]}
                            if mun in CENTROIDES else None
                        ),
                    }
                    for mun in sorted(municipios)
                ],
            }
            for dep, municipios in sorted(CATALOGO.items())
        ],
        "total_departamentos": len(CATALOGO),
    }


@router.get("/enrich")
async def enriquecer_ubicacion(
    lat: float = Query(..., ge=-90, le=90, description="Latitud (WGS84)"),
    lon: float = Query(..., ge=-180, le=180, description="Longitud (WGS84)"),
    address: str | None = Query(None, description="Dirección para geocodificar (opcional)"),
):
    """Enriquece coordenadas con datos de clima, suelo, NDVI y GIS.
    
    Consulta múltiples APIs externas en paralelo:
    - IDEAM: datos climáticos históricos y de referencia
    - Google Maps: geocodificación inversa y elevación
    - IGAC: datos edafológicos (placeholder)
    - Copernicus: NDVI (placeholder)
    """
    try:
        data = await enrich_location_data(lat, lon, address)
        # Agregar datos históricos del IDEAM
        ideam_hist = await fetch_ideam_historical(lat, lon, months=6)
        data["clima_historico"] = ideam_hist
        return {
            "status": "ok",
            "ubicacion": {"lat": lat, "lon": lon},
            **data,
        }
    except Exception as e:
        logger.error("enrich_location_error", lat=lat, lon=lon, error=str(e))
        raise HTTPException(status_code=500, detail={"code": "EXTERNAL_API_ERROR", "message": str(e)})


@router.get("/climate")
async def datos_clima(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Obtiene datos climáticos actuales e históricos del IDEAM.
    
    Si la API del IDEAM no está disponible, retorna datos climatológicos
    de referencia del Atlas Climatológico de Colombia (1981-2010).
    """
    try:
        historico = await fetch_ideam_historical(lat, lon, months=12)
        referencia = await fetch_ideam_climate_offline(lat, lon)
        return {
            "status": "ok",
            "referencia_climatologica": referencia,
            "historico": historico,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "CLIMATE_ERROR", "message": str(e)})


@router.get("/geocode")
async def geocodificar(
    address: str = Query(..., min_length=3, description="Dirección o lugar en Colombia"),
):
    """Convierte una dirección en coordenadas usando Google Maps Geocoding.
    
    Si la API de Google Maps no está configurada, retorna error.
    """
    result = await fetch_gis_location(address)
    if result is None:
        raise HTTPException(
            status_code=502,
            detail={"code": "GEOCODING_UNAVAILABLE", "message": "Servicio de geocodificación no disponible. Configure GOOGLE_MAPS_API_KEY."},
        )
    return {"status": "ok", **result}


@router.get("/elevation")
async def altitud(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Obtiene la altitud para coordenadas usando Google Maps Elevation API."""
    result = await fetch_gis_elevation(lat, lon)
    if result is None:
        # Fallback: estimar por región climática
        offline = await fetch_ideam_climate_offline(lat, lon)
        return {
            "status": "ok",
            "fuente": "IDEAM (estimación por región)",
            "lat": lat,
            "lon": lon,
            "altitud_estimada_msnm": offline.get("altitud_estimada_msnm"),
        }
    return {"status": "ok", **result}
