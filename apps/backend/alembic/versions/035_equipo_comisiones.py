"""035 · Equipo de trabajo, tarifas, comisiones, miembros y novedades.

Soporta el flujo operativo de órdenes de trabajo (toma de medidas en fincas):
equipo humano auditable, comisiones por finca con valores/costos y novedades
(incapacidades) con reemplazo.

Revision ID: 035_equipo_comisiones
Revises: 034_visitas_bpa
Create Date: 2026-08-28
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "035_equipo_comisiones"
down_revision = "034_visitas_bpa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Empleados (equipo de trabajo) ──
    op.create_table(
        "equipo_trabajo",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("nombres", sa.String(120), nullable=False),
        sa.Column("apellidos", sa.String(120), nullable=False),
        sa.Column("tipo_documento", sa.String(10), nullable=False),
        sa.Column("numero_documento", sa.String(20), nullable=False),
        sa.Column("lugar_domicilio", sa.String(200), nullable=True),
        sa.Column("numero_contacto", sa.String(20), nullable=True),
        sa.Column("contacto_emergencia_nombre", sa.String(200), nullable=True),
        sa.Column("contacto_emergencia_telefono", sa.String(20), nullable=True),
        sa.Column("rol", sa.String(30), nullable=False),
        sa.Column("fecha_ingreso", sa.Date(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="activo"),
        sa.Column("valor_dia_cop", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("uq_equipo_documento", "equipo_trabajo", ["numero_documento"], unique=True, schema="agroia")
    op.create_index("idx_equipo_rol_estado", "equipo_trabajo", ["rol", "estado"], schema="agroia")

    # ── Tarifas por rol (valor por día de trabajo) ──
    op.create_table(
        "tarifas_rol",
        sa.Column("rol", sa.String(30), primary_key=True),
        sa.Column("valor_dia_cop", sa.Numeric(12, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )

    # ── Comisiones (orden de trabajo por finca) ──
    op.create_table(
        "comisiones",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("servicio", sa.String(60), nullable=True),
        sa.Column("fecha_asignacion", sa.Date(), nullable=False),
        sa.Column("fecha_inicio_tomas", sa.Date(), nullable=True),
        sa.Column("fecha_fin_tomas", sa.Date(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="asignada"),
        sa.Column("valor_comision_cop", sa.Numeric(14, 2), nullable=True),
        sa.Column("valor_cobro_servicio_cop", sa.Numeric(14, 2), nullable=True),
        sa.Column("valor_validacion_cop", sa.Numeric(14, 2), nullable=True),
        sa.Column("valor_plataforma_cop", sa.Numeric(14, 2), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("idx_comisiones_finca", "comisiones", ["finca_id", "estado"], schema="agroia")

    # ── Miembros de comisión (instrumentador, cadeneros, chofer, agrónomo) ──
    op.create_table(
        "comision_miembros",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("comision_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.comisiones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("empleado_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.equipo_trabajo.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("rol_en_comision", sa.String(30), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("idx_comision_miembros_comision", "comision_miembros", ["comision_id"], schema="agroia")

    # ── Novedades de equipo (incapacidades/ausencias con reemplazo) ──
    op.create_table(
        "novedades_equipo",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("empleado_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.equipo_trabajo.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("comision_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.comisiones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("reemplazo_empleado_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.equipo_trabajo.id", ondelete="SET NULL"), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="abierta"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="agroia",
    )
    op.create_index("idx_novedades_empleado", "novedades_equipo", ["empleado_id", "estado"], schema="agroia")


def downgrade() -> None:
    op.drop_table("novedades_equipo", schema="agroia")
    op.drop_table("comision_miembros", schema="agroia")
    op.drop_table("comisiones", schema="agroia")
    op.drop_table("tarifas_rol", schema="agroia")
    op.drop_table("equipo_trabajo", schema="agroia")
