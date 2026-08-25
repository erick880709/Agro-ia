"""Initial migration — Motor de Recomendaciones AgroIA

Revision ID: 001_recomendaciones
Create Date: 2026-08-04

Crea las tablas del motor de recomendaciones:
  - recomendaciones
  - discordancias
  - reglas_agronomicas
  - modelos_ml
  - metricas_modelo

Todas en schema 'agroia'.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_recomendaciones"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Enums ──
    clasificacion_upra_enum = postgresql.ENUM(
        "Alta", "Media", "Baja", "NoApta",
        name="clasificacion_upra_enum",
        schema="agroia",
        create_type=False,
    )
    clasificacion_upra_enum.create(op.get_bind(), checkfirst=True)

    estado_recomendacion_enum = postgresql.ENUM(
        "Publicada", "Advertencia", "Bloqueada",
        name="estado_recomendacion_enum",
        schema="agroia",
        create_type=False,
    )
    estado_recomendacion_enum.create(op.get_bind(), checkfirst=True)

    estado_discordancia_enum = postgresql.ENUM(
        "Pendiente", "Revisada", "Bloqueada",
        name="estado_discordancia_enum",
        schema="agroia",
        create_type=False,
    )
    estado_discordancia_enum.create(op.get_bind(), checkfirst=True)

    variable_suelo_enum = postgresql.ENUM(
        "pH", "N", "P", "K", "Ca", "Mg", "S", "Fe", "Mn",
        "Zn", "Cu", "B", "MO", "CIC", "textura", "humedad",
        "temperatura_suelo", "CE",
        name="variable_suelo_enum",
        schema="agroia",
        create_type=False,
    )
    variable_suelo_enum.create(op.get_bind(), checkfirst=True)

    prioridad_regla_enum = postgresql.ENUM(
        "Critica", "Alta", "Media", "Baja",
        name="prioridad_regla_enum",
        schema="agroia",
        create_type=False,
    )
    prioridad_regla_enum.create(op.get_bind(), checkfirst=True)

    stage_modelo_enum = postgresql.ENUM(
        "Staging", "Production", "Archived",
        name="stage_modelo_enum",
        schema="agroia",
        create_type=False,
    )
    stage_modelo_enum.create(op.get_bind(), checkfirst=True)

    # ── Tabla: recomendaciones ──
    op.create_table(
        "recomendaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cultivo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clasificacion_upra", clasificacion_upra_enum, nullable=False),
        sa.Column("confianza", sa.Float(), nullable=False, comment="F1-score (0-1)"),
        sa.Column("justificacion", postgresql.JSONB(), nullable=False),
        sa.Column("estado", estado_recomendacion_enum, nullable=False, server_default="Publicada"),
        sa.Column("tecnico_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("ix_recomendaciones_finca_id", "recomendaciones", ["finca_id"], schema="agroia")
    op.create_index("ix_recomendaciones_cultivo_id", "recomendaciones", ["cultivo_id"], schema="agroia")
    op.create_index("ix_recomendaciones_estado", "recomendaciones", ["estado"], schema="agroia")
    op.create_index("ix_recomendaciones_tenant_id", "recomendaciones", ["tenant_id"], schema="agroia")
    op.create_index("ix_recomendaciones_created_at", "recomendaciones", ["created_at"], schema="agroia")

    # ── Tabla: discordancias ──
    op.create_table(
        "discordancias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recomendacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prediccion_ml", postgresql.JSONB(), nullable=False),
        sa.Column("regla_aplicada", postgresql.JSONB(), nullable=False),
        sa.Column("motivo_conflicto", sa.Text(), nullable=False),
        sa.Column("estado", estado_discordancia_enum, nullable=False, server_default="Pendiente"),
        sa.Column("resolucion", sa.Text(), nullable=True),
        sa.Column("tecnico_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sla_vencimiento", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("ix_discordancias_recomendacion_id", "discordancias", ["recomendacion_id"], schema="agroia")
    op.create_index("ix_discordancias_estado", "discordancias", ["estado"], schema="agroia")

    # ── Tabla: reglas_agronomicas ──
    op.create_table(
        "reglas_agronomicas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cultivo_id", postgresql.UUID(as_uuid=True), nullable=True, comment="NULL = universal"),
        sa.Column("variable", variable_suelo_enum, nullable=False),
        sa.Column("umbral_min", sa.Float(), nullable=True),
        sa.Column("umbral_max", sa.Float(), nullable=True),
        sa.Column("accion", sa.Text(), nullable=False),
        sa.Column("prioridad", prioridad_regla_enum, nullable=False, server_default="Media"),
        sa.Column("fuente", sa.String(100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("ix_reglas_variable", "reglas_agronomicas", ["variable"], schema="agroia")
    op.create_index("ix_reglas_cultivo", "reglas_agronomicas", ["cultivo_id"], schema="agroia")

    # ── Tabla: modelos_ml ──
    op.create_table(
        "modelos_ml",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("tipo_modelo", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("f1_score", sa.Float(), nullable=True),
        sa.Column("mlflow_run_id", sa.String(100), nullable=True),
        sa.Column("stage", stage_modelo_enum, nullable=False, server_default="Staging"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("ix_modelos_ml_nombre", "modelos_ml", ["nombre"], schema="agroia")

    # ── Tabla: metricas_modelo ──
    op.create_table(
        "metricas_modelo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("modelo_ml_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metrica", sa.String(50), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("fecha_registro", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("ix_metricas_modelo_ml_id", "metricas_modelo", ["modelo_ml_id"], schema="agroia")
    op.create_index("ix_metricas_fecha", "metricas_modelo", ["fecha_registro"], schema="agroia")


def downgrade() -> None:
    op.drop_table("metricas_modelo", schema="agroia")
    op.drop_table("modelos_ml", schema="agroia")
    op.drop_table("reglas_agronomicas", schema="agroia")
    op.drop_table("discordancias", schema="agroia")
    op.drop_table("recomendaciones", schema="agroia")

    # ── Drop enums ──
    for enum_name in (
        "stage_modelo_enum", "prioridad_regla_enum", "variable_suelo_enum",
        "estado_discordancia_enum", "estado_recomendacion_enum", "clasificacion_upra_enum",
    ):
        op.execute(f"DROP TYPE IF EXISTS agroia.{enum_name}")
