"""Modelo ParametroCalidadSensor — parámetros administrables con versión (E7, HU-13).

Cada parámetro de calidad (rangos, saturación, humedad mínima, tolerancias,
ventanas de contexto, incertidumbres) es editable con auditoría de cambios y
versionado de la regla.
"""

import uuid
from datetime import datetime

from agroia.database import Base
from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class ParametroCalidadSensor(Base):
    """Parámetro administrable del motor de calidad."""

    __tablename__ = "parametro_calidad_sensor"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clave: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True,
        comment="Clave del parámetro (ph_min, ce_max_dsm, humedad_minima_pct…)",
    )
    valor: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Valor numérico del parámetro",
    )
    descripcion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False,
    )
