"""Modelo VariedadCultivo — variedades/cultivares por cultivo (ICA/Cenicafé)."""

import uuid

from agroia.database import Base
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class VariedadCultivo(Base):
    """Variedad o cultivar recomendada de un cultivo, con rango de altitud."""

    __tablename__ = "variedades_cultivo"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cultivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cultivos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre_variedad: Mapped[str] = mapped_column(String(100), nullable=False)
    resistencias: Mapped[str | None] = mapped_column(Text, nullable=True)
    altitud_min_msnm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    altitud_max_msnm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mercado_objetivo: Mapped[str | None] = mapped_column(String(60), nullable=True)
    fuente: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<VariedadCultivo {self.nombre_variedad}>"
