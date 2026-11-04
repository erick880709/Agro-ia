"""054 · Protocolo de muestreo y contexto (Épica E5).

Revision ID: 054_sesion_muestreo
Revises: 053_calibracion_sensor
Create Date: 2026-11-04

1. Crea `sesion_muestreo` (punto, réplicas, profundidad, contexto de
   fertilización/riego/lluvia, observaciones, foto).
2. Agrega a `sensor_readings` los metadatos de muestreo: `profundidad_cm`,
   `punto_id`, `replica_n` y `sesion_muestreo_id` (RF-076).

Reversible.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "054_sesion_muestreo"
down_revision = "053_calibracion_sensor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sesion_muestreo",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", UUID(as_uuid=True), nullable=False),
        sa.Column("lote_id", UUID(as_uuid=True), nullable=True),
        sa.Column("punto_id", sa.String(100), nullable=False),
        sa.Column("replicas", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("profundidad_cm", sa.Integer(), nullable=True),
        sa.Column("pedregosidad", sa.String(50), nullable=True),
        sa.Column("tiempo_estabilizacion_s", sa.Integer(), nullable=True),
        sa.Column("observaciones", sa.String(500), nullable=True),
        sa.Column("foto_url", sa.String(500), nullable=True),
        sa.Column("fecha_ultima_fertilizacion", sa.Date(), nullable=True),
        sa.Column("fecha_ultimo_riego", sa.Date(), nullable=True),
        sa.Column("fecha_ultima_lluvia", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index(
        "ix_sesion_muestreo_finca", "sesion_muestreo", ["finca_id"],
        schema="agroia",
    )
    op.create_foreign_key(
        "fk_sesion_muestreo_finca", "sesion_muestreo", "fincas",
        ["finca_id"], ["id"], source_schema="agroia", referent_schema="agroia",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_sesion_muestreo_lote", "sesion_muestreo", "lotes",
        ["lote_id"], ["id"], source_schema="agroia", referent_schema="agroia",
        ondelete="SET NULL",
    )

    op.add_column(
        "sensor_readings",
        sa.Column("profundidad_cm", sa.Integer(), nullable=True,
                  comment="Profundidad de la lectura (centro de la capa)"),
        schema="agroia",
    )
    op.add_column(
        "sensor_readings",
        sa.Column("punto_id", sa.String(100), nullable=True,
                  comment="Identificador del punto de muestreo"),
        schema="agroia",
    )
    op.add_column(
        "sensor_readings",
        sa.Column("replica_n", sa.Integer(), nullable=True,
                  comment="Número de réplica dentro del punto"),
        schema="agroia",
    )
    op.add_column(
        "sensor_readings",
        sa.Column("sesion_muestreo_id", UUID(as_uuid=True), nullable=True,
                  comment="Sesión de muestreo a la que pertenece la lectura"),
        schema="agroia",
    )
    op.create_foreign_key(
        "fk_sensor_readings_sesion", "sensor_readings", "sesion_muestreo",
        ["sesion_muestreo_id"], ["id"],
        source_schema="agroia", referent_schema="agroia",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_sensor_readings_sesion", "sensor_readings",
                       schema="agroia", type_="foreignkey")
    op.drop_column("sensor_readings", "sesion_muestreo_id", schema="agroia")
    op.drop_column("sensor_readings", "replica_n", schema="agroia")
    op.drop_column("sensor_readings", "punto_id", schema="agroia")
    op.drop_column("sensor_readings", "profundidad_cm", schema="agroia")
    op.drop_table("sesion_muestreo", schema="agroia")
