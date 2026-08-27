"""tabla de labores / órdenes de trabajo.

Revision ID: 018_labores
Revises: 017_ciclo_inicio
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "018_labores"
down_revision = "017_ciclo_inicio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "labores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lote_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agroia.lotes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "recomendacion_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agroia.recomendaciones.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
            comment="Recomendación que originó la labor",
        ),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column(
            "tipo",
            sa.String(30),
            nullable=False,
            server_default="Fertilización",
            comment="Fertilización | Enmienda | Riego | Control Fitosanitario",
        ),
        sa.Column("producto", sa.String(150), nullable=True),
        sa.Column(
            "dosis_kg_ha",
            sa.Float(),
            nullable=True,
            comment="Dosis en kg/ha",
        ),
        sa.Column("fecha_programada", sa.Date(), nullable=True, index=True),
        sa.Column("fecha_ejecucion", sa.Date(), nullable=True),
        sa.Column(
            "responsable_id",
            UUID(as_uuid=True),
            sa.ForeignKey("agroia.usuarios.id"),
            nullable=True,
            comment="Usuario responsable de ejecutar la labor",
        ),
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default="Pendiente",
            comment="Pendiente | En Progreso | Completada | Cancelada",
        ),
        sa.Column("observaciones_ejecucion", sa.Text(), nullable=True),
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


def downgrade() -> None:
    op.drop_table("labores", schema="agroia")
