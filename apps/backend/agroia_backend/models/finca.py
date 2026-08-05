"""Modelo Finca — predio agrícola del usuario."""
import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agroia.database import Base
from agroia_backend.models import TenantMixin, TimestampMixin


class Finca(Base, TenantMixin, TimestampMixin):
    """Predio agrícola registrado por un usuario."""

    __tablename__ = "fincas"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.usuarios.id"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    latitud: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Latitud GPS (WGS84)"
    )
    longitud: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True,
        comment="Longitud GPS (WGS84)"
    )
    area_hectareas: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Área total en hectáreas"
    )
    altitud_msnm: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Altitud en metros sobre el nivel del mar"
    )
    departamento: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    municipio: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Finca {self.nombre}>"
