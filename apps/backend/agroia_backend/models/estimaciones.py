"""Modelos AGC-COST (F3) — estimaciones con snapshot inmutable y eventos.

Ciclo de vida: borrador → emitida → aceptada/rechazada/vencida (RFP §10).
El snapshot guarda los parámetros resueltos y su hash SHA-256 para
reproducibilidad dígito a dígito. Dinero en NUMERIC(18,4).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from agroia.database import Base
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

ESTADOS_ESTIMACION = ("borrador", "emitida", "aceptada", "rechazada", "vencida")


class Estimacion(Base):
    """Estimación de costo persistida para una finca (RFP §9)."""

    __tablename__ = "estimacion"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consecutivo: Mapped[str | None] = mapped_column(String(30), nullable=True, unique=True)
    finca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.fincas.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    conjunto_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="RESTRICT"),
        nullable=True,
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="borrador", server_default="borrador",
        comment="borrador | emitida | aceptada | rechazada | vencida",
    )
    fecha_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    area_total_ha: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    total_directo: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    total_ajustado: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    precio_lista: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    descuento_aplicado: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    total_final: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    margen_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    vence_en: Mapped[date | None] = mapped_column(Date, nullable=True)
    emitido_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    emitido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo_excepcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    seleccion: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Estimacion {self.consecutivo or self.id} {self.estado}>"


class EstimacionLinea(Base):
    """Línea de desglose de una estimación (RFP §9)."""

    __tablename__ = "estimacion_linea"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estimacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.estimacion.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    lote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.lotes.id", ondelete="SET NULL"),
        nullable=True,
    )
    servicio_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_servicio.id", ondelete="SET NULL"),
        nullable=True,
    )
    componente_codigo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    descripcion: Mapped[str] = mapped_column(String(250), nullable=False)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("1"))
    unidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    parametro_ref: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<EstimacionLinea {self.descripcion} {self.valor}>"


class EstimacionSnapshot(Base):
    """Copia inmutable de los parámetros resueltos y su hash (RFP §9)."""

    __tablename__ = "estimacion_snapshot"
    __table_args__ = {"schema": "agroia"}

    estimacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.estimacion.id", ondelete="CASCADE"),
        primary_key=True,
    )
    parametros: Mapped[dict] = mapped_column(JSONB, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<EstimacionSnapshot {self.estimacion_id} {self.hash_sha256[:12]}>"


class EstimacionEvento(Base):
    """Evento del ciclo de vida de una estimación (RFP §9)."""

    __tablename__ = "estimacion_evento"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estimacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.estimacion.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    evento: Mapped[str] = mapped_column(String(40), nullable=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<EstimacionEvento {self.evento}>"
