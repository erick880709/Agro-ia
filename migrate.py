"""Create tables via asyncpg (sin problemas de encoding)."""
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

# Import all models so Base.metadata knows about them
from agroia_backend.models.recomendacion import Recomendacion  # noqa: F401
from agroia_backend.models.discordancia import Discordancia  # noqa: F401
from agroia_backend.models.regla_agronomica import ReglaAgronomica  # noqa: F401
from agroia_backend.models.modelo_ml import ModeloML  # noqa: F401
from agroia_backend.models.metrica_modelo import MetricaModelo  # noqa: F401
from agroia_backend.models.sensor_reading import SensorReading  # noqa: F401
from agroia_backend.models.dispositivo_iot import DispositivoIoT  # noqa: F401
from agroia_backend.models.cultivo import Cultivo  # noqa: F401
from agroia_backend.models.usuario import Usuario  # noqa: F401
from agroia_backend.models.finca import Finca  # noqa: F401
from agroia_backend.models.finca_usuario import FincaUsuario  # noqa: F401


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    print("Creating schema 'agroia' if not exists...")
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS agroia"))

    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Verify
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'agroia' ORDER BY table_name"
            )
        )
        tables = [row[0] for row in result]
        print(f"✅ Tables created successfully! Tables ({len(tables)}): {', '.join(tables)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
