"""Modelo Discordancia — conflicto ML vs reglas agronómicas."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from agroia.database import Base
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agroia_backend.models import TenantMixin, TimestampMixin

if TYPE_CHECKING:
    from agroia_backend.models.recomendacion import Recomendacion


class EstadoDiscordancia(str, enum.Enum):
    PENDIENTE = "Pendiente"
    REVISADA = "Revisada"
    BLOQUEADA = "Bloqueada"


class Discordancia(Base, TenantMixin, TimestampMixin):
    """Caso de conflicto entre predicción ML y validación del sistema experto."""

    __tablename__ = "discordancias"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recomendacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.recomendaciones.id"),
        nullable=False,
        index=True,
    )
    prediccion_ml: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="Salida del modelo ML"
    )
    regla_aplicada: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="Regla del sistema experto que bloqueó"
    )
    motivo_conflicto: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Descripción del conflicto ML vs reglas"
    )
    estado: Mapped[EstadoDiscordancia] = mapped_column(
        nullable=False,
        default=EstadoDiscordancia.PENDIENTE,
    )
    resolucion: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Decisión del técnico revisor"
    )
    tecnico_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.usuarios.id"), nullable=True
    )
    sla_vencimiento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Fecha límite: created_at + 10 días hábiles",
    )

    # Relaciones
    recomendacion: Mapped["Recomendacion"] = relationship(
        "Recomendacion", back_populates="discordancias"
    )

    def __repr__(self) -> str:
        return f"<Discordancia DISC-{self.id.hex[:8]} estado={self.estado.value}>"
