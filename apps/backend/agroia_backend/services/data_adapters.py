"""Data Adapters para el motor de recomendaciones.

Proveen una interfaz unificada para consultar datos de suelo, clima,
NDVI y GIS, abstrayendo la fuente de almacenamiento subyacente.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from agroia.logging import get_logger

from agroia_backend.models.sensor_reading import SensorReading

logger = get_logger(__name__)

# ── Variables bloqueantes vs no bloqueantes ──
# Relajado (2026-08-25, brecha G3): los sensores ESP32 solo entregan pH + CE
# de forma confiable. Se permite recomendación parcial con advertencia
# cuando faltan materia orgánica, NPK u otras variables no bloqueantes.
VARIABLES_BLOQUEANTES = {"ph", "conductividad_electrica"}
VARIABLES_NO_BLOQUEANTES = {"boro", "sodio"}  # y micronutrientes restantes
ALL_SOIL_VARIABLES = [
    "ph", "nitrogeno", "fosforo", "potasio",
    "calcio", "magnesio", "azufre",
    "hierro", "manganeso", "zinc", "cobre", "boro",
    "materia_organica", "cic", "textura", "humedad",
    "temperatura_suelo", "conductividad_electrica",
]


@dataclass
class SoilData:
    """Datos de suelo normalizados para el motor de recomendaciones."""
    finca_id: str
    ts: datetime
    ph: float | None = None
    nitrogeno: float | None = None
    fosforo: float | None = None
    potasio: float | None = None
    calcio: float | None = None
    magnesio: float | None = None
    azufre: float | None = None
    hierro: float | None = None
    manganeso: float | None = None
    zinc: float | None = None
    cobre: float | None = None
    boro: float | None = None
    materia_organica: float | None = None
    cic: float | None = None
    textura: str | None = None
    humedad: float | None = None
    temperatura_suelo: float | None = None
    conductividad_electrica: float | None = None
    calidad: str | None = "OK"
    missing_blocking: list[str] = field(default_factory=list)
    missing_non_blocking: list[str] = field(default_factory=list)

    @property
    def has_sufficient_data(self) -> bool:
        """¿Hay suficientes datos para generar una recomendación?"""
        return len(self.missing_blocking) == 0

    def to_dict(self) -> dict:
        """Convierte a diccionario para el motor ML."""
        return {
            v: getattr(self, v)
            for v in ALL_SOIL_VARIABLES
            if getattr(self, v) is not None
        }


# ── Rangos físicos de validación ──
SOIL_RANGES = {
    "ph": (0, 14),
    "nitrogeno": (0, 500),
    "fosforo": (0, 500),
    "potasio": (0, 500),
    "calcio": (0, 10000),
    "magnesio": (0, 5000),
    "azufre": (0, 500),
    "hierro": (0, 100),
    "manganeso": (0, 50),
    "zinc": (0, 50),
    "cobre": (0, 20),
    "boro": (0, 10),
    "materia_organica": (0, 100),
    "cic": (0, 100),
    "humedad": (0, 100),
    "temperatura_suelo": (-20, 60),
    "conductividad_electrica": (0, 20),
}


def validate_soil_reading(reading: SensorReading) -> SoilData:
    """Valida una lectura de sensor y la convierte a SoilData normalizado."""
    data = SoilData(
        finca_id=str(reading.finca_id),
        ts=reading.ts,
    )
    for var in ALL_SOIL_VARIABLES:
        value = getattr(reading, var, None)
        setattr(data, var, value)

        # Validar rangos físicos
        if value is not None and var in SOIL_RANGES:
            lo, hi = SOIL_RANGES[var]
            if value < lo or value > hi:
                logger.warning(
                    "soil_value_out_of_range",
                    variable=var, value=value, range=f"[{lo}, {hi}]",
                    finca_id=str(reading.finca_id),
                )
                data.calidad = "out_of_range"

        # Clasificar como faltante
        if value is None:
            if var in VARIABLES_BLOQUEANTES:
                data.missing_blocking.append(var)
            else:
                data.missing_non_blocking.append(var)

    return data


class SueloAdapter:
    """Adaptador para consultar datos de suelo desde PostgreSQL+TimescaleDB."""

    def __init__(self, db_session):
        self.db = db_session

    async def get_latest(self, finca_id: str, max_age_hours: int = 24) -> SoilData | None:
        """Obtiene la lectura más reciente para una finca (máx. 24h de antigüedad)."""
        from sqlalchemy import desc, select

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        stmt = (
            select(SensorReading)
            .where(
                SensorReading.finca_id == finca_id,
                SensorReading.ts >= cutoff,
            )
            .order_by(desc(SensorReading.ts))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        reading = result.scalar_one_or_none()
        if reading is None:
            logger.info("no_recent_soil_data", finca_id=finca_id, max_age_hours=max_age_hours)
            return None
        return validate_soil_reading(reading)

    async def get_history(
        self, finca_id: str, days: int = 90
    ) -> list[SoilData]:
        """Obtiene el histórico de lecturas para una finca."""
        from sqlalchemy import select

        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(SensorReading)
            .where(
                SensorReading.finca_id == finca_id,
                SensorReading.ts >= cutoff,
            )
            .order_by(SensorReading.ts)
        )
        result = await self.db.execute(stmt)
        return [validate_soil_reading(r) for r in result.scalars().all()]
