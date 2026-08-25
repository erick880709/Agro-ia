"""Alembic environment configuration for AgroIA backend."""

import asyncio
import os
from logging.config import fileConfig

# ── Importar todos los modelos para que Alembic los detecte ──
from agroia.database import Base
from agroia_backend.models.discordancia import Discordancia  # noqa: F401
from agroia_backend.models.metrica_modelo import MetricaModelo  # noqa: F401
from agroia_backend.models.modelo_ml import ModeloML  # noqa: F401
from agroia_backend.models.recomendacion import Recomendacion  # noqa: F401
from agroia_backend.models.regla_agronomica import ReglaAgronomica  # noqa: F401
from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Alembic Config ──
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# La URL se toma del entorno (DATABASE_URL); por defecto la BD local de
# desarrollo. El CI la inyecta con el servicio PostgreSQL del job.
_database_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://agroia:agroia_dev@localhost:5434/agroia",
)
# asyncpg no acepta `sslmode` (Neon/Supabase); convertir a `ssl=require`.
if _database_url.startswith("postgresql+asyncpg://") and "sslmode=" in _database_url:
    _database_url = _database_url.replace("sslmode=require", "ssl=require")
config.set_main_option("sqlalchemy.url", _database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL without DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="agroia",
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    # El schema 'agroia' puede no existir en bases recién creadas (CI).
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS agroia"))
    # Los casts de tipos enum de SQLAlchemy no van calificados; poner el
    # schema agroia en el search_path (necesario en Neon/Supabase).
    connection.execute(text("SET search_path TO public, agroia"))
    connection.commit()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="agroia",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Ejecuta migraciones con motor async (URL asyncpg)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connected to DB)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
