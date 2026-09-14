"""Pruebas del clima enriquecido en las alertas (estado actual + pronóstico 7 días).

Cubre:
- Mapeo de códigos WMO a español.
- Resumen del clima actual para los mensajes.
- Parseo del clima completo de Open-Meteo (actual + pronóstico enriquecido).
- Degradación con gracia del conector.
- Persistencia del clima en las alertas (evaluación con clima inyectado).
- Endpoints: clima en vivo por finca y listado de alertas con clima.
"""

import os
import types
import uuid as uuid_mod
from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

# Fuente lunar estática para pruebas deterministas (sin red ni efemérides).
os.environ["BRISTOL_MODO"] = "static"
os.environ["BRISTOL_ACTIVADO"] = "true"

from agroia.database import async_session_factory  # noqa: E402
from agroia_backend.api.alertas import _alerta_a_dict  # noqa: E402
from agroia_backend.main import app  # noqa: E402
from agroia_backend.models.alerta_climatica import AlertaClimatica  # noqa: E402
from agroia_backend.models.finca import Finca  # noqa: E402
from agroia_backend.models.labor import Labor  # noqa: E402
from agroia_backend.models.lote import Lote  # noqa: E402
from agroia_backend.services.clima_alertas import (  # noqa: E402
    _dia_helada,
    _dia_lluvia_fuerte,
    _resumen_clima_actual,
    evaluar_alertas_finca,
)
from agroia_backend.services.external_apis import (  # noqa: E402
    codigo_clima_a_texto,
    fetch_clima_completo_open_meteo,
)


@pytest.fixture()
async def cli():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _cabeceras(rol="Admin", email="admin@agroia.co"):
    return {"X-User-Role": rol, "X-User-Email": email}


# ── Mapeo WMO ──

def test_codigos_wmo_mapeados():
    assert codigo_clima_a_texto(0)["descripcion"] == "Despejado"
    assert codigo_clima_a_texto(0)["emoji"] == "☀️"
    assert codigo_clima_a_texto(2)["descripcion"] == "Parcialmente nublado"
    assert codigo_clima_a_texto(63)["descripcion"] == "Lluvia moderada"
    assert codigo_clima_a_texto(95)["descripcion"] == "Tormenta eléctrica"
    # Desconocidos o nulos → cielo variable, nunca un error
    assert codigo_clima_a_texto(None)["descripcion"] == "Cielo variable"
    assert codigo_clima_a_texto(1234)["descripcion"] == "Cielo variable"
    assert codigo_clima_a_texto("2")["codigo"] == 2


# ── Resumen del clima actual ──

def test_resumen_clima_actual():
    actual = {
        "temperatura_c": 24.5,
        "sensacion_termica_c": 25.6,
        "humedad_pct": 70.0,
        "viento_kmh": 8.0,
        "uv": 5.0,
        "descripcion": "Parcialmente nublado",
    }
    res = _resumen_clima_actual(actual)
    assert "24.5 °C" in res
    assert "sensación térmica 25.6 °C" in res
    assert "humedad 70 %" in res
    assert "viento 8.0 km/h" in res
    assert "UV 5.0" in res
    assert "parcialmente nublado" in res


def test_resumen_clima_actual_sin_datos():
    assert _resumen_clima_actual(None) is None
    assert _resumen_clima_actual({}) is None
    assert _resumen_clima_actual({"humedad_pct": 80.0}) is None  # sin temperatura no hay resumen


# ── Días disparadores de las reglas ──

def test_dia_lluvia_fuerte_y_helada():
    pron = [
        {"fecha": "2026-09-13", "precipitacion_mm": 5.0, "temp_min_c": 12.0},
        {"fecha": "2026-09-14", "precipitacion_mm": 40.0, "temp_min_c": 4.0},
    ]
    assert _dia_lluvia_fuerte(pron)["fecha"] == "2026-09-14"
    assert _dia_helada(pron)["fecha"] == "2026-09-14"
    assert _dia_lluvia_fuerte([{"fecha": "x", "precipitacion_mm": 0.0}]) is None
    assert _dia_helada([{"fecha": "x", "temp_min_c": 10.0}]) is None


# ── Conector Open-Meteo (clima completo) ──

