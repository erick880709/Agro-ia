"""Modelo PrecioInsumo — precios dinámicos de insumos agrícolas (COP/kg).

El plan económico (ROI) lee estos precios para no quedar desactualizado:
si un producto no tiene registro, `economia.calcular_plan_economico`
usa el costo estático de referencia y lo advierte en el reporte.
"""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class PrecioInsumo(Base):
    """Precio vigente de un insumo (producto) en COP por kilogramo."""

    __tablename__ = "precios_insumos"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    producto: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True,
        comment="Nombre comercial del insumo (clave de negocio)",
    )
    precio_kg_cop: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Precio en COP por kilogramo"
    )
    fecha_actualizacion: Mapped[date] = mapped_column(
        Date, nullable=False, index=True,
        comment="Fecha en que el Admin actualizó el precio",
    )
    fuente: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Fuente del precio (cotización, agrotienda, bolsa…)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<PrecioInsumo {self.producto} {self.precio_kg_cop} COP/kg>"
