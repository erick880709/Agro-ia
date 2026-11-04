"""058 · Lote en lecturas de sensor (diferenciación multi-lote).

Revision ID: 058_sensor_reading_lote
Revises: 057_par_calibracion_unidad_suelo
Create Date: 2026-11-04

Agrega `lote_id` a `sensor_readings` para separar las mediciones por lote
(la trama del sensor envía `lote`, que se resuelve al UUID del lote de la
finca). Reversible.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "058_sensor_reading_lote"
down_revision = "057_par_calibracion_unidad_suelo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column(
            "lote_id",
            UUID(as_uuid=True),
            nullable=True,
            comment="Lote al que pertenece la medición (diferenciación multi-lote)",
        ),
        schema="agroia",
    )
    op.create_index(
        "ix_sensor_readings_lote_id",
        "sensor_readings",
        ["lote_id"],
        schema="agroia",
    )
    op.create_foreign_key(
        "fk_sensor_readings_lote",
        "sensor_readings",
        "lotes",
        ["lote_id"],
        ["id"],
        source_schema="agroia",
        referent_schema="agroia",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_sensor_readings_lote",
        "sensor_readings",
        schema="agroia",
        type_="foreignkey",
    )
    op.drop_index("ix_sensor_readings_lote_id", table_name="sensor_readings", schema="agroia")
    op.drop_column("sensor_readings", "lote_id", schema="agroia")
