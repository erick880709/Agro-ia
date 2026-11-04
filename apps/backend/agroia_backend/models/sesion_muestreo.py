"""Modelo SesionMuestreo — protocolo de muestreo y contexto (Épica E5, RF-076/077).

Agrupa las réplicas de un punto de muestreo con su contexto agronómico
(fertilización, riego y lluvia reciente), que condiciona la calidad de las
lecturas de pH/CE/NPK.
"""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class SesionMuestreo(Base):
    """Sesión de muestreo: punto, réplicas y contexto agronómico."""

    __tablename__ = "sesion_muestreo"
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
        ForeignKey("agroia.lotes.id", ondelete="SET NULL"),
        nullable=True,
    )
    punto_id: Mapped[str] = mapped_column(String(100), nullable=False)
    replicas: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    profundidad_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pedregosidad: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tiempo_estabilizacion_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(String(500), nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Contexto agronómico (RF-077)
    fecha_ultima_fertilizacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_ultimo_riego: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_ultima_lluvia: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
