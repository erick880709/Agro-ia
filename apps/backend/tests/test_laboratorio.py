"""Tests del módulo de Laboratorios ICA (v3): ingesta, historial y eliminación."""
from agroia_backend.main import app
from httpx import ASGITransport, AsyncClient

FINCA_DEMO = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
ADMIN = {"email": "admin@agroia.co", "password": "Admin123!"}


async def _login(client) -> str:
    r = await client.post("/api/v1/auth/login", json=ADMIN)
    return r.json()["access_token"]


async def test_ingesta_laboratorio_valida_y_rechaza_desconocidas():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await _login(c)
        r = await c.post(
            f"/api/v1/fincas/{FINCA_DEMO}/lab/ingestar",
            json={
                "laboratorio_nombre": "Agrilab Quindio (test)",
                "fecha_muestreo": "2026-08-20",
                "fecha_resultado": "2026-08-26",
                "resultados": {"pH": 6.1, "N": 145, "P": 32, "K": 210, "desconocida": 5},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 201
    data = r.json()
    assert "ph" in data["data"]["resultados"]
    assert "desconocida" in data["rechazadas"]


async def test_historial_y_filtro_por_finca():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await _login(c)
        r = await c.get(
            f"/api/v1/fincas/{FINCA_DEMO}/lab/analisis",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    assert r.json()["total"] >= 1


async def test_cliente_no_puede_ingerir():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        login = await c.post("/api/v1/auth/login", json={
            "email": "maria.cliente@agroia.co", "password": "Cliente123!",
        })
        token = login.json()["access_token"]
        r = await c.post(
            f"/api/v1/fincas/{FINCA_DEMO}/lab/ingestar",
            json={
                "fecha_muestreo": "2026-08-20",
                "fecha_resultado": "2026-08-26",
                "resultados": {"pH": 6.0},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code in (401, 403)


async def test_eliminar_solo_admin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        token = await _login(c)
        lista = await c.get(
            f"/api/v1/fincas/{FINCA_DEMO}/lab/analisis",
            headers={"Authorization": f"Bearer {token}"},
        )
        analisis_id = lista.json()["data"][0]["id"]
        r = await c.delete(
            f"/api/v1/fincas/{FINCA_DEMO}/lab/analisis/{analisis_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
