"""Migration 003 — Infraestructura: usuarios, fincas, sensor_readings, fincas_usuarios.

Estas tablas existían en desarrollo vía `migrate.py` (create_all) pero no
estaban cubiertas por la cadena Alembic; el CI fallaba porque la migración
003 (dispositivos_iot) referencia `agroia.fincas`.

Revision ID: 003_infra_fincas
Down revision: 002_catalogo_cultivos
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_infra_fincas"
down_revision: str | None = "002_catalogo_cultivos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _crear_enum(nombre: str, valores: list[str]) -> postgresql.ENUM:
    enum = postgresql.ENUM(
        *valores, name=nombre, schema="agroia", create_type=False
    )
    enum.create(op.get_bind(), checkfirst=True)
    return enum


def upgrade() -> None:
    rol_enum = _crear_enum(
        "rolusuario",
        ["Admin", "Agronomo", "Cliente", "Tecnico", "Investigador"],
    )
    plan_enum = _crear_enum("planmembresia", ["Mensual", "Semestral", "Anual"])
    estado_membresia_enum = _crear_enum(
        "estadomembresia", ["Activa", "Vencida", "Cancelada"]
    )
    textura_enum = _crear_enum("texturasuelo", ["Arena", "Limo", "Arcilla"])

    # ── usuarios ──
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("rol", rol_enum, nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "consentimiento_datos", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
            comment="Consentimiento informado Ley 1581/2012",
        ),
        sa.Column(
            "email_verificado", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="agroia",
    )

    # ── membresias ──
    op.create_table(
        "membresias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agroia.usuarios.id"), nullable=False, unique=True, index=True,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("plan", plan_enum, nullable=False),
        sa.Column("estado", estado_membresia_enum, nullable=False, server_default="Activa"),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("fecha_vencimiento", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "fincas_permitidas", sa.Integer(), nullable=False, server_default="1",
            comment="Número máximo de fincas según el plan",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="agroia",
    )

    # ── fincas ──
    op.create_table(
        "fincas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agroia.usuarios.id"), nullable=False, index=True,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("latitud", sa.Float(), nullable=True, comment="Latitud GPS (WGS84)"),
        sa.Column("longitud", sa.Float(), nullable=True, comment="Longitud GPS (WGS84)"),
        sa.Column("area_hectareas", sa.Float(), nullable=True, comment="Área total en hectáreas"),
        sa.Column("altitud_msnm", sa.Float(), nullable=True, comment="Altitud en metros sobre el nivel del mar"),
        sa.Column("departamento", sa.String(100), nullable=True),
        sa.Column("municipio", sa.String(100), nullable=True),
        sa.Column("coordenadas_google", sa.String(500), nullable=True, comment="Enlace de Google Maps o 'lat,lng'"),
        sa.Column("propietario", sa.String(200), nullable=True),
        sa.Column("contacto_telefono", sa.String(50), nullable=True),
        sa.Column("contacto_email", sa.String(255), nullable=True),
        sa.Column("largo_metros", sa.Float(), nullable=True),
        sa.Column("ancho_metros", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="agroia",
    )

    # ── sensor_readings (base; ambientales se agregan en 004) ──
    op.create_table(
        "sensor_readings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "finca_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agroia.fincas.id"), nullable=False, index=True,
        ),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("ph", sa.Float(), nullable=True),
        sa.Column("nitrogeno", sa.Float(), nullable=True),
        sa.Column("fosforo", sa.Float(), nullable=True),
        sa.Column("potasio", sa.Float(), nullable=True),
        sa.Column("calcio", sa.Float(), nullable=True),
        sa.Column("magnesio", sa.Float(), nullable=True),
        sa.Column("azufre", sa.Float(), nullable=True),
        sa.Column("hierro", sa.Float(), nullable=True),
        sa.Column("manganeso", sa.Float(), nullable=True),
        sa.Column("zinc", sa.Float(), nullable=True),
        sa.Column("cobre", sa.Float(), nullable=True),
        sa.Column("boro", sa.Float(), nullable=True),
        sa.Column("materia_organica", sa.Float(), nullable=True),
        sa.Column("cic", sa.Float(), nullable=True),
        sa.Column("textura", textura_enum, nullable=True),
        sa.Column("humedad", sa.Float(), nullable=True),
        sa.Column("temperatura_suelo", sa.Float(), nullable=True),
        sa.Column("conductividad_electrica", sa.Float(), nullable=True),
        sa.Column("sensor_id", sa.String(100), nullable=True),
        sa.Column("calidad", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="agroia",
    )

    # ── fincas_usuarios (acceso a reportes por cliente) ──
    op.create_table(
        "fincas_usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "finca_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column(
            "usuario_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agroia.usuarios.id", ondelete="CASCADE"),
            nullable=False, index=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("finca_id", "usuario_id", name="uq_finca_usuario"),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("fincas_usuarios", schema="agroia")
    op.drop_table("sensor_readings", schema="agroia")
    op.drop_table("fincas", schema="agroia")
    op.drop_table("membresias", schema="agroia")
    op.drop_table("usuarios", schema="agroia")
