"""036 · Autenticación JWT — blacklist de tokens y refresh tokens revocables.

Revision ID: 036_tokens_auth
Revises: 035_equipo_comisiones
Create Date: 2026-08-28
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "036_tokens_auth"
down_revision = "035_equipo_comisiones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tokens_blacklist",
        sa.Column("jti", sa.String(64), primary_key=True),
        sa.Column("tipo", sa.String(20), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="agroia",
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column(
            "revocado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
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
        "fk_refresh_tokens_usuario",
        "refresh_tokens",
        "usuarios",
        ["usuario_id"],
        ["id"],
        source_schema="agroia",
        referent_schema="agroia",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens", schema="agroia")
    op.drop_table("tokens_blacklist", schema="agroia")
