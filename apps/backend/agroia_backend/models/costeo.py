"""Modelos AGC-COST (F1) — catálogo de parámetros de costeo versionado.

Estructura según RFP AgroIA v4 §9: conjunto → servicios → componentes →
tramos; factores con opciones; densidad, zonas, impuestos, política y
descuentos. Dinero en NUMERIC(18,4) (Decimal). Todas las tablas llevan
auditoría creado_por/creado_en/actualizado_por/actualizado_en.

Las tablas de estimación (`estimacion*`) y cobro (`cobro_*`) se agregan en
las fases F3 y F5 del RFP.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from agroia.database import Base
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

ESTADOS_CONJUNTO = ("borrador", "en_revision", "publicado", "archivado")
TIPOS_COMPONENTE = (
    "fijo", "escalonado", "por_unidad", "por_distancia",
    "por_jornada", "porcentual", "condicional",
)
MODOS_TRAMO = ("marginal", "completo")
MODOS_REDONDEO = ("ninguno", "mitad_superior", "techo", "piso")


class CosteoConjunto(Base):
    """Conjunto versionado de parámetros de costeo (fotografía completa)."""

    __tablename__ = "costeo_conjunto"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="borrador", server_default="borrador",
        comment="borrador | en_revision | publicado | archivado",
    )
    vigencia_desde: Mapped[date | None] = mapped_column(Date, nullable=True)
    vigencia_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    moneda: Mapped[str] = mapped_column(String(5), nullable=False, default="COP", server_default="COP")
    aprobado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    aprobado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CosteoConjunto {self.nombre} v{self.version} {self.estado}>"


class CosteoServicio(Base):
    """Servicio cotizable del catálogo (muestreo en grilla, visita, sensor…)."""

    __tablename__ = "costeo_servicio"
    __table_args__ = (
        UniqueConstraint("conjunto_id", "codigo", name="uq_costeo_servicio_codigo"),
        {"schema": "agroia"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conjunto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    unidad: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="punto | hectarea | dispositivo | dia | visita"
    )
    requiere_lote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
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
        return f"<CosteoServicio {self.codigo} unidad={self.unidad}>"


class CosteoComponente(Base):
    """Componente de costo de un servicio (sumando de la fórmula)."""

    __tablename__ = "costeo_componente"
    __table_args__ = (
        UniqueConstraint("servicio_id", "codigo", name="uq_costeo_componente_codigo"),
        {"schema": "agroia"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    servicio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_servicio.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="fijo | escalonado | por_unidad | por_distancia | por_jornada | porcentual | condicional",
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    afectable_por_factores: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CosteoComponente {self.codigo} tipo={self.tipo}>"


class CosteoTramo(Base):
    """Tramo escalonado de un componente (desde–hasta → valor unitario)."""

    __tablename__ = "costeo_tramo"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    componente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_componente.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    desde: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    hasta: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    modo: Mapped[str] = mapped_column(
        String(20), nullable=False, default="marginal", server_default="marginal",
        comment="marginal | completo",
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
        return f"<CosteoTramo {self.desde}-{self.hasta} @ {self.valor} {self.modo}>"


class CosteoFactor(Base):
    """Escala de factor (dificultad, urgencia, día no hábil…)."""

    __tablename__ = "costeo_factor"
    __table_args__ = (
        UniqueConstraint("conjunto_id", "codigo", name="uq_costeo_factor_codigo"),
        {"schema": "agroia"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conjunto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    aplicacion: Mapped[str] = mapped_column(
        String(20), nullable=False, default="porcentual", server_default="porcentual",
        comment="porcentual | multiplicativo",
    )
    combinacion: Mapped[str] = mapped_column(
        String(20), nullable=False, default="suma", server_default="suma",
        comment="suma | multiplica",
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
        return f"<CosteoFactor {self.codigo} combinacion={self.combinacion}>"


class CosteoFactorOpcion(Base):
    """Opción de una escala de factor (plano 0%, moderada 15%…)."""

    __tablename__ = "costeo_factor_opcion"
    __table_args__ = (
        UniqueConstraint("factor_id", "codigo", name="uq_costeo_factor_opcion_codigo"),
        {"schema": "agroia"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_factor.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    etiqueta: Mapped[str] = mapped_column(String(150), nullable=False)
    porcentaje: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, default=Decimal("0"), server_default="0"
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
        return f"<CosteoFactorOpcion {self.codigo} {self.porcentaje}%>"


class CosteoDensidad(Base):
    """Regla de densidad de muestreo por rango de área (opcional por cultivo)."""

    __tablename__ = "costeo_densidad"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conjunto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    area_min: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    area_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    puntos_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    puntos_max: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    puntos_por_ha: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    cultivo_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CosteoDensidad {self.area_min}-{self.area_max} ha>"


class CosteoZona(Base):
    """Zona de desplazamiento: factor, km incluidos, tarifa por km, peajes."""

    __tablename__ = "costeo_zona"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conjunto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    departamento: Mapped[str] = mapped_column(String(60), nullable=False)
    municipio: Mapped[str | None] = mapped_column(String(80), nullable=True)
    factor: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0"), server_default="0")
    km_incluidos: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=Decimal("0"), server_default="0")
    tarifa_km: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"), server_default="0")
    peajes_estimados: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"), server_default="0")

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CosteoZona {self.departamento}/{self.municipio or '*'} factor={self.factor}>"


class CosteoImpuesto(Base):
    """Impuesto o retención del conjunto (IVA, ReteFuente, ReteICA…)."""

    __tablename__ = "costeo_impuesto"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conjunto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    porcentaje: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0"), server_default="0")
    base: Mapped[str] = mapped_column(
        String(30), nullable=False, default="subtotal", server_default="subtotal",
        comment="directo | ajustado | lista",
    )
    informativo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
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
        return f"<CosteoImpuesto {self.codigo} {self.porcentaje}% informativo={self.informativo}>"


class CosteoPolitica(Base):
    """Política comercial: márgenes, piso de rentabilidad, redondeo, vigencia."""

    __tablename__ = "costeo_politica"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conjunto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    margen_objetivo: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0"), server_default="0")
    margen_minimo: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0"), server_default="0")
    piso_visita: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"), server_default="0")
    vigencia_cotizacion_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=30, server_default="30")
    redondeo_multiplo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("1"), server_default="1")
    redondeo_modo: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ninguno", server_default="ninguno",
        comment="ninguno | mitad_superior | techo | piso",
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
        return f"<CosteoPolitica margen={self.margen_objetivo}% piso={self.piso_visita}>"


class CosteoDescuento(Base):
    """Regla de descuento o recargo comercial con tope por rol."""

    __tablename__ = "costeo_descuento"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conjunto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.costeo_conjunto.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    criterio: Mapped[str] = mapped_column(
        String(40), nullable=False,
        comment="volumen_ha | n_fincas | contrato | asociacion | urgencia | no_habil | manual",
    )
    umbral: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    porcentaje: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0"), server_default="0")
    tope_rol: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    creado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CosteoDescuento {self.codigo} {self.porcentaje}% criterio={self.criterio}>"
