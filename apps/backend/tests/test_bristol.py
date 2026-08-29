"""Pruebas del módulo Almanaque Bristol (calendario lunar, v3.4)."""

import os
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

# Fuente estática para pruebas deterministas (sin red ni efemérides).
os.environ["BRISTOL_MODO"] = "static"
os.environ["BRISTOL_ACTIVADO"] = "true"

from agroia.database import async_session_factory  # noqa: E402
from agroia_backend.main import app  # noqa: E402
from agroia_backend.services.calendario_lunar import (  # noqa: E402
    FASES_FAVORABLES,
    calendario_mes,
    clima_favorable_siembra,
    estado_bristol,
    fase_estatica,
    get_lunar_phase,
    mapear_recomendacion_bristol,
    pronostico_lunar,
    resumen_bristol,
)


@pytest.fixture()
async def cli():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _cabeceras(rol="Agronomo", email="agronomo@agroia.co"):
    return {"X-User-Role": rol, "X-User-Email": email}


# ── Cálculo lunar ──

def test_luna_nueva_de_referencia():
    """El 2000-01-06 (medianoche UTC) está dentro de la luna nueva de referencia."""
    resultado = fase_estatica(date(2000, 1, 6))
    fase = resultado["fase"]
    assert fase["nombre"] == "Luna Nueva"
    assert fase["nombre_en"] == "New Moon"
    assert fase["emoji"] == "🌑"
    # La referencia exacta es 2000-01-06 18:14 UTC: la edad ronda 0 o el
    # final del ciclo (≈ 29.5) según la hora del día.
    assert fase["edad_dias"] < 1.0 or fase["edad_dias"] > 28.5
    assert fase["iluminacion"] < 0.05


def test_luna_llena_conocida():
    """≈ 14.77 días después de la luna nueva de referencia hay luna llena."""
    resultado = fase_estatica(date(2000, 1, 21))
    fase = resultado["fase"]
    assert fase["nombre"] == "Luna Llena"
    assert fase["iluminacion"] > 0.95
    assert 13.0 < fase["edad_dias"] < 16.0


def test_contrato_fase_completo():
    resultado = get_lunar_phase(date(2026, 8, 29))
    assert resultado["fecha"] == "2026-08-29"
    fase = resultado["fase"]
    assert set(fase) == {"nombre", "nombre_en", "iluminacion", "edad_dias", "emoji"}
    assert 0.0 <= fase["iluminacion"] <= 1.0
    assert 0.0 <= fase["edad_dias"] <= 29.6
    eventos = resultado["proximos_eventos"]
    assert eventos["proxima_luna_llena"] > resultado["fecha"]
    assert eventos["proxima_luna_nueva"] > resultado["fecha"]
    assert resultado["fuente"] == "static"


def test_resumen_bristol_incluye_recomendacion():
    resultado = resumen_bristol(date(2000, 1, 6))
    reco = resultado["recomendacion_bristol"]
    assert reco["tipo"] == "raices"
    assert reco["favorable"] is True
    assert "Zanahoria" in reco["cultivos"]


def test_pronostico_lunar():
    dias = pronostico_lunar(7)
    assert len(dias) == 7
    for dia in dias:
        assert "fase" in dia and "recomendacion_bristol" in dia
        assert "favorable" in dia["recomendacion_bristol"]


def test_calendario_mes():
    resultado = calendario_mes(2026, 8)
    assert resultado["anio"] == 2026
    assert resultado["mes"] == 8
    assert len(resultado["dias"]) == 31
    for i, dia in enumerate(resultado["dias"], start=1):
        assert dia["fecha"] == f"2026-08-{i:02d}"
        assert dia["fase"]["emoji"] in {"🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"}
        assert 0.0 <= dia["fase"]["iluminacion"] <= 1.0
    # Febrero bisiesto (2024) → 29 días
    assert len(calendario_mes(2024, 2)["dias"]) == 29


# ── Tabla Bristol ──

