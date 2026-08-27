"""feedback humano sobre recomendaciones + campos agronómicos de la finca.

Revision ID: 010_feedback_recomendaciones
Revises: 009_reparar_enums_2
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "010_feedback_recomendaciones"
down_revision = "009_reparar_enums_2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Campos agronómicos de la finca (topografía, drenaje, historial, fenología) ──
    op.add_column(
        "fincas",
        sa.Column("pendiente_pct", sa.Float(), nullable=True,
                  comment="Pendiente del lote en porcentaje"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("drenaje", sa.String(20), nullable=True,
                  comment="Drenaje del lote: Bueno | Regular | Deficiente"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("historial_agronomico", JSONB(), nullable=True,
                  comment="Historial de manejo: cultivo anterior, fertilización, encalado"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("validacion_laboratorio", sa.Boolean(), nullable=False,
                  server_default=sa.text("false"),
                  comment="¿El análisis fue validado en laboratorio?"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("cultivo_sembrado", sa.String(100), nullable=True,
                  comment="Cultivo actualmente sembrado en la finca"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("edad_anos", sa.Float(), nullable=True,
                  comment="Edad del cultivo/árbol sembrado en años"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("etapa_fenologica", sa.String(30), nullable=True,
                  comment="Etapa fenológica: Vegetativa | Floración | Fructificación | Cosecha"),
        schema="agroia",
    )

    # ── Aceptaciones humanas de recomendaciones (feedback para el modelo) ──
    op.create_table(
        "aceptaciones_recomendacion",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("cultivo_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.cultivos.id", ondelete="SET NULL"),
                  nullable=True, index=True),
        sa.Column("rol", sa.String(20), nullable=False,
                  comment="Rol que aceptó: Admin | Agronomo"),
        sa.Column("comentario", sa.Text(), nullable=True,
                  comment="Ampliación/ajustes del experto"),
        sa.Column("resumen", JSONB(), nullable=True,
                  comment="Recomendaciones aceptadas (variables/acciones)"),
        sa.Column("clasificacion_previa", sa.String(50), nullable=True),
        sa.Column("confianza_previa", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("aceptaciones_recomendacion", schema="agroia")
    for col in (
        "pendiente_pct", "drenaje", "historial_agronomico",
        "validacion_laboratorio", "cultivo_sembrado", "edad_anos",
        "etapa_fenologica",
    ):
        op.drop_column("fincas", col, schema="agroia")
