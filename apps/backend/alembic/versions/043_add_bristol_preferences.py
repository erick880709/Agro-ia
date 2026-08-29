"""043 · Almanaque Bristol: preferencias de calendario lunar.

Revision ID: 043_add_bristol_preferences
Revises: 042_vision_etiqueta_confirmada
Create Date: 2026-08-29

Nota: la especificación proponía extender un enum `agroia.tipoalerta` con
'siembra_lunar'; en AgroIA el tipo de alerta es VARCHAR (`alertas_climaticas.tipo`),
por lo que no se requiere ALTER TYPE — el nuevo tipo se usa directamente.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "043_add_bristol_preferences"
down_revision = "042_vision_etiqueta_confirmada"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "preferencias_bristol",
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agroia.usuarios.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "mostrar_en_reportes",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "generar_alertas_siembra",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("preferencias_bristol", schema="agroia")
