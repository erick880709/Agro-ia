"""inicio rápido de ciclo: fecha de siembra/variedad/densidad en lote y ciclos.

Revision ID: 017_ciclo_inicio
Revises: 016_historial_ciclos_lote
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op

revision = "017_ciclo_inicio"
down_revision = "016_historial_ciclos_lote"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Lote: ciclo actual (se actualiza al iniciar un ciclo) ──
    op.add_column(
        "lotes",
        sa.Column(
            "fecha_siembra",
            sa.Date(),
            nullable=True,
            comment="Fecha de siembra del ciclo actual del lote",
        ),
        schema="agroia",
    )
    op.add_column(
        "lotes",
        sa.Column(
            "variedad",
            sa.String(100),
            nullable=True,
            comment="Variedad sembrada en el ciclo actual",
        ),
        schema="agroia",
    )
    op.add_column(
        "lotes",
        sa.Column(
            "densidad_siembra_plantas_ha",
            sa.Numeric(8, 0),
            nullable=True,
            comment="Densidad de siembra (plantas/ha)",
        ),
        schema="agroia",
    )

    # ── Ciclo: material de siembra ──
    op.add_column(
        "historial_ciclos_lote",
        sa.Column(
            "variedad",
            sa.String(100),
            nullable=True,
            comment="Variedad sembrada",
        ),
        schema="agroia",
    )
    op.add_column(
        "historial_ciclos_lote",
        sa.Column(
            "densidad_siembra_plantas_ha",
            sa.Numeric(8, 0),
            nullable=True,
            comment="Densidad de siembra (plantas/ha)",
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("historial_ciclos_lote", "densidad_siembra_plantas_ha", schema="agroia")
    op.drop_column("historial_ciclos_lote", "variedad", schema="agroia")
    op.drop_column("lotes", "densidad_siembra_plantas_ha", schema="agroia")
    op.drop_column("lotes", "variedad", schema="agroia")
    op.drop_column("lotes", "fecha_siembra", schema="agroia")
