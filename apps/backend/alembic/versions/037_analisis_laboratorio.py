"""037 · Análisis de laboratorio ICA (ingesta de resultados de suelo).

Revision ID: 037_analisis_laboratorio
Revises: 036_tokens_auth
Create Date: 2026-08-28
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "037_analisis_laboratorio"
down_revision = "036_tokens_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analisis_laboratorio",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("lote_id", UUID(as_uuid=True), nullable=True),
        sa.Column("usuario_id", UUID(as_uuid=True), nullable=True),
        sa.Column("laboratorio_nombre", sa.String(200), nullable=True),
        sa.Column("fecha_muestreo", sa.Date(), nullable=False, index=True),
        sa.Column("fecha_resultado", sa.Date(), nullable=False, index=True),
        sa.Column(
            "resultados",
            JSONB(),
            nullable=False,
            comment="Pares variable -> valor (pH, N, P, K, MO…)",
        ),
        sa.Column(
            "fuente",
            sa.String(40),
            nullable=False,
            server_default="ingreso_manual",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="agroia",
    )
    op.create_foreign_key(
        "fk_analisis_lab_finca",
        "analisis_laboratorio",
        "fincas",
        ["finca_id"],
        ["id"],
        source_schema="agroia",
        referent_schema="agroia",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_analisis_lab_lote",
        "analisis_laboratorio",
        "lotes",
        ["lote_id"],
        ["id"],
        source_schema="agroia",
        referent_schema="agroia",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_analisis_lab_usuario",
        "analisis_laboratorio",
        "usuarios",
        ["usuario_id"],
        ["id"],
        source_schema="agroia",
        referent_schema="agroia",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_table("analisis_laboratorio", schema="agroia")
