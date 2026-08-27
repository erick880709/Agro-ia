"""Load seed cultivos into the database."""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, "apps/shared")
sys.path.insert(0, "apps/backend")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from agroia.config import get_settings
from agroia.database import configure_search_path, normalize_asyncpg_url

from agroia_backend.models.cultivo import Cultivo, FichaTecnica, EstadoFicha, TipoFuente
from agroia_backend.models.recomendacion import Recomendacion  # noqa: F401 (needed for relationship)
from agroia_backend.models.discordancia import Discordancia  # noqa: F401 (needed for relationship)
from agroia_backend.models.usuario import Usuario  # noqa: F401 (needed for FK)
from agroia_backend.models.regla_agronomica import ReglaAgronomica, VariableSuelo, PrioridadRegla
from agroia_backend.seeds.cultivos import CULTIVOS_COLOMBIA, CULTIVOS_INTERNACIONALES
from agroia_backend.seeds.reglas import REGLAS_UNIVERSALES, REGLAS_POR_CULTIVO

import uuid

# Use async engine directly
settings = get_settings()
engine = create_async_engine(normalize_asyncpg_url(settings.database_url), echo=False)
configure_search_path(engine)
factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def cargar_seed_data():
    """Carga los cultivos semilla en la BD."""
    async with factory() as session:
        # Check existing
        result = await session.execute(text("SELECT COUNT(*) FROM agroia.cultivos"))
        count = result.scalar()
        if count > 0:
            print(f"   ⚠️  Ya existen {count} cultivos. Aplicando backfill de fisiología…")
            _FISIOLOGIA_KEYS = (
                "profundidad_radicular_min_cm", "gdd_total_requerido", "dias_ciclo",
            )
            actualizados = 0
            for cdata in CULTIVOS_COLOMBIA:
                valores = {k: cdata[k] for k in _FISIOLOGIA_KEYS if k in cdata}
                if not valores:
                    continue
                set_sql = ", ".join(f"{k} = :{k}" for k in valores)
                params = {"nombre": cdata["nombre"], **valores}
                r = await session.execute(
                    text(
                        f"UPDATE agroia.cultivos SET {set_sql} "
                        "WHERE nombre = :nombre AND "
                        f"{next(iter(valores))} IS NULL"
                    ),
                    params,
                )
                actualizados += r.rowcount or 0
            await session.commit()
            print(f"   ✅ Fisiología actualizada en {actualizados} cultivo(s).")
            return

        cultivos_data = list(CULTIVOS_COLOMBIA) + [
            {"nombre": n, "descripcion": f"Cultivo internacional: {n}", "icono": "🌱"}
            for n in CULTIVOS_INTERNACIONALES
        ]

        created = 0
        for cdata in cultivos_data:
            cultivo = Cultivo(
                id=uuid.uuid4(),
                nombre=cdata["nombre"],
                nombre_cientifico=cdata.get("nombre_cientifico"),
                descripcion=cdata.get("descripcion"),
                icono=cdata.get("icono", "🌱"),
                activo=True,
                profundidad_radicular_min_cm=cdata.get("profundidad_radicular_min_cm"),
                gdd_total_requerido=cdata.get("gdd_total_requerido"),
                dias_ciclo=cdata.get("dias_ciclo"),
            )
            session.add(cultivo)

            # Add ficha técnica if available
            ficha_data = cdata.get("ficha")
            if ficha_data:
                ficha = FichaTecnica(
                    id=uuid.uuid4(),
                    cultivo_id=cultivo.id,
                    estado=EstadoFicha.PUBLICADO,
                    tipo_fuente=TipoFuente.NACIONAL if ficha_data.get("tipo_fuente") == "Nacional" else TipoFuente.INTERNACIONAL,
                    fuente=ficha_data["fuente"],
                    umbrales=ficha_data.get("umbrales", {}),
                    datos_economicos=ficha_data.get("datos_economicos", {}),
                )
                session.add(ficha)

            created += 1

        await session.commit()
        print(f"✅ {created} cultivos cargados en la base de datos")


async def cargar_reglas():
    """Carga las reglas agronómicas del sistema experto (UC1 + UC2)."""
    async with factory() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM agroia.reglas_agronomicas")
        )
        count = result.scalar()
        if count > 0:
            print(f"   ⚠️  Ya existen {count} reglas agronómicas. Saltando seed...")
            return

        # Mapa nombre → id de cultivos ya sembrados
        cultivos = await session.execute(
            text("SELECT id, nombre FROM agroia.cultivos")
        )
        nombre_to_id = {nombre: str(cid) for cid, nombre in cultivos.all()}

        creadas = 0
        saltadas = 0

        def _regla(r, cultivo_id):
            return ReglaAgronomica(
                id=uuid.uuid4(),
                cultivo_id=cultivo_id,
                variable=VariableSuelo(r["variable"]),
                umbral_min=r.get("min"),
                umbral_max=r.get("max"),
                accion=r["accion"],
                prioridad=PrioridadRegla(r["prioridad"]),
                fuente=r["fuente"],
                version=1,
                activa=True,
            )

        # Reglas universales (cultivo_id NULL)
        for r in REGLAS_UNIVERSALES:
            session.add(_regla(r, None))
            creadas += 1

        # Reglas por cultivo
        for nombre_cultivo, reglas in REGLAS_POR_CULTIVO.items():
            cultivo_id_str = nombre_to_id.get(nombre_cultivo)
            if cultivo_id_str is None:
                print(
                    f"   ⚠️  Cultivo '{nombre_cultivo}' no encontrado en BD. "
                    f"Saltando {len(reglas)} reglas."
                )
                saltadas += len(reglas)
                continue
            for r in reglas:
                session.add(_regla(r, uuid.UUID(cultivo_id_str)))
                creadas += 1

        await session.commit()
        print(f"✅ {creadas} reglas agronómicas cargadas ({saltadas} saltadas)")


async def main():
    await cargar_seed_data()
    await cargar_reglas()


if __name__ == "__main__":
    asyncio.run(main())
