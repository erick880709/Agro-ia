"""041 · Diagnósticos de visión por computadora (plagas).

Revision ID: 041_vision_diagnosticos
Revises: 040_sync_offline
Create Date: 2026-08-28
"""
import sqlalchemy as sa
from alembic import op

revision = "041_vision_diagnosticos"
down_revision = "040_sync_offline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vision_diagnosticos",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("finca_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("usuario_id", sa.Uuid(), nullable=True, index=True),
        sa.Column("imagen_url", sa.String(500), nullable=True),
        sa.Column("resultado_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("vision_diagnosticos", schema="agroia")
