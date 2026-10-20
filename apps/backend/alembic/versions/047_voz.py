"""047 · Interacción por voz (RFP-AGROIA-001): parámetros y métricas.

Revision ID: 047_voz
Revises: 046_costeo_estimaciones_cobros
Create Date: 2026-10-19

Crea las tablas `parametro_voz` (configuración global: activación, duración
máxima e idioma) y `metrica_voz` (agregados mensuales de uso: consultas,
errores y duración total, sin audio ni contenido). Reversible.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "047_voz"
down_revision = "046_costeo_estimaciones_cobros"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parametro_voz",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("activado", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("duracion_maxima_segundos", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("idioma", sa.String(10), nullable=False, server_default="es"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )

    op.create_table(
        "metrica_voz",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("periodo", sa.String(7), nullable=False, index=True, comment="Periodo de agregación YYYY-MM"),
        sa.Column("consultas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errores", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duracion_total_ms", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("periodo", name="uq_metrica_voz_periodo"),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("metrica_voz", schema="agroia")
    op.drop_table("parametro_voz", schema="agroia")
