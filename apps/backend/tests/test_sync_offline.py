"""Pruebas de sincronización offline (PWA) — tramas y labores idempotentes."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from agroia_backend.main import app


@pytest.fixture()
async def cli():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _cabeceras(rol="Agronomo", email="agronomo@agroia.co"):
    return {"X-User-Role": rol, "X-User-Email": email}


async def test_estado_sync_requiere_rol(cli):
    r = await cli.get("/api/v1/sync/estado")
    assert r.status_code == 401
    r = await cli.get("/api/v1/sync/estado", headers=_cabeceras())
    assert r.status_code == 200
    body = r.json()
    assert body["estado"] == "ok"
    assert "server_time" in body


async def test_sync_sensores_idempotente(cli):
    key = "sync-sensor-" + uuid.uuid4().hex
    trama = {
        "device_id": "esp32-sync-test",
        "finca_id": None,
        "humidity": 71.0,
        "temperature": 24.5,
        "conductivity": 410.0,
        "ph": 6.2,
        "nitrogen": 55.0,
        "phosphorus": 30.0,
        "potassium": 120.0,
    }
    payload = {"items": [{"idempotency_key": key, "trama": trama}]}
    r = await cli.post("/api/v1/sync/sensor-readings", json=payload, headers=_cabeceras())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["aceptados"] == 1
    assert not body["errores"]
    # Reenvío idéntico → duplicado detectado
    r2 = await cli.post("/api/v1/sync/sensor-readings", json=payload, headers=_cabeceras())
    assert r2.status_code == 200
    assert r2.json()["duplicados"] == 1
    assert r2.json()["aceptados"] == 0


async def test_sync_labores_requiere_labor_valida(cli):
    key = "sync-labor-" + uuid.uuid4().hex
    payload = {
        "items": [{
            "idempotency_key": key,
            "labor_id": str(uuid.uuid4()),
            "estado": "Completada",
            "observaciones_ejecucion": "offline",
        }],
    }
    r = await cli.post("/api/v1/sync/labores", json=payload, headers=_cabeceras())
    assert r.status_code == 200
    body = r.json()
    assert body["aceptados"] == 0
    assert body["errores"] and "labor no encontrada" in body["errores"][0]["error"]


async def test_sync_prohibido_para_cliente(cli):
    r = await cli.get(
        "/api/v1/sync/estado",
        headers=_cabeceras(rol="Cliente", email="maria.cliente@agroia.co"),
    )
    assert r.status_code == 200  # estado es informativo
    payload = {"items": [{"idempotency_key": "x" * 12, "trama": {"device_id": "d"}}]}
    r = await cli.post(
        "/api/v1/sync/sensor-readings",
        json=payload,
        headers=_cabeceras(rol="Cliente", email="maria.cliente@agroia.co"),
    )
    assert r.status_code in (401, 403)
