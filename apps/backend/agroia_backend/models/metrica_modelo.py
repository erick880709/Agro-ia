"""Modelo MetricaModelo — evolución de métricas para drift monitoring."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from agroia.database import Base
from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from agroia_backend.models.modelo_ml import ModeloML


class MetricaModelo(Base):
    """Métrica registrada para un modelo. Sin tenant_id (datos compartidos)."""

    __tablename__ = "metricas_modelo"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    modelo_ml_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.modelos_ml.id"),
        nullable=False,
        index=True,
    )
    metrica: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Nombre de la métrica: F1, precision, recall, PSI"
    )
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relaciones
    modelo_ml: Mapped["ModeloML"] = relationship("ModeloML", back_populates="metricas")

    def __repr__(self) -> str:
        return f"<MetricaModelo {self.metrica}={self.valor:.4f}>"
