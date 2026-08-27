"""fisiología del cultivo: profundidad radicular, GDD y días de ciclo.

Revision ID: 014_fisiologia_cultivos
Revises: 013_chat_imagen
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op

revision = "014_fisiologia_cultivos"
down_revision = "013_chat_imagen"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cultivos",
        sa.Column(
            "profundidad_radicular_min_cm",
            sa.Integer(),
            nullable=True,
            comment="Profundidad radicular mínima requerida (cm)",
        ),
        schema="agroia",
    )
    op.add_column(
        "cultivos",
        sa.Column(
            "gdd_total_requerido",
            sa.Integer(),
            nullable=True,
            comment="Grados-día acumulados (GDD, T base 10 °C) para madurez",
        ),
        schema="agroia",
    )
    op.add_column(
        "cultivos",
        sa.Column(
            "dias_ciclo",
            sa.Integer(),
            nullable=True,
            comment="Duración del ciclo (días, siembra→cosecha)",
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("cultivos", "dias_ciclo", schema="agroia")
    op.drop_column("cultivos", "gdd_total_requerido", schema="agroia")
    op.drop_column("cultivos", "profundidad_radicular_min_cm", schema="agroia")
