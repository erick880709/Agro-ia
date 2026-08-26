"""Diagnóstico TEMPORAL de tipos enum en la BD (se elimina tras usar)."""

from fastapi import APIRouter
from sqlalchemy import text

from agroia.database import async_session_factory

router = APIRouter(prefix="/api/v1", tags=["debug"])


@router.get("/debug/types")
async def debug_types():
    async with async_session_factory() as db:
        search_path = (await db.execute(text("SHOW search_path"))).scalar()
        tipos_textura = [
            tuple(r)
            for r in (
                await db.execute(
                    text(
                        "SELECT n.nspname, t.typname, t.typtype FROM pg_type t "
                        "JOIN pg_namespace n ON n.oid = t.typnamespace "
                        "WHERE t.typname LIKE '%textura%' OR t.typname LIKE '%suelo%'"
                    )
                )
            ).all()
        ]
        col_textura = (
            await db.execute(
                text(
                    "SELECT format_type(a.atttypid, a.atttypmod) "
                    "FROM pg_attribute a "
                    "JOIN pg_class c ON c.oid = a.attrelid "
                    "JOIN pg_namespace n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = 'agroia' AND c.relname = 'sensor_readings' "
                    "AND a.attname = 'textura'"
                )
            )
        ).scalar()
        version = (
            await db.execute(text("SELECT version_num FROM agroia.alembic_version"))
        ).scalars().all()
        enums_agroia = (
            await db.execute(
                text(
                    "SELECT t.typname FROM pg_type t "
                    "JOIN pg_namespace n ON n.oid = t.typnamespace "
                    "WHERE n.nspname = 'agroia' AND t.typtype = 'e' "
                    "ORDER BY t.typname"
                )
            )
        ).scalars().all()
    return {
        "search_path": search_path,
        "tipos_textura": tipos_textura,
        "columna_textura_tipo": col_textura,
        "alembic_version": version,
        "enums_agroia": enums_agroia,
        "orm_insert_test": await _orm_insert_test(),
        "pool_probe": await _pool_probe(),
    }


async def _pool_probe():
    """Prueba 8 sesiones del pool: search_path + INSERT ORM por sesión."""
    import asyncio

    from datetime import datetime, timezone
    from uuid import uuid4

    from sqlalchemy import select, text

    from agroia_backend.models.finca import Finca
    from agroia_backend.models.sensor_reading import SensorReading

    async def una(n: int):
        async with async_session_factory() as db:
            sp = (await db.execute(text("SHOW search_path"))).scalar()
            finca = (await db.execute(select(Finca).limit(1))).scalars().first()
            if finca is None:
                return {"n": n, "sp": sp, "ok": False, "error": "sin fincas"}
            try:
                db.add(
                    SensorReading(
                        id=uuid4(),
                        finca_id=finca.id,
                        ts=datetime.now(timezone.utc),
                        ph=6.5,
                        sensor_id=f"debug-pool-{n}",
                        calidad="debug",
                    )
                )
                await db.flush()
                ok = True
                error = None
            except Exception as e:  # noqa: BLE001
                ok = False
                error = f"{type(e).__name__}: {str(e)[:200]}"
            await db.rollback()
            return {"n": n, "sp": sp, "ok": ok, "error": error}

    return await asyncio.gather(*(una(i) for i in range(8)))


async def _orm_insert_test():
    """Inserta una lectura de sensor vía ORM y la revierte (solo diagnóstico)."""
    from datetime import datetime, timezone
    from uuid import uuid4

    from sqlalchemy import select

    from agroia_backend.models.dispositivo_iot import DispositivoIoT
    from agroia_backend.models.finca import Finca
    from agroia_backend.models.sensor_reading import SensorReading, TexturaSuelo

    async with async_session_factory() as db:
        finca = (await db.execute(select(Finca).limit(1))).scalars().first()
        if finca is None:
            return "sin fincas"
        try:
            db.add(
                SensorReading(
                    id=uuid4(),
                    finca_id=finca.id,
                    ts=datetime.now(timezone.utc),
                    ph=6.5,
                    nitrogeno=100.0,
                    textura=TexturaSuelo.LIMO,
                    sensor_id="debug-test",
                    calidad="debug",
                )
            )
            await db.flush()
            ok = True
            error = None
        except Exception as e:  # noqa: BLE001
            ok = False
            error = f"{type(e).__name__}: {e}"
        await db.rollback()
        # reportar dispositivos/fincas para contexto
        dispositivos = (await db.execute(select(DispositivoIoT))).scalars().all()
        return {
            "ok": ok,
            "error": error,
            "dispositivos": [
                {"device_id": d.device_id, "finca_id": str(d.finca_id)}
                for d in dispositivos[:10]
            ],
        }
