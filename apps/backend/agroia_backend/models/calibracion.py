"""Modelos de calibración local del sensor (Épica E4, RF-015 / RF-017).

- `CalibracionSensor`: regresión lineal (pendiente/intercepto) por dispositivo,
  variable y unidad de suelo, con n, R², RMSE, sesgo, vigencia y responsable.
  Sustituye el factor multiplicativo único (brecha G4).
- `ParCalibracion`: par sensor–laboratorio (misma muestra, mismo día y
  profundidad) que alimenta la calibración.
"""

import uuid
from datetime import date, datetime

from agroia.database import Base
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class CalibracionSensor(Base):
    """Calibración vigente (regresión lineal) de una variable de un sensor."""

    __tablename__ = "calibracion_sensor"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dispositivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.dispositivos_iot.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variable: Mapped[str] = mapped_column(
        String(40), nullable=False,
        comment="Variable calibrada (ph, humedad, conductividad_electrica, nitrogeno, fosforo, potasio)",
    )
    unidad_suelo: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Unidad de suelo de la calibración (andisol, oxisol, aluvial…)",
    )
    pendiente: Mapped[float] = mapped_column(Float, nullable=False)
    intercepto: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    n: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r2: Mapped[float | None] = mapped_column(Float, nullable=True)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    sesgo: Mapped[float | None] = mapped_column(Float, nullable=True)
    vigencia: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsable: Mapped[str | None] = mapped_column(String(200), nullable=True)
    activa: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ParCalibracion(Base):
    """Par sensor–laboratorio (RF-017): misma muestra, mismo día y profundidad."""

    __tablename__ = "par_calibracion"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    calibracion_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.calibracion_sensor.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    dispositivo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.dispositivos_iot.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variable: Mapped[str] = mapped_column(String(40), nullable=False)
    valor_sensor: Mapped[float] = mapped_column(Float, nullable=False)
    valor_laboratorio: Mapped[float] = mapped_column(Float, nullable=False)
    metodo: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="Método de laboratorio (pH 1:1, Bray II, acetato de amonio, CE 1:5…)",
    )
    laboratorio: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    profundidad_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    punto_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
