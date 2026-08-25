"""Migration 003 — Dispositivos IoT + variables ambientales.

Cierra las brechas de ingesta IoT:
  - Tabla dispositivos_iot (registro device_id → finca, calibración NPK).
  - Columnas humedad_ambiental / temperatura_ambiental en sensor_readings.

Revision ID: 003_dispositivos_iot
Down revision: 002_catalogo_cultivos
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_dispositivos_iot"
down_revision: str | None = "002_catalogo_cultivos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Tabla dispositivos_iot ──
    op.create_table(
        "dispositivos_iot",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "device_id", sa.String(100), nullable=False, unique=True, index=True,
            comment="ID que envía el firmware (ej. esp32-npk-001)",
        ),
        sa.Column(
            "finca_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agroia.fincas.id"), nullable=False, index=True,
        ),
        sa.Column("nombre", sa.String(200), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "npk_calibrado", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("factores_calibracion", postgresql.JSONB(), nullable=True),
        sa.Column("ultima_transmision", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rssi", sa.Integer(), nullable=True),
        sa.Column("uptime_s", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="agroia",
    )

    # ── Variables ambientales en sensor_readings ──
    op.add_column(
        "sensor_readings",
        sa.Column("humedad_ambiental", sa.Float(), nullable=True, comment="% HR ambiente"),
        schema="agroia",
    )
    op.add_column(
        "sensor_readings",
        sa.Column("temperatura_ambiental", sa.Float(), nullable=True, comment="°C ambiente"),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("sensor_readings", "humedad_ambiental", schema="agroia")
    op.drop_column("sensor_readings", "temperatura_ambiental", schema="agroia")
    op.drop_table("dispositivos_iot", schema="agroia")
