"""Modelo Auditoria — bitácora de acciones de los usuarios (admin y equipo).

Cada fila registra QUIÉN (email/nombre/rol), QUÉ acción, SOBRE QUÉ entidad
y CUÁNDO. Es la fuente de la pantalla «🕵️ Auditoría» (solo administrador).
"""

import uuid
from datetime import datetime

from agroia.database import Base
from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class Auditoria(Base):
    """Evento de auditoría (acciones de usuarios sobre el sistema)."""

    __tablename__ = "auditoria"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True,
        comment="Email del usuario que ejecutó la acción",
    )
    usuario_nombre: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Nombre del usuario que ejecutó la acción"
    )
    rol: Mapped[str | None] = mapped_column(
        String(30), nullable=True, comment="Rol del usuario en el momento de la acción"
    )
    accion: Mapped[str] = mapped_column(
        String(80), nullable=False, index=True,
        comment="Código de la acción: finca.crear, usuario.eliminar, lote.actualizar…",
    )
    entidad: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True,
        comment="Entidad afectada: finca | lote | usuario | auth | demo | reporte",
    )
    entidad_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="ID (UUID) de la entidad afectada"
    )
    detalle: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Contexto de la acción: campos cambiados, resumen, etc.",
    )
    ip: Mapped[str | None] = mapped_column(
        String(45), nullable=True, comment="IP de origen de la petición"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<Auditoria {self.accion} {self.entidad_id or ''} por {self.usuario_email}>"
