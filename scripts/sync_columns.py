"""Sync DB columns with SQLAlchemy metadata (dev-only helper).

Adds missing columns to existing tables in schema 'agroia'.
Unlike `Base.metadata.create_all`, this alters existing tables.
"""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, "apps/shared")
sys.path.insert(0, "apps/backend")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from agroia.config import get_settings
from agroia.database import Base

import agroia_backend.models.cultivo  # noqa: F401
import agroia_backend.models.discordancia  # noqa: F401
import agroia_backend.models.dispositivo_iot  # noqa: F401
import agroia_backend.models.finca  # noqa: F401
import agroia_backend.models.metrica_modelo  # noqa: F401
import agroia_backend.models.modelo_ml  # noqa: F401
import agroia_backend.models.recomendacion  # noqa: F401
import agroia_backend.models.regla_agronomica  # noqa: F401
import agroia_backend.models.sensor_reading  # noqa: F401
import agroia_backend.models.usuario  # noqa: F401

# Tipos SQL por tipo Python de SQLAlchemy (suficiente para dev)
TYPE_MAP = {
    "FLOAT": "DOUBLE PRECISION",
    "VARCHAR": "VARCHAR",
    "INTEGER": "INTEGER",
    "BOOLEAN": "BOOLEAN",
    "JSONB": "JSONB",
    "TIMESTAMP": "TIMESTAMP WITH TIME ZONE",
    "UUID": "UUID",
}


def sql_type(col) -> str:
    t = col.type
    name = type(t).__name__.upper()
    if name == "VARCHAR":
        return f"VARCHAR({t.length or 255})"
    if name == "ENUM":
        return t.name  # nombre del enum existente en la BD
    return TYPE_MAP.get(name, "TEXT")


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        # Columnas existentes por tabla
        rows = await conn.execute(text("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'agroia'
        """))
        existing = {}
        for table, col in rows:
            existing.setdefault(table, set()).add(col)

        added = 0
        for key in sorted(Base.metadata.tables):
            table_obj = Base.metadata.tables[key]
            if table_obj.schema != "agroia":
                continue
            table_name = table_obj.name  # sin prefijo de esquema
            model_cols = table_obj.columns
            have = existing.get(table_name, set())
            for col in model_cols:
                if col.name not in have:
                    ddl = (
                        f"ALTER TABLE agroia.{table_name} "
                        f"ADD COLUMN {col.name} {sql_type(col)}"
                        + ("" if col.nullable else " NOT NULL")
                    )
                    print(f"+ {ddl}")
                    await conn.execute(text(ddl))
                    added += 1

        print(f"✅ {added} columnas agregadas")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
