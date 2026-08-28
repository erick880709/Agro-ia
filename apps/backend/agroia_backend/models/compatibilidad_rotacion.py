"""Modelo CompatibilidadRotacion — reglas de rotación entre cultivos."""

import uuid

from agroia.database import Base
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class CompatibilidadRotacion(Base):
    """Regla de rotación: cultivo actual → cultivo siguiente con beneficio."""

    __tablename__ = "compatibilidad_rotacion"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cultivo_actual_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.cultivos.id"), nullable=False
    )
    cultivo_siguiente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.cultivos.id"), nullable=False
    )
    beneficio: Mapped[str | None] = mapped_column(String(20), nullable=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CompatibilidadRotacion {self.cultivo_actual_id} → {self.cultivo_siguiente_id}>"
