"""033 · Reparar pos_x/pos_y históricas: grados GPS → metros relativos.

Antes de la conversión automática (services/geo_utils.py), las tramas
guardaban latitude/longitude (grados decimales) directamente en
pos_x/pos_y. Esta migración repara las lecturas heredadas usando el
centroide (latitud/longitud) de cada finca.

Revision ID: 033_reparar_gps_relativo
Revises: 023_modulos_v4
Create Date: 2026-08-28
"""
import math

from alembic import op
from sqlalchemy import text

revision = "033_reparar_gps_relativo"
down_revision = "023_modulos_v4"
branch_labels = None
depends_on = None

R_TIERRA_M = 6371000.0


def _relativa(lat_c: float, lon_c: float, lat: float, lon: float) -> tuple[float, float]:
    """(x, y) en metros al Este/Norte del centroide (misma fórmula que geo_utils)."""
    dlat = math.radians(lat - lat_c)
    dlon = math.radians(lon - lon_c)
    x = R_TIERRA_M * dlon * math.cos(math.radians((lat_c + lat) / 2.0))
    y = R_TIERRA_M * dlat
    return round(x, 2), round(y, 2)


def upgrade() -> None:
    bind = op.get_bind()
    fincas = bind.execute(text(
        "SELECT id, latitud, longitud FROM agroia.fincas "
        "WHERE latitud IS NOT NULL AND longitud IS NOT NULL"
    )).mappings().all()
    reparadas = 0
    for finca in fincas:
        # Grados legados: pos_x = latitud (4..13 en Colombia) y pos_y = longitud (-79..-66).
        # En metros de lote, pos_y jamás cae en ese rango → la doble condición es segura.
        lecturas = bind.execute(text(
            "SELECT id, pos_x, pos_y FROM agroia.sensor_readings "
            "WHERE finca_id = :fid "
            "AND pos_x BETWEEN -4.5 AND 13 AND pos_y BETWEEN -79.5 AND -66"
        ), {"fid": finca["id"]}).mappings().all()
        for lectura in lecturas:
            lat_deg = float(lectura["pos_x"])
            lon_deg = float(lectura["pos_y"])
            x, y = _relativa(
                float(finca["latitud"]), float(finca["longitud"]),
                lat_deg, lon_deg,
            )
            bind.execute(text(
                "UPDATE agroia.sensor_readings SET pos_x = :x, pos_y = :y WHERE id = :rid"
            ), {"x": x, "y": y, "rid": lectura["id"]})
            reparadas += 1
    print(f"[033_reparar_gps_relativo] Lecturas GPS reparadas a metros relativos: {reparadas}")


def downgrade() -> None:
    """No reversible: los grados originales no se conservan."""
    pass
