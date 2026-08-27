"""Enriquecimiento de suelo con capas oficiales IGAC / UPRA (SIG).

El sistema ya no depende 100 % del sensor para textura / materia orgánica /
CIC: al registrar la finca se consulta la zona de referencia oficial
(Estudio General de Suelos del IGAC y zonificaciones UPRA) mediante
intersección espacial simplificada (centroide del polígono GeoJSON vs.
regiones de referencia), y se precargan esos valores en `sensor_readings`
con `calidad = 'estimado_por_sig'`.

Precedencia de datos:
  1. Lectura del sensor (si la variable llega medida) → gana SIEMPRE.
  2. Estimación SIG (IGAC/UPRA) → rellena solo lo que el sensor no mide.

El conector a geoservicios reales (WMS/WFS GetFeatureInfo) queda preparado
y configurable por variable de entorno; sin configuración se degrada con
gracia a las zonas de referencia locales.
"""

import os
from datetime import datetime, timedelta, timezone

from agroia.logging import get_logger
from sqlalchemy import text

logger = get_logger(__name__)

CALIDAD_SIG = "estimado_por_sig"
SENSOR_ID_SIG = "sig-igac-upra"
VENTANA_REUSO_DIAS = 180  # no duplicar filas SIG en este período

# ── Zonas de referencia (IGAC — Estudio General de Suelos, 1:100.000;
#    zonificaciones UPRA/SIPRA para vocación). Valores representativos del
#    suelo dominante por región. ──
ZONAS_SUELOS_COLOMBIA: dict[str, dict] = {
    "eje_cafetero": {
        "region": "Eje Cafetero (Quindío/Risaralda/Caldas)",
        "textura": "FRANCO_ARCILLOSA",
        "textura_desc": "Franco-arcillosa",
        "materia_organica_pct": 9.5,
        "cic_meq": 24.0,
        "drenaje": "Bueno",
        "profundidad_efectiva_cm": 100,
        "pedregosidad": "MODERADA",
        "capa_limitante": "Ceniza volcánica (Andisoles) — sin limitante severo",
        "fuente": "IGAC Estudio General de Suelos (Andisoles de cordillera Central) + UPRA/SIPRA",
    },
    "antioquia": {
        "region": "Antioquia (valles y montaña)",
        "textura": "FRANCO_ARCILLOSA",
        "textura_desc": "Franco-arcillosa",
        "materia_organica_pct": 6.5,
        "cic_meq": 20.0,
        "drenaje": "Bueno a moderado",
        "profundidad_efectiva_cm": 80,
        "pedregosidad": "MODERADA",
        "capa_limitante": None,
        "fuente": "IGAC Estudio General de Suelos (Inceptisoles/Oxisoles) + UPRA/SIPRA",
    },
    "cundinamarca": {
        "region": "Cundinamarca / Sabana de Bogotá",
        "textura": "FRANCO_ARCILLOSA",
        "textura_desc": "Franco-arcillosa",
        "materia_organica_pct": 7.5,
        "cic_meq": 28.0,
        "drenaje": "Moderado",
        "profundidad_efectiva_cm": 70,
        "pedregosidad": "NINGUNA",
        "capa_limitante": "Posible fragipán/arcillolita en sectores planos (verificar en campo)",
        "fuente": "IGAC Estudio General de Suelos (Andisoles/Vertisoles de sabana) + UPRA/SIPRA",
    },
    "boyaca": {
        "region": "Boyacá (altiplano)",
        "textura": "FRANCA",
        "textura_desc": "Franca",
        "materia_organica_pct": 5.5,
        "cic_meq": 18.0,
        "drenaje": "Bueno",
        "profundidad_efectiva_cm": 85,
        "pedregosidad": "MODERADA",
        "capa_limitante": None,
        "fuente": "IGAC Estudio General de Suelos (Inceptisoles de altiplano) + UPRA/SIPRA",
    },
    "santander": {
        "region": "Santander (valles interandinos)",
        "textura": "FRANCO_ARCILLOSA",
        "textura_desc": "Franco-arcillosa",
        "materia_organica_pct": 4.0,
        "cic_meq": 22.0,
        "drenaje": "Moderado",
        "profundidad_efectiva_cm": 75,
        "pedregosidad": "ALTA",
        "capa_limitante": None,
        "fuente": "IGAC Estudio General de Suelos (Inceptisoles/Vertisoles) + UPRA/SIPRA",
    },
    "tolima": {
        "region": "Tolima (valle del Magdalena)",
        "textura": "FRANCO_ARENOSA",
        "textura_desc": "Franco-arenosa",
        "materia_organica_pct": 2.5,
        "cic_meq": 12.0,
        "drenaje": "Bueno a excesivo",
        "profundidad_efectiva_cm": 110,
        "pedregosidad": "NINGUNA",
        "capa_limitante": None,
        "fuente": "IGAC Estudio General de Suelos (Entisoles aluviales) + UPRA/SIPRA",
    },
    "narino": {
        "region": "Nariño (altiplano volcánico)",
        "textura": "FRANCO_LIMOSA",
        "textura_desc": "Franco-limosa",
        "materia_organica_pct": 10.5,
        "cic_meq": 30.0,
        "drenaje": "Bueno",
        "profundidad_efectiva_cm": 95,
        "pedregosidad": "MODERADA",
        "capa_limitante": "Capa de ceniza volcánica (Andisoles)",
        "fuente": "IGAC Estudio General de Suelos (Andisoles del macizo volcánico) + UPRA/SIPRA",
    },
    "costa_atlantica": {
        "region": "Costa Atlántica (Caribe seco)",
        "textura": "FRANCO_ARENOSA",
        "textura_desc": "Franco-arenosa",
        "materia_organica_pct": 1.8,
        "cic_meq": 10.0,
        "drenaje": "Excesivo",
        "profundidad_efectiva_cm": 120,
        "pedregosidad": "NINGUNA",
        "capa_limitante": None,
        "fuente": "IGAC Estudio General de Suelos (Alfisoles/Inceptisoles del Caribe) + UPRA/SIPRA",
    },
    "costa_pacifica": {
        "region": "Costa Pacífica (Chocó biogeográfico)",
        "textura": "FRANCO_ARCILLOSA",
        "textura_desc": "Franco-arcillosa",
        "materia_organica_pct": 6.0,
        "cic_meq": 20.0,
        "drenaje": "Pobre",
        "profundidad_efectiva_cm": 60,
        "pedregosidad": "NINGUNA",
        "capa_limitante": "Nivel freático alto en valles (drenaje pobre)",
        "fuente": "IGAC Estudio General de Suelos (Ultisoles/Inceptisoles del Pacífico) + UPRA/SIPRA",
    },
    "llanos": {
        "region": "Orinoquía (Llanos Orientales)",
        "textura": "FRANCO_ARCILLOSA",
        "textura_desc": "Franco-arcillosa",
        "materia_organica_pct": 2.5,
        "cic_meq": 11.0,
        "drenaje": "Moderado",
        "profundidad_efectiva_cm": 90,
        "pedregosidad": "NINGUNA",
        "capa_limitante": "Suelos ácidos de sábana (Oxisoles/Ultisoles)",
        "fuente": "IGAC Estudio General de Suelos (Oxisoles de altillanura) + UPRA/SIPRA",
    },
    "amazonia": {
        "region": "Amazonia colombiana",
        "textura": "FRANCO_ARCILLOSA",
        "textura_desc": "Franco-arcillosa",
        "materia_organica_pct": 3.5,
        "cic_meq": 14.0,
        "drenaje": "Moderado a pobre",
        "profundidad_efectiva_cm": 70,
        "pedregosidad": "NINGUNA",
        "capa_limitante": "Suelos ácidos de terraza (Oxisoles/Ultisoles)",
        "fuente": "IGAC Estudio General de Suelos (Amazonia) + UPRA/SIPRA",
    },
    "default": {
        "region": "Colombia (referencia nacional)",
        "textura": "FRANCA",
        "textura_desc": "Franca",
        "materia_organica_pct": 4.0,
        "cic_meq": 16.0,
        "drenaje": "Moderado",
        "profundidad_efectiva_cm": 80,
        "pedregosidad": "MODERADA",
        "capa_limitante": None,
        "fuente": "IGAC Estudio General de Suelos (referencia nacional) + UPRA/SIPRA",
    },
}


