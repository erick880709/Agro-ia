"""Migration 002 — Catálogo de cultivos y fichas técnicas.

Crea tablas: cultivos, fichas_tecnicas
Enums: estado_ficha_enum, tipo_fuente_enum
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_catalogo_cultivos"
down_revision: Union[str, None] = "001_recomendaciones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ──
    estado_ficha_enum = postgresql.ENUM(
        "Borrador", "EnRevision", "Publicado",
        name="estado_ficha_enum", schema="agroia", create_type=False,
    )
    estado_ficha_enum.create(op.get_bind(), checkfirst=True)

    tipo_fuente_enum = postgresql.ENUM(
        "Nacional", "Internacional",
        name="tipo_fuente_enum", schema="agroia", create_type=False,
    )
    tipo_fuente_enum.create(op.get_bind(), checkfirst=True)

    # ── cultivos ──
    op.create_table(
        "cultivos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False, unique=True),
        sa.Column("nombre_cientifico", sa.String(200), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("icono", sa.String(50), nullable=True, comment="Emoji o código de icono"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="agroia",
    )
    op.create_index("ix_cultivos_nombre", "cultivos", ["nombre"], schema="agroia")

    # ── fichas_tecnicas ──
    op.create_table(
        "fichas_tecnicas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cultivo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("estado", estado_ficha_enum, nullable=False, server_default="Borrador"),
        sa.Column("tipo_fuente", tipo_fuente_enum, nullable=False, server_default="Nacional"),
        sa.Column("fuente", sa.String(255), nullable=False),
        sa.Column("etiqueta_internacional", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("umbrales", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("datos_economicos", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("creado_por", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revisado_por", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fecha_envio_revision", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_revision", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_ultima_revision", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notas_revision", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="agroia",
    )
    op.create_index("ix_fichas_cultivo_id", "fichas_tecnicas", ["cultivo_id"], schema="agroia")
    op.create_index("ix_fichas_estado", "fichas_tecnicas", ["estado"], schema="agroia")


def downgrade() -> None:
    op.drop_table("fichas_tecnicas", schema="agroia")
    op.drop_table("cultivos", schema="agroia")
    for enum_name in ("tipo_fuente_enum", "estado_ficha_enum"):
        op.execute(f"DROP TYPE IF EXISTS agroia.{enum_name}")
