"""Reparación idempotente de pos_x/pos_y históricas en grados GPS.

Cubre las lecturas que quedaron guardadas con latitude/longitude (grados)
en pos_x/pos_y antes de la conversión automática, incluidas las insertadas
entre la ejecución de la migración 033 y el corte del despliegue.

Se ejecuta en cada arranque (main.lifespan); es idempotente: una fila ya
convertida a metros relativos nunca vuelve a caer en el rango de grados.
"""

import logging

from sqlalchemy import text

from agroia.database import async_session_factory
from agroia_backend.services.geo_utils import haversine_relativa

logger = logging.getLogger(__name__)

# Grados legados: pos_x = latitud (4..13 en Colombia) y pos_y = longitud
# (-79..-66). En metros de lote pos_y jamás cae en ese rango → doble
# condición segura.
_RANGO_GRADOS_X = "pos_x BETWEEN -4.5 AND 13"
_RANGO_GRADOS_Y = "pos_y BETWEEN -79.5 AND -66"


async def reparar_gps_legado() -> int:
    """Convierte lecturas en grados a metros relativos al centroide de la finca."""
    reparadas = 0
    async with async_session_factory() as db:
        fincas = (await db.execute(text(
            "SELECT id, latitud, longitud FROM agroia.fincas "
            "WHERE latitud IS NOT NULL AND longitud IS NOT NULL"
        ))).mappings().all()
        for finca in fincas:
            lecturas = (await db.execute(text(
                f"SELECT id, pos_x, pos_y FROM agroia.sensor_readings "
                f"WHERE finca_id = :fid AND {_RANGO_GRADOS_X} AND {_RANGO_GRADOS_Y}"
            ), {"fid": finca["id"]})).mappings().all()
            for lectura in lecturas:
                lat_deg = float(lectura["pos_x"])
                lon_deg = float(lectura["pos_y"])
                x, y = haversine_relativa(
                    float(finca["latitud"]), float(finca["longitud"]),
                    lat_deg, lon_deg,
                )
                await db.execute(text(
                    "UPDATE agroia.sensor_readings SET pos_x = :x, pos_y = :y "
                    "WHERE id = :rid"
                ), {"x": x, "y": y, "rid": lectura["id"]})
                reparadas += 1
        if reparadas:
            await db.commit()
    if reparadas:
        logger.info("reparacion_gps_legado", reparadas=reparadas)
    return reparadas
