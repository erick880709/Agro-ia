"""Modelos AGC-COST (F4-F5) — identidad, teléfonos y configuración de cobro.

P-14 (identidad y contacto) y P-15 (documentos de cobro) del RFP AgroIA v4.
Dinero en NUMERIC(18,4) (Decimal). Auditoría creado_por/creado_en/
actualizado_por/actualizado_en.
"""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class CosteoIdentidad(Base):
    """Identidad de la empresa para cotizaciones y documentos (P-14)."""

    __tablename__ = "costeo_identidad"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conjunto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="SET NULL"),
        nullable=True,
    )
    nombre_comercial: Mapped[str] = mapped_column(String(150), nullable=False)
    razon_social: Mapped[str | None] = mapped_column(String(150), nullable=True)
    nit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    regimen: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sitio_web: Mapped[str | None] = mapped_column(String(200), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_oscuro_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    color_acento: Mapped[str | None] = mapped_column(String(9), nullable=True, server_default="#1b5e20")
    pie_legal: Mapped[str | None] = mapped_column(Text, nullable=True)
    terminos_condiciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    sede_latitud: Mapped[float | None] = mapped_column(nullable=True)
    sede_longitud: Mapped[float | None] = mapped_column(nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CosteoIdentidad {self.nombre_comercial}>"


class CosteoTelefono(Base):
    """Teléfono de contacto con etiqueta y orden (P-14)."""

    __tablename__ = "costeo_telefono"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identidad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_identidad.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    etiqueta: Mapped[str] = mapped_column(String(40), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    whatsapp: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CosteoTelefono {self.etiqueta} {self.numero}>"


class CobroConfig(Base):
    """Configuración de documentos de cobro: numeración y resolución (P-15)."""

    __tablename__ = "cobro_config"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conjunto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="SET NULL"),
        nullable=True,
    )
    tipo_documento: Mapped[str] = mapped_column(
        String(30), nullable=False, default="cuenta_cobro", server_default="cuenta_cobro",
        comment="cuenta_cobro | factura_venta",
    )
    prefijo: Mapped[str] = mapped_column(String(10), nullable=False, default="CC", server_default="CC")
    numero_desde: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    numero_hasta: Mapped[int] = mapped_column(Integer, nullable=False, default=10000, server_default="10000")
    resolucion_dian: Mapped[str | None] = mapped_column(String(40), nullable=True)
    resolucion_vigencia_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    plazo_pago_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=30, server_default="30")
    medios_pago: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cuenta_bancaria: Mapped[str | None] = mapped_column(Text, nullable=True)
    textos_legales: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    aviso_numeracion_restante: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, server_default="10"
    )

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CobroConfig {self.tipo_documento} {self.prefijo}>"
