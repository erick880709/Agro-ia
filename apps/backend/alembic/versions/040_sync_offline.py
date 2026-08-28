"""040 · Registro de sincronización offline (idempotencia de batches).

Revision ID: 040_sync_offline
Revises: 039_precios_cosecha
Create Date: 2026-08-28
"""
import sqlalchemy as sa
from alembic import op

revision = "040_sync_offline"
down_revision = "039_precios_cosecha"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_registro",
        sa.Column("idempotency_key", sa.String(128), primary_key=True),
        sa.Column("tipo", sa.String(30), nullable=False, index=True),
        sa.Column("usuario_email", sa.String(200), nullable=True),
        sa.Column("resultado", sa.String(400), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("sync_registro", schema="agroia")
