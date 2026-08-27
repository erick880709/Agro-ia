"""características físicas del suelo y tipo de riego.

Revision ID: 012_suelo_riego
Revises: 011_fincas_geo_lotes
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "012_suelo_riego"
down_revision = "011_fincas_geo_lotes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums nuevos (nombres alineados con los modelos Python)
    op.execute(
        "DO $$ BEGIN CREATE TYPE agroia.pedregosidad AS ENUM "
        "('NINGUNA','MODERADA','ALTA'); EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    )
    op.execute(
        "DO $$ BEGIN CREATE TYPE agroia.tiporiego AS ENUM "
        "('GOTEO','ASPERSION','GRAVEDAD','SECANO'); EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    )

    op.add_column(
        "lotes",
        sa.Column("profundidad_suelo_cm", sa.Integer(), nullable=True,
                  comment="Profundidad efectiva del suelo (cm); categorías: 25, 45, 75, 100"),
        schema="agroia",
    )
    op.add_column(
        "lotes",
        sa.Column("pedregosidad", postgresql.ENUM("NINGUNA", "MODERADA", "ALTA",
                                                   name="pedregosidad", schema="agroia",
                                                   create_type=False),
                  nullable=True, comment="Pedregosidad del lote"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("tipo_riego", postgresql.ENUM("GOTEO", "ASPERSION", "GRAVEDAD", "SECANO",
                                                 name="tiporiego", schema="agroia",
                                                 create_type=False),
                  nullable=True, comment="Tipo de riego predominante"),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("fincas", "tipo_riego", schema="agroia")
    op.drop_column("lotes", "pedregosidad", schema="agroia")
    op.drop_column("lotes", "profundidad_suelo_cm", schema="agroia")
    op.execute("DROP TYPE IF EXISTS agroia.tiporiego")
    op.execute("DROP TYPE IF EXISTS agroia.pedregosidad")
