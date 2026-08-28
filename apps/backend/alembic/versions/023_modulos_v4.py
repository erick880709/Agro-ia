"""Módulos v4 (especificación técnica v4): migraciones 023 → 032.

023 analisis_agua_riego · 024 curvas_extraccion · 025 kc_cultivo ·
026 monitoreo_plagas · 027 variedades_cultivo · 028 compatibilidad_rotacion ·
029 checklist_bpa + periodos_carencia · 030 compactacion_lote ·
031 preferencias_notificacion · 032 rol_extensionista.

Revision ID: 023_modulos_v4
Revises: 022_imagenes_y_rendimiento
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "023_modulos_v4"
down_revision = "022_imagenes_y_rendimiento"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 023 · Análisis de agua de riego (FAO-29) ──
    op.create_table(
        "analisis_agua_riego",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", UUID(as_uuid=True), sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lote_id", UUID(as_uuid=True), sa.ForeignKey("agroia.lotes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("ce_agua_ds_m", sa.Numeric(6, 3), nullable=True),
        sa.Column("ras", sa.Numeric(6, 2), nullable=True),
        sa.Column("cloruros_mg_l", sa.Numeric(8, 2), nullable=True),
        sa.Column("boro_mg_l", sa.Numeric(6, 3), nullable=True),
        sa.Column("ph_agua", sa.Numeric(4, 2), nullable=True),
        sa.Column("fuente", sa.String(20), nullable=False, server_default="laboratorio"),
        sa.Column("clasificacion_restriccion", sa.String(30), nullable=True),
        sa.Column("creado_por", UUID(as_uuid=True), sa.ForeignKey("agroia.usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("idx_agua_riego_finca", "analisis_agua_riego", ["finca_id", "fecha"], schema="agroia")

    # ── 024 · Curvas de extracción nutricional ──
    op.create_table(
        "curvas_extraccion",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("cultivo_id", UUID(as_uuid=True), sa.ForeignKey("agroia.cultivos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("etapa_fenologica", sa.String(30), nullable=False),
        sa.Column("nutriente", sa.String(10), nullable=False),
        sa.Column("pct_extraccion_acumulado", sa.Numeric(5, 2), nullable=False),
        sa.Column("fuente", sa.Text(), nullable=True),
        sa.UniqueConstraint("cultivo_id", "etapa_fenologica", "nutriente", name="uq_curva_cultivo_etapa_nutriente"),
        schema="agroia",
    )

    # ── 025 · Kc FAO-56 en cultivos (balance hídrico) ──
    op.add_column("cultivos", sa.Column("kc_inicial", sa.Numeric(3, 2), nullable=True), schema="agroia")
    op.add_column("cultivos", sa.Column("kc_medio", sa.Numeric(3, 2), nullable=True), schema="agroia")
    op.add_column("cultivos", sa.Column("kc_final", sa.Numeric(3, 2), nullable=True), schema="agroia")

    # ── 026 · Monitoreo integrado de plagas ──
    op.create_table(
        "monitoreo_plagas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", UUID(as_uuid=True), sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lote_id", UUID(as_uuid=True), sa.ForeignKey("agroia.lotes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("cultivo_id", UUID(as_uuid=True), sa.ForeignKey("agroia.cultivos.id"), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("plaga_nombre", sa.String(120), nullable=False),
        sa.Column("plaga_nombre_cientifico", sa.String(150), nullable=True),
        sa.Column("metodo", sa.String(30), nullable=True),
        sa.Column("severidad", sa.String(10), nullable=True),
        sa.Column("incidencia_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("foto_url", sa.String(500), nullable=True),
        sa.Column("creado_por", UUID(as_uuid=True), sa.ForeignKey("agroia.usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )

    # ── 027 · Variedades/cultivares ──
    op.create_table(
        "variedades_cultivo",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("cultivo_id", UUID(as_uuid=True), sa.ForeignKey("agroia.cultivos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nombre_variedad", sa.String(100), nullable=False),
        sa.Column("resistencias", sa.Text(), nullable=True),
        sa.Column("altitud_min_msnm", sa.Integer(), nullable=True),
        sa.Column("altitud_max_msnm", sa.Integer(), nullable=True),
        sa.Column("mercado_objetivo", sa.String(60), nullable=True),
        sa.Column("fuente", sa.Text(), nullable=True),
        schema="agroia",
    )

    # ── 028 · Compatibilidad de rotación ──
    op.create_table(
        "compatibilidad_rotacion",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("cultivo_actual_id", UUID(as_uuid=True), sa.ForeignKey("agroia.cultivos.id"), nullable=False),
        sa.Column("cultivo_siguiente_id", UUID(as_uuid=True), sa.ForeignKey("agroia.cultivos.id"), nullable=False),
        sa.Column("beneficio", sa.String(20), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=True),
        schema="agroia",
    )

    # ── 029 · Trazabilidad BPA: checklist + períodos de carencia ──
    op.create_table(
        "checklist_bpa",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", UUID(as_uuid=True), sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item", sa.String(200), nullable=False),
        sa.Column("categoria", sa.String(60), nullable=True),
        sa.Column("cumple", sa.Boolean(), nullable=True),
        sa.Column("evidencia_url", sa.String(500), nullable=True),
        sa.Column("fecha_verificacion", sa.Date(), nullable=True),
        sa.Column("verificado_por", UUID(as_uuid=True), sa.ForeignKey("agroia.usuarios.id"), nullable=True),
        schema="agroia",
    )
    op.create_table(
        "periodos_carencia",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("producto", sa.String(150), nullable=False, unique=True),
        sa.Column("dias_carencia", sa.Integer(), nullable=False),
        sa.Column("fuente", sa.String(255), nullable=True),
        schema="agroia",
    )

    # ── 030 · Compactación del suelo (campo en lotes) ──
    op.add_column("lotes", sa.Column("resistencia_penetracion_kpa", sa.Numeric(6, 2), nullable=True), schema="agroia")

    # ── 031 · Preferencias de notificación ──
    op.create_table(
        "preferencias_notificacion",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", UUID(as_uuid=True), sa.ForeignKey("agroia.usuarios.id"), nullable=True),
        sa.Column("finca_id", UUID(as_uuid=True), sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"), nullable=True),
        sa.Column("canal", sa.String(20), nullable=False, server_default="ninguno"),
        sa.Column("telefono", sa.String(20), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        schema="agroia",
    )

    # ── 032 · Rol Extensionista + municipios asignados ──
    op.execute("ALTER TYPE agroia.rolusuario ADD VALUE IF NOT EXISTS 'EXTENSIONISTA'")
    op.add_column(
        "usuarios",
        sa.Column("municipios_asignados", sa.dialects.postgresql.ARRAY(sa.String()), nullable=True),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("usuarios", "municipios_asignados", schema="agroia")
    op.drop_table("preferencias_notificacion", schema="agroia")
    op.drop_column("lotes", "resistencia_penetracion_kpa", schema="agroia")
    op.drop_table("periodos_carencia", schema="agroia")
    op.drop_table("checklist_bpa", schema="agroia")
    op.drop_table("compatibilidad_rotacion", schema="agroia")
    op.drop_table("variedades_cultivo", schema="agroia")
    op.drop_table("monitoreo_plagas", schema="agroia")
    op.drop_column("cultivos", "kc_final", schema="agroia")
    op.drop_column("cultivos", "kc_medio", schema="agroia")
    op.drop_column("cultivos", "kc_inicial", schema="agroia")
    op.drop_table("curvas_extraccion", schema="agroia")
    op.drop_index("idx_agua_riego_finca", table_name="analisis_agua_riego", schema="agroia")
    op.drop_table("analisis_agua_riego", schema="agroia")
