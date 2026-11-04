"""055 · Parámetros administrables de calidad (Épica E7, HU-13).

Revision ID: 055_parametro_calidad
Revises: 054_sesion_muestreo
Create Date: 2026-11-04

Crea `parametro_calidad_sensor` (clave única, valor, versión, actor, fecha)
para administrar los umbrales del motor de calidad sin tocar código.

Reversible.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "055_parametro_calidad"
down_revision = "054_sesion_muestreo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parametro_calidad_sensor",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("clave", sa.String(100), nullable=False, unique=True),
        sa.Column("valor", sa.Float(), nullable=True),
        sa.Column("descripcion", sa.String(300), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("actor", sa.String(200), nullable=True),
        sa.Column("actualizado_en", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("parametro_calidad_sensor", schema="agroia")
