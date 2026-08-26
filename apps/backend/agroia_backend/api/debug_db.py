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
    }
