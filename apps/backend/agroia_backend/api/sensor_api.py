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
    finca_id: str | None = Field(
        None,
        description=(
            "UUID de la finca a la que pertenece la medición (opcional; si el "
            "dispositivo ya está registrado se usa su finca, y si se envía, "
            "se asocia a esta)."
        ),
    )
    humidity: float | None = Field(None, description="% HR ambiente (DHT22)")
    temperature: float | None = Field(None, description="°C ambiente")
    conductivity: float | None = Field(None, description="µS/cm")
    ph: float | None = Field(None, description="0-14")
    nitrogen: float | None = Field(None, description="ppm")
    phosphorus: float | None = Field(None, description="ppm")
    potassium: float | None = Field(None, description="ppm")
    rssi: int | None = Field(None, description="dBm de la señal")
    uptime_s: int | None = Field(None, description="Segundos desde encendido")
    pos_x: float | None = Field(None, description="Posición X de la toma en el lote (metros, muestreo en cuadrícula)")
    pos_y: float | None = Field(None, description="Posición Y de la toma en el lote (metros, muestreo en cuadrícula)")


@router.post("/sensor", status_code=202)
async def ingesta_sensor(frame: SensorFrame):
    """Recibe una trama del sensor y la procesa en el pipeline de AgroIA."""
    from agroia_backend.services.normalizacion_iot import normalizar_trama
    from agroia_backend.services.puente_iot import process_sensor_message

    def _a_entero(v):
        try:
            return int(float(v)) if v is not None else None
        except (TypeError, ValueError):
            return None

    payload, advertencias = normalizar_trama(frame.model_dump())

    async with async_session_factory() as db:
        # ── Resolver finca indicada en la trama (opcional) ──
        finca_indicada = None
        if frame.finca_id:
            try:
                finca_indicada = (
                    await db.execute(
                        select(Finca).where(Finca.id == frame.finca_id)
                    )
                ).scalar_one_or_none()
            except Exception:
                finca_indicada = None
            if finca_indicada is None:
                raise HTTPException(status_code=422, detail={
                    "code": "FINCA_NOT_FOUND",
                    "message": (
                        f"La finca '{frame.finca_id}' indicada en la trama no está "
                        "registrada. Verifique el ID de la finca."
                    ),
                })

        dispositivo = (
            await db.execute(
                select(DispositivoIoT).where(
                    DispositivoIoT.device_id == frame.device_id
                )
            )
        ).scalar_one_or_none()

        auto_registrado = False
        if dispositivo is None:
            # Sensor sin registro previo: se asocia a la finca de la trama
            # (si viene) o a la primera finca disponible.
            if finca_indicada is not None:
                finca = finca_indicada
            else:
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
        elif finca_indicada is not None and dispositivo.finca_id != finca_indicada.id:
            # El dispositivo ya existía pero la trama trae otra finca:
            # se reasocia (p. ej. sensor movido de lote).
            logger.info(
                "sensor_finca_actualizada",
                device_id=frame.device_id,
                finca_anterior=str(dispositivo.finca_id),
                finca_nueva=str(finca_indicada.id),
            )
            dispositivo.finca_id = finca_indicada.id
            await db.commit()

        success = await process_sensor_message({
            "device_id": frame.device_id,
            "finca_id": str(dispositivo.finca_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rssi": _a_entero(frame.rssi),
            "uptime_s": _a_entero(frame.uptime_s),
            "pos_x": frame.pos_x,
            "pos_y": frame.pos_y,
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
