"""Modelo PreferenciaLecturaVoz — preferencias de lectura en voz alta.

Guarda, por usuario, si la lectura está activa, la voz elegida y la velocidad
(RT-025 / RF-038). Se usa el email como clave de usuario, igual que la memoria
del chat, para no depender del id interno en el frontend.
"""

import uuid

from agroia.database import Base
from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia_backend.models import TimestampMixin


class PreferenciaLecturaVoz(Base, TimestampMixin):
    """Preferencia de lectura por usuario (activado, voz, velocidad)."""

    __tablename__ = "preferencia_lectura_voz"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    activado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voz: Mapped[str] = mapped_column(
        String(20), nullable=False, default="femenina",
        comment="femenina | masculina | mi-voz",
    )
    velocidad: Mapped[str] = mapped_column(
        String(10), nullable=False, default="1",
        comment="0.75 | 1 | 1.25 | 1.5",
    )
