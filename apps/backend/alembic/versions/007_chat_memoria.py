"""Migration 007 — Memoria conversacional del chat por finca."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "007_chat_memoria"
down_revision = "006_posiciones_muestreo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_memoria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "finca_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("usuario_email", sa.String(255), nullable=True),
        sa.Column("rol", sa.String(50), nullable=True),
        sa.Column("pregunta", sa.Text(), nullable=False),
        sa.Column("respuesta", sa.Text(), nullable=False),
        sa.Column(
            "fuentes", sa.String(500), nullable=True,
            comment="Fuentes de conocimiento usadas",
        ),
        sa.Column(
            "confianza", sa.String(50), nullable=True,
            comment="Alta / Media / Baja",
        ),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("chat_memoria", schema="agroia")
