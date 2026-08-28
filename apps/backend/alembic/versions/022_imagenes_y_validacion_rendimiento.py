"""fotos de labores en disco y flag de rendimiento atípico en ciclos.

Revision ID: 022_imagenes_y_validacion_rendimiento
Revises: 021_precios_insumos
Create Date: 2026-08-27
"""
import sqlalchemy as sa
from alembic import op

revision = "022_imagenes_y_rendimiento"
down_revision = "021_precios_insumos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fotos de labores: solo la ruta en BD (el archivo vive en disco/S3)
    op.add_column(
        "labores",
        sa.Column(
            "imagen_url",
            sa.String(500),
            nullable=True,
            comment="Ruta del archivo de la foto (disco/S3); la imagen NO va en BD",
        ),
        schema="agroia",
    )
    # Rendimiento atípico: marca ciclos cuyo rendimiento declarado está fuera
    # de rango (outlier humano) para que NO envenenen el Ground Truth del ML
    op.add_column(
        "historial_ciclos_lote",
        sa.Column(
            "rendimiento_atipico",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="True si el rendimiento declarado es atípico vs ficha técnica",
        ),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("historial_ciclos_lote", "rendimiento_atipico", schema="agroia")
    op.drop_column("labores", "imagen_url", schema="agroia")
