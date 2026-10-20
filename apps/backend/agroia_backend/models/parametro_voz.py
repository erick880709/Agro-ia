"""Modelo ParametroVoz — parámetros administrables de la interacción por voz.

Una única fila de configuración global (RT-019): activación, duración máxima
por consulta e idioma. Los valores no quedan fijos en el código: el
administrador puede cambiarlos desde Administración → Parámetros (RF-037).
"""

import uuid

from agroia.database import Base
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia_backend.models import TimestampMixin


class ParametroVoz(Base, TimestampMixin):
    """Configuración global de la función de voz (una sola fila)."""

    __tablename__ = "parametro_voz"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    activado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    duracion_maxima_segundos: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    idioma: Mapped[str] = mapped_column(String(10), nullable=False, default="es")
