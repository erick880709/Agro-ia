"""Modelo AnalisisLaboratorio — resultados de laboratorios ICA acreditados.

Los análisis recientes (< 90 días) tienen prioridad sobre la lectura del
sensor en el motor de recomendaciones y eliminan la penalización
`npk_sin_calibrar` para las variables que cubren (N/P/K/pH/MO).
"""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class AnalisisLaboratorio(Base):
    """Resultado de análisis de suelo de un laboratorio acreditado."""

    __tablename__ = "analisis_laboratorio"
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
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    laboratorio_nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fecha_muestreo: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fecha_resultado: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    resultados: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="Pares variable -> valor (pH, N, P, K, MO…)"
    )
    fuente: Mapped[str] = mapped_column(
        String(40), nullable=False, default="ingreso_manual",
        comment="ingreso_manual | csv | api | webhook",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
