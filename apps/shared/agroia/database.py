"""Conexión a base de datos PostgreSQL con SQLAlchemy async.

Provee el engine, session factory y la base declarativa compartida.
Soporta PostGIS y pgvector como extensiones.
"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from agroia.config import get_settings

settings = get_settings()


def normalize_asyncpg_url(url: str) -> str:
    """Adapta URLs de Postgres externos (Neon/Supabase) al driver asyncpg.

    asyncpg no acepta el parámetro `sslmode` (es exclusivo de libpq); usa
    `ssl` con el modo como valor (p. ej. ssl=require).
    """
    if url.startswith("postgresql+asyncpg://") and "sslmode=" in url:
        return url.replace("sslmode=require", "ssl=require")
    return url


def configure_search_path(engine) -> None:
    """Pone el schema `agroia` en el search_path de cada conexión.

    Los casts de tipos enum que genera SQLAlchemy no van calificados con
    schema (p. ej. ::rolusuario), así que dependen del search_path. En bases
    externas (Neon/Supabase) el usuario no se llama `agroia`, por lo que el
    schema no se resuelve por defecto.
    """
    @event.listens_for(engine.sync_engine, "connect")
    def _set_search_path(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET search_path TO public, agroia")
        finally:
            cursor.close()


# Engine asíncrono para PostgreSQL
engine = create_async_engine(
    normalize_asyncpg_url(settings.database_url),
    echo=settings.environment == "development",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    # `server_settings` es el mecanismo nativo de asyncpg para fijar el
    # search_path en CADA conexión nueva (el event listener de arriba no
    # siempre alcanza a ejecutarse en todas las conexiones del pool).
    connect_args={"server_settings": {"search_path": "public, agroia"}},
)
configure_search_path(engine)

# Factory de sesiones asíncronas
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos SQLAlchemy."""


async def get_db() -> AsyncSession:
    """Dependency de FastAPI que provee una sesión de BD por request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_health() -> bool:
    """Verifica que la base de datos responde (para health check)."""
    try:
        async with async_session_factory() as session:
            await session.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        return True
    except Exception:
        return False
