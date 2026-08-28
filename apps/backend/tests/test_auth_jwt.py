"""Tests de autenticaciÃ³n JWT (v3): login, /me, refresh, logout y anti-suplantaciÃ³n.

Requieren la BD local (Docker agroia-postgres en :5434) con los usuarios demo.
"""
from agroia.config import get_settings
from agroia_backend.main import app
from httpx import ASGITransport, AsyncClient

settings = get_settings()

# El pool global de asyncpg se enlaza al event loop: compartir uno por mÃ³dulo

ADMIN = {"email": "admin@agroia.co", "password": "Admin123!"}
AGRONOMO = {"email": "agronomo@agroia.co", "password": "Agronomo123!"}


async def test_login_devuelve_tokens():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/auth/login", json=ADMIN)
    assert res.status_code == 200
    data = res.json()
    assert data["rol"] == "Admin"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.jwt_access_token_expire_minutes * 60


async def test_me_con_bearer():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/v1/auth/login", json=ADMIN)
        token = login.json()["access_token"]
        res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert res.status_code == 200
    assert res.json()["email"] == ADMIN["email"]


async def test_el_token_gana_sobre_cabeceras_falsas():
    """La cabecera X-User-Role falsificada debe ser sobrescrita por el token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/v1/auth/login", json=AGRONOMO)
        token = login.json()["access_token"]
        res = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
                "X-User-Role": "Admin",
                "X-User-Email": "admin@agroia.co",
            },
        )
    assert res.status_code == 200
    assert res.json()["rol"] == "Agronomo"
    assert res.json()["email"] == AGRONOMO["email"]


async def test_refresh_rota_tokens():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/v1/auth/login", json=ADMIN)
        refresh_old = login.json()["refresh_token"]
        res = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_old}
        )
        assert res.status_code == 200
        nuevo = res.json()
        assert nuevo["access_token"] != login.json()["access_token"]
        # El refresh anterior fue revocado (rotaciÃ³n)
        res2 = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_old}
        )
        assert res2.status_code in (401, 500)


async def test_logout_invalida_access():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post("/api/v1/auth/login", json=ADMIN)
        data = login.json()
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        res = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": data["refresh_token"]},
            headers=headers,
        )
        assert res.status_code == 200
        res2 = await client.get("/api/v1/auth/me", headers=headers)
        assert res2.status_code == 401


async def test_sin_token_401_en_produccion():
    """Con legacy headers deshabilitadas (producciÃ³n), sin Bearer â†’ 401."""
    settings.auth_allow_legacy_headers = False
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(
                "/api/v1/auth/me",
                headers={"X-User-Role": "Admin", "X-User-Email": ADMIN["email"]},
            )
        assert res.status_code == 401
    finally:
        settings.auth_allow_legacy_headers = None


async def test_rutas_ingesta_iot_siguen_publicas():
    """Las rutas de ingesta de tramas NO deben exigir Bearer (firmware ESP32).

    Sin token deben llegar a su propia validación de negocio (422/404),
    nunca 401 del middleware JWT.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1) Ruta del firmware: POST /api/sensor sin device_id → 422 de Pydantic
        r1 = await client.post("/api/sensor", json={"humidity": 50.0})
        assert r1.status_code == 422, r1.text
        # 2) Ruta canónica: POST /api/v1/iot/sensor con device no registrado
        r2 = await client.post(
            "/api/v1/iot/sensor",
            json={"device_id": "esp32-no-registrado-test", "ph": 6.0},
        )
        assert r2.status_code == 404, r2.text
        assert r2.json()["detail"]["code"] == "DEVICE_NOT_REGISTERED"
        # 3) Ingesta del consumidor: POST /api/v1/iot/ingest sin payload → 422
        r3 = await client.post("/api/v1/iot/ingest", json={"device_id": "x"})
        assert r3.status_code == 422, r3.text
