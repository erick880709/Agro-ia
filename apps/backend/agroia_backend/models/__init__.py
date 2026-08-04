"""Modelos SQLAlchemy del motor de recomendaciones de AgroIA.

Incluye: Recomendacion, Discordancia, ReglaAgronomica, ModeloML, MetricaModelo.
Todos los modelos con datos de cliente heredan de TenantMixin para RLS.
"""

import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agroia.database import Base


class TenantMixin:
    """Mixin que agrega tenant_id para Row-Level Security en PostgreSQL."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )


class TimestampMixin:
    """Mixin que agrega created_at y updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

