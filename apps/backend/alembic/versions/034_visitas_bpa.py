"""034 · Visitas de verificación BPA (trazabilidad por visita/medición).

Revision ID: 034_visitas_bpa
Revises: 033_reparar_gps_relativo
Create Date: 2026-08-28
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "034_visitas_bpa"
down_revision = "033_reparar_gps_relativo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checklist_bpa_visitas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("items", JSONB, nullable=False),
        sa.Column("verificado_por_email", sa.String(255), nullable=True),
        sa.Column("verificado_por_nombre", sa.String(200), nullable=True),
        sa.Column("verificado_rol", sa.String(40), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index(
        "idx_bpa_visitas_finca_fecha", "checklist_bpa_visitas",
        ["finca_id", "fecha"], schema="agroia",
    )


def downgrade() -> None:
    op.drop_index("idx_bpa_visitas_finca_fecha", table_name="checklist_bpa_visitas", schema="agroia")
    op.drop_table("checklist_bpa_visitas", schema="agroia")
