"""050 · Configuración de dispositivos IoT y valor crudo del sensor (E1).

Revision ID: 050_dispositivo_configuracion
Revises: 049_lote_perimetro
Create Date: 2026-11-03

Épica E1 (Integridad de la ingesta, RFP-AGROIA-003):

1. `dispositivos_iot`: campos de configuración del sensor JXBS-3001-NPK-RS
   (modelo, variante, dirección Modbus, baudios, bus, firmware, instalación,
   lote, mantenimiento y salud) — habilita HU-01 (registro con configuración).
2. `sensor_readings.valor_crudo` (JSONB): conserva los enteros crudos de los
   registros Modbus decodificados (principio "el valor crudo se conserva
   siempre"). TT-04 (E2) añadirá valor_escalado/unidad/incertidumbre sin
   re-crear esta columna.

Reversible.
"""

import sqlalchemy as sa
from alembic import op

revision = "050_dispositivo_configuracion"
down_revision = "049_lote_perimetro"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "dispositivos_iot",
        sa.Column("modelo", sa.String(100), nullable=True,
                  comment="Modelo del sensor (ej. JXBS-3001-NPK-RS)"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("variante", sa.String(100), nullable=True,
                  comment="Variante (confirmar con etiqueta física)"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("direccion_modbus", sa.Integer(), nullable=True,
                  comment="Dirección Modbus RTU (0x01 por defecto, configurable en 0x0100)"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("baudios", sa.Integer(), nullable=True,
                  comment="Baudios del bus RS485 (9600 8N1 por defecto)"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("bus_id", sa.String(50), nullable=True,
                  comment="Identificador del bus RS485 (unicidad dirección ↔ bus)"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("firmware", sa.String(100), nullable=True,
                  comment="Versión de firmware del dispositivo"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("fecha_instalacion", sa.Date(), nullable=True,
                  comment="Fecha de instalación en campo"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("profundidad_cm", sa.Integer(), nullable=True,
                  comment="Profundidad de instalación o lectura (cm)"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("modo_instalacion", sa.String(20), nullable=True,
                  comment="Modo de instalación: superficial | enterrado"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("lote_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True,
                  comment="Lote al que pertenece el dispositivo"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("ultimo_mantenimiento", sa.Date(), nullable=True,
                  comment="Fecha del último mantenimiento"),
        schema="agroia",
    )
    op.add_column(
        "dispositivos_iot",
        sa.Column("estado_salud", sa.String(50), nullable=True,
                  comment="Estado de salud agregado del dispositivo"),
        schema="agroia",
    )
    op.create_foreign_key(
        "fk_dispositivos_iot_lote",
        "dispositivos_iot",
        "lotes",
        ["lote_id"],
        ["id"],
        source_schema="agroia",
        referent_schema="agroia",
    )

    op.add_column(
        "sensor_readings",
        sa.Column("valor_crudo", sa.dialects.postgresql.JSONB(), nullable=True,
                  comment="Enteros crudos de los registros Modbus (clave hex → valor)"),
        schema="agroia",
    )


def downgrade() -> None:
    op.drop_column("sensor_readings", "valor_crudo", schema="agroia")
    op.drop_constraint("fk_dispositivos_iot_lote", "dispositivos_iot",
                       schema="agroia", type_="foreignkey")
    for col in (
        "estado_salud", "ultimo_mantenimiento", "lote_id", "modo_instalacion",
        "profundidad_cm", "fecha_instalacion", "firmware", "bus_id", "baudios",
        "direccion_modbus", "variante", "modelo",
    ):
        op.drop_column("dispositivos_iot", col, schema="agroia")
