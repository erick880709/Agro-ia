"""Modelos AGC-COST (F5) — documentos de cobro, líneas, pagos y eventos.

El documento hereda las líneas de una estimación aceptada y es inmutable
una vez emitido (RFP §9). Numeración consecutiva asignada en el servidor.
Dinero en NUMERIC(18,4).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from agroia.database import Base
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

ESTADOS_COBRO = ("borrador", "emitido", "enviado", "pagado_parcial", "pagado", "vencido", "anulado")


class CobroDocumento(Base):
    """Documento de cobro emitido desde una estimación aceptada (RFP §9)."""

    __tablename__ = "cobro_documento"
    __table_args__ = (
        UniqueConstraint("prefijo", "consecutivo", name="uq_cobro_consecutivo"),
        {"schema": "agroia"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consecutivo: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prefijo: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tipo: Mapped[str] = mapped_column(
        String(30), nullable=False, default="cuenta_cobro", server_default="cuenta_cobro",
        comment="cuenta_cobro | factura_venta",
    )
    estimacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.estimacion.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    estado: Mapped[str] = mapped_column(
        String(25), nullable=False, default="borrador", server_default="borrador",
        comment="borrador | emitido | enviado | pagado_parcial | pagado | vencido | anulado",
    )
    fecha_emision: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    impuestos: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    saldo: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    identidad_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cufe: Mapped[str | None] = mapped_column(String(120), nullable=True)
    xml_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    anulado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    motivo_anulacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    documento_anulado_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CobroDocumento {self.prefijo}-{self.consecutivo} {self.estado}>"


class CobroLinea(Base):
    """Línea heredada de la estimación en el documento de cobro."""

    __tablename__ = "cobro_linea"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cobro_documento.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    descripcion: Mapped[str] = mapped_column(String(250), nullable=False)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("1"))
    unidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    impuesto_codigo: Mapped[str | None] = mapped_column(String(40), nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CobroLinea {self.descripcion} {self.valor}>"


class CobroPago(Base):
    """Pago total o parcial aplicado a un documento de cobro."""

    __tablename__ = "cobro_pago"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cobro_documento.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    medio: Mapped[str | None] = mapped_column(String(40), nullable=True)
    referencia: Mapped[str | None] = mapped_column(String(120), nullable=True)
    soporte_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    registrado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CobroPago {self.valor} {self.medio}>"


class CobroEvento(Base):
    """Evento del ciclo de vida del documento de cobro."""

    __tablename__ = "cobro_evento"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cobro_documento.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    evento: Mapped[str] = mapped_column(String(40), nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CobroEvento {self.evento}>"
