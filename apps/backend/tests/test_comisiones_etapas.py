"""Reglas de etapas de comisión: recomendación y reporte fin de etapa.

Flujo validado:
  1. Sin comisión → NO se genera recomendación (409).
  2. Recomendación → comisión pasa a `en_recomendacion`.
  3. Reporte sin pasar por recomendación → 409.
  4. Reporte tras recomendación → 200 y comisión pasa a
     `generacion_reporte_fin_etapa`.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text

from agroia.database import async_session_factory
from agroia_backend.main import app
from agroia_backend.models.comision import Comision
from agroia_backend.models.finca import Finca
from agroia_backend.models.usuario import Usuario


@pytest.fixture()
async def cli():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _cabeceras(rol="Agronomo", email="agronomo@agroia.co"):
    return {"X-User-Role": rol, "X-User-Email": email}


async def _finca_sin_comision() -> str:
    """Crea una finca temporal sin comisión y devuelve su id."""
    async with async_session_factory() as db:
        await db.execute(text("SET LOCAL search_path TO public, agroia"))
        usuario = (
            await db.execute(select(Usuario).order_by(Usuario.id).limit(1))
        ).scalars().first()
        finca = Finca(
            id=uuid.uuid4(),
            usuario_id=usuario.id,
            tenant_id=usuario.tenant_id,
            nombre="Finca temporal sin comisión",
        )
        db.add(finca)
        await db.commit()
        await db.refresh(finca)
        return str(finca.id)


async def _borrar_finca(finca_id: str) -> None:
    async with async_session_factory() as db:
        await db.execute(text("SET LOCAL search_path TO public, agroia"))
        await db.execute(delete(Finca).where(Finca.id == uuid.UUID(finca_id)))
        await db.commit()


async def _estado_comision(finca_id: str) -> str | None:
    async with async_session_factory() as db:
        await db.execute(text("SET LOCAL search_path TO public, agroia"))
        comision = (
            await db.execute(
                select(Comision)
                .where(Comision.finca_id == uuid.UUID(finca_id))
                .order_by(Comision.fecha_asignacion.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return comision.estado if comision else None


async def _poner_estado(finca_id: str, estado: str) -> None:
    async with async_session_factory() as db:
        await db.execute(text("SET LOCAL search_path TO public, agroia"))
        comision = (
            await db.execute(
                select(Comision)
                .where(Comision.finca_id == uuid.UUID(finca_id))
                .order_by(Comision.fecha_asignacion.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if comision is not None:
            comision.estado = estado
            await db.commit()


async def _finca_demo(nombre: str) -> str | None:
    """Busca una finca del set demo local por nombre."""
    async with async_session_factory() as db:
        await db.execute(text("SET LOCAL search_path TO public, agroia"))
        finca = (
            await db.execute(select(Finca).where(Finca.nombre == nombre))
        ).scalar_one_or_none()
        return str(finca.id) if finca else None


async def test_analyze_sin_comision_bloqueado(cli):
    finca_id = await _finca_sin_comision()
    try:
        r = await cli.post(
            "/api/v1/recomendaciones/analyze",
            headers=_cabeceras(),
            json={"finca_id": finca_id, "cultivo_id": None},
        )
        assert r.status_code == 409, r.text
        assert r.json()["detail"]["code"] == "FINCA_SIN_COMISION"
    finally:
        await _borrar_finca(finca_id)


async def test_analyze_mueve_comision_a_en_recomendacion(cli):
    """Finca demo con comisión 'asignada' → la recomendación la pasa a
    'en_recomendacion'."""
    finca_id = await _finca_demo("Villa Café")
    if finca_id is None:
        pytest.skip("Requiere el set demo (restablecer_demo).")
    await _poner_estado(finca_id, "asignada")
    r = await cli.post(
        "/api/v1/recomendaciones/analyze",
        headers=_cabeceras(),
        json={"finca_id": finca_id, "cultivo_id": None},
    )
    assert r.status_code == 200, r.text
    assert r.json()["comision_estado"] == "en_recomendacion"
    assert await _estado_comision(finca_id) == "en_recomendacion"


async def test_reporte_sin_recomendacion_bloqueado(cli):
    """El reporte exige haber pasado por la etapa de recomendación."""
    finca_id = await _finca_demo("El Cafetal")
    if finca_id is None:
        pytest.skip("Requiere el set demo (restablecer_demo).")
    await _poner_estado(finca_id, "asignada")
    r = await cli.post(
        "/api/v1/reportes/generar",
        headers=_cabeceras(),
        json={"finca_id": finca_id, "tipo": "siembra"},
    )
    assert r.status_code == 409, r.text
    assert r.json()["detail"]["code"] == "REPORTE_SIN_RECOMENDACION"


async def test_reporte_despues_recomendacion_mueve_estado(cli):
    """El Vergel (comisión en 'en_recomendacion'): el reporte se genera y la
    comisión pasa a 'generacion_reporte_fin_etapa'."""
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
    existe = await _finca_demo("Finca Demo — El Vergel")
    if existe is None:
        pytest.skip("Requiere el set demo (restablecer_demo).")
    await _poner_estado(finca_id, "en_recomendacion")
    r = await cli.post(
        "/api/v1/reportes/generar",
        headers=_cabeceras(),
        json={"finca_id": finca_id, "tipo": "siembra"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["comision_estado"] == "generacion_reporte_fin_etapa"
    assert await _estado_comision(finca_id) == "generacion_reporte_fin_etapa"


async def test_reporte_regenerable_tras_fin_etapa(cli):
    """Un reporte ya generado puede regenerarse (estado posterior permitido)."""
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
    existe = await _finca_demo("Finca Demo — El Vergel")
    if existe is None:
        pytest.skip("Requiere el set demo (restablecer_demo).")
    await _poner_estado(finca_id, "generacion_reporte_fin_etapa")
    r = await cli.post(
        "/api/v1/reportes/generar",
        headers=_cabeceras(),
        json={"finca_id": finca_id, "tipo": "siembra"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["comision_estado"] == "generacion_reporte_fin_etapa"
