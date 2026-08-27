"""Modelo Labor — órdenes de trabajo del plan agronómico.

Convierte las acciones del diagnóstico en tareas ejecutables con
trazabilidad: quién, qué, cuándo y con qué resultado. Cada labor se
asocia a un lote y opcionalmente a la recomendación que la originó.
"""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

ESTADOS_LABOR = {"Pendiente", "En Progreso", "Completada", "Cancelada"}
TIPOS_LABOR = {"Fertilización", "Enmienda", "Riego", "Control Fitosanitario"}


class Labor(Base):
    """Orden de trabajo (labor) de una recomendación para un lote."""

    __tablename__ = "labores"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.lotes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recomendacion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.recomendaciones.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Recomendación que originó la labor",
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Fertilización",
        comment="Fertilización | Enmienda | Riego | Control Fitosanitario",
    )
    producto: Mapped[str | None] = mapped_column(String(150), nullable=True)
    dosis_kg_ha: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Dosis en kg/ha"
    )
    fecha_programada: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    fecha_ejecucion: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.usuarios.id"), nullable=True,
        comment="Usuario responsable de ejecutar la labor",
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Pendiente", server_default="Pendiente",
        comment="Pendiente | En Progreso | Completada | Cancelada",
    )
    observaciones_ejecucion: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Labor {self.titulo[:40]} estado={self.estado}>"
