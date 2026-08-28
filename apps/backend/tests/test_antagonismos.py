"""Tests de reglas de antagonismo/sinergia nutricional (v3, Ola 1)."""
import pytest
from agroia.database import async_session_factory
from agroia_backend.services.rules_engine import RulesEngine

pytestmark = pytest.mark.asyncio(loop_scope="module")


async def test_antagonismos_detecta_interacciones():
    from agroia_backend.services.asegurar_reglas import asegurar_reglas

    await asegurar_reglas()  # siembra idempotente (incluye tipo='antagonismo')
    suelo = {
        "potasio": 500,      # exceso → reduce Ca/Mg
        "calcio": 500,       # deficit (< 1000)
        "magnesio": 50,      # deficit (< 100)
        "fosforo": 600,      # exceso → fija Zn
        "zinc": 1,           # deficit
        "ph": 5.0,           # < 5.5 con Mg bajo → cal dolomítica
        "nitrogeno": 300,    # exceso en fructificación
    }
    async with async_session_factory() as db:
        engine = RulesEngine(db)
        filas = await engine.evaluar_antagonismos(suelo, "Fructificación")
    variables = {f["variable"] for f in filas}
    assert "K-Ca-Mg" in variables
    assert "P-Zn" in variables
    assert "pH-Ca-Mg" in variables
    assert "N-maduracion" in variables
    assert all(f["estado"] == "INTERACCION" for f in filas)
    assert all(f["accion"] for f in filas)


async def test_antagonismos_sin_datos_no_explota():
    async with async_session_factory() as db:
        engine = RulesEngine(db)
        filas = await engine.evaluar_antagonismos({}, None)
    assert filas == []
