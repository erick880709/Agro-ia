"""Pruebas de la API de costeo (F1): parámetros vigentes y simulación.

Requiere base de datos con migraciones aplicadas; el conjunto semilla se
crea de forma idempotente dentro de cada prueba (asegurar_conjunto_semilla).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from agroia.database import async_session_factory
from agroia_backend.main import app
from agroia_backend.services.costeo_seed import asegurar_conjunto_semilla


@pytest.fixture()
async def cli():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _cabeceras(rol="Admin", email="admin@agroia.co"):
    return {"X-User-Role": rol, "X-User-Email": email}


async def _semilla() -> None:
    async with async_session_factory() as db:
        await asegurar_conjunto_semilla(db)


async def test_parametros_vigentes(cli):
    await _semilla()
    r = await cli.get("/api/v1/costeo/parametros/vigentes", headers=_cabeceras())
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    conjunto = cuerpo["conjunto"]
    assert conjunto["estado"] == "publicado"
    servicio = next(s for s in conjunto["servicios"] if s["codigo"] == "muestreo_en_grilla")
    assert servicio["unidad"] == "punto"
    codigos = {c["codigo"] for c in servicio["componentes"]}
    assert codigos == {"tarifa_base", "puntos_muestreo"}
    puntos = next(c for c in servicio["componentes"] if c["codigo"] == "puntos_muestreo")
    assert len(puntos["tramos"]) == 3
    factor = next(f for f in conjunto["factores"] if f["codigo"] == "dificultad")
    assert {o["codigo"] for o in factor["opciones"]} == {
        "plano", "pendiente_moderada", "acceso_dificil",
    }


async def test_parametros_vigentes_prohibido_cliente(cli):
    r = await cli.get("/api/v1/costeo/parametros/vigentes",
                      headers=_cabeceras(rol="Cliente", email="maria.cliente@agroia.co"))
    assert r.status_code == 403


async def test_simular_ca01(cli):
    await _semilla()
    r = await cli.post("/api/v1/costeo/simular", headers=_cabeceras(), json={
        "area_ha": 1, "puntos": 10, "dificultad": "plano",
        "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": 10}],
    })
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["total_final"] == 250000.0
    assert cuerpo["indicadores"]["costo_por_punto"] == 25000.0
    assert cuerpo["indicadores"]["costo_por_ha"] == 250000.0


async def test_simular_ca03(cli):
    await _semilla()
    r = await cli.post("/api/v1/costeo/simular", headers=_cabeceras(), json={
        "area_ha": 20, "puntos": 20, "dificultad": "acceso_dificil",
        "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": 20}],
    })
    assert r.status_code == 200, r.text
    assert r.json()["total_final"] == 487500.0


async def test_simular_conjunto_inexistente(cli):
    await _semilla()
    r = await cli.post("/api/v1/costeo/simular", headers=_cabeceras(), json={
        "conjunto_id": "00000000-0000-0000-0000-000000000000",
        "area_ha": 1,
        "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": 10}],
    })
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "CONJUNTO_NOT_FOUND"
