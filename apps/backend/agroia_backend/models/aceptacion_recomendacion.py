"""Modelo AceptacionRecomendacion — feedback humano sobre recomendaciones.

Cada aceptación de un Admin/Agrónomo alimenta la confianza del modelo
(human-in-the-loop): el orquestador suma un refuerzo de confianza
proporcional al número de aceptaciones registradas para la finca/cultivo.
"""
import uuid
from datetime import datetime

from agroia.database import Base
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class AceptacionRecomendacion(Base):
    """Aceptación explícita de una recomendación por un experto humano."""

    __tablename__ = "aceptaciones_recomendacion"
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
    cultivo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cultivos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rol: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Rol que aceptó: Admin | Agronomo"
    )
    comentario: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Ampliación/ajustes del experto"
    )
    resumen: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Recomendaciones aceptadas"
    )
    clasificacion_previa: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    confianza_previa: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AceptacionRecomendacion finca={self.finca_id} rol={self.rol}>"
