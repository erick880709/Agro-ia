"""georreferenciación de fincas + separación Finca/Lote.

Revision ID: 011_fincas_geo_lotes
Revises: 010_feedback_recomendaciones
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "011_fincas_geo_lotes"
down_revision = "010_feedback_recomendaciones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fincas",
        sa.Column("vereda", sa.String(100), nullable=True,
                  comment="Vereda / corregimiento"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("precision_gps", sa.Float(), nullable=True,
                  comment="Precisión GPS en metros"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("fuente_geolocalizacion", sa.String(30), nullable=True,
                  comment="gps_navegador | mapa | google_maps | manual"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("geometria", JSONB(), nullable=True,
                  comment="Geometría GeoJSON del predio (polígono)"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("area_declarada_ha", sa.Float(), nullable=True,
                  comment="Área declarada por el usuario (ha)"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("area_calculada_ha", sa.Float(), nullable=True,
                  comment="Área calculada desde la geometría (ha)"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("perimetro_m", sa.Float(), nullable=True,
                  comment="Perímetro calculado desde la geometría (m)"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("tipo_area", sa.String(30), nullable=False,
                  server_default="finca_completa",
                  comment="finca_completa | lote | parcela"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("tiene_multiples_lotes", sa.Boolean(), nullable=False,
                  server_default=sa.text("false"),
                  comment="¿La finca tiene varios lotes?"),
        schema="agroia",
    )
    op.add_column(
        "fincas",
        sa.Column("fecha_georreferenciacion", sa.DateTime(timezone=True), nullable=True,
                  comment="Fecha en que se capturaron las coordenadas"),
        schema="agroia",
    )

    # ── Lotes: unidad productiva dentro de una finca ──
    op.create_table(
        "lotes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("finca_id", UUID(as_uuid=True),
                  sa.ForeignKey("agroia.fincas.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("area_ha", sa.Float(), nullable=True),
        sa.Column("geometria", JSONB(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_table("lotes", schema="agroia")
    for col in (
        "vereda", "precision_gps", "fuente_geolocalizacion", "geometria",
        "area_declarada_ha", "area_calculada_ha", "perimetro_m", "tipo_area",
        "tiene_multiples_lotes", "fecha_georreferenciacion",
    ):
        op.drop_column("fincas", col, schema="agroia")
