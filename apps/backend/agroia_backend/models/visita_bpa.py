"""Visita de verificación BPA — trazabilidad por visita/medición (1.G)."""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class VisitaBpa(Base):
    """Cada visita de verificación de Buenas Prácticas Agrícolas.

    Guarda qué ítems se evaluaron y su cumplimiento en esa visita,
    construyendo la línea de tiempo de trazabilidad de la finca.
    """

    __tablename__ = "checklist_bpa_visitas"
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
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    # [{item, categoria, cumple, evidencia_url}]
    items: Mapped[list] = mapped_column(JSONB, nullable=False)
    verificado_por_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verificado_por_nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    verificado_rol: Mapped[str | None] = mapped_column(String(40), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