def test_mapeo_tabla_bristol():
    esperados = {
        "New Moon": "raices",
        "Waxing Crescent": "hojas",
        "First Quarter": "hojas",
        "Full Moon": "frutos",
        "Last Quarter": "reposo",
        "Waning Crescent": "reposo",
    }
    for fase_en, tipo in esperados.items():
        reco = mapear_recomendacion_bristol(fase_en)
        assert reco["tipo"] == tipo
        assert reco["descripcion"]
        assert isinstance(reco["cultivos"], list)


def test_favorabilidad_fases():
    assert mapear_recomendacion_bristol("New Moon")["favorable"] is True
    assert mapear_recomendacion_bristol("Full Moon")["favorable"] is True
    assert mapear_recomendacion_bristol("Waning Gibbous")["favorable"] is False
    assert FASES_FAVORABLES == {"New Moon", "Waxing Crescent", "First Quarter", "Full Moon"}


# ── Clima favorable para siembra ──

def test_clima_favorable_siembra():
    bueno = [
        {"fecha": "2026-08-29", "precipitacion_mm": 5.0, "temp_min_c": 12.0},
        {"fecha": "2026-08-30", "precipitacion_mm": 0.0, "temp_min_c": 11.0},
    ]
    assert clima_favorable_siembra(bueno) is True
    lluvia = [{"fecha": "2026-08-29", "precipitacion_mm": 25.0, "temp_min_c": 12.0}]
    assert clima_favorable_siembra(lluvia) is False
    helada = [{"fecha": "2026-08-29", "precipitacion_mm": 2.0, "temp_min_c": 3.0}]
    assert clima_favorable_siembra(helada) is False
    assert clima_favorable_siembra([]) is False


def test_estado_bristol():
    estado = estado_bristol()
    assert estado["activado"] is True
    assert estado["modo"] == "static"
    assert estado["fuente_activa"] in {"skyfield", "usnavy", "static"}


# ── Endpoints ──

async def test_endpoint_actual(cli):
    r = await cli.get("/api/v1/calendario-lunar/actual", headers=_cabeceras())
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["fase"]["nombre"]
    assert "recomendacion_bristol" in cuerpo


async def test_endpoint_pronostico(cli):
    r = await cli.get("/api/v1/calendario-lunar/pronostico", params={"dias": 3}, headers=_cabeceras())
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] == 3
    assert len(cuerpo["data"]) == 3


async def test_endpoint_mes(cli):
    r = await cli.get(
        "/api/v1/calendario-lunar/mes", params={"anio": 2026, "mes": 8}, headers=_cabeceras()
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert len(cuerpo["dias"]) == 31
    assert cuerpo["dias"][0]["fase"]["emoji"]


async def test_endpoint_estado_solo_admin(cli):
    r = await cli.get("/api/v1/calendario-lunar/estado", headers=_cabeceras(rol="Cliente"))
    assert r.status_code == 403
    r = await cli.get("/api/v1/calendario-lunar/estado", headers=_cabeceras(rol="Admin"))
    assert r.status_code == 200
    assert "fuente_activa" in r.json()


# ── Preferencias (BD) ──

async def test_preferencias_bristol_upsert():
    from sqlalchemy import delete, select

    from agroia_backend.models.preferencia_bristol import PreferenciaBristol
    from agroia_backend.models.usuario import Usuario

    async with async_session_factory() as db:
        usuario = (
            await db.execute(
                select(Usuario).where(Usuario.email == "maria.cliente@agroia.co")
            )
        ).scalar_one_or_none()
        if usuario is None:
            pytest.skip("Seed de usuarios ausente (requiere load_seeds).")
        try:
            pref = PreferenciaBristol(
                usuario_id=usuario.id,
                mostrar_en_reportes=False,
                generar_alertas_siembra=False,
            )
            db.add(pref)
            await db.commit()
            leida = (
                await db.execute(
                    select(PreferenciaBristol).where(
                        PreferenciaBristol.usuario_id == usuario.id
                    )
                )
            ).scalar_one()
            assert leida.mostrar_en_reportes is False
            assert leida.generar_alertas_siembra is False
        finally:
            await db.execute(
                delete(PreferenciaBristol).where(
                    PreferenciaBristol.usuario_id == usuario.id
                )
            )
            await db.commit()
