"""API de ingesta para sensores físicos (ESP32/LoRaWAN).

Este es el endpoint que consumen los sensores en campo, con el formato
exacto del firmware (ver log del dispositivo):

    POST /api/sensor
    {
      "device_id": "esp32-npk-001",
      "humidity": 0.0, "temperature": 26.8, "conductivity": 0.0,
      "ph": 8.6, "nitrogen": 0.0, "phosphorus": 0.0, "potassium": 0.0,
      "rssi": -41, "uptime_s": 64
    }

La trama se normaliza (µS/cm → dS/m, variables en español canónicas),
se persiste en `sensor_readings`, se actualiza la telemetría del
dispositivo y alimenta el motor de recomendaciones.

Si el `device_id` no está registrado, se auto-registra contra la primera
finca disponible (para sensores recién instalados sin registro previo).
"""

from datetime import datetime, timezone

from agroia.database import async_session_factory
from agroia.logging import get_logger
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from agroia_backend.models.dispositivo_iot import DispositivoIoT
from agroia_backend.models.finca import Finca

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["sensor-api"])


class SensorFrame(BaseModel, extra="allow"):
    """Trama tal como la envía el firmware del sensor."""

    device_id: str = Field(..., description="ID del dispositivo (ej. esp32-npk-001)")
    humidity: float | None = Field(None, description="% HR ambiente (DHT22)")
    temperature: float | None = Field(None, description="°C ambiente")
    conductivity: float | None = Field(None, description="µS/cm")
    ph: float | None = Field(None, description="0-14")
    nitrogen: float | None = Field(None, description="ppm")
    phosphorus: float | None = Field(None, description="ppm")
    potassium: float | None = Field(None, description="ppm")
    rssi: int | None = Field(None, description="dBm de la señal")
    uptime_s: int | None = Field(None, description="Segundos desde encendido")


@router.post("/sensor", status_code=202)
async def ingesta_sensor(frame: SensorFrame):
    """Recibe una trama del sensor y la procesa en el pipeline de AgroIA."""
    from agroia_backend.services.normalizacion_iot import normalizar_trama
    from apps.iot.agroia_iot.consumer import process_sensor_message

    def _a_entero(v):
        try:
            return int(float(v)) if v is not None else None
        except (TypeError, ValueError):
            return None

    payload, advertencias = normalizar_trama(frame.model_dump())

    async with async_session_factory() as db:
        dispositivo = (
            await db.execute(
                select(DispositivoIoT).where(
                    DispositivoIoT.device_id == frame.device_id
                )
            )
        ).scalar_one_or_none()

        auto_registrado = False
        if dispositivo is None:
            # Sensor sin registro previo: se auto-registra a la primera finca
            finca = (
                await db.execute(select(Finca).order_by(Finca.created_at).limit(1))
            ).scalars().first()
            if finca is None:
                raise HTTPException(status_code=422, detail={
                    "code": "NO_FINCAS",
                    "message": "No hay fincas registradas para asociar el sensor.",
                })

            dispositivo = DispositivoIoT(
                finca_id=finca.id,
                device_id=frame.device_id,
                nombre=f"Auto {frame.device_id}",
                activo=True,
                npk_calibrado=False,
            )
            db.add(dispositivo)
            await db.commit()
            await db.refresh(dispositivo)
            auto_registrado = True
            logger.info("sensor_auto_registrado", device_id=frame.device_id, finca_id=str(finca.id))

        success = await process_sensor_message({
            "device_id": frame.device_id,
            "finca_id": str(dispositivo.finca_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rssi": _a_entero(frame.rssi),
            "uptime_s": _a_entero(frame.uptime_s),
            "payload": payload,
        })
        if not success:
            raise HTTPException(status_code=422, detail={
                "code": "INGEST_ERROR",
                "message": "Error al procesar la trama del sensor.",
            })

    return {
        "status": "accepted",
        "device_id": frame.device_id,
        "finca_id": str(dispositivo.finca_id),
        "auto_registrado": auto_registrado,
        "variables_recibidas": sorted(payload.keys()),
        "advertencias": advertencias,
        "recibida_en": datetime.now(timezone.utc).isoformat(),
    }
