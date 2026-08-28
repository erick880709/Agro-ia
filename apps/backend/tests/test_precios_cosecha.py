"""Tests de precios de cosecha (v3, Ola 1): API admin y enriquecimiento UC1."""
from agroia.database import async_session_factory
from agroia_backend.main import app
from agroia_backend.services.precios_cosecha import enriquecer_sugerencias
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from agroia_backend.models.cultivo import Cultivo


ADMIN = {"email": "admin@agroia.co", "password": "Admin123!"}
AGRONOMO = {"email": "agronomo@agroia.co", "password": "Agronomo123!"}


async def _login(client, creds) -> str:
    r = await client.post("/api/v1/auth/login", json=creds)
    return r.json()["access_token"]


async def test_admin_actualiza_y_consulta_precios():
    async with async_session_factory() as db:
        cultivo = (
            await db.execute(select(Cultivo).limit(1))
        ).scalars().first()
        cultivo_id = str(cultivo.id)
        nombre = cultivo.nombre

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await _login(c, ADMIN)
        r = await c.put(
            "/api/v1/admin/precios-cosecha",
            json={
                "cultivo_id": cultivo_id,
                "departamento": "QuindÃ­o",
                "precio_promedio_cop_kg": 9500,
                "rendimiento_promedio_t_ha": 5.2,
                "fuente": "test",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["data"]["cultivo"] == nombre
        lista = await c.get(
            "/api/v1/cultivos/precios?departamento=QuindÃ­o",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert lista.status_code == 200
        assert any(p["cultivo_id"] == cultivo_id for p in lista.json()["data"])


async def test_no_admin_no_puede_actualizar():
    async with async_session_factory() as db:
        cultivo = (
            await db.execute(select(Cultivo).limit(1))
        ).scalars().first()
        cultivo_id = str(cultivo.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await _login(c, AGRONOMO)
        r = await c.put(
            "/api/v1/admin/precios-cosecha",
            json={
                "cultivo_id": cultivo_id,
                "departamento": "QuindÃ­o",
                "precio_promedio_cop_kg": 100,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 403


async def test_enriquecimiento_calcula_utilidad_y_mas_rentable():
    async with async_session_factory() as db:
        cultivos = (await db.execute(select(Cultivo).limit(2))).scalars().all()
        ids = [str(c.id) for c in cultivos]
        sugerencias = [
            {"cultivo_id": ids[0], "cultivo": cultivos[0].nombre, "score": 80.0},
            {"cultivo_id": ids[1], "cultivo": cultivos[1].nombre, "score": 60.0},
        ]
        enriquecidas = await enriquecer_sugerencias(
            db, sugerencias, "QuindÃ­o", costo_insumos=1_000_000
        )
    # Al menos el cultivo con precio registrado en el test anterior tiene utilidad
    con_utilidad = [s for s in enriquecidas if s.get("utilidad_estimada_cop_ha") is not None]
    assert con_utilidad, "se esperaba al menos un cultivo con precio y utilidad"
    rentables = [s for s in enriquecidas if s.get("mas_rentable")]
    assert rentables
    assert all("score_ponderado" in s for s in enriquecidas)
