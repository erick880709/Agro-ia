"""Modelo SensorReading — datos crudos de sensores IoT (18 variables).

Usa TimescaleDB hypertable para series temporales.
No tiene tenant_id — los datos de sensor se asocian vía finca_id.
"""

import uuid
from datetime import datetime
from typing import Optional

import enum

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agroia.database import Base


class TexturaSuelo(str, enum.Enum):
    ARENA = "Arena"
    LIMO = "Limo"
    ARCILLA = "Arcilla"


class SensorReading(Base):
    """Lectura de sensor IoT de suelo (18 variables)."""

    __tablename__ = "sensor_readings"
    __table_args__ = {"schema": "agroia"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agroia.fincas.id"),
        nullable=False,
        index=True,
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        comment="Marca de tiempo de la medición (fuente: sensor IoT)"
    )

    # ── Macronutrientes ──
    ph: Mapped[float | None] = mapped_column(Float, nullable=True, comment="0-14")
    nitrogeno: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")
    fosforo: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")
    potasio: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")

    # ── Nutrientes secundarios ──
    calcio: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")
    magnesio: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")
    azufre: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")

    # ── Micronutrientes ──
    hierro: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")
    manganeso: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")
    zinc: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")
    cobre: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")
    boro: Mapped[float | None] = mapped_column(Float, nullable=True, comment="ppm")

    # ── Propiedades físicas y químicas ──
    materia_organica: Mapped[float | None] = mapped_column(Float, nullable=True, comment="%")
    cic: Mapped[float | None] = mapped_column(Float, nullable=True, comment="meq/100g")
    textura: Mapped[TexturaSuelo | None] = mapped_column(
        nullable=True,
    )
    humedad: Mapped[float | None] = mapped_column(Float, nullable=True, comment="%")
    temperatura_suelo: Mapped[float | None] = mapped_column(Float, nullable=True, comment="°C")
    conductividad_electrica: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="dS/m"
    )

    # ── Ambientales (telemetría del sensor, NO variables de suelo) ──
    humedad_ambiental: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="% humedad relativa ambiente (DHT22)"
    )
    temperatura_ambiental: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="°C temperatura ambiente"
    )

    # ── Estado del dato ──
    sensor_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="ID del dispositivo LoRaWAN"
    )
    calidad: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="Indicador de calidad: OK, out_of_range, frozen, gap"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SensorReading finca={self.finca_id} ts={self.ts}>"
