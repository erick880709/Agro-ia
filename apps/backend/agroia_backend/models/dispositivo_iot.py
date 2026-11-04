"""Modelo DispositivoIoT — registro de dispositivos de sensores IoT.

Permite asociar un device_id (ej. `esp32-npk-001`) a una finca y guardar
el estado de calibración NPK del dispositivo (brecha G4).
"""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia_backend.models import TimestampMixin


class DispositivoIoT(Base, TimestampMixin):
    """Dispositivo sensor IoT registrado en la plataforma."""

    __tablename__ = "dispositivos_iot"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    device_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True,
        comment="ID que envía el firmware (ej. esp32-npk-001)",
    )
    finca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.fincas.id"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Nombre amigable del dispositivo"
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Calibración NPK (brecha G4) ──
    npk_calibrado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="True cuando NPK fue calibrado contra análisis de laboratorio",
    )
    factores_calibracion: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Factores multiplicativos por variable: {\"nitrogeno\": 1.2, ...}",
    )

    # ── Configuración del sensor (E1, HU-01) ──
    modelo: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Modelo (ej. JXBS-3001-NPK-RS)"
    )
    variante: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Variante (confirmar con etiqueta física)"
    )
    direccion_modbus: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Dirección Modbus RTU (0x01 por defecto, configurable en 0x0100)",
    )
    baudios: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Baudios del bus RS485 (9600 8N1 por defecto)"
    )
    bus_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Identificador del bus RS485 (dirección ↔ bus)"
    )
    firmware: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Versión de firmware del dispositivo"
    )
    fecha_instalacion: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="Fecha de instalación en campo"
    )
    profundidad_cm: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Profundidad de instalación o lectura (cm)"
    )
    modo_instalacion: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Modo de instalación: superficial | enterrado"
    )
    lote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.lotes.id"),
        nullable=True,
        comment="Lote al que pertenece el dispositivo",
    )
    ultimo_mantenimiento: Mapped[date | None] = mapped_column(
        Date, nullable=True, comment="Fecha del último mantenimiento"
    )
    estado_salud: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Estado de salud agregado del dispositivo"
    )

    # ── Telemetría del dispositivo ──
    ultima_transmision: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rssi: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="dBm de la última transmisión"
    )
    uptime_s: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Segundos desde el último reinicio"
    )

    def __repr__(self) -> str:
        return f"<DispositivoIoT {self.device_id} finca={self.finca_id}>"
