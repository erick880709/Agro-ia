"""API endpoints para ingesta IoT y estado de sensores."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agroia.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/iot", tags=["iot"])


# ── Schemas ──

class SensorMessage(BaseModel):
    """Mensaje entrante de un sensor IoT LoRaWAN."""
    device_id: str = Field(..., description="ID único del dispositivo LoRaWAN")
    finca_id: str = Field(..., description="UUID de la finca asociada")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp de la medición")
    payload: dict = Field(..., description="Variables de suelo medidas (JSON dinámico)")


class SensorStatus(BaseModel):
    finca_id: str
    device_id: str
    last_transmission: Optional[str] = None
    hours_since_last: Optional[float] = None
    status: str  # "online", "offline", "datos_desactualizados"


# ── Endpoints ──

@router.post("/ingest", status_code=202)
async def ingest_sensor_data(message: SensorMessage):
    """Recibe datos de un sensor IoT y los encola para procesamiento.

    En producción, este endpoint lo llama el gateway LoRaWAN.
    En desarrollo, acepta POST directo desde simuladores.
    """
    from agroia_backend.services.data_adapters import ALL_SOIL_VARIABLES

    payload = message.payload
    vars_received = [v for v in ALL_SOIL_VARIABLES if v in payload and payload[v] is not None]

    logger.info(
        "sensor_data_received",
        device_id=message.device_id,
        finca_id=message.finca_id,
        vars_count=len(vars_received),
    )

    # Encolar en RabbitMQ (en producción) o procesar directamente (dev)
    from apps.iot.agroia_iot.consumer import process_sensor_message

    success = await process_sensor_message({
        "device_id": message.device_id,
        "finca_id": message.finca_id,
        "timestamp": message.timestamp,
        "payload": payload,
    })

    return {
        "status": "accepted" if success else "error",
        "device_id": message.device_id,
        "variables_recibidas": vars_received,
        "variables_faltantes": [v for v in ALL_SOIL_VARIABLES if v not in vars_received],
    }


@router.get("/sensores/{finca_id}/status")
async def sensor_status(finca_id: str):
    """Consulta el estado de los sensores de una finca."""
    from datetime import datetime, timezone

    from sqlalchemy import desc, func, select

    from agroia.database import async_session_factory
    from agroia_backend.models.sensor_reading import SensorReading

    async with async_session_factory() as session:
        stmt = (
            select(SensorReading.sensor_id, func.max(SensorReading.ts).label("last_ts"))
            .where(SensorReading.finca_id == finca_id)
            .group_by(SensorReading.sensor_id)
        )
        result = await session.execute(stmt)
        rows = result.all()

    now = datetime.now(timezone.utc)
    sensores = []
    for row in rows:
        last_ts = row.last_ts
        hours = (now - last_ts).total_seconds() / 3600 if last_ts else None
        status = "offline" if hours is None or hours > 24 else ("datos_desactualizados" if hours > 12 else "online")
        sensores.append({
            "device_id": row.sensor_id,
            "last_transmission": last_ts.isoformat() if last_ts else None,
            "hours_since_last": round(hours, 1) if hours else None,
            "status": status,
        })

    return {
        "finca_id": finca_id,
        "sensores": sensores,
        "total": len(sensores),
        "online": sum(1 for s in sensores if s["status"] == "online"),
        "offline": sum(1 for s in sensores if s["status"] != "online"),
    }


@router.get("/externas/enrich")
async def enrich_location(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    address: Optional[str] = None,
):
    """Enriquece una ubicación con datos de APIs externas (IDEAM, GIS, IGAC, Copernicus)."""
    from agroia_backend.services.external_apis import enrich_location_data

    results = await enrich_location_data(lat, lon, address)
    return {"lat": lat, "lon": lon, "apis": results}
