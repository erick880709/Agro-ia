"""Modelo ModeloML — registro de modelos entrenados en MLflow."""

import enum
import uuid

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agroia.database import Base
from agroia_backend.models import TimestampMixin


class StageModelo(str, enum.Enum):
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"


class ModeloML(Base, TimestampMixin):
    """Registro de un modelo de ML versionado. Sin tenant_id (datos compartidos)."""

    __tablename__ = "modelos_ml"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Nombre del modelo (ej. RF_UPRA_Clasificador)"
    )
    tipo_modelo: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Algoritmo: RandomForest, XGBoost, LSTM, Ensemble"
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    f1_score: Mapped[float] = mapped_column(
        Float, nullable=True, comment="F1-score en validación"
    )
    mlflow_run_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Run ID en MLflow"
    )
    stage: Mapped[StageModelo] = mapped_column(
        nullable=False,
        default=StageModelo.STAGING,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="¿Es el modelo activo en producción?"
    )

    # Relaciones
    metricas: Mapped[list["MetricaModelo"]] = relationship(
        "MetricaModelo", back_populates="modelo_ml"
    )

    def __repr__(self) -> str:
        return f"<ModeloML {self.nombre} v{self.version} F1={self.f1_score}>"
