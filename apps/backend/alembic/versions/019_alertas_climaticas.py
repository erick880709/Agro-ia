"""tabla de alertas climáticas proactivas.

Revision ID: 019_alertas_climaticas
Revises: 018_labores
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "019_alertas_climaticas"
down_revision = "018_labores"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alertas_climaticas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "finca_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tipo",
            sa.String(40),
            nullable=False,
            index=True,
            comment="lluvia_aplicacion | helada_floracion",
        ),
        sa.Column(
            "severidad",
            sa.String(20),
            nullable=False,
            server_default="Alta",
            comment="Alta | Media",
        ),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("fecha_alerta", sa.Date(), nullable=False, index=True),
        sa.Column(
            "pronostico",
            JSONB(),
            nullable=True,
            comment="Pronóstico que disparó la alerta",
        ),
        sa.Column(
            "activa",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("alertas_climaticas", schema="agroia")
