"""038 · Reglas de antagonismo/sinergia nutricional (tipo en reglas_agronomicas).

Revision ID: 038_reglas_antagonismo
Revises: 037_analisis_laboratorio
Create Date: 2026-08-28
"""
import sqlalchemy as sa
from alembic import op

revision = "038_reglas_antagonismo"
down_revision = "037_analisis_laboratorio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reglas_agronomicas",
        sa.Column(
            "tipo",
            sa.String(30),
            nullable=False,
            server_default="primaria",
            comment="primaria | antagonismo",
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("reglas_agronomicas", "tipo", schema="agroia")
