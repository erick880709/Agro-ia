"""046 · AGC-COST F2-F7: estimaciones, identidad y documentos de cobro.

Revision ID: 046_costeo_estimaciones_cobros
Revises: 045_costeo_parametros
Create Date: 2026-09-18

Tablas de las fases F3-F5 del RFP AgroIA v4 §9:
  - estimacion / estimacion_linea / estimacion_snapshot / estimacion_evento
  - costeo_identidad / costeo_telefono (P-14)
  - cobro_config / cobro_documento / cobro_linea / cobro_pago / cobro_evento
Además agrega `origen_estimacion_id` a comision (F6: trazabilidad de origen).
Dinero en NUMERIC(18,4) — nunca flotante. Reversible.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "046_costeo_estimaciones_cobros"
down_revision = "045_costeo_parametros"
branch_labels = None
depends_on = None


def _audit() -> list[sa.Column]:
    """Columnas de auditoría comunes (RFP §9)."""
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
    # ── P-14 · Identidad y contacto ────────────────────────────────────────
    op.create_table(
        "costeo_identidad",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("conjunto_id", UUID(as_uuid=True), nullable=True),
        sa.Column("nombre_comercial", sa.String(150), nullable=False),
        sa.Column("razon_social", sa.String(150), nullable=True),
        sa.Column("nit", sa.String(30), nullable=True),
        sa.Column("regimen", sa.String(40), nullable=True),
        sa.Column("sitio_web", sa.String(200), nullable=True),
        sa.Column("correo", sa.String(120), nullable=True),
        sa.Column("direccion", sa.String(200), nullable=True),
        sa.Column("ciudad", sa.String(100), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("logo_oscuro_url", sa.String(500), nullable=True),
        sa.Column("color_acento", sa.String(9), nullable=True, server_default="#1b5e20"),
        sa.Column("pie_legal", sa.Text(), nullable=True),
        sa.Column("terminos_condiciones", sa.Text(), nullable=True),
        sa.Column("sede_latitud", sa.Float(), nullable=True),
        sa.Column("sede_longitud", sa.Float(), nullable=True),
        *_audit(),
        schema="agroia",
    )
    op.create_table(
        "costeo_telefono",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "identidad_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_identidad.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("etiqueta", sa.String(40), nullable=False),
        sa.Column("numero", sa.String(20), nullable=False),
        sa.Column("whatsapp", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
        schema="agroia",
    )

    # ── P-15 · Configuración de documentos de cobro ────────────────────────
    op.create_table(
        "cobro_config",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("conjunto_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "tipo_documento", sa.String(30), nullable=False, server_default="cuenta_cobro",
            comment="cuenta_cobro | factura_venta",
        ),
        sa.Column("prefijo", sa.String(10), nullable=False, server_default="CC"),
        sa.Column("numero_desde", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("numero_hasta", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("resolucion_dian", sa.String(40), nullable=True),
        sa.Column("resolucion_vigencia_hasta", sa.Date(), nullable=True),
        sa.Column("plazo_pago_dias", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("medios_pago", JSONB(), nullable=True),
        sa.Column("cuenta_bancaria", sa.Text(), nullable=True),
        sa.Column("textos_legales", JSONB(), nullable=True),
        sa.Column("aviso_numeracion_restante", sa.Integer(), nullable=False, server_default="10"),
        *_audit(),
        schema="agroia",
    )

    # ── F3 · Estimaciones ──────────────────────────────────────────────────
    op.create_table(
        "estimacion",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("consecutivo", sa.String(30), nullable=True),
        sa.Column(
            "finca_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.fincas.id", ondelete="RESTRICT"),
            nullable=False, index=True,
        ),
        sa.Column(
            "cliente_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "conjunto_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_conjunto.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "estado", sa.String(20), nullable=False, server_default="borrador",
            comment="borrador | emitida | aceptada | rechazada | vencida",
        ),
        sa.Column("fecha_referencia", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("area_total_ha", sa.Numeric(18, 4), nullable=True),
        sa.Column("total_directo", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("total_ajustado", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("precio_lista", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("descuento_aplicado", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("total_final", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("margen_pct", sa.Numeric(12, 4), nullable=True),
        sa.Column("vence_en", sa.Date(), nullable=True),
        sa.Column("emitido_por", UUID(as_uuid=True), nullable=True),
        sa.Column("emitido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo_excepcion", sa.Text(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("seleccion", JSONB(), nullable=True),
        sa.UniqueConstraint("consecutivo", name="uq_estimacion_consecutivo"),
        *_audit(),
        schema="agroia",
    )
    op.create_table(
        "estimacion_linea",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "estimacion_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.estimacion.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column(
            "lote_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.lotes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "servicio_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.costeo_servicio.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("componente_codigo", sa.String(40), nullable=True),
        sa.Column("descripcion", sa.String(250), nullable=False),
        sa.Column("cantidad", sa.Numeric(18, 4), nullable=False, server_default="1"),
        sa.Column("unidad", sa.String(20), nullable=True),
        sa.Column("valor_unitario", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("valor", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("parametro_ref", JSONB(), nullable=True),
        *_audit(),
        schema="agroia",
    )
    op.create_table(
        "estimacion_snapshot",
        sa.Column(
            "estimacion_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.estimacion.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("parametros", JSONB(), nullable=False),
        sa.Column("hash_sha256", sa.String(64), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_table(
        "estimacion_evento",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "estimacion_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.estimacion.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("evento", sa.String(40), nullable=False),
        sa.Column("usuario_id", UUID(as_uuid=True), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )

    # ── F5 · Documentos de cobro ───────────────────────────────────────────
    op.create_table(
        "cobro_documento",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("consecutivo", sa.Integer(), nullable=True),
        sa.Column("prefijo", sa.String(10), nullable=True),
        sa.Column(
            "tipo", sa.String(30), nullable=False, server_default="cuenta_cobro",
            comment="cuenta_cobro | factura_venta",
        ),
        sa.Column(
            "estimacion_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.estimacion.id", ondelete="RESTRICT"),
            nullable=False, index=True,
        ),
        sa.Column(
            "cliente_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.usuarios.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "estado", sa.String(25), nullable=False, server_default="borrador",
            comment="borrador | emitido | enviado | pagado_parcial | pagado | vencido | anulado",
        ),
        sa.Column("fecha_emision", sa.Date(), nullable=True),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=True),
        sa.Column("subtotal", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("impuestos", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("saldo", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("identidad_snapshot", JSONB(), nullable=True),
        sa.Column("cufe", sa.String(120), nullable=True),
        sa.Column("xml_url", sa.String(500), nullable=True),
        sa.Column("anulado_por", UUID(as_uuid=True), nullable=True),
        sa.Column("motivo_anulacion", sa.Text(), nullable=True),
        sa.Column("documento_anulado_id", UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("prefijo", "consecutivo", name="uq_cobro_consecutivo"),
        *_audit(),
        schema="agroia",
    )
    op.create_table(
        "cobro_linea",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "documento_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.cobro_documento.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("descripcion", sa.String(250), nullable=False),
        sa.Column("cantidad", sa.Numeric(18, 4), nullable=False, server_default="1"),
        sa.Column("unidad", sa.String(20), nullable=True),
        sa.Column("valor_unitario", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("valor", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("impuesto_codigo", sa.String(40), nullable=True),
        *_audit(),
        schema="agroia",
    )
    op.create_table(
        "cobro_pago",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "documento_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.cobro_documento.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("valor", sa.Numeric(18, 4), nullable=False),
        sa.Column("medio", sa.String(40), nullable=True),
        sa.Column("referencia", sa.String(120), nullable=True),
        sa.Column("soporte_url", sa.String(500), nullable=True),
        sa.Column("registrado_por", UUID(as_uuid=True), nullable=True),
        *_audit(),
        schema="agroia",
    )
    op.create_table(
        "cobro_evento",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "documento_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.cobro_documento.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("evento", sa.String(40), nullable=False),
        sa.Column("usuario_id", UUID(as_uuid=True), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )

    # ── F6 · Trazabilidad comisión ← estimación ────────────────────────────
    op.add_column(
        "comisiones",
        sa.Column(
            "origen_estimacion_id", UUID(as_uuid=True),
            sa.ForeignKey("agroia.estimacion.id", ondelete="SET NULL"),
            nullable=True,
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("comisiones", "origen_estimacion_id", schema="agroia")
    for tabla in (
        "cobro_evento", "cobro_pago", "cobro_linea", "cobro_documento",
        "estimacion_evento", "estimacion_snapshot", "estimacion_linea", "estimacion",
        "cobro_config", "costeo_telefono", "costeo_identidad",
    ):
        op.drop_table(tabla, schema="agroia")
