"""039 · Precios de cosecha por cultivo y departamento (inteligencia de mercado).

Revision ID: 039_precios_cosecha
Revises: 038_reglas_antagonismo
Create Date: 2026-08-28
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "039_precios_cosecha"
down_revision = "038_reglas_antagonismo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "precios_cosecha",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("cultivo_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("departamento", sa.String(100), nullable=False, index=True),
        sa.Column("precio_promedio_cop_kg", sa.Float(), nullable=False),
        sa.Column(
            "rendimiento_promedio_t_ha",
            sa.Float(),
            nullable=True,
            comment="Rendimiento de referencia regional (t/ha) para utilidad",
        ),
        sa.Column("fecha_actualizacion", sa.Date(), nullable=False, index=True),
        sa.Column("fuente", sa.String(100), nullable=False, server_default="Ingreso manual"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="agroia",
    )
    op.create_foreign_key(
        "fk_precios_cosecha_cultivo",
        "precios_cosecha",
        "cultivos",
        ["cultivo_id"],
        ["id"],
        source_schema="agroia",
        referent_schema="agroia",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_table("precios_cosecha", schema="agroia")
