"""Modelo VozPersonalizada — voz sintética del propio usuario (Fase 2).

Registra el ciclo de vida de la voz clonada: procesando, activa, desactivada o
eliminada. La muestra y la representación de voz viven en el servicio de GPU
(RT-026); aquí solo se guarda la referencia y el estado, sin audio en la BD.
"""

import uuid
from datetime import datetime

from agroia.database import Base
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia_backend.models import TimestampMixin


class VozPersonalizada(Base, TimestampMixin):
    """Voz personalizada del usuario (aislamiento por usuario)."""

    __tablename__ = "voz_personalizada"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="procesando",
        comment="procesando | activa | desactivada | eliminada",
    )
    referencia: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Identificador del artefacto en el servicio de GPU"
    )
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
