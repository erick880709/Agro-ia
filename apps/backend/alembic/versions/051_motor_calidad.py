"""051 · Motor de calidad con 10 estados (Épica E2).

Revision ID: 051_motor_calidad
Revises: 050_dispositivo_configuracion
Create Date: 2026-11-03

1. `sensor_readings`: agrega `motivos_calidad` (JSONB) y `version_regla`.
2. Renombra los estados de calidad legados a los del motor de 10 estados:
     'OK'               → 'valida'
     'npk_no_calibrado' → 'no_calibrada'
     'estimado_por_sig' → 'estimado_sig'
   ('invalidada' y NULL se conservan). La reclasificación con las reglas
   nuevas sobre el histórico es TT-16; aquí solo se renombran los enums.

Reversible.
"""

import sqlalchemy as sa
from alembic import op

revision = "051_motor_calidad"
down_revision = "050_dispositivo_configuracion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column("motivos_calidad", sa.dialects.postgresql.JSONB(), nullable=True,
                  comment="Lista de motivos de la clasificación de calidad"),
        schema="agroia",
    )
    op.add_column(
        "sensor_readings",
        sa.Column("version_regla", sa.String(50), nullable=True,
                  comment="Versión de la regla de calidad aplicada"),
        schema="agroia",
    )

    op.execute(
        "UPDATE agroia.sensor_readings SET calidad = 'valida' "
        "WHERE calidad = 'OK'"
    )
    op.execute(
        "UPDATE agroia.sensor_readings SET calidad = 'no_calibrada' "
        "WHERE calidad = 'npk_no_calibrado'"
    )
    op.execute(
        "UPDATE agroia.sensor_readings SET calidad = 'estimado_sig' "
        "WHERE calidad = 'estimado_por_sig'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE agroia.sensor_readings SET calidad = 'estimado_por_sig' "
        "WHERE calidad = 'estimado_sig'"
    )
    op.execute(
        "UPDATE agroia.sensor_readings SET calidad = 'npk_no_calibrado' "
        "WHERE calidad = 'no_calibrada'"
    )
    op.execute(
        "UPDATE agroia.sensor_readings SET calidad = 'OK' "
        "WHERE calidad = 'valida'"
    )
    op.drop_column("sensor_readings", "version_regla", schema="agroia")
    op.drop_column("sensor_readings", "motivos_calidad", schema="agroia")
