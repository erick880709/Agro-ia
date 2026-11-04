"""Modelo MantenimientoSensor — registro de mantenimiento por dispositivo (E8, HU-14)."""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class MantenimientoSensor(Base):
    """Acción de mantenimiento registrada por dispositivo (limpieza, revisión, reemplazo)."""

    __tablename__ = "mantenimiento_sensor"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dispositivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.dispositivos_iot.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(
        String(40), nullable=False,
        comment="Tipo de mantenimiento: limpieza | revision | reemplazo",
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    observaciones: Mapped[str | None] = mapped_column(String(500), nullable=True)
    responsable: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
