"""056 · Ciclo de vida del sensor (Épica E8).

Revision ID: 056_ciclo_vida_sensor
Revises: 055_parametro_calidad
Create Date: 2026-11-04

1. Crea `mantenimiento_sensor` (registro de limpieza/revisión/reemplazo).
2. Agrega a `dispositivos_iot`: `voltaje_alimentacion` y `errores_crc`
   (telemetría de salud, TT-13).

Reversible.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "056_ciclo_vida_sensor"
down_revision = "055_parametro_calidad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mantenimiento_sensor",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("dispositivo_id", UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("observaciones", sa.String(500), nullable=True),
        sa.Column("responsable", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index(
        "ix_mantenimiento_sensor_dispositivo",
        "mantenimiento_sensor", ["dispositivo_id"],
        schema="agroia",
    )
    op.create_foreign_key(
        "fk_mantenimiento_sensor_dispositivo",
        "mantenimiento_sensor", "dispositivos_iot",
        ["dispositivo_id"], ["id"],
        source_schema="agroia", referent_schema="agroia",
        ondelete="CASCADE",
    )

    op.add_column(
        "dispositivos_iot",
        sa.Column("voltaje_alimentacion", sa.Float(), nullable=True,
                  comment="Voltaje de alimentación (V)"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("errores_crc", sa.Integer(), nullable=True,
                  server_default="0",
                  comment="Errores CRC acumulados"),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("dispositivos_iot", "errores_crc", schema="agroia")
    op.drop_column("dispositivos_iot", "voltaje_alimentacion", schema="agroia")
    op.drop_table("mantenimiento_sensor", schema="agroia")
