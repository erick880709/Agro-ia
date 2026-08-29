"""042 · Visión: etiqueta_confirmada para aprendizaje activo (RQ-V6-01).

Revision ID: 042_vision_etiqueta_confirmada
Revises: 041_vision_diagnosticos
Create Date: 2026-08-29
"""
import sqlalchemy as sa
from alembic import op

revision = "042_vision_etiqueta_confirmada"
down_revision = "041_vision_diagnosticos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vision_diagnosticos",
        sa.Column("etiqueta_confirmada", sa.Text(), nullable=True),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("vision_diagnosticos", "etiqueta_confirmada", schema="agroia")
