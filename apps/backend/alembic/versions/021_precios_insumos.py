"""tabla de precios dinámicos de insumos (ROI actualizable).

Revision ID: 021_precios_insumos
Revises: 020_texturas_sig
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "021_precios_insumos"
down_revision = "020_texturas_sig"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "precios_insumos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "producto",
            sa.String(100),
            nullable=False,
            unique=True,
            index=True,
            comment="Nombre comercial del insumo (clave de negocio)",
        ),
        sa.Column(
            "precio_kg_cop",
            sa.Float(),
            nullable=False,
            comment="Precio en COP por kilogramo",
        ),
        sa.Column(
            "fecha_actualizacion",
            sa.Date(),
            nullable=False,
            index=True,
            comment="Fecha en que el Admin actualizó el precio",
        ),
        sa.Column(
            "fuente",
            sa.String(255),
            nullable=True,
            comment="Fuente del precio (cotización, agrotienda, bolsa…)",
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
    op.drop_table("precios_insumos", schema="agroia")
