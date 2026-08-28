"""Equipo de trabajo y tarifas por rol (módulo operativo de comisiones)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from agroia.database import Base
from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

ROLES_EQUIPO = ("instrumentador", "cadenero_sensorista", "chofer", "agronomo")
ROLES_EQUIPO_ETIQUETA = {
    "instrumentador": "Instrumentador",
    "cadenero_sensorista": "Cadenero sensorista",
    "chofer": "Chofer",
    "agronomo": "Agrónomo",
}
ESTADOS_EMPLEADO = ("activo", "desvinculado")


class EquipoTrabajo(Base):
    """Empleado del equipo de campo (auditable)."""

    __tablename__ = "equipo_trabajo"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombres: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo_documento: Mapped[str] = mapped_column(String(10), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    lugar_domicilio: Mapped[str | None] = mapped_column(String(200), nullable=True)
    numero_contacto: Mapped[str | None] = mapped_column(String(20), nullable=True)
    contacto_emergencia_nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contacto_emergencia_telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    fecha_ingreso: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activo")
    valor_dia_cop: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TarifaRol(Base):
    """Valor por día de trabajo por rol."""

    __tablename__ = "tarifas_rol"
    __table_args__ = {"schema": "agroia"}

    rol: Mapped[str] = mapped_column(String(30), primary_key=True)
    valor_dia_cop: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
