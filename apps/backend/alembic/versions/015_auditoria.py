"""tabla de auditoría: bitácora de acciones de usuarios.

Revision ID: 015_auditoria
Revises: 014_fisiologia_cultivos
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "015_auditoria"
down_revision = "014_fisiologia_cultivos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auditoria",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "usuario_email",
            sa.String(255),
            nullable=False,
            index=True,
            comment="Email del usuario que ejecutó la acción",
        ),
        sa.Column(
            "usuario_nombre",
            sa.String(200),
            nullable=True,
            comment="Nombre del usuario que ejecutó la acción",
        ),
        sa.Column(
            "rol",
            sa.String(30),
            nullable=True,
            comment="Rol del usuario en el momento de la acción",
        ),
        sa.Column(
            "accion",
            sa.String(80),
            nullable=False,
            index=True,
            comment="Código de la acción: finca.crear, usuario.eliminar…",
        ),
        sa.Column(
            "entidad",
            sa.String(40),
            nullable=False,
            index=True,
            comment="Entidad afectada: finca | lote | usuario | auth | demo",
        ),
        sa.Column(
            "entidad_id",
            sa.String(64),
            nullable=True,
            comment="ID (UUID) de la entidad afectada",
        ),
        sa.Column(
            "detalle",
            JSONB(),
            nullable=True,
            comment="Contexto de la acción: campos cambiados, resumen, etc.",
        ),
        sa.Column(
            "ip",
            sa.String(45),
            nullable=True,
            comment="IP de origen de la petición",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            index=True,
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("auditoria", schema="agroia")
