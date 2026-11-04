"""049 · Perímetro calculado por lote (georreferenciación de lotes).

Revision ID: 049_lote_perimetro
Revises: 048_lectura_voz
Create Date: 2026-11-03

Agrega `perimetro_m` a `lotes` para que cada lote, además del área, registre
su perímetro calculado desde su geometría (el backend lo recalcula al
crear/editar). Reversible.
"""

import sqlalchemy as sa
from alembic import op

revision = "049_lote_perimetro"
down_revision = "048_lectura_voz"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lotes",
        sa.Column("perimetro_m", sa.Float(), nullable=True,
                  comment="Perímetro calculado de la geometría (m)"),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("lotes", "perimetro_m", schema="agroia")
