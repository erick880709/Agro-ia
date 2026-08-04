"""Script de verificación del entorno de desarrollo.

Valida que todas las dependencias necesarias estén instaladas
y configuradas antes de ejecutar la aplicación.
"""

import sys


def check_python() -> bool:
    """Verifica versión de Python."""
    v = sys.version_info
    ok = v >= (3, 11)
    print(f"  Python {v.major}.{v.minor}.{v.micro}: {'✅' if ok else '❌ (requiere 3.11+)'}")
    return ok


def check_env_file() -> bool:
    """Verifica que .env existe."""
    from pathlib import Path
    ok = Path(".env").exists()
    print(f"  .env: {'✅' if ok else '❌ (copia .env.example → .env)'}")
    return ok


def check_docker() -> bool:
    """Verifica que Docker esté disponible."""
    import subprocess
    try:
        subprocess.run(["docker", "--version"], capture_output=True, timeout=5)
        print("  Docker: ✅")
        return True
    except Exception:
        print("  Docker: ⚠️ no detectado (requerido para PostgreSQL/Redis local)")
        return False


def check_datasets() -> bool:
    """Verifica que los datasets existen."""
    from pathlib import Path
    base = Path("datasets")
    rec = base / "crop-recommendation" / "Crop_recommendation.csv"
    npk = base / "crops-npk" / "sensor_Crop_Dataset (1).csv"
    ok_rec = rec.exists()
    ok_npk = npk.exists()
    print(f"  datasets/crop-recommendation: {'✅' if ok_rec else '❌'}")
    print(f"  datasets/crops-npk: {'✅' if ok_npk else '❌'}")
    return ok_rec and ok_npk


def main():
    print("🔍 AgroIA — Verificación del entorno de desarrollo")
    print("=" * 50)

    results = [
        ("Python 3.11+", check_python()),
        ("Archivo .env", check_env_file()),
        ("Docker", check_docker()),
        ("Datasets ML", check_datasets()),
    ]

    print("=" * 50)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"Resultado: {passed}/{total} checks pasados")

    if passed == total:
        print("✅ Entorno listo. Ejecuta: docker compose up -d postgres redis rabbitmq")
        print("   Luego: make run-backend")
    else:
        print("⚠️  Corrige los checks fallidos antes de continuar.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
