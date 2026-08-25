"""Consumidor RabbitMQ para ingesta de datos IoT (LoRaWAN).

Escucha la cola 'sensor.data.received', decodifica tramas LoRaWAN,
normaliza las 18 variables de suelo y las persiste en PostgreSQL+TimescaleDB.
"""

import asyncio
import json
from datetime import datetime, timezone

from agroia.config import get_settings
from agroia.database import async_session_factory
from agroia.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Tópico / routing key
QUEUE_NAME = settings.rabbitmq_queue_iot  # "sensor.data.received"


async def get_dispositivo(device_id: str):
    """Busca el registro del dispositivo (device_id → finca_id + calibración)."""
    from sqlalchemy import select

    from agroia_backend.models.dispositivo_iot import DispositivoIoT

    async with async_session_factory() as session:
        result = await session.execute(
            select(DispositivoIoT).where(DispositivoIoT.device_id == device_id)
        )
        return result.scalar_one_or_none()


async def process_sensor_message(message: dict) -> bool:
    """Procesa un mensaje de sensor IoT y lo persiste en la BD.

    Soporta dos formatos (brecha G1/G2):
      - Formato gateway: {device_id, finca_id, timestamp, payload: {...}}
      - Trama cruda ESP32: variables en la raíz del dict, sin finca_id
        (se resuelve la finca vía registro de dispositivos).

    Returns:
        True si se procesó correctamente, False si hubo error.
    """
    from agroia_backend.models.dispositivo_iot import DispositivoIoT
    from agroia_backend.models.sensor_reading import SensorReading
    from agroia_backend.services.normalizacion_iot import (
        aplicar_calibracion,
        normalizar_trama,
    )

    try:
        # ── Extraer campos del mensaje ──
        device_id = message.get("device_id")
        finca_id = message.get("finca_id")
        raw = message.get("payload") or message  # trama directa ESP32
        ts_raw = message.get("timestamp") or datetime.now(timezone.utc).isoformat()
        ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))

        # ── Resolver finca desde el registro de dispositivos si no viene ──
        dispositivo = None
        if not finca_id:
            if not device_id:
                logger.warning("sensor_message_missing_finca_id", device_id=device_id)
                return False
            dispositivo = await get_dispositivo(device_id)
            if dispositivo is None:
                logger.warning("sensor_device_not_registered", device_id=device_id)
                return False
            finca_id = str(dispositivo.finca_id)

        # ── Normalizar trama al formato canónico (brecha G2) ──
        payload, advertencias = normalizar_trama(raw)

        # ── Calibración NPK (brecha G4) ──
        npk_calibrado = bool(dispositivo and dispositivo.npk_calibrado)
        if npk_calibrado:
            factores = dispositivo.factores_calibracion if dispositivo else None
            payload = aplicar_calibracion(payload, factores)
            calidad = "OK"
        else:
            calidad = "npk_no_calibrado" if "npk_sin_calibrar" in advertencias else "OK"

        # ── Crear lectura de sensor ──
        reading = SensorReading(
            finca_id=finca_id,
            ts=ts,
            sensor_id=device_id,
            ph=payload.get("ph"),
            nitrogeno=payload.get("nitrogeno"),
            fosforo=payload.get("fosforo"),
            potasio=payload.get("potasio"),
            calcio=payload.get("calcio"),
            magnesio=payload.get("magnesio"),
            azufre=payload.get("azufre"),
            hierro=payload.get("hierro"),
            manganeso=payload.get("manganeso"),
            zinc=payload.get("zinc"),
            cobre=payload.get("cobre"),
            boro=payload.get("boro"),
            materia_organica=payload.get("materia_organica"),
            cic=payload.get("cic"),
            textura=payload.get("textura"),
            humedad=payload.get("humedad"),
            temperatura_suelo=payload.get("temperatura_suelo"),
            conductividad_electrica=payload.get("conductividad_electrica"),
            humedad_ambiental=payload.get("humedad_ambiental"),
            temperatura_ambiental=payload.get("temperatura_ambiental"),
            calidad=calidad,
        )

        async with async_session_factory() as session:
            session.add(reading)

            # ── Actualizar telemetría del dispositivo ──
            if device_id:
                from sqlalchemy import select

                disp = (
                    await session.execute(
                        select(DispositivoIoT).where(
                            DispositivoIoT.device_id == device_id
                        )
                    )
                ).scalar_one_or_none()
                if disp is not None:
                    disp.ultima_transmision = datetime.now(timezone.utc)
                    disp.rssi = message.get("rssi")
                    disp.uptime_s = message.get("uptime_s")

            await session.commit()

        logger.info(
            "sensor_reading_stored",
            finca_id=str(finca_id),
            device_id=device_id,
            vars_count=len(payload),
            calidad=calidad,
        )
        return True

    except Exception as e:
        logger.error("sensor_message_processing_error", error=str(e), device_id=message.get("device_id"))
        return False


class IoTIngestionConsumer:
    """Consumidor RabbitMQ para el servicio IoT."""

    def __init__(self):
        self._running = False

    async def start(self):
        """Inicia el consumidor (modo polling — simula RabbitMQ en desarrollo)."""
        self._running = True
        logger.info("iot_consumer_started", queue=QUEUE_NAME)
        # En producción, aquí se conectaría a RabbitMQ vía aio-pika
        # Para desarrollo local, el consumidor se ejecuta como tarea de Celery
        # o se usa polling del backend
        while self._running:
            await asyncio.sleep(30)  # Polling cada 30s en dev
            # TODO: conectar a RabbitMQ en producción
            # connection = await aio_pika.connect(settings.rabbitmq_url)
            # async with connection:
            #     channel = await connection.channel()
            #     queue = await channel.declare_queue(QUEUE_NAME, durable=True)
            #     async for msg in queue:
            #         await process_sensor_message(json.loads(msg.body))

    async def stop(self):
        """Detiene el consumidor."""
        self._running = False
        logger.info("iot_consumer_stopped")


# Instancia global para el lifespan de FastAPI
consumer = IoTIngestionConsumer()
