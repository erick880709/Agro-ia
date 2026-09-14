"""Especificación v8 — accesibilidad y lenguaje simple del reporte.

Valida los hallazgos H1–H6 sobre el HTML generado por /reportes/generar:
  - audiencia efectiva: rol de sesión en vivo, parámetro explícito al exportar
  - H1: semáforo con "Sin violaciones activas" + explicación por barra
  - H2: siglas traducidas solo en audiencia Agricultor
  - H3: RSSI/Uptime colapsados solo en audiencia Agricultor
  - H4: frase-resumen antes del mapa de calor (todas las audiencias)
  - H5: sin porcentaje duplicado cuando base == real
  - H6: orden simple-primero solo en audiencia Agricultor
"""

import re
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from agroia.database import async_session_factory
from agroia_backend.main import app
from agroia_backend.models.comision import Comision
from agroia_backend.models.finca import Finca


@pytest.fixture()
async def cli():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _cabeceras(rol="Agronomo", email="agronomo@agroia.co"):
    return {"X-User-Role": rol, "X-User-Email": email}


async def _finca_vergel() -> str | None:
    async with async_session_factory() as db:
        await db.execute(text("SET LOCAL search_path TO public, agroia"))
        finca = (
            await db.execute(select(Finca).where(Finca.id == uuid.UUID(
                "3a47d0c6-fb00-4106-91ba-0a707f612e86"
            )))
        ).scalar_one_or_none()
        return str(finca.id) if finca else None


async def _comision_en_recomendacion(finca_id: str) -> None:
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
        if comision is None:
            # Regla de negocio v3.5: sin comisión no se genera reporte.
            # En CI no existe el set demo → crear una en la etapa requerida.
            from datetime import date

            comision = Comision(
                finca_id=uuid.UUID(finca_id),
                servicio="Prueba accesibilidad v8",
                fecha_asignacion=date.today(),
                estado="en_recomendacion",
            )
            db.add(comision)
        else:
            comision.estado = "en_recomendacion"
        await db.commit()


async def _asegurar_lectura_sensor(cli, finca_id: str) -> None:
    """Siembra lecturas georreferenciadas (trama real del firmware, vía POST
    /api/sensor) para que el reporte tenga datos: sin lecturas el motor
    entrega un análisis preliminar sin semáforo de confianza (H1) ni mapa
    de calor con puntos medidos (H4). El mapa de calor exige ≥ 2 puntos con
    la misma variable, por eso se envían dos tomas en posiciones distintas;
    el pH 4.0 viola las reglas de pH de todos los cultivos, lo que garantiza
    el umbral de pH en los ajustes del ranking (celdas "fuera de lo ideal")."""
    for pos_x, pos_y in ((5.0, 5.0), (8.0, 5.0)):
        r = await cli.post("/api/sensor", json={
            "device_id": "test-accesibilidad-v8",
            "finca_id": finca_id,
            "pos_x": pos_x,
            "pos_y": pos_y,
            "ph": 4.0,
            "nitrogen": 80.0,
            "phosphorus": 30.0,
            "potassium": 150.0,
        })
        assert r.status_code == 202, r.text


async def _generar(cli, finca_id, headers, audiencia=None, tipo="siembra"):
    cuerpo = {"finca_id": finca_id, "tipo": tipo}
    if audiencia:
        cuerpo["audiencia"] = audiencia
    return await cli.post("/api/v1/reportes/generar", headers=headers, json=cuerpo)


async def test_reportes_accesibilidad(cli):
    finca_id = await _finca_vergel()
    if finca_id is None:
        pytest.skip("Requiere el set demo (restablecer_demo).")
    await _comision_en_recomendacion(finca_id)
    await _asegurar_lectura_sensor(cli, finca_id)

    # ── Agrónomo sin audiencia → versión técnica (rol de sesión) ──
    r_tec = await _generar(cli, finca_id, _cabeceras())
    assert r_tec.status_code == 200, r_tec.text
    html_tec = r_tec.json()["html"]
    assert r_tec.json()["audiencia"] == "tecnica"
    # H1: semáforo con negación en el título y explicación por barra
    assert "Sin violaciones activas" in html_tec
    assert "no hay alertas críticas pendientes" in html_tec or \
        "hay alertas críticas pendientes" in html_tec
    # H2: agrónomo conserva el formato compacto de siglas
    assert "(MO, CIC, Ca, Mg, S, Fe, Mn, Zn, Cu, B)" in html_tec
    # H3: RSSI/Uptime visibles sin colapsar
    assert "RSSI" in html_tec
    assert "Ver detalle técnico del sensor" not in html_tec
    # H4: frase-resumen del mapa de calor presente
    assert "puntos que se midieron en su lote" in html_tec
    # H5: sin porcentaje repetido entre paréntesis (base == real)
    assert re.search(r"(\d+(?:\.\d+)?)% \(real \1%\)", html_tec) is None
    # H6: orden técnico: ranking (02) antes que lenguaje simple (03)
    assert html_tec.find('block-num">02<') < html_tec.find('block-num">03<')

    # ── Agrónomo exportando con audiencia Agricultor (caso crítico 0.1) ──
    r_agr = await _generar(cli, finca_id, _cabeceras(), audiencia="agricultor")
    assert r_agr.status_code == 200, r_agr.text
    html_agr = r_agr.json()["html"]
    assert r_agr.json()["audiencia"] == "agricultor"
    # H2: siglas traducidas
    assert "micronutrientes hierro, manganeso, zinc, cobre y boro" in html_agr
    assert "(MO, CIC, Ca, Mg, S, Fe, Mn, Zn, Cu, B)" not in html_agr
    # H3: telemetría técnica colapsada
    assert "Ver detalle técnico del sensor" in html_agr
    # H4: frase-resumen también presente
    assert "puntos que se midieron en su lote" in html_agr
    # H6: lenguaje simple y próximos pasos ANTES que la tabla técnica
    assert html_agr.find('block-num">03<') < html_agr.find('block-num">02<')
    assert html_agr.find('block-num">05<') < html_agr.find('block-num">02<')

    # ── Cliente en vivo → audiencia Agricultor por rol ──
    r_cli = await _generar(
        cli, finca_id, _cabeceras(rol="Cliente", email="cliente@agroia.co"),
    )
    assert r_cli.status_code == 200, r_cli.text
    assert r_cli.json()["audiencia"] == "agricultor"
    assert "Ver detalle técnico del sensor" in r_cli.json()["html"]


async def test_reporte_audiencia_invalida_422(cli):
    finca_id = await _finca_vergel()
    if finca_id is None:
        pytest.skip("Requiere el set demo (restablecer_demo).")
    r = await _generar(cli, finca_id, _cabeceras(), audiencia="otro")
    assert r.status_code == 422
