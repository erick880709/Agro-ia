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
from agroia.database import configure_search_path, normalize_asyncpg_url
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
    engine = create_async_engine(normalize_asyncpg_url(settings.database_url), echo=False)
    configure_search_path(engine)
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
        for lect in LECTURAS:
            lectura = SensorReading(
                finca_id=FINCA_ID,
                ts=ahora - timedelta(days=lect["dias_atras"], minutes=lect["dias_atras"] * 7),
                sensor_id=DEVICE_ID,
                ph=lect["ph"],
                nitrogeno=lect["nitrogeno"],
                fosforo=lect["fosforo"],
                potasio=lect["potasio"],
                calcio=lect["calcio"],
                magnesio=lect["magnesio"],
                azufre=lect["azufre"],
                hierro=lect["hierro"],
                manganeso=lect["manganeso"],
                zinc=lect["zinc"],
                cobre=lect["cobre"],
                boro=lect["boro"],
                materia_organica=lect["materia_organica"],
                cic=lect["cic"],
                textura=lect["textura"],
                humedad=lect["humedad"],
                temperatura_suelo=lect["temperatura_suelo"],
                conductividad_electrica=lect["conductividad_electrica"],
                humedad_ambiental=lect["humedad_ambiental"],
                temperatura_ambiental=lect["temperatura_ambiental"],
                calidad=lect["calidad"],
            )
            session.add(lectura)
            insertadas += 1

        await session.commit()
        print(f"✅ {insertadas} lecturas simuladas insertadas (18 variables cada una)")

        # ── Cuadrícula de muestreo 3×3 para el mapa de calor del lote ──
        # (250 m × 100 m → posiciones x: 20/125/230, y: 10/50/90)
        ya_geo = (
            await session.execute(
                select(SensorReading)
                .where(
                    SensorReading.finca_id == FINCA_ID,
                    SensorReading.pos_x.isnot(None),
                )
                .limit(1)
            )
        ).scalars().first()
        if ya_geo is not None:
            print("ℹ️ Ya existen muestras georreferenciadas; se omite la cuadrícula.")
        else:
            cuadricula = []
            # gradientes simples por posición (col, fila) para pintar el mapa
            for fila, y in enumerate([90.0, 50.0, 10.0]):
                for col, x in enumerate([20.0, 125.0, 230.0]):
                    t = (col + fila) / 4.0  # 0.0 → 1.0 según la posición
                    cuadricula.append({
                        "pos_x": x, "pos_y": y,
                        "ph": round(5.6 + t * 1.1, 2),                 # 5.6 → 6.7
                        "nitrogeno": round(210 - t * 80, 1),           # 250 → 170
                        "fosforo": round(20 + t * 16, 1),              # 20 → 36
                        "potasio": round(75 + t * 40, 1),              # 75 → 115
                        "calcio": round(1450 + t * 450, 0),            # 1450 → 1900
                        "magnesio": round(240 + t * 140, 0),           # 240 → 380
                        "azufre": round(14 + t * 15, 1),               # 14 → 29
                        "hierro": round(60 + t * 30, 1),
                        "manganeso": round(22 + t * 12, 1),
                        "zinc": round(3.2 + t * 2.6, 2),
                        "cobre": round(1.6 + t * 1.2, 2),
                        "boro": round(0.4 + t * 0.5, 2),
                        "materia_organica": round(7.0 + t * 8.0, 1),   # 7 → 15
                        "cic": round(13.5 + t * 8.5, 1),               # 13.5 → 22
                        "humedad": round(25 + t * 18, 1),              # 25 → 43
                        "temperatura_suelo": round(18.0 + t * 4.5, 1),
                        "conductividad_electrica": round(0.4 + t * 0.45, 2),
                        "humedad_ambiental": round(68 + t * 15, 1),
                        "temperatura_ambiental": round(19.5 + t * 3.0, 1),
                    })
            n_geo = 0
            for g in cuadricula:
                session.add(SensorReading(
                    finca_id=FINCA_ID,
                    ts=ahora - timedelta(minutes=3),
                    sensor_id=DEVICE_ID,
                    pos_x=g["pos_x"],
                    pos_y=g["pos_y"],
                    ph=g["ph"],
                    nitrogeno=g["nitrogeno"],
                    fosforo=g["fosforo"],
                    potasio=g["potasio"],
                    calcio=g["calcio"],
                    magnesio=g["magnesio"],
                    azufre=g["azufre"],
                    hierro=g["hierro"],
                    manganeso=g["manganeso"],
                    zinc=g["zinc"],
                    cobre=g["cobre"],
                    boro=g["boro"],
                    materia_organica=g["materia_organica"],
                    cic=g["cic"],
                    textura=TexturaSuelo.ARCILLA,
                    humedad=g["humedad"],
                    temperatura_suelo=g["temperatura_suelo"],
                    conductividad_electrica=g["conductividad_electrica"],
                    humedad_ambiental=g["humedad_ambiental"],
                    temperatura_ambiental=g["temperatura_ambiental"],
                    calidad="OK",
                ))
                n_geo += 1
            await session.commit()
            print(f"✅ Cuadrícula 3×3 insertada ({n_geo} muestras con posición x,y para el mapa de calor)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
