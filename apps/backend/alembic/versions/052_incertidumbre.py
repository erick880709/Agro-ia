"""052 · Incertidumbre por lectura (Épica E3).

Revision ID: 052_incertidumbre
Revises: 051_motor_calidad
Create Date: 2026-11-04

Agrega `sensor_readings.incertidumbre` (JSONB): mapa variable → incertidumbre
estándar (distribución rectangular, exactitud/√3) calculada al ingestar.
Reversible.
"""

import sqlalchemy as sa
from alembic import op

revision = "052_incertidumbre"
down_revision = "051_motor_calidad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column("incertidumbre", sa.dialects.postgresql.JSONB(), nullable=True,
                  comment="Mapa variable → incertidumbre estándar (exactitud/√3)"),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("sensor_readings", "incertidumbre", schema="agroia")
