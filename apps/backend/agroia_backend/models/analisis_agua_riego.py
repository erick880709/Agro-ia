"""Modelo AnalisisAguaRiego — calidad del agua de riego (FAO-29)."""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class AnalisisAguaRiego(Base):
    """Análisis de calidad del agua usada para riego (CE, RAS, cloruros, boro)."""

    __tablename__ = "analisis_agua_riego"
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
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    ce_agua_ds_m: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    ras: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    cloruros_mg_l: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    boro_mg_l: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    ph_agua: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    fuente: Mapped[str] = mapped_column(
        String(20), nullable=False, default="laboratorio", server_default="laboratorio"
    )
    clasificacion_restriccion: Mapped[str | None] = mapped_column(
        String(30), nullable=True,
        comment="Calculada FAO-29: ninguna | leve_moderada | severa",
    )
    creado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.usuarios.id"), nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AnalisisAguaRiego finca={self.finca_id} {self.fecha}>"
