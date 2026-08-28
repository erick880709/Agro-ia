"""Modelo PreferenciaNotificacion — canal de alertas (WhatsApp/SMS/email)."""

import uuid

from agroia.database import Base
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class PreferenciaNotificacion(Base):
    """Preferencia de canal de notificación por usuario/finca."""

    __tablename__ = "preferencias_notificacion"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.usuarios.id"), nullable=True
    )
    finca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.fincas.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    canal: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ninguno", server_default="ninguno"
    )
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    def __repr__(self) -> str:
        return f"<PreferenciaNotificacion {self.canal} finca={self.finca_id}>"