CLIMA_JSON = {
    "current": {
        "time": "2026-09-13T09:15",
        "temperature_2m": 24.3,
        "apparent_temperature": 25.8,
        "relative_humidity_2m": 72.0,
        "precipitation": 0.0,
        "weather_code": 2,
        "wind_speed_10m": 7.5,
        "wind_gusts_10m": 11.2,
        "cloud_cover": 45.0,
        "pressure_msl": 1012.5,
        "uv_index": 6.3,
        "is_day": 1,
    },
    "daily": {
        "time": ["2026-09-13", "2026-09-14", "2026-09-15"],
        "precipitation_sum": [1.2, 25.0, 3.0],
        "precipitation_probability_max": [20, 85, 40],
        "temperature_2m_min": [15.0, 14.0, 16.0],
        "temperature_2m_max": [26.0, 24.0, 27.0],
        "apparent_temperature_min": [15.5, 14.8, 16.6],
        "apparent_temperature_max": [27.1, 25.0, 28.0],
        "weather_code": [2, 63, 3],
        "wind_speed_10m_max": [9.0, 14.0, 8.0],
        "relative_humidity_2m_min": [60, 70, 55],
        "relative_humidity_2m_max": [90, 98, 88],
        "uv_index_max": [7.0, 3.0, 8.0],
        "sunshine_duration": [36000.0, 18000.0, 28800.0],
        "sunrise": ["2026-09-13T05:51", "2026-09-14T05:51", "2026-09-15T05:51"],
        "sunset": ["2026-09-13T18:03", "2026-09-14T18:03", "2026-09-15T18:03"],
    },
}


class _RespuestaFalsa:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _ClienteFalso:
    def __init__(self, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, params=None):
        return _RespuestaFalsa(CLIMA_JSON)


class _ClienteRoto:
    def __init__(self, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, params=None):
        raise RuntimeError("sin red")


async def test_fetch_clima_completo_parsea_respuesta(monkeypatch):
    monkeypatch.setattr(
        "agroia_backend.services.external_apis.httpx.AsyncClient", _ClienteFalso
    )
    clima = await fetch_clima_completo_open_meteo(4.5, -75.7, dias=7, usar_cache=False)
    assert clima is not None
    # Clima actual del día en transcurso
    actual = clima["actual"]
    assert actual["temperatura_c"] == 24.3
    assert actual["sensacion_termica_c"] == 25.8
    assert actual["humedad_pct"] == 72.0
    assert actual["descripcion"] == "Parcialmente nublado"
    assert actual["emoji"] == "⛅"
    assert actual["viento_kmh"] == 7.5
    # Pronóstico enriquecido: claves clásicas + nuevas
    pron = clima["pronostico"]
    assert len(pron) == 3
    assert pron[1]["precipitacion_mm"] == 25.0
    assert pron[1]["temp_min_c"] == 14.0
    assert pron[1]["probabilidad_lluvia_pct"] == 85
    assert pron[1]["descripcion"] == "Lluvia moderada"
    assert pron[1]["sensacion_min_c"] == 14.8
    assert pron[1]["viento_max_kmh"] == 14.0
    assert pron[1]["humedad_max_pct"] == 98
    assert pron[1]["horas_sol"] == 5.0
    assert pron[1]["salida_sol"] == "2026-09-14T05:51"
    assert clima["fuente"] == "open-meteo"
    assert clima["zona_horaria"] == "America/Bogota"


async def test_fetch_clima_completo_degradacion(monkeypatch):
    monkeypatch.setattr(
        "agroia_backend.services.external_apis.httpx.AsyncClient", _ClienteRoto
    )
    clima = await fetch_clima_completo_open_meteo(4.5, -75.7, usar_cache=False)
    assert clima is None


# ── Forma del dict de alerta ──

def test_alerta_a_dict_expone_clima():
    a = types.SimpleNamespace(
        id=uuid_mod.uuid4(),
        finca_id=uuid_mod.uuid4(),
        tipo="siembra_lunar",
        severidad="Media",
        mensaje="hola",
        fecha_alerta=date(2026, 9, 13),
        pronostico={
            "dia": {"fecha": "2026-09-13"},
            "actual": {"temperatura_c": 24.0},
            "pronostico": [{"fecha": "2026-09-14", "temp_min_c": 15.0}],
        },
        activa=True,
        created_at=datetime(2026, 9, 13, tzinfo=timezone.utc),
    )
    d = _alerta_a_dict(a)
    assert d["clima_actual"]["temperatura_c"] == 24.0
    assert d["pronostico_detallado"][0]["fecha"] == "2026-09-14"


def test_alerta_a_dict_sin_clima():
    a = types.SimpleNamespace(
        id=uuid_mod.uuid4(),
        finca_id=uuid_mod.uuid4(),
        tipo="helada_floracion",
        severidad="Alta",
        mensaje="hola",
        fecha_alerta=None,
        pronostico=None,
        activa=True,
        created_at=None,
    )
    d = _alerta_a_dict(a)
    assert d["clima_actual"] is None
    assert d["pronostico_detallado"] is None


# ── Evaluación de alertas con clima inyectado (persistencia del clima) ──

