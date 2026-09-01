"""044 · Comisiones: etapas de recomendación y reporte fin de etapa.

Revision ID: 044_comision_etapas
Revises: 043_add_bristol_preferences
Create Date: 2026-08-31

Amplía `comisiones.estado` de VARCHAR(20) a VARCHAR(40) para dar cabida a
los nuevos estados del flujo:
  - `en_recomendacion`            (se generó al menos una recomendación)
  - `generacion_reporte_fin_etapa` (se generó el reporte fin de etapa)
"""

import sqlalchemy as sa
from alembic import op

revision = "044_comision_etapas"
down_revision = "043_add_bristol_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "comisiones",
        "estado",
        existing_type=sa.String(length=20),
        type_=sa.String(length=40),
        existing_nullable=False,
        schema="agroia",
    )


def downgrade() -> None:
    op.alter_column(
        "comisiones",
        "estado",
        existing_type=sa.String(length=40),
        type_=sa.String(length=20),
        existing_nullable=False,
        schema="agroia",
    )
