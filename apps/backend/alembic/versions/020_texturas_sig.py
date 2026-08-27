"""ampliar enum de texturas con clases granulométricas IGAC.

Revision ID: 020_texturas_sig
Revises: 019_alertas_climaticas
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op

revision = "020_texturas_sig"
down_revision = "019_alertas_climaticas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ADD VALUE IF NOT EXISTS (PostgreSQL 12+) para clases IGAC
    op.execute(
        sa.text(
            "ALTER TYPE agroia.texturasuelo ADD VALUE IF NOT EXISTS 'FRANCA'"
        )
    )
    op.execute(
        sa.text(
            "ALTER TYPE agroia.texturasuelo ADD VALUE IF NOT EXISTS 'FRANCO_ARENOSA'"
        )
    )
    op.execute(
        sa.text(
            "ALTER TYPE agroia.texturasuelo ADD VALUE IF NOT EXISTS 'FRANCO_ARCILLOSA'"
        )
    )
    op.execute(
        sa.text(
            "ALTER TYPE agroia.texturasuelo ADD VALUE IF NOT EXISTS 'FRANCO_LIMOSA'"
        )
    )


def downgrade() -> None:
    # PostgreSQL no permite remover valores de un enum; no-op honesto.
    pass
