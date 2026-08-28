"""Pruebas del módulo de visión por computadora (diagnóstico de plagas)."""

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


@pytest.fixture()
def png_minimo():
    # PNG de 1x1 válido
    import base64
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )


async def test_analizar_plaga_flujo_completo(cli, png_minimo):
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"  # Finca Demo
    r = await cli.post(
        f"/api/v1/vision/analizar-plaga?finca_id={finca_id}",
        headers=_cabeceras(),
        files={"file": ("hoja.png", png_minimo, "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["plaga"] == "No determinada"
    assert body["fuente"] == "modelo_agroia_v1_stub"
    assert body["imagen_url"].startswith("/media/vision/")
    assert body["confianza"] == 0.0
    # Historial
    r2 = await cli.get(f"/api/v1/vision/diagnosticos/{finca_id}", headers=_cabeceras())
    assert r2.status_code == 200
    diags = r2.json()["diagnosticos"]
    assert any(d["id"] == body["diagnostico_id"] for d in diags)


async def test_analizar_plaga_formato_rechazado(cli):
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
    r = await cli.post(
        f"/api/v1/vision/analizar-plaga?finca_id={finca_id}",
        headers=_cabeceras(),
        files={"file": ("nota.txt", b"hola", "text/plain")},
    )
    assert r.status_code == 415


async def test_analizar_plaga_cliente_prohibido(cli, png_minimo):
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
    r = await cli.post(
        f"/api/v1/vision/analizar-plaga?finca_id={finca_id}",
        headers=_cabeceras(rol="Cliente", email="maria.cliente@agroia.co"),
        files={"file": ("hoja.png", png_minimo, "image/png")},
    )
    assert r.status_code in (401, 403)


async def test_reentrenar_solo_admin(cli):
    r = await cli.post("/api/v1/vision/admin/reentrenar", headers=_cabeceras())
    assert r.status_code == 403
    r = await cli.post(
        "/api/v1/vision/admin/reentrenar",
        headers=_cabeceras(rol="Admin", email="admin@agroia.co"),
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "programado"


async def test_diagnosticos_finca_inexistente(cli):
    r = await cli.get(
        f"/api/v1/vision/diagnosticos/{uuid.uuid4()}",
        headers=_cabeceras(),
    )
    assert r.status_code in (200, 403, 404)
