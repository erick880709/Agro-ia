"""Modelo Recomendacion — resultado de un análisis de aptitud de suelo."""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agroia.database import Base
from agroia_backend.models import TenantMixin, TimestampMixin

# ── Enums ──

class ClasificacionUPRA(str, enum.Enum):
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"
    NO_APTA = "NoApta"


class EstadoRecomendacion(str, enum.Enum):
    PUBLICADA = "Publicada"
    ADVERTENCIA = "Advertencia"
    BLOQUEADA = "Bloqueada"


# ── Modelo ──

class Recomendacion(Base, TenantMixin, TimestampMixin):
    """Recomendación generada para una finca sobre un cultivo."""

    __tablename__ = "recomendaciones"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.fincas.id"), nullable=False, index=True
    )
    cultivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.cultivos.id"), nullable=False, index=True
    )
    clasificacion_upra: Mapped[ClasificacionUPRA] = mapped_column(
        nullable=False,
    )
    confianza: Mapped[float] = mapped_column(
        Float, nullable=False, comment="F1-score de la predicción (0-1)"
    )
    justificacion: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="Variables que influyeron, riesgos, beneficios, costo, impacto"
    )
    estado: Mapped[EstadoRecomendacion] = mapped_column(
        nullable=False,
        default=EstadoRecomendacion.PUBLICADA,
    )
    tecnico_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.usuarios.id"),
        nullable=True,
        comment="Técnico que revisó la recomendación (si fue escalada)",
    )

    # Relaciones
    discordancias: Mapped[list["Discordancia"]] = relationship(
        "Discordancia", back_populates="recomendacion"
    )

    def __repr__(self) -> str:
        return f"<Recomendacion {self.id} finca={self.finca_id} upra={self.clasificacion_upra.value}>"
