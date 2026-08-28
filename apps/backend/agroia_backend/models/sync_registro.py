"""Modelo SyncRegistro — idempotencia de datos sincronizados desde la app offline."""

from datetime import datetime

from agroia.database import Base
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column


class SyncRegistro(Base):
    """Llave de idempotencia de un item sincronizado (sensor/labor)."""

    __tablename__ = "sync_registro"
    __table_args__ = {"schema": "agroia"}

    idempotency_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    usuario_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    resultado: Mapped[str | None] = mapped_column(String(400), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
