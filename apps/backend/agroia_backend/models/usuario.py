"""Modelo Usuario y Membresía para AgroIA.

Usuarios con 4 roles RBAC, consentimiento Ley 1581, y planes de membresía.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from agroia.database import Base
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agroia_backend.models import TenantMixin, TimestampMixin


class RolUsuario(str, enum.Enum):
    ADMIN = "Admin"
    AGRONOMO = "Agronomo"
    CLIENTE = "Cliente"
    TECNICO = "Tecnico"
    INVESTIGADOR = "Investigador"
    EXTENSIONISTA = "Extensionista"


# Enum con schema explícito: evita que un tipo `rolusuario` residual en el
# schema `public` (creado en deploys antiguos sin search_path) opaque el tipo
# real `agroia.rolusuario` y reviente los UPDATE de rol en producción.
_ROL_ENUM = Enum(RolUsuario, name="rolusuario", schema="agroia")


class PlanMembresia(str, enum.Enum):
    MENSUAL = "Mensual"
    SEMESTRAL = "Semestral"
    ANUAL = "Anual"


class EstadoMembresia(str, enum.Enum):
    ACTIVA = "Activa"
    VENCIDA = "Vencida"
    CANCELADA = "Cancelada"


class Usuario(Base, TenantMixin, TimestampMixin):
    """Usuario de la plataforma AgroIA."""

    __tablename__ = "usuarios"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        _ROL_ENUM,
        nullable=False,
        default=RolUsuario.CLIENTE,
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    consentimiento_datos: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Consentimiento informado Ley 1581/2012"
    )
    email_verificado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Rol Extensionista: municipios de su zona asignada (multi-finca) ──
    municipios_asignados: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True,
        comment="Municipios asignados al extensionista (filtro de zona)",
    )

    # Relaciones
    membresia: Mapped[Optional["Membresia"]] = relationship(
        "Membresia", back_populates="usuario", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Usuario {self.email} rol={self.rol.value}>"


class Membresia(Base, TenantMixin, TimestampMixin):
    """Plan de membresía de un usuario (cliente)."""

    __tablename__ = "membresias"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.usuarios.id"), nullable=False, unique=True, index=True
    )
    plan: Mapped[PlanMembresia] = mapped_column(
        nullable=False,
    )
    estado: Mapped[EstadoMembresia] = mapped_column(
        nullable=False,
        default=EstadoMembresia.ACTIVA,
    )
    fecha_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    fecha_vencimiento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fincas_permitidas: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Número máximo de fincas según el plan"
    )

    # Relaciones
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="membresia")

    # Plan defaults
    PLAN_LIMITS = {
        PlanMembresia.MENSUAL: {"fincas": 1, "duracion_meses": 1},
        PlanMembresia.SEMESTRAL: {"fincas": 3, "duracion_meses": 6},
        PlanMembresia.ANUAL: {"fincas": 5, "duracion_meses": 12},
    }

    def __repr__(self) -> str:
        return f"<Membresia {self.plan.value} estado={self.estado.value}>"
