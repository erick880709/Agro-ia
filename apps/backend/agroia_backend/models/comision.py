"""Comisiones de trabajo por finca (órdenes de trabajo de toma de medidas)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from agroia.database import Base
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

ESTADOS_COMISION = (
    "asignada",
    "en_campo",
    "en_recomendacion",               # se generó al menos una recomendación
    "generacion_reporte_fin_etapa",   # se generó el reporte fin de etapa
    "finalizada",
    "cancelada",
)


class Comision(Base):
    """Comisión asignada a una finca para la toma de medidas de suelo."""

    __tablename__ = "comisiones"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.fincas.id", ondelete="CASCADE"), nullable=False
    )
    servicio: Mapped[str | None] = mapped_column(String(60), nullable=True)
    fecha_asignacion: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_inicio_tomas: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin_tomas: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(String(40), nullable=False, default="asignada")
    valor_comision_cop: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    valor_cobro_servicio_cop: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    valor_validacion_cop: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    valor_plataforma_cop: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ComisionMiembro(Base):
    """Miembro de una comisión (instrumentador, cadeneros, chofer, agrónomo)."""

    __tablename__ = "comision_miembros"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    comision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.comisiones.id", ondelete="CASCADE"), nullable=False
    )
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.equipo_trabajo.id", ondelete="RESTRICT"), nullable=False
    )
    rol_en_comision: Mapped[str] = mapped_column(String(30), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
