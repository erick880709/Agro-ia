"""Modelo MonitoreoPlaga — monitoreo integrado de plagas (MIP) en campo."""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class MonitoreoPlaga(Base):
    """Registro de monitoreo de plagas en un lote (incidencia observada)."""

    __tablename__ = "monitoreo_plagas"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.fincas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.lotes.id", ondelete="CASCADE"),
        nullable=True,
    )
    cultivo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.cultivos.id"), nullable=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    plaga_nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    plaga_nombre_cientifico: Mapped[str | None] = mapped_column(String(150), nullable=True)
    metodo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    severidad: Mapped[str | None] = mapped_column(String(10), nullable=True)
    incidencia_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.usuarios.id"), nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MonitoreoPlaga {self.plaga_nombre} {self.fecha}>"
