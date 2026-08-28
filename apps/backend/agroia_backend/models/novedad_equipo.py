"""Novedades del equipo de trabajo (incapacidades/ausencias con reemplazo)."""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

TIPOS_NOVEDAD = ("incapacidad", "ausencia", "otro")


class NovedadEquipo(Base):
    """Novedad de un empleado; puede marcar reemplazo para una comisión."""

    __tablename__ = "novedades_equipo"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.equipo_trabajo.id", ondelete="RESTRICT"), nullable=False
    )
    comision_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.comisiones.id", ondelete="SET NULL"), nullable=True
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    reemplazo_empleado_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.equipo_trabajo.id", ondelete="SET NULL"), nullable=True
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="abierta")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
