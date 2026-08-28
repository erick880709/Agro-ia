"""Modelos ChecklistBpa y PeriodoCarencia — trazabilidad BPA / certificación."""

import uuid
from datetime import date

from agroia.database import Base
from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class ChecklistBpa(Base):
    """Ítem del checklist de Buenas Prácticas Agrícolas (Res. ICA 30021/2017)."""

    __tablename__ = "checklist_bpa"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.fincas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(60), nullable=True)
    cumple: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    evidencia_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fecha_verificacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    verificado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agroia.usuarios.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ChecklistBpa {self.item}>"


class PeriodoCarencia(Base):
    """Período de carencia (días) de un producto agroquímico para exportación."""

    __tablename__ = "periodos_carencia"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    producto: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    dias_carencia: Mapped[int] = mapped_column(Integer, nullable=False)
    fuente: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<PeriodoCarencia {self.producto} {self.dias_carencia}d>"
