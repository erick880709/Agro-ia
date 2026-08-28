"""Modelos de autenticación JWT — blacklist de tokens y refresh tokens revocables.

- `tokens_blacklist`: jti de tokens invalidades (logout) con expiración;
  una tarea diaria del lifespan limpia los registros vencidos.
- `refresh_tokens`: refresh tokens persistidos como **hash SHA-256** (nunca
  el token en claro) para permitir revocación manual y rotación.
"""

import uuid
from datetime import datetime

from agroia.database import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class TokenBlacklist(Base):
    """Tokens JWT invalidadas (logout) — se revisan por `jti` en el middleware."""

    __tablename__ = "tokens_blacklist"
    __table_args__ = {"schema": "agroia"}

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    tipo: Mapped[str] = mapped_column(
        String(20), nullable=False, default="access", index=True,
        comment="access | refresh",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RefreshToken(Base):
    """Refresh token persistido (hash) — rotación y revocación manual."""

    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revocado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
