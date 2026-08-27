"""historial de ciclos productivos por lote.

Revision ID: 016_historial_ciclos_lote
Revises: 015_auditoria
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "016_historial_ciclos_lote"
down_revision = "015_auditoria"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "historial_ciclos_lote",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lote_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agroia.lotes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "cultivo_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agroia.cultivos.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("fecha_siembra", sa.Date(), nullable=False),
        sa.Column("fecha_cosecha", sa.Date(), nullable=True),
        sa.Column(
            "rendimiento_tn_ha",
            sa.Numeric(8, 2),
            nullable=True,
            comment="Toneladas por hectárea",
        ),
        sa.Column(
            "calidad_cosecha",
            sa.String(20),
            nullable=True,
            comment="Premium | Estándar | Rechazo",
        ),
        sa.Column(
            "aplicaciones",
            JSONB(),
            nullable=True,
            comment="[{producto, dosis_kg_ha, fecha, tipo}, …]",
        ),
        sa.Column(
            "incidencias",
            JSONB(),
            nullable=True,
            comment="[{plaga, severidad, fecha, control}, …]",
        ),
        sa.Column(
            "practicas_riego",
            sa.String(50),
            nullable=True,
            comment="Goteo | Gravedad | Aspersión | Secano",
        ),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="agroia",
    )
    op.create_index(
        "idx_ciclos_lote",
        "historial_ciclos_lote",
        ["lote_id", "fecha_siembra"],
        unique=False,
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_index("idx_ciclos_lote", table_name="historial_ciclos_lote", schema="agroia")
    op.drop_table("historial_ciclos_lote", schema="agroia")