def _centroide_geometria(geometria: dict | None) -> tuple[float, float] | None:
    """Centroide simple de un polígono GeoJSON (promedio de vértices)."""
    if not isinstance(geometria, dict):
        return None
    coords: list[tuple[float, float]] = []
    tipo = geometria.get("type")
    if tipo == "Polygon" and geometria.get("coordinates"):
        anillo = geometria["coordinates"][0]
        coords = [(float(p[0]), float(p[1])) for p in anillo if len(p) >= 2]
    elif tipo == "Point" and geometria.get("coordinates"):
        p = geometria["coordinates"]
        return float(p[0]), float(p[1])
    if not coords:
        return None
    lats = [c[1] for c in coords]
    lons = [c[0] for c in coords]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def resolver_zona_sig(
    lat: float, lon: float, geometria: dict | None = None,
) -> dict:
    """Resuelve la zona de referencia IGAC/UPRA por intersección espacial.

    Usa el centroide del polígono GeoJSON (si existe) para ubicar la finca
    en las regiones de referencia del Estudio General de Suelos.
    """
    from agroia_backend.services.external_apis import _estimate_region_from_coords

    lat_uso, lon_uso = lat, lon
    if geometria is not None:
        centro = _centroide_geometria(geometria)
        if centro is not None:
            lat_uso, lon_uso = centro
    region_clave = _estimate_region_from_coords(lat_uso, lon_uso)
    zona = ZONAS_SUELOS_COLOMBIA.get(region_clave, ZONAS_SUELOS_COLOMBIA["default"])
    return {
        "region_clave": region_clave,
        "lat": lat_uso,
        "lon": lon_uso,
        "metodo": "interseccion_espacial_zonas_referencia_igac_upra",
        **zona,
    }


