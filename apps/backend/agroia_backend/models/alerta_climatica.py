"""Modelo AlertaClimatica — alertas meteorológicas proactivas por finca.

El servicio programado cruza el pronóstico (IDEAM/NASA POWER/Open-Meteo)
con la fenología y las labores programadas, y persiste aquí las alertas
activas que el Dashboard muestra y el reporte refleja.
"""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class AlertaClimatica(Base):
    """Alerta climática proactiva para una finca."""

    __tablename__ = "alertas_climaticas"
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
    tipo: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True,
        comment="lluvia_aplicacion | helada_floracion",
    )
    severidad: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Alta",
        comment="Alta | Media",
    )
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_alerta: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    pronostico: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Pronóstico que disparó la alerta"
    )
    activa: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AlertaClimatica {self.tipo} finca={self.finca_id} activa={self.activa}>"
