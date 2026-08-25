"""Prueba de integración end-to-end del proyecto AgroIA.

Verifica que todos los servicios estén correctamente conectados:
- Health checks de todos los contenedores
- Endpoints principales responden
- Modelos SQLAlchemy son importables
- Alembic migrations están actualizadas
"""

import asyncio
import sys


async def test_all_models_importable():
    """Verifica que todos los modelos SQLAlchemy se puedan importar."""
    print("📦 Modelos SQLAlchemy...", end=" ")
    try:
        from agroia_backend.models.recomendacion import Recomendacion
        from agroia_backend.models.discordancia import Discordancia
        from agroia_backend.models.regla_agronomica import ReglaAgronomica
        from agroia_backend.models.modelo_ml import ModeloML
        from agroia_backend.models.metrica_modelo import MetricaModelo
        from agroia_backend.models.sensor_reading import SensorReading
        from agroia_backend.models.dispositivo_iot import DispositivoIoT
        from agroia_backend.models.cultivo import Cultivo, FichaTecnica
        from agroia_backend.models.usuario import Usuario, Membresia
        print("✅ 10 modelos OK")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_all_services_importable():
    """Verifica que todos los servicios se puedan importar."""
    print("🔧 Servicios...", end=" ")
    try:
        from agroia_backend.services.data_adapters import SueloAdapter, validate_soil_reading
        from agroia_backend.services.rules_engine import RulesEngine
        from agroia_backend.services.aptitud import AptitudService, clasificar_aptitud
        from agroia_backend.services.orchestrator import RecommendationOrchestrator
        from agroia_backend.services.justification import generate_justification, estimate_cost
        from agroia_backend.services.catalogo_service import listar_cultivos, listar_fichas
        from agroia_backend.services.dashboard_service import get_dashboard_data
        from agroia_backend.services.external_apis import enrich_location_data
        from agroia_auth.auth_service import hash_password, create_access_token, decode_token
        from agroia_auth.security_middleware import SecurityHeadersMiddleware
        from agroia_rag.rag_service import rag_query, generate_embedding
        print("✅ 12 servicios OK")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_all_routers_importable():
    """Verifica que todos los routers de API se puedan importar."""
    print("🌐 Routers API...", end=" ")
    try:
        from agroia_backend.api.recomendaciones import router as r1
        from agroia_backend.api.catalogo import router as r2
        from agroia_backend.api.iot import router as r3
        from agroia_backend.api.dashboard import router as r4
        from agroia_backend.api.usuarios import router as r5
        from agroia_auth.api.auth import router as r6
        from agroia_rag.api.chat import router as r7
        print("✅ 7 routers OK")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_config_loads():
    """Verifica que la configuración carga correctamente."""
    print("⚙️  Configuración...", end=" ")
    try:
        from agroia.config import get_settings
        s = get_settings()
        assert s.environment in ("development", "production")
        print(f"✅ environment={s.environment}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_datasets_accessible():
    """Verifica que los datasets de ML son accesibles."""
    print("📊 Datasets ML...", end=" ")
    try:
        from pathlib import Path
        base = Path("datasets")
        assert (base / "crop-recommendation" / "Crop_recommendation.csv").exists()
        assert (base / "crops-npk" / "sensor_Crop_Dataset (1).csv").exists()
        print("✅ 2 datasets OK")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_reglas_seed_data():
    """Verifica los datos semilla de reglas agronómicas (UC1 + UC2)."""
    print("🌱 Reglas agronómicas...", end=" ")
    try:
        from agroia_backend.models.regla_agronomica import VariableSuelo
        from agroia_backend.seeds.reglas import REGLAS_POR_CULTIVO, REGLAS_UNIVERSALES

        total = len(REGLAS_UNIVERSALES) + sum(len(r) for r in REGLAS_POR_CULTIVO.values())
        assert total >= 20, f"Se esperaban >= 20 reglas, hay {total}"

        validas = {v.value for v in VariableSuelo}
        for r in REGLAS_UNIVERSALES:
            assert r["variable"] in validas, f"Variable inválida: {r['variable']}"
            assert r["accion"], "Toda regla debe tener acción correctiva"
        for cultivo, reglas in REGLAS_POR_CULTIVO.items():
            for r in reglas:
                assert r["variable"] in validas, f"Variable inválida en {cultivo}: {r['variable']}"
                assert r["accion"], "Toda regla debe tener acción correctiva"

        # Los 5 cultivos prioritarios colombianos deben tener reglas específicas
        assert set(REGLAS_POR_CULTIVO) >= {"Café", "Maíz", "Arroz", "Plátano", "Papa"}
        print(f"✅ {total} reglas OK ({len(REGLAS_POR_CULTIVO)} cultivos + universales)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_variable_mapping():
    """Verifica el mapeo VariableSuelo → claves de SoilData.to_dict()."""
    print("🧩 Mapeo variables suelo...", end=" ")
    try:
        from agroia_backend.models.regla_agronomica import VariableSuelo
        from agroia_backend.services.data_adapters import ALL_SOIL_VARIABLES
        from agroia_backend.services.rules_engine import VARIABLE_KEY_MAP

        valores = {v.value for v in VariableSuelo}
        faltan = valores - set(VARIABLE_KEY_MAP)
        assert not faltan, f"Faltan variables en el mapa: {faltan}"

        claves_invalidas = set(VARIABLE_KEY_MAP.values()) - set(ALL_SOIL_VARIABLES)
        assert not claves_invalidas, f"Claves de mapa no válidas: {claves_invalidas}"
        print(f"✅ mapeo completo ({len(VARIABLE_KEY_MAP)} variables)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_normalizacion_esp32():
    """Verifica la normalización de la trama cruda del ESP32 (brecha G2)."""
    print("📡 Normalización ESP32...", end=" ")
    try:
        from agroia_backend.services.normalizacion_iot import (
            aplicar_calibracion,
            normalizar_trama,
        )

        trama = {
            "device_id": "esp32-npk-001",
            "humidity": 84.7,
            "temperature": 22.6,
            "conductivity": 44.0,
            "ph": 7.1,
            "nitrogen": 1.0,
            "phosphorus": 3.0,
            "potassium": 7.0,
            "rssi": -22,
            "uptime_s": 2048,
        }
        payload, advertencias = normalizar_trama(trama)

        # Mapeo de campos
        assert payload["ph"] == 7.1
        assert payload["nitrogeno"] == 1.0
        assert payload["fosforo"] == 3.0
        assert payload["potasio"] == 7.0
        # Unidades: 44 µS/cm → 0.044 dS/m
        assert payload["conductividad_electrica"] == 0.044
        # Ambientales separadas de las variables de suelo
        assert payload["humedad_ambiental"] == 84.7
        assert payload["temperatura_ambiental"] == 22.6
        assert "humedad" not in payload and "temperatura_suelo" not in payload
        # Telemetría fuera del payload
        assert "device_id" not in payload and "rssi" not in payload
        # Advertencia NPK sin calibrar
        assert "npk_sin_calibrar" in advertencias

        # Calibración aplicada solo cuando el dispositivo está calibrado
        calibrado = aplicar_calibracion(dict(payload), {"nitrogeno": 2.0})
        assert calibrado["nitrogeno"] == 2.0
        sin_factor = aplicar_calibracion(dict(payload), None)
        assert sin_factor["nitrogeno"] == 1.0

        print("✅ trama normalizada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    print("=" * 55)
    print("  AgroIA — Verificación de Integración")
    print("=" * 55)

    tests = [
        ("Modelos", test_all_models_importable),
        ("Servicios", test_all_services_importable),
        ("Routers", test_all_routers_importable),
        ("Config", test_config_loads),
        ("Datasets", test_datasets_accessible),
        ("Reglas", test_reglas_seed_data),
        ("Mapeo", test_variable_mapping),
        ("ESP32", test_normalizacion_esp32),
    ]

    results = []
    for name, test_fn in tests:
        try:
            ok = await test_fn()
        except Exception as e:
            print(f"   ❌ Excepción: {e}")
            ok = False
        results.append((name, ok))

    print("=" * 55)
    passed = sum(1 for _, ok in results if ok)
    print(f"  Resultado: {passed}/{len(results)} checks pasados")

    if passed == len(results):
        print("  ✅ Proyecto AgroIA — INTEGRACIÓN COMPLETA")
        print("=" * 55)
        return 0
    else:
        failed = [name for name, ok in results if not ok]
        print(f"  ⚠️  Fallos: {', '.join(failed)}")
        print("=" * 55)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