async def intentar_geoservicio_igac(lat: float, lon: float) -> dict | None:
    """Best-effort contra el geoservicio WMS/WFS oficial (opcional).

    Se activa definiendo SIG_IGAC_WMS_URL (ej. GetFeatureInfo del mapa de
    suelos del IGAC/SIAC). Sin configuración devuelve None y el sistema
    degrada con gracia a las zonas de referencia locales.
    """
    url = os.environ.get("SIG_IGAC_WMS_URL")
    if not url:
        logger.info("geoservicio_igac_no_configurado", lat=lat, lon=lon)
        return None
    try:
        import httpx

        params = {
            "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetFeatureInfo",
            "QUERY_LAYERS": "suelos_igac", "INFO_FORMAT": "application/json",
            "I": "10", "J": "10", "WIDTH": "20", "HEIGHT": "20",
            "SRS": "EPSG:4326", "BBOX": f"{lon-0.01},{lat-0.01},{lon+0.01},{lat+0.01}",
            "X": "10", "Y": "10",
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        # El payload depende del servicio; se normaliza si trae textura
        return {"fuente_geoservicio": "IGAC/SIAC WMS", "payload": data}
    except Exception as e:  # noqa: BLE001 — graceful degradation
        logger.warning("geoservicio_igac_no_disponible", error=str(e))
        return None


async def ultima_lectura_sig(db, finca_id) -> dict | None:
    """Última fila de enriquecimiento SIG de una finca."""
    from sqlalchemy import select

    from agroia_backend.models.sensor_reading import SensorReading

    lectura = (
        await db.execute(
            select(SensorReading)
            .where(
                SensorReading.finca_id == finca_id,
                SensorReading.calidad == CALIDAD_SIG,
            )
            .order_by(SensorReading.ts.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if lectura is None:
        return None
    return {
        "id": str(lectura.id),
        "ts": lectura.ts.isoformat(),
        "textura": lectura.textura.value if lectura.textura else None,
        "materia_organica": float(lectura.materia_organica) if lectura.materia_organica is not None else None,
        "cic": float(lectura.cic) if lectura.cic is not None else None,
        "calidad": lectura.calidad,
        "sensor_id": lectura.sensor_id,
    }


async def enriquecer_finca_sig(db, finca, forzar: bool = False) -> dict:
    """Precarga textura/MO/CIC oficiales en sensor_readings y completa el lote.

    Si el sensor ya midió esas variables, sus lecturas tienen precedencia
    (el merge en SueloAdapter lo garantiza). Devuelve un resumen.
    """
    from sqlalchemy import select

    from agroia_backend.models.lote import Lote, Pedregosidad
    from agroia_backend.models.sensor_reading import SensorReading, TexturaSuelo

    if finca.latitud is None or finca.longitud is None:
        return {"estado": "sin_coordenadas", "mensaje": "La finca no tiene coordenadas."}

    zona = resolver_zona_sig(float(finca.latitud), float(finca.longitud), finca.geometria)

    # Reutilizar fila SIG reciente (idempotente, evita duplicados en P2)
    if not forzar:
        corte = datetime.now(timezone.utc) - timedelta(days=VENTANA_REUSO_DIAS)
        existente = (
            await db.execute(
                select(SensorReading)
                .where(
                    SensorReading.finca_id == finca.id,
                    SensorReading.calidad == CALIDAD_SIG,
                    SensorReading.ts >= corte,
                )
                .order_by(SensorReading.ts.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if existente is not None:
            return {
                "estado": "reutilizada",
                "mensaje": "La finca ya tiene enriquecimiento SIG reciente.",
                "zona": zona,
                "lectura": await ultima_lectura_sig(db, finca.id),
            }

    await db.execute(
        text("SET LOCAL search_path TO public, agroia")
    )

    # 1) Lectura con calidad estimado_por_sig (el sensor gana si mide)
    lectura = SensorReading(
        finca_id=finca.id,
        ts=datetime.now(timezone.utc),
        textura=TexturaSuelo[zona["textura"]],
        materia_organica=float(zona["materia_organica_pct"]),
        cic=float(zona["cic_meq"]),
        calidad=CALIDAD_SIG,
        sensor_id=SENSOR_ID_SIG,
    )
    db.add(lectura)

    # 2) Completar el lote principal con atributos físicos oficiales
    lote = (
        await db.execute(
            select(Lote)
            .where(Lote.finca_id == finca.id, Lote.activo.is_(True))
            .order_by(Lote.created_at)
            .limit(1)
        )
    ).scalar_one_or_none()
    lote_cambios = []
    if lote is not None:
        if lote.profundidad_suelo_cm is None:
            lote.profundidad_suelo_cm = float(zona["profundidad_efectiva_cm"])
            lote_cambios.append("profundidad_suelo_cm")
        if lote.pedregosidad is None:
            lote.pedregosidad = Pedregosidad[zona["pedregosidad"]]
            lote_cambios.append("pedregosidad")

    await db.commit()
    await db.refresh(lectura)
    logger.info(
        "sig_enriquecimiento_aplicado",
        finca_id=str(finca.id), region=zona["region_clave"],
        textura=zona["textura"], lote_cambios=lote_cambios,
    )
    return {
        "estado": "enriquecida",
        "zona": {
            "region": zona["region"],
            "textura": zona["textura_desc"],
            "materia_organica_pct": zona["materia_organica_pct"],
            "cic_meq": zona["cic_meq"],
            "drenaje": zona["drenaje"],
            "profundidad_efectiva_cm": zona["profundidad_efectiva_cm"],
            "pedregosidad": zona["pedregosidad"],
            "capa_limitante": zona["capa_limitante"],
            "fuente": zona["fuente"],
            "metodo": zona["metodo"],
        },
        "lectura": await ultima_lectura_sig(db, finca.id),
        "lote_completado": lote_cambios,
    }
