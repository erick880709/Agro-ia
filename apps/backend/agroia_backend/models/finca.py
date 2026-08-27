"""Modelo Finca — predio agrícola del usuario."""
import uuid

from agroia.database import Base
from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia_backend.models import TenantMixin, TimestampMixin


class Finca(Base, TenantMixin, TimestampMixin):
    """Predio agrícola registrado por un usuario."""

    __tablename__ = "fincas"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.usuarios.id"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    latitud: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Latitud GPS (WGS84)"
    )
    longitud: Mapped[float | None] = mapped_column(
        Float, nullable=True,
        comment="Longitud GPS (WGS84)"
    )
    area_hectareas: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Área total en hectáreas"
    )
    altitud_msnm: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Altitud en metros sobre el nivel del mar"
    )
    departamento: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    municipio: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    # ── Registro de finca (rol administrador) ──
    coordenadas_google: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        comment="Enlace de Google Maps o 'lat,lng' del predio"
    )
    propietario: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Nombre del propietario"
    )
    contacto_telefono: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Teléfono de contacto"
    )
    contacto_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Email de contacto"
    )
    largo_metros: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Largo del terreno en metros (opcional)"
    )
    ancho_metros: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Ancho del terreno en metros (opcional)"
    )
    # ── Topografía, drenaje e historial de manejo (2026-08-27) ──
    pendiente_pct: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Pendiente del lote en porcentaje"
    )
    drenaje: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        comment="Drenaje del lote: Bueno | Regular | Deficiente"
    )
    historial_agronomico: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Historial de manejo: cultivo anterior, fertilización, encalado"
    )
    validacion_laboratorio: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
        comment="¿El análisis fue validado en laboratorio?"
    )
    cultivo_sembrado: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Cultivo actualmente sembrado"
    )
    edad_anos: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Edad del cultivo/árbol en años"
    )
    etapa_fenologica: Mapped[str | None] = mapped_column(
        String(30), nullable=True,
        comment="Etapa fenológica: Vegetativa | Floración | Fructificación | Cosecha"
    )

    def __repr__(self) -> str:
        return f"<Finca {self.nombre}>"
