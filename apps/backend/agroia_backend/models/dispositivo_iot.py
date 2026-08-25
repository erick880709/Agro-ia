"""Modelo DispositivoIoT — registro de dispositivos de sensores IoT.

Permite asociar un device_id (ej. `esp32-npk-001`) a una finca y guardar
el estado de calibración NPK del dispositivo (brecha G4).
"""

import uuid

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia.database import Base
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
    nombre: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="Nombre amigable del dispositivo"
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Calibración NPK (brecha G4) ──
    npk_calibrado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="True cuando NPK fue calibrado contra análisis de laboratorio",
    )
    factores_calibracion: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="Factores multiplicativos por variable: {\"nitrogeno\": 1.2, ...}",
    )

    # ── Telemetría del dispositivo ──
    ultima_transmision: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rssi: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="dBm de la última transmisión"
    )
    uptime_s: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Segundos desde el último reinicio"
    )

    def __repr__(self) -> str:
        return f"<DispositivoIoT {self.device_id} finca={self.finca_id}>"
