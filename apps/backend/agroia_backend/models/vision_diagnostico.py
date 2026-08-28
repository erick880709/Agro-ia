"""Modelo VisionDiagnostico — resultados de análisis de imágenes de plagas."""

import uuid
from datetime import datetime

from agroia.database import Base
from sqlalchemy import JSON, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class VisionDiagnostico(Base):
    """Un diagnóstico de visión por computadora asociado a una finca."""

    __tablename__ = "vision_diagnosticos"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    finca_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    imagen_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resultado_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
