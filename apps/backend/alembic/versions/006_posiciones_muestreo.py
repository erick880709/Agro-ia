"""Migration 006 — Posición de muestreo (x, y) en lecturas de sensor.

Soporta el muestreo en cuadrícula del lote: cada toma tiene coordenadas
(pos_x, pos_y) en metros desde la esquina del terreno. Estas posiciones
permiten pintar el mapa de calor por variable en el reporte.
"""

import sqlalchemy as sa
from alembic import op

revision = "006_posiciones_muestreo"
down_revision = "005_fix_enum_values"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column(
            "pos_x", sa.Float(), nullable=True,
            comment="Posición X de la toma en el lote (metros desde la esquina, muestreo en cuadrícula)",
        ),
        schema="agroia",
    )
    op.add_column(
        "sensor_readings",
        sa.Column(
            "pos_y", sa.Float(), nullable=True,
            comment="Posición Y de la toma en el lote (metros desde la esquina, muestreo en cuadrícula)",
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("sensor_readings", "pos_y", schema="agroia")
    op.drop_column("sensor_readings", "pos_x", schema="agroia")
