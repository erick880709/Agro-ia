"""Modelo CurvaExtraccion — extracción nutricional por etapa fenológica."""

import uuid

from agroia.database import Base
from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class CurvaExtraccion(Base):
    """Punto de la curva de extracción de un nutriente por etapa del cultivo."""

    __tablename__ = "curvas_extraccion"
    __table_args__ = (
        UniqueConstraint(
            "cultivo_id", "etapa_fenologica", "nutriente",
            name="uq_curva_cultivo_etapa_nutriente",
        ),
        {"schema": "agroia"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cultivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cultivos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    etapa_fenologica: Mapped[str] = mapped_column(String(30), nullable=False)
    nutriente: Mapped[str] = mapped_column(String(10), nullable=False)
    pct_extraccion_acumulado: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, comment="Porcentaje acumulado 0-100"
    )
    fuente: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CurvaExtraccion {self.cultivo_id} {self.etapa_fenologica} "
            f"{self.nutriente} {self.pct_extraccion_acumulado}%>"
        )
