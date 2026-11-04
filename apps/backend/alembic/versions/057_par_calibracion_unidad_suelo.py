"""057 · Unidad de suelo en pares de calibración (Épica E9, TT-15).

Revision ID: 057_par_calibracion_unidad_suelo
Revises: 056_ciclo_vida_sensor
Create Date: 2026-11-04

Agrega `unidad_suelo` a `par_calibracion` para reportar el rendimiento del
modelo por unidad de suelo. Reversible.
"""

import sqlalchemy as sa
from alembic import op

revision = "057_par_calibracion_unidad_suelo"
down_revision = "056_ciclo_vida_sensor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "par_calibracion",
        sa.Column("unidad_suelo", sa.String(100), nullable=True,
                  comment="Unidad de suelo del par (andisol, oxisol, aluvial…)"),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("par_calibracion", "unidad_suelo", schema="agroia")
