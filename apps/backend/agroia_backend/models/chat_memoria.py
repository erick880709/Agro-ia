"""Modelo ChatMemoria — memoria conversacional por finca.

Permite que el usuario regrese después y la plataforma recuerde las
consultas y respuestas asociadas a cada finca (memoria de finca).
"""

import uuid
from datetime import datetime

from agroia.database import Base
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia_backend.models import TimestampMixin


class ChatMemoria(Base, TimestampMixin):
    """Consulta-respuesta del chat agronómico ligada a una finca."""

    __tablename__ = "chat_memoria"
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
    usuario_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pregunta: Mapped[str] = mapped_column(Text, nullable=False)
    respuesta: Mapped[str] = mapped_column(Text, nullable=False)
    fuentes: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Fuentes de conocimiento usadas"
    )
    confianza: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Alta / Media / Baja"
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
