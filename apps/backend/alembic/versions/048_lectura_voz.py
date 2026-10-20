"""048 · Lectura en voz alta (RFP-AGROIA-002): preferencias, métricas y voz personalizada.

Revision ID: 048_lectura_voz
Revises: 047_voz
Create Date: 2026-10-19

Crea `preferencia_lectura_voz` (activado/voz/velocidad por usuario),
`metrica_lectura_voz` (agregados mensuales de uso) y `voz_personalizada`
(ciclo de vida de la voz clonada, Fase 2). Reversible.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "048_lectura_voz"
down_revision = "047_voz"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "preferencia_lectura_voz",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_email", sa.String(255), nullable=False),
        sa.Column("activado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("voz", sa.String(20), nullable=False, server_default="femenina"),
        sa.Column("velocidad", sa.String(10), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("usuario_email", name="uq_preferencia_lectura_email"),
        schema="agroia",
    )
    op.create_index(
        "ix_preferencia_lectura_voz_email", "preferencia_lectura_voz", ["usuario_email"],
        unique=True, schema="agroia",
    )

    op.create_table(
        "metrica_lectura_voz",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("activaciones", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("voz_elegida", sa.String(20), nullable=True),
        sa.Column("errores", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("caracteres_leidos", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("periodo", name="uq_metrica_lectura_periodo"),
        schema="agroia",
    )
    op.create_index(
        "ix_metrica_lectura_voz_periodo", "metrica_lectura_voz", ["periodo"], schema="agroia"
    )

    op.create_table(
        "voz_personalizada",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_email", sa.String(255), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="procesando"),
        sa.Column("referencia", sa.String(255), nullable=True),
        sa.Column("creada_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("usuario_email", name="uq_voz_personalizada_email"),
        schema="agroia",
    )
    op.create_index(
        "ix_voz_personalizada_email", "voz_personalizada", ["usuario_email"],
        unique=True, schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("voz_personalizada", schema="agroia")
    op.drop_table("metrica_lectura_voz", schema="agroia")
    op.drop_table("preferencia_lectura_voz", schema="agroia")
