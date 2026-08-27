"""imagen adjunta en el chat asesor (imagen_base64).

Revision ID: 013_chat_imagen
Revises: 012_suelo_riego
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op

revision = "013_chat_imagen"
down_revision = "012_suelo_riego"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_memoria",
        sa.Column(
            "imagen_base64",
            sa.Text(),
            nullable=True,
            comment="Foto del cultivo adjuntada en el chat (JPG/PNG en base64)",
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("chat_memoria", "imagen_base64", schema="agroia")
