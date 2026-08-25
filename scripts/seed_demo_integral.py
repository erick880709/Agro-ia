"""Siembra la finca demo integral con lecturas simuladas completas.

Crea/actualiza el dispositivo `esp32-demo-001` (calibrado) y 3 lecturas
históricas con las 18 variables de suelo para la finca demo, de modo que
todos los casos de uso (UC1, UC2, reportes, historial) tengan datos ricos.

Uso:  python scripts/seed_demo_integral.py
"""

import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, "apps/shared")
sys.path.insert(0, "apps/backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agroia.config import get_settings
from agroia_backend.models.dispositivo_iot import DispositivoIoT
from agroia_backend.models.finca import Finca  # noqa: F401 (registra la tabla en metadata)
from agroia_backend.models.sensor_reading import SensorReading, TexturaSuelo

FINCA_ID = uuid.UUID("8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936")
DEVICE_ID = "esp32-demo-001"

# 3 lecturas: deficiente → en corrección → actual (casi óptima para café)
LECTURAS = [
    {
        "dias_atras": 15,
        "ph": 7.2, "nitrogeno": 45, "fosforo": 14, "potasio": 78,
        "calcio": 1400, "magnesio": 260, "azufre": 15,
        "hierro": 65, "manganeso": 24, "zinc": 3.5, "cobre": 1.8, "boro": 0.5,
        "materia_organica": 8.2, "cic": 15.2, "textura": TexturaSuelo.ARCILLA,
        "humedad": 28, "temperatura_suelo": 19.5, "conductividad_electrica": 0.50,
        "humedad_ambiental": 72.0, "temperatura_ambiental": 20.5,
        "calidad": "OK",
    },
    {
        "dias_atras": 7,
        "ph": 6.8, "nitrogeno": 140, "fosforo": 22, "potasio": 88,
        "calcio": 1500, "magnesio": 280, "azufre": 18,
        "hierro": 70, "manganeso": 26, "zinc": 4.0, "cobre": 2.0, "boro": 0.6,
        "materia_organica": 9.5, "cic": 16.5, "textura": TexturaSuelo.ARCILLA,
        "humedad": 30, "temperatura_suelo": 20.0, "conductividad_electrica": 0.55,
        "humedad_ambiental": 74.0, "temperatura_ambiental": 20.8,
        "calidad": "OK",
    },
    {
        "dias_atras": 0,
        "ph": 6.1, "nitrogeno": 260, "fosforo": 28, "potasio": 95,
        "calcio": 1680, "magnesio": 310, "azufre": 22,
        "hierro": 75, "manganeso": 28, "zinc": 4.5, "cobre": 2.2, "boro": 0.7,
        "materia_organica": 11.5, "cic": 17.8, "textura": TexturaSuelo.ARCILLA,
        "humedad": 34, "temperatura_suelo": 20.5, "conductividad_electrica": 0.62,
        "humedad_ambiental": 76.5, "temperatura_ambiental": 21.2,
        "calidad": "OK",
    },
]


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # ── Dispositivo (calibrado) ──
        disp = (
            await session.execute(
                select(DispositivoIoT).where(DispositivoIoT.device_id == DEVICE_ID)
            )
        ).scalar_one_or_none()
        if disp is None:
            disp = DispositivoIoT(
                finca_id=FINCA_ID,
                device_id=DEVICE_ID,
                nombre="Sensor Integral Demo",
                activo=True,
                npk_calibrado=True,
                factores_calibracion={"nitrogeno": 1.0, "fosforo": 1.0, "potasio": 1.0},
                rssi=-45,
                uptime_s=604800,
                ultima_transmision=datetime.now(timezone.utc),
            )
            session.add(disp)
            await session.flush()
            print(f"✅ Dispositivo {DEVICE_ID} creado (NPK calibrado)")
        else:
            disp.npk_calibrado = True
            disp.factores_calibracion = {"nitrogeno": 1.0, "fosforo": 1.0, "potasio": 1.0}
            print(f"ℹ️ Dispositivo {DEVICE_ID} ya existía; calibración actualizada")

        # ── Lecturas ──
        ahora = datetime.now(timezone.utc)
        insertadas = 0
        for l in LECTURAS:
            lectura = SensorReading(
                finca_id=FINCA_ID,
                ts=ahora - timedelta(days=l["dias_atras"], minutes=l["dias_atras"] * 7),
                sensor_id=DEVICE_ID,
                ph=l["ph"],
                nitrogeno=l["nitrogeno"],
                fosforo=l["fosforo"],
                potasio=l["potasio"],
                calcio=l["calcio"],
                magnesio=l["magnesio"],
                azufre=l["azufre"],
                hierro=l["hierro"],
                manganeso=l["manganeso"],
                zinc=l["zinc"],
                cobre=l["cobre"],
                boro=l["boro"],
                materia_organica=l["materia_organica"],
                cic=l["cic"],
                textura=l["textura"],
                humedad=l["humedad"],
                temperatura_suelo=l["temperatura_suelo"],
                conductividad_electrica=l["conductividad_electrica"],
                humedad_ambiental=l["humedad_ambiental"],
                temperatura_ambiental=l["temperatura_ambiental"],
                calidad=l["calidad"],
            )
            session.add(lectura)
            insertadas += 1

        await session.commit()
        print(f"✅ {insertadas} lecturas simuladas insertadas (18 variables cada una)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
