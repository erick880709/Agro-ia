"""053 · Calibración local del sensor (Épica E4).

Revision ID: 053_calibracion_sensor
Revises: 052_incertidumbre
Create Date: 2026-11-04

Crea:
  - `calibracion_sensor`: regresión lineal (pendiente/intercepto) por
    dispositivo, variable y unidad de suelo, con métricas y vigencia.
  - `par_calibracion`: pares sensor–laboratorio que alimentan la calibración.

Reversible.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "053_calibracion_sensor"
down_revision = "052_incertidumbre"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calibracion_sensor",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("dispositivo_id", UUID(as_uuid=True), nullable=False),
        sa.Column("variable", sa.String(40), nullable=False),
        sa.Column("unidad_suelo", sa.String(100), nullable=True),
        sa.Column("pendiente", sa.Float(), nullable=False),
        sa.Column("intercepto", sa.Float(), nullable=False, server_default="0"),
        sa.Column("n", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("r2", sa.Float(), nullable=True),
        sa.Column("rmse", sa.Float(), nullable=True),
        sa.Column("sesgo", sa.Float(), nullable=True),
        sa.Column("vigencia", sa.Date(), nullable=True),
        sa.Column("responsable", sa.String(200), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index(
        "ix_calibracion_sensor_dispositivo_variable",
        "calibracion_sensor", ["dispositivo_id", "variable"],
        schema="agroia",
    )
    op.create_foreign_key(
        "fk_calibracion_sensor_dispositivo",
        "calibracion_sensor", "dispositivos_iot",
        ["dispositivo_id"], ["id"],
        source_schema="agroia", referent_schema="agroia",
        ondelete="CASCADE",
    )

    op.create_table(
        "par_calibracion",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("calibracion_id", UUID(as_uuid=True), nullable=True),
        sa.Column("dispositivo_id", UUID(as_uuid=True), nullable=False),
        sa.Column("variable", sa.String(40), nullable=False),
        sa.Column("valor_sensor", sa.Float(), nullable=False),
        sa.Column("valor_laboratorio", sa.Float(), nullable=False),
        sa.Column("metodo", sa.String(200), nullable=True),
        sa.Column("laboratorio", sa.String(200), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("profundidad_cm", sa.Integer(), nullable=True),
        sa.Column("punto_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index(
        "ix_par_calibracion_dispositivo_variable",
        "par_calibracion", ["dispositivo_id", "variable"],
        schema="agroia",
    )
    op.create_foreign_key(
        "fk_par_calibracion_dispositivo",
        "par_calibracion", "dispositivos_iot",
        ["dispositivo_id"], ["id"],
        source_schema="agroia", referent_schema="agroia",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_par_calibracion_calibracion",
        "par_calibracion", "calibracion_sensor",
        ["calibracion_id"], ["id"],
        source_schema="agroia", referent_schema="agroia",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_table("par_calibracion", schema="agroia")
    op.drop_table("calibracion_sensor", schema="agroia")
