"""059 · Backfill lote_id de la finca Carcel Peñas blancas (datos productivos).

Revision ID: 059_backfill_lote_carcel
Revises: 058_sensor_reading_lote
Create Date: 2026-11-04

Backfill de datos (no es schema): asigna `lote_id` a las lecturas existentes
de la finca 042217d5-0c84-40be-aa5f-080429fbfcba, que históricamente se
tomaron en dos puntos fijos de muestreo sin lote asociado:

  - Lote frijol (ea2c82e7-5d9a-4b4c-92d8-5a9cee9ca8b3): pos_x=148.71, pos_y=-613.37
  - Lote cafe  (b53e55e3-6cae-4753-9cd9-fb6cc3140b66): pos_x=87.18,  pos_y=-458.92

Fuente: reports/mediciones-carcel-penas-blancas.md (2 puntos de muestreo,
110 registros frijol + 89 café). Los registros con GPS defectuoso y la
precarga SIG quedan sin lote (lote_id NULL).

Idempotente y reversible (solo toca lecturas de esa finca en esos puntos).
"""

from alembic import op

revision = "059_backfill_lote_carcel"
down_revision = "058_sensor_reading_lote"
branch_labels = None
depends_on = None

FINCA = "042217d5-0c84-40be-aa5f-080429fbfcba"
LOTE_FRIJOL = "ea2c82e7-5d9a-4b4c-92d8-5a9cee9ca8b3"
LOTE_CAFE = "b53e55e3-6cae-4753-9cd9-fb6cc3140b66"


def upgrade() -> None:
    # Tolerancia ±0.005 m para absorber el redondeo de los flotantes.
    op.execute(
        f"""
        UPDATE agroia.sensor_readings
        SET lote_id = '{LOTE_FRIJOL}'::uuid
        WHERE finca_id = '{FINCA}'::uuid
          AND pos_x BETWEEN 148.705 AND 148.715
          AND pos_y BETWEEN -613.375 AND -613.365
        """
    )
    op.execute(
        f"""
        UPDATE agroia.sensor_readings
        SET lote_id = '{LOTE_CAFE}'::uuid
        WHERE finca_id = '{FINCA}'::uuid
          AND pos_x BETWEEN 87.175 AND 87.185
          AND pos_y BETWEEN -458.925 AND -458.915
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE agroia.sensor_readings
        SET lote_id = NULL
        WHERE finca_id = '{FINCA}'::uuid
          AND lote_id IN ('{LOTE_FRIJOL}'::uuid, '{LOTE_CAFE}'::uuid)
        """
    )
