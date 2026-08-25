"""Modelo FincaUsuario — relación muchos-a-muchos entre fincas y usuarios.

Define qué fincas puede observar cada usuario (cliente) para sus reportes.
"""

import uuid

from agroia.database import Base
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia_backend.models import TimestampMixin


class FincaUsuario(Base, TimestampMixin):
    """Asociación finca ↔ usuario (acceso a reportes)."""

    __tablename__ = "fincas_usuarios"
    __table_args__ = (
        UniqueConstraint("finca_id", "usuario_id", name="uq_finca_usuario"),
        {"schema": "agroia"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.fincas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
