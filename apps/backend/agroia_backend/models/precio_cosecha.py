"""Modelo PrecioCosecha — precios de venta por cultivo y región (inteligencia de mercado)."""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class PrecioCosecha(Base):
    """Precio promedio de venta de un cultivo en un departamento."""

    __tablename__ = "precios_cosecha"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cultivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cultivos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    departamento: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    precio_promedio_cop_kg: Mapped[float] = mapped_column(Float, nullable=False)
    rendimiento_promedio_t_ha: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Rendimiento de referencia regional (t/ha) para utilidad",
    )
    fecha_actualizacion: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, default=date.today
    )
    fuente: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Ingreso manual",
        comment="DANE, Bolsa Nacional, gremio o ingreso manual",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
