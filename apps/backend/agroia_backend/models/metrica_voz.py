"""Modelo MetricaVoz — métricas agregadas de uso de la función de voz.

Contadores mensuales (RF-036): consultas por voz, errores y duración total.
No se almacena audio ni contenido de las consultas, y las métricas no se
asocian a usuarios individuales (agregado anónimo por periodo).
"""

import uuid

from agroia.database import Base
from sqlalchemy import BigInteger, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia_backend.models import TimestampMixin


class MetricaVoz(Base, TimestampMixin):
    """Agregado mensual de uso de la función de voz."""

    __tablename__ = "metrica_voz"
    __table_args__ = (
        UniqueConstraint("periodo", name="uq_metrica_voz_periodo"),
        {"schema": "agroia"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    periodo: Mapped[str] = mapped_column(
        String(7), nullable=False, index=True, comment="Periodo de agregación YYYY-MM"
    )
    consultas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errores: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duracion_total_ms: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, comment="Suma de duraciones de las consultas"
    )
