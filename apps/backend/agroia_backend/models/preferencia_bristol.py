"""Modelo PreferenciaBristol — preferencias del Almanaque Bristol por usuario."""

import uuid
from datetime import datetime

from agroia.database import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class PreferenciaBristol(Base):
    """Preferencias del Almanaque Bristol (calendario lunar) de un usuario."""

    __tablename__ = "preferencias_bristol"
    __table_args__ = {"schema": "agroia"}

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    mostrar_en_reportes: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    generar_alertas_siembra: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<PreferenciaBristol usuario={self.usuario_id} "
            f"alertas={self.generar_alertas_siembra} reportes={self.mostrar_en_reportes}>"
        )
