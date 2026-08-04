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


async def process_sensor_message(message: dict) -> bool:
    """Procesa un mensaje de sensor IoT y lo persiste en la BD.

    Args:
        message: Diccionario con los datos del sensor (formato JSON)

    Returns:
        True si se procesó correctamente, False si hubo error
    """
    from agroia_backend.models.sensor_reading import SensorReading

    try:
        # Extraer campos del mensaje
        device_id = message.get("device_id")
        finca_id = message.get("finca_id")
        payload = message.get("payload", {})
        ts = message.get("timestamp", datetime.now(timezone.utc).isoformat())

        if not finca_id:
            logger.warning("sensor_message_missing_finca_id", device_id=device_id)
            return False

        # Crear lectura de sensor
        reading = SensorReading(
            finca_id=finca_id,
            ts=datetime.fromisoformat(ts.replace("Z", "+00:00")),
            sensor_id=device_id,
            ph=payload.get("ph"),
            nitrogeno=payload.get("nitrogeno") or payload.get("n"),
            fosforo=payload.get("fosforo") or payload.get("p"),
            potasio=payload.get("potasio") or payload.get("k"),
            calcio=payload.get("calcio") or payload.get("ca"),
            magnesio=payload.get("magnesio") or payload.get("mg"),
            azufre=payload.get("azufre") or payload.get("s"),
            hierro=payload.get("hierro") or payload.get("fe"),
            manganeso=payload.get("manganeso") or payload.get("mn"),
            zinc=payload.get("zinc") or payload.get("zn"),
            cobre=payload.get("cobre") or payload.get("cu"),
            boro=payload.get("boro") or payload.get("b"),
            materia_organica=payload.get("materia_organica") or payload.get("mo"),
            cic=payload.get("cic"),
            textura=payload.get("textura"),
            humedad=payload.get("humedad"),
            temperatura_suelo=payload.get("temperatura_suelo"),
            conductividad_electrica=payload.get("conductividad_electrica") or payload.get("ce"),
            calidad="OK",
        )

        async with async_session_factory() as session:
            session.add(reading)
            await session.commit()

        logger.info(
            "sensor_reading_stored",
            finca_id=str(finca_id),
            device_id=device_id,
            vars_count=sum(1 for v in payload.values() if v is not None),
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
