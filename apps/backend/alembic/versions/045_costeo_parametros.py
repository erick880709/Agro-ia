"""045 · AGC-COST: catálogo de parámetros de costeo (F1).

Revision ID: 045_costeo_parametros
Revises: 044_comision_etapas
Create Date: 2026-09-18

Tablas del catálogo de parámetros administrables del módulo AGC-COST
(RFP AgroIA v4): conjunto versionado, servicios cotizables, componentes
de costo, tramos escalonados, factores, densidad, zonas, impuestos,
política comercial y descuentos. Dinero en NUMERIC(18,4) — nunca flotante.
Todas las tablas llevan auditoría (creado_por/creado_en/actualizado_por/
actualizado_en). Reversible.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "045_costeo_parametros"
down_revision = "044_comision_etapas"
branch_labels = None
depends_on = None


def _audit() -> list[sa.Column]:
    """Columnas de auditoría comunes a todas las tablas del módulo (RFP §9)."""
    return [
        sa.Column("creado_por", UUID(as_uuid=True), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actualizado_por", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "costeo_conjunto",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "estado", sa.String(20), nullable=False, server_default="borrador",
            comment="borrador | en_revision | publicado | archivado",
        ),
        sa.Column("vigencia_desde", sa.Date(), nullable=True),
        sa.Column("vigencia_hasta", sa.Date(), nullable=True),
        sa.Column("moneda", sa.String(5), nullable=False, server_default="COP"),
        sa.Column("aprobado_por", UUID(as_uuid=True), nullable=True),
        sa.Column("aprobado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        *_audit(),
        schema="agroia",
    )

    op.create_table(
        "costeo_servicio",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conjunto_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column(
            "unidad", sa.String(20), nullable=False,
            comment="punto | hectarea | dispositivo | dia | visita",
        ),
        sa.Column("requiere_lote", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
        sa.UniqueConstraint("conjunto_id", "codigo", name="uq_costeo_servicio_codigo"),
        schema="agroia",
    )

    op.create_table(
        "costeo_componente",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "servicio_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_servicio.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column(
            "tipo", sa.String(30), nullable=False,
            comment="fijo | escalonado | por_unidad | por_distancia | por_jornada | porcentual | condicional",
        ),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "afectable_por_factores", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "config", JSONB(), nullable=True,
            comment="Parámetros del tipo de componente (valor, unidad_ref, base, si…)",
        ),
        *_audit(),
        sa.UniqueConstraint("servicio_id", "codigo", name="uq_costeo_componente_codigo"),
        schema="agroia",
    )

    op.create_table(
        "costeo_tramo",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "componente_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_componente.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("desde", sa.Numeric(14, 2), nullable=False),
        sa.Column("hasta", sa.Numeric(14, 2), nullable=True),
        sa.Column("valor", sa.Numeric(18, 4), nullable=False),
        sa.Column(
            "modo", sa.String(20), nullable=False, server_default="marginal",
            comment="marginal | completo",
        ),
        *_audit(),
        schema="agroia",
    )

    op.create_table(
        "costeo_factor",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conjunto_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column(
            "aplicacion", sa.String(20), nullable=False, server_default="porcentual",
            comment="porcentual | multiplicativo",
        ),
        sa.Column(
            "combinacion", sa.String(20), nullable=False, server_default="suma",
            comment="suma | multiplica (cómo se combinan varios factores)",
        ),
        *_audit(),
        sa.UniqueConstraint("conjunto_id", "codigo", name="uq_costeo_factor_codigo"),
        schema="agroia",
    )

    op.create_table(
        "costeo_factor_opcion",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "factor_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_factor.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("etiqueta", sa.String(150), nullable=False),
        sa.Column("porcentaje", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
        sa.UniqueConstraint("factor_id", "codigo", name="uq_costeo_factor_opcion_codigo"),
        schema="agroia",
    )

    op.create_table(
        "costeo_densidad",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conjunto_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("area_min", sa.Numeric(12, 2), nullable=False),
        sa.Column("area_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("puntos_min", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("puntos_max", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("puntos_por_ha", sa.Numeric(8, 2), nullable=True),
        sa.Column("cultivo_id", UUID(as_uuid=True), nullable=True),
        *_audit(),
        schema="agroia",
    )

    op.create_table(
        "costeo_zona",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conjunto_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("departamento", sa.String(60), nullable=False),
        sa.Column("municipio", sa.String(80), nullable=True),
        sa.Column("factor", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("km_incluidos", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("tarifa_km", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("peajes_estimados", sa.Numeric(18, 4), nullable=False, server_default="0"),
        *_audit(),
        schema="agroia",
    )

    op.create_table(
        "costeo_impuesto",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conjunto_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("porcentaje", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column(
            "base", sa.String(30), nullable=False, server_default="subtotal",
            comment="directo | ajustado | lista (base gravable)",
        ),
        sa.Column(
            "informativo", sa.Boolean(), nullable=False, server_default=sa.text("false"),
            comment="true = se muestra pero no suma al total",
        ),
        *_audit(),
        schema="agroia",
    )

    op.create_table(
        "costeo_politica",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conjunto_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
            nullable=False, unique=True,
        ),
        sa.Column("margen_objetivo", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("margen_minimo", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("piso_visita", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("vigencia_cotizacion_dias", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("redondeo_multiplo", sa.Numeric(12, 2), nullable=False, server_default="1"),
        sa.Column(
            "redondeo_modo", sa.String(20), nullable=False, server_default="ninguno",
            comment="ninguno | mitad_superior | techo | piso",
        ),
        *_audit(),
        schema="agroia",
    )

    op.create_table(
        "costeo_descuento",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conjunto_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column(
            "criterio", sa.String(40), nullable=False,
            comment="volumen_ha | n_fincas | contrato | asociacion | urgencia | no_habil | manual",
        ),
        sa.Column("umbral", sa.Numeric(14, 2), nullable=True),
        sa.Column("porcentaje", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column(
            "tope_rol", JSONB(), nullable=True,
            comment='Tope de descuento por rol, ej. {"agronomo": 5, "admin": null}',
        ),
        *_audit(),
        schema="agroia",
    )


def downgrade() -> None:
    for tabla in (
        "costeo_descuento",
        "costeo_politica",
        "costeo_impuesto",
        "costeo_zona",
        "costeo_densidad",
        "costeo_factor_opcion",
        "costeo_factor",
        "costeo_tramo",
        "costeo_componente",
        "costeo_servicio",
        "costeo_conjunto",
    ):
        op.drop_table(tabla, schema="agroia")
