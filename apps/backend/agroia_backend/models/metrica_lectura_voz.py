"""Modelo MetricaLecturaVoz — métricas agregadas de la lectura en voz alta.

Contadores mensuales (RF-056): activaciones, voz elegida, errores y caracteres
leídos. Sin audio ni contenido de respuestas.
"""

import uuid

from agroia.database import Base
from sqlalchemy import BigInteger, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia_backend.models import TimestampMixin


class MetricaLecturaVoz(Base, TimestampMixin):
    """Agregado mensual de uso de la lectura en voz alta."""

    __tablename__ = "metrica_lectura_voz"
    __table_args__ = (
        UniqueConstraint("periodo", name="uq_metrica_lectura_periodo"),
        {"schema": "agroia"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    periodo: Mapped[str] = mapped_column(
        String(7), nullable=False, index=True, comment="Periodo YYYY-MM"
    )
    activaciones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    voz_elegida: Mapped[str | None] = mapped_column(String(20), nullable=True)
    errores: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    caracteres_leidos: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
