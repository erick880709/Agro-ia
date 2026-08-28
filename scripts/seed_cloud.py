"""Siembra usuarios, fincas y asociaciones en la base de datos de la nube.

Ejecutar UNA SOLA VEZ después del primer despliegue en Render/Neon
(las tablas ya deben existir porque el deploy corre las migraciones).

Uso (PowerShell):
    $env:DATABASE_URL="postgresql+asyncpg://usuario:clave@host/neondb?sslmode=require"
    $env:PYTHONPATH="<repo>/apps/shared;<repo>/apps/backend"
    .venv\Scripts\python.exe scripts/seed_cloud.py

Crea (idempotente, no duplica):
  - Usuarios: admin@agroia.co / Admin123!, agronomo@agroia.co / Agronomo123!,
    cliente@agroia.co / Cliente123!
  - Fincas: La Esperanza, El Porvenir, El Milagro, Demo Integral
  - Asociaciones fincas_usuarios (agrónomo ve todas; cliente solo las suyas)
"""

import asyncio
import sys
import uuid

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, "apps/shared")
sys.path.insert(0, "apps/backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agroia.config import get_settings
from agroia.database import configure_search_path, normalize_asyncpg_url
from agroia_backend.models.finca import Finca
from agroia_backend.models.finca_usuario import FincaUsuario
from agroia_backend.models.usuario import RolUsuario, Usuario
from agroia_backend.services.auth_utils import hash_password

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

USUARIOS = [
    ("admin@agroia.co", "Admin123!", "Administrador AgroIA", RolUsuario.ADMIN),
    ("agronomo@agroia.co", "Agronomo123!", "María Agrónoma", RolUsuario.AGRONOMO),
    ("cliente@agroia.co", "Cliente123!", "Juan Campesino", RolUsuario.CLIENTE),
    ("maria.cliente@agroia.co", "Cliente123!", "María Cliente", RolUsuario.CLIENTE),
]

FINCAS = [
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "nombre": "La Esperanza",
        "departamento": "Antioquia",
        "municipio": "Rionegro",
        "latitud": 6.1536, "longitud": -75.3740, "altitud_msnm": 2120,
        "area_hectareas": 4.5,
        "coordenadas_google": "https://maps.app.goo.gl/LaEsperanza",
        "propietario": "Familia Giraldo",
        "contacto_telefono": "3101234567",
        "contacto_email": "cliente@agroia.co",
        "largo_metros": 300.0, "ancho_metros": 150.0,
    },
    {
        "id": "584c4c7b-8f7a-4d48-bbfd-4f3db357c9c2",
        "nombre": "El Porvenir",
        "departamento": "Cundinamarca",
        "municipio": "Zipaquirá",
        "latitud": 5.0250, "longitud": -74.0040, "altitud_msnm": 2650,
        "area_hectareas": 7.0,
        "coordenadas_google": "https://maps.app.goo.gl/ElPorvenir",
        "propietario": "Familia Giraldo",
        "contacto_telefono": "3101234567",
        "contacto_email": "cliente@agroia.co",
        "largo_metros": 350.0, "ancho_metros": 200.0,
    },
    {
        "id": "87111e1a-da45-4556-8936-81a1af7d5ed8",
        "nombre": "El Milagro",
        "departamento": "Huila",
        "municipio": "Garzón",
        "latitud": 2.1960, "longitud": -75.6270, "altitud_msnm": 830,
        "area_hectareas": 3.2,
        "coordenadas_google": "https://maps.app.goo.gl/ElMilagro",
        "propietario": "Cooperativa Huila Verde",
        "contacto_telefono": "3207654321",
        "contacto_email": "cooperativa@example.com",
        "largo_metros": 200.0, "ancho_metros": 160.0,
    },
    {
        "id": "8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936",
        "nombre": "Demo Integral",
        "departamento": "Risaralda",
        "municipio": "Pereira",
        "latitud": 4.8133, "longitud": -75.6961, "altitud_msnm": 1411,
        "area_hectareas": 2.5,
        "coordenadas_google": "https://maps.app.goo.gl/DemoIntegral",
        "propietario": "Finca Demo AgroIA",
        "contacto_telefono": "3009998877",
        "contacto_email": "demo@agroia.co",
        "largo_metros": 250.0, "ancho_metros": 100.0,
    },
    {
        "id": "3a47d0c6-fb00-4106-91ba-0a707f612e86",
        "nombre": "Finca Demo",
        "departamento": "Quindío",
        "municipio": "Armenia",
        "latitud": 4.5306, "longitud": -75.6809, "altitud_msnm": 1480,
        "area_hectareas": 1.5,
        "coordenadas_google": "https://maps.app.goo.gl/FincaDemo",
        "propietario": "Finca Demo AgroIA",
        "contacto_telefono": "3001112233",
        "contacto_email": "demo@agroia.co",
        "largo_metros": 150.0, "ancho_metros": 100.0,
    },
]


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(normalize_asyncpg_url(settings.database_url), echo=False)
    configure_search_path(engine)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # ── Usuarios ──
        creados_u: dict[str, uuid.UUID] = {}
        for email, pwd, nombre, rol in USUARIOS:
            u = (
                await session.execute(select(Usuario).where(Usuario.email == email))
            ).scalar_one_or_none()
            if u is None:
                u = Usuario(
                    email=email,
                    password_hash=hash_password(pwd),
                    nombre=nombre,
                    rol=rol,
                    tenant_id=TENANT_ID,
                    activo=True,
                    consentimiento_datos=True,
                    email_verificado=True,
                )
                session.add(u)
                await session.flush()
                print(f"✅ Usuario {email} ({rol.value}) creado")
            else:
                print(f"ℹ️  Usuario {email} ya existía")
            creados_u[email] = u.id

        admin_id = creados_u["admin@agroia.co"]
        agronomo_id = creados_u["agronomo@agroia.co"]
        cliente_id = creados_u["cliente@agroia.co"]
        maria_id = creados_u["maria.cliente@agroia.co"]

        # ── Fincas ──
        fincas_ids: list[uuid.UUID] = []
        for f in FINCAS:
            fid = uuid.UUID(f["id"])
            finca = (
                await session.execute(select(Finca).where(Finca.id == fid))
            ).scalar_one_or_none()
            if finca is None:
                finca = Finca(
                    id=fid,
                    usuario_id=admin_id,
                    tenant_id=TENANT_ID,
                    nombre=f["nombre"],
                    departamento=f["departamento"],
                    municipio=f["municipio"],
                    latitud=f["latitud"],
                    longitud=f["longitud"],
                    altitud_msnm=f["altitud_msnm"],
                    area_hectareas=f["area_hectareas"],
                    coordenadas_google=f["coordenadas_google"],
                    propietario=f["propietario"],
                    contacto_telefono=f["contacto_telefono"],
                    contacto_email=f["contacto_email"],
                    largo_metros=f["largo_metros"],
                    ancho_metros=f["ancho_metros"],
                )
                session.add(finca)
                await session.flush()
                print(f"✅ Finca {f['nombre']} creada")
            else:
                print(f"ℹ️  Finca {f['nombre']} ya existía")
            fincas_ids.append(fid)

        # ── Asociaciones finca ↔ usuario ──
        # Agrónomo: todas las fincas. Cliente: La Esperanza y Demo Integral.
        asociaciones = [(agronomo_id, fid) for fid in fincas_ids]
        asociaciones += [
            (cliente_id, uuid.UUID("22222222-2222-2222-2222-222222222222")),
            (cliente_id, uuid.UUID("8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936")),
            (maria_id, uuid.UUID("3a47d0c6-fb00-4106-91ba-0a707f612e86")),
        ]
        for uid, fid in asociaciones:
            existe = (
                await session.execute(
                    select(FincaUsuario).where(
                        FincaUsuario.usuario_id == uid,
                        FincaUsuario.finca_id == fid,
                    )
                )
            ).scalar_one_or_none()
            if existe is None:
                session.add(FincaUsuario(finca_id=fid, usuario_id=uid))
                print(f"✅ Asociación usuario={uid} ↔ finca={fid} creada")

        await session.commit()
        print("✅ Seed de nube completado.")

        # ── Verificación ──
        n_u = (await session.execute(select(Usuario))).scalars().all()
        n_f = (await session.execute(select(Finca))).scalars().all()
        print(f"   Total usuarios: {len(n_u)} | Total fincas: {len(n_f)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