async def test_evaluar_alertas_persiste_clima_completo():
    async with async_session_factory() as db:
        finca = (
            await db.execute(
                select(Finca)
                .where(Finca.latitud.is_not(None), Finca.longitud.is_not(None))
                .limit(1)
            )
        ).scalars().first()
        if finca is None:
            pytest.skip("No hay fincas con coordenadas (requiere seeds).")
        lote = (
            await db.execute(select(Lote).where(Lote.finca_id == finca.id).limit(1))
        ).scalars().first()
        if lote is None:
            pytest.skip("No hay lote para la finca (requiere seeds).")

        labor = Labor(
            lote_id=lote.id,
            titulo="Fertilización prueba clima",
            tipo="Fertilización",
            producto="Urea",
            estado="Pendiente",
            fecha_programada=date.today(),
        )
        db.add(labor)
        await db.commit()

        try:
            pronostico = [
                {
                    "fecha": (date.today() + timedelta(days=i)).isoformat(),
                    "precipitacion_mm": 40.0 if i == 0 else 5.0,
                    "temp_min_c": 12.0,
                    "temp_max_c": 26.0,
                }
                for i in range(7)
            ]
            clima = {
                "actual": {
                    "fecha": "2026-09-13T09:15",
                    "temperatura_c": 24.5,
                    "sensacion_termica_c": 25.6,
                    "humedad_pct": 70.0,
                    "viento_kmh": 8.0,
                    "uv": 5.0,
                    "codigo_clima": 2,
                    "descripcion": "Parcialmente nublado",
                    "emoji": "⛅",
                },
                "pronostico": pronostico,
            }
            creadas = await evaluar_alertas_finca(db, finca, clima=clima)
            tipos = {c["tipo"] for c in creadas}
            assert "lluvia_aplicacion" in tipos

            alerta = (
                await db.execute(
                    select(AlertaClimatica).where(
                        AlertaClimatica.finca_id == finca.id,
                        AlertaClimatica.tipo == "lluvia_aplicacion",
                        AlertaClimatica.activa.is_(True),
                    )
                )
            ).scalars().first()
            assert alerta is not None
            assert alerta.pronostico["actual"]["temperatura_c"] == 24.5
            assert alerta.pronostico["actual"]["descripcion"] == "Parcialmente nublado"
            assert len(alerta.pronostico["pronostico"]) == 7
            assert "Clima actual" in alerta.mensaje
            assert "24.5 °C" in alerta.mensaje
        finally:
            # Limpieza: quitar alerta y labor creadas por la prueba
            await db.execute(
                delete(AlertaClimatica).where(
                    AlertaClimatica.finca_id == finca.id,
                    AlertaClimatica.mensaje.ilike("%Clima actual%"),
                )
            )
            await db.execute(delete(Labor).where(Labor.id == labor.id))
            await db.commit()


# ── Endpoints ──

async def _clima_falso(lat, lon, dias=7, modelo="auto", usar_cache=True):
    return {
        "fuente": "open-meteo",
        "modelo": "auto",
        "zona_horaria": "America/Bogota",
        "hora_consulta": datetime.now(timezone.utc).isoformat(),
        "actual": {"temperatura_c": 24.5, "descripcion": "Parcialmente nublado", "emoji": "⛅"},
        "pronostico": [
            {"fecha": "2026-09-14", "precipitacion_mm": 2.0, "temp_min_c": 15.0, "temp_max_c": 26.0}
            for _ in range(7)
        ],
    }


async def test_endpoint_clima_finca(monkeypatch):
    monkeypatch.setattr(
        "agroia_backend.api.alertas.fetch_clima_completo_open_meteo", _clima_falso
    )
    async with async_session_factory() as db:
        finca = (
            await db.execute(
                select(Finca)
                .where(Finca.latitud.is_not(None), Finca.longitud.is_not(None))
                .limit(1)
            )
        ).scalars().first()
        if finca is None:
            pytest.skip("No hay fincas con coordenadas (requiere seeds).")
        fid = str(finca.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get(f"/api/v1/fincas/{fid}/clima", headers=_cabeceras())
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["disponible"] is True
    assert cuerpo["actual"]["temperatura_c"] == 24.5
    assert len(cuerpo["pronostico"]) == 7


async def test_endpoint_clima_finca_sin_coordenadas(monkeypatch):
    monkeypatch.setattr(
        "agroia_backend.api.alertas.fetch_clima_completo_open_meteo", _clima_falso
    )
    async with async_session_factory() as db:
        finca = (
            await db.execute(select(Finca).where(Finca.latitud.is_(None)).limit(1))
        ).scalars().first()
        if finca is None:
            pytest.skip("No hay fincas sin coordenadas (requiere seeds).")
        fid = str(finca.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get(f"/api/v1/fincas/{fid}/clima", headers=_cabeceras())
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "SIN_COORDENADAS"


async def test_endpoint_alertas_globales_expone_clima():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        r = await c.get("/api/v1/alertas-climaticas", headers=_cabeceras())
    assert r.status_code == 200
    cuerpo = r.json()
    for item in cuerpo["data"]:
        # Cada alerta expone el clima completo (aunque sea None si es vieja)
        assert "clima_actual" in item
        assert "pronostico_detallado" in item
