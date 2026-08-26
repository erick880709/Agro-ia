"""Puente hacia el consumidor IoT de `apps/iot` que funciona en ambos entornos.

En el contenedor de producción, `/app/apps/iot` está en el PYTHONPATH y el
paquete se importa como `agroia_iot`. En desarrollo local, el repo raíz está
en el path y se importa como `apps.iot.agroia_iot`. Este módulo resuelve el
import correcto para no duplicar la lógica del consumidor.
"""

try:  # contenedor producción (Dockerfile: PYTHONPATH incluye /app/apps/iot)
    from agroia_iot.consumer import process_sensor_message
except ModuleNotFoundError:  # desarrollo local (repo raíz en el path)
    from apps.iot.agroia_iot.consumer import process_sensor_message

__all__ = ["process_sensor_message"]
