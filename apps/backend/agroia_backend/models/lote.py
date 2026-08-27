"""Modelo Lote — unidad productiva dentro de una finca.

Separación arquitectónica: la finca identifica el predio; el lote es la
unidad productiva que después se analiza (sensores, muestras, reportes).
"""
import enum
import uuid
from datetime import datetime

from agroia.database import Base
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class Pedregosidad(str, enum.Enum):
    NINGUNA = "Ninguna"
    MODERADA = "Moderada"
    ALTA = "Alta"


class Lote(Base):
    """Lote o unidad productiva de una finca."""

    __tablename__ = "lotes"
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
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    area_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometria: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Geometría GeoJSON del lote"
    )
    # ── Características físicas del suelo del lote (2026-08-27) ──
    profundidad_suelo_cm: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Profundidad efectiva del suelo (cm); categorías: 25, 45, 75, 100"
    )
    pedregosidad: Mapped[Pedregosidad | None] = mapped_column(
        nullable=True, comment="Pedregosidad del lote"
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Lote {self.nombre} finca={self.finca_id}>"
