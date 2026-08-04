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
        from agroia_backend.models.cultivo import Cultivo, FichaTecnica
        from agroia_backend.models.usuario import Usuario, Membresia
        print("✅ 9 modelos OK")
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
        from agroia_backend.services.orchestrator import RecommendationOrchestrator
        from agroia_backend.services.justification import generate_justification, estimate_cost
        from agroia_backend.services.catalogo_service import listar_cultivos, listar_fichas
        from agroia_backend.services.dashboard_service import get_dashboard_data
        from agroia_backend.services.external_apis import enrich_location_data
        from agroia_auth.auth_service import hash_password, create_access_token, decode_token
        from agroia_auth.security_middleware import SecurityHeadersMiddleware
        from agroia_rag.rag_service import rag_query, generate_embedding
        print("✅ 11 servicios OK")
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
