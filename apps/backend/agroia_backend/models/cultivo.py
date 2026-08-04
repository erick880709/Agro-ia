"""Modelo Cultivo — catálogo de cultivos con fichas técnicas."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agroia.database import Base
from agroia_backend.models import TimestampMixin

# ── Enums ──

class EstadoFicha(str, Enum):
    BORRADOR = "Borrador"
    EN_REVISION = "EnRevision"
    PUBLICADO = "Publicado"


class TipoFuente(str, Enum):
    NACIONAL = "Nacional"
    INTERNACIONAL = "Internacional"


# ── Modelos ──

class Cultivo(Base, TimestampMixin):
    """Catálogo de cultivos. Datos compartidos (sin tenant_id)."""

    __tablename__ = "cultivos"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    nombre_cientifico: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    icono: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Emoji o código de icono"
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relaciones
    fichas_tecnicas: Mapped[list["FichaTecnica"]] = relationship(
        "FichaTecnica", back_populates="cultivo"
    )
    recomendaciones: Mapped[list["Recomendacion"]] = relationship(
        "Recomendacion", backref="cultivo_rel"
    )

    def __repr__(self) -> str:
        return f"<Cultivo {self.nombre}>"


class FichaTecnica(Base, TimestampMixin):
    """Ficha técnica de un cultivo con umbrales edafoclimáticos.

    Flujo: Borrador → En Revisión → Publicado.
    SLA de revisión: 5 días hábiles desde envío.
    Alerta si no ha sido revisada en 12 meses.
    """

    __tablename__ = "fichas_tecnicas"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cultivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.cultivos.id"),
        nullable=False,
        index=True,
    )
    estado: Mapped[EstadoFicha] = mapped_column(
        Enum(EstadoFicha, name="estado_ficha_enum", schema="agroia"),
        nullable=False,
        default=EstadoFicha.BORRADOR,
    )
    tipo_fuente: Mapped[TipoFuente] = mapped_column(
        Enum(TipoFuente, name="tipo_fuente_enum", schema="agroia"),
        nullable=False,
        default=TipoFuente.NACIONAL,
    )
    fuente: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Origen verificable (Cenicafé, 2007, Guía...)"
    )
    etiqueta_internacional: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="True si solo tiene fuente internacional (FAO GAEZ)"
    )

    # ── Umbrales edafoclimáticos (JSONB) ──
    umbrales: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Umbrales ideales: {ph: {min, max, unidad}, temperatura: {...}, ...}"
    )

    # ── Datos económicos (JSONB) ──
    datos_economicos: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="Rendimiento esperado, precio referencia, costo producción, ciclo"
    )

    # ── Trazabilidad ──
    creado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.usuarios.id"), nullable=True
    )
    revisado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.usuarios.id"), nullable=True,
        comment="Técnico que revisó/aprobó"
    )
    fecha_envio_revision: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Cuándo se envió a revisión (para SLA 5 días)"
    )
    fecha_revision: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Cuándo fue revisada (aprobada o rechazada)"
    )
    fecha_ultima_revision: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Última vez que un técnico revisó esta ficha"
    )
    notas_revision: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Notas del técnico al rechazar"
    )

    # Relaciones
    cultivo: Mapped["Cultivo"] = relationship("Cultivo", back_populates="fichas_tecnicas")

    @property
    def sla_vencido(self) -> bool:
        """¿Se venció el SLA de revisión (5 días hábiles)?"""
        if self.fecha_envio_revision and self.estado == EstadoFicha.EN_REVISION:
            return datetime.utcnow() > self.fecha_envio_revision + timedelta(days=7)
        return False

    @property
    def requiere_revision_periodica(self) -> bool:
        """¿Han pasado más de 12 meses desde la última revisión?"""
        if self.estado == EstadoFicha.PUBLICADO and self.fecha_ultima_revision:
            return datetime.utcnow() > self.fecha_ultima_revision + timedelta(days=365)
        return False

    @property
    def puede_usarse_en_recomendaciones(self) -> bool:
        """¿Los umbrales de esta ficha pueden usarse para generar recomendaciones?"""
        return self.estado == EstadoFicha.PUBLICADO and not self.etiqueta_internacional

    def __repr__(self) -> str:
        return f"<FichaTecnica cultivo={self.cultivo_id} estado={self.estado.value}>"
