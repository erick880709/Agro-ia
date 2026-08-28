"""Modelo CicloLote — historial de ciclos productivos de un lote.

Cada fila registra un ciclo completo (siembra → cosecha) de un lote:
fechas clave, rendimiento, calidad, manejo agronómico estructurado
(aplicaciones e incidencias en JSONB) y observaciones del agrónomo.
"""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class CicloLote(Base):
    """Ciclo productivo de un lote (historial agronómico estructurado)."""

    __tablename__ = "historial_ciclos_lote"
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
    cultivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cultivos.id"),
        nullable=False,
        index=True,
    )
    # ── Fechas clave ──
    fecha_siembra: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_cosecha: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Material de siembra ──
    variedad: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Variedad sembrada"
    )
    densidad_siembra_plantas_ha: Mapped[float | None] = mapped_column(
        Numeric(8, 0), nullable=True, comment="Densidad de siembra (plantas/ha)"
    )

    # ── Resultados productivos ──
    rendimiento_tn_ha: Mapped[float | None] = mapped_column(
        Numeric(8, 2), nullable=True, comment="Toneladas por hectárea"
    )
    calidad_cosecha: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Premium | Estándar | Rechazo"
    )

    # ── Manejo agronómico (estructurado) ──
    aplicaciones: Mapped[list | None] = mapped_column(
        JSONB, nullable=True,
        comment='[{producto, dosis_kg_ha, fecha, tipo}, …]',
    )
    incidencias: Mapped[list | None] = mapped_column(
        JSONB, nullable=True,
        comment='[{plaga, severidad, fecha, control}, …]',
    )
    practicas_riego: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Goteo | Gravedad | Aspersión | Secano"
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Protección del Ground Truth del ML ──
    rendimiento_atipico: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
        comment="True si el rendimiento declarado es atípico vs ficha técnica "
                "(outlier humano); no alimenta el aprendizaje activo",
    )

    # ── Protección del Ground Truth del ML ──
    rendimiento_atipico: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
        comment="True si el rendimiento declarado es atípico vs ficha técnica "
                "(outlier humano); no alimenta el aprendizaje activo",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CicloLote lote={self.lote_id} siembra={self.fecha_siembra}>"
