"""Modelo ReglaAgronomica — reglas del sistema experto."""

import enum
import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia.database import Base
from agroia_backend.models import TimestampMixin


class PrioridadRegla(str, enum.Enum):
    CRITICA = "Critica"
    ALTA = "Alta"
    MEDIA = "Media"
    BAJA = "Baja"


class VariableSuelo(str, enum.Enum):
    PH = "pH"
    N = "N"
    P = "P"
    K = "K"
    Ca = "Ca"
    Mg = "Mg"
    S = "S"
    Fe = "Fe"
    Mn = "Mn"
    Zn = "Zn"
    Cu = "Cu"
    B = "B"
    MO = "MO"
    CIC = "CIC"
    TEXTURA = "textura"
    HUMEDAD = "humedad"
    TEMPERATURA_SUELO = "temperatura_suelo"
    CE = "CE"


class ReglaAgronomica(Base, TimestampMixin):
    """Regla del sistema experto agronómico. Sin tenant_id (datos compartidos)."""

    __tablename__ = "reglas_agronomicas"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cultivo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cultivos.id"),
        nullable=True,
        comment="NULL = regla universal para todos los cultivos",
    )
    variable: Mapped[VariableSuelo] = mapped_column(
        nullable=False,
    )
    umbral_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    umbral_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    accion: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Recomendación correctiva"
    )
    prioridad: Mapped[PrioridadRegla] = mapped_column(
        nullable=False,
        default=PrioridadRegla.MEDIA,
    )
    fuente: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Origen: UPRA, Cenicafé, AGROSAVIA, Manual"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<ReglaAgronomica {self.variable.value} [{self.umbral_min}-{self.umbral_max}] v{self.version}>"
