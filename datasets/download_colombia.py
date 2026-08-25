"""Descarga datasets colombianos de AGROSAVIA, IDEAM y Cenicafé desde datos.gov.co.

Usa la API Socrata (SODA) de datos.gov.co para descubrir y descargar
datasets relevantes para AgroIA.
"""

import os
import time
import requests
from pathlib import Path

BASE_DIR = Path(r"C:\Users\ELITEBOOK\OneDrive\Documentos\Repositorio\Trabajo\Agro-ia\datasets")
SOCRATA_DOMAIN = "www.datos.gov.co"

# ── Config ──
HEADERS = {
    "User-Agent": "AgroIA/0.1.0 (agroia-colombia; research project)",
    "Accept": "application/json",
}
APP_TOKEN = None  # Socrata permite acceso anónimo con rate limit

def socrata_search(query: str, limit: int = 10) -> list:
    """Busca datasets en datos.gov.co usando la API de descubrimiento."""
    url = f"https://{SOCRATA_DOMAIN}/api/catalog/v1"
    params = {
        "q": query,
        "limit": limit,
        "only": "datasets",
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


def socrata_download(dataset_id: str, dest_dir: Path, name: str) -> bool:
    """Descarga un dataset completo como CSV desde Socrata."""
    url = f"https://{SOCRATA_DOMAIN}/api/views/{dataset_id}/rows.csv"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{name}.csv"

    print(f"   ⏳ Descargando {dataset_id} ...", end=" ")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        resp.raise_for_status()

        # Guardar
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        size_mb = os.path.getsize(dest) / (1024 * 1024)
        # Contar líneas
        with open(dest, "r", encoding="utf-8", errors="replace") as f:
            lines = sum(1 for _ in f)
        print(f"✅ {lines:,} filas, {size_mb:.1f} MB")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# ═══════════════════════════════════════════════════════════
# 1. BUSCAR DATASETS AGROSAVIA
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("🔍 Buscando datasets AGROSAVIA en datos.gov.co ...")
print("=" * 60)

agrosavia_results = socrata_search("AGROSAVIA suelos", limit=15)
print(f"   Encontrados: {len(agrosavia_results)} datasets\n")

downloaded_agrosavia = 0
for ds in agrosavia_results:
    rid = ds.get("resource", {}).get("id", "")
    name = ds.get("name", "Sin nombre")
    desc = (ds.get("description", "") or "")[:120]
    print(f"   📋 {name}")
    print(f"      {desc}")
    if rid:
        safe_name = name.lower().replace(" ", "_").replace("/", "_")[:60]
        if socrata_download(rid, BASE_DIR / "agrosavia", safe_name):
            downloaded_agrosavia += 1
    print()

# ═══════════════════════════════════════════════════════════
# 2. BUSCAR DATASETS IDEAM
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("🔍 Buscando datasets IDEAM en datos.gov.co ...")
print("=" * 60)

ideam_results = socrata_search("IDEAM clima estaciones", limit=10)
print(f"   Encontrados: {len(ideam_results)} datasets\n")

downloaded_ideam = 0
for ds in ideam_results:
    rid = ds.get("resource", {}).get("id", "")
    name = ds.get("name", "Sin nombre")
    desc = (ds.get("description", "") or "")[:120]
    print(f"   📋 {name}")
    print(f"      {desc}")
    if rid:
        safe_name = name.lower().replace(" ", "_").replace("/", "_")[:60]
        if socrata_download(rid, BASE_DIR / "ideam", safe_name):
            downloaded_ideam += 1
    print()

# ═══════════════════════════════════════════════════════════
# 3. BUSCAR DATASETS ESPECÍFICOS DEL QUINDÍO
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("🔍 Buscando datasets del Quindío / Eje Cafetero ...")
print("=" * 60)

quindio_results = socrata_search("Quindío agro cafe", limit=10)
print(f"   Encontrados: {len(quindio_results)} datasets\n")

for ds in quindio_results:
    rid = ds.get("resource", {}).get("id", "")
    name = ds.get("name", "Sin nombre")
    desc = (ds.get("description", "") or "")[:120]
    print(f"   📋 {name}")
    print(f"      {desc}")
    if rid:
        safe_name = name.lower().replace(" ", "_").replace("/", "_")[:60]
        socrata_download(rid, BASE_DIR / "quindio", safe_name)
    print()

# ═══════════════════════════════════════════════════════════
# 4. RESUMEN
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("📊 RESUMEN DE DESCARGAS")
print("=" * 60)
total = 0
for folder in ["agrosavia", "ideam", "quindio"]:
    d = BASE_DIR / folder
    if d.exists():
        files = list(d.glob("*.csv"))
        size = sum(f.stat().st_size for f in files) / (1024 * 1024)
        print(f"   {folder}/ — {len(files)} archivos, {size:.1f} MB")
        total += len(files)
    else:
        print(f"   {folder}/ — 0 archivos")

print(f"\n   ✅ Total descargado: {total} datasets de datos.gov.co")
if total == 0:
    print("\n   ⚠️  No se encontraron datasets accesibles vía API Socrata.")
    print("   Posibles causas:")
    print("   1. Los datasets requieren autenticación o token de aplicación")
    print("   2. Los IDs de dataset en el portal cambiaron")
    print("   3. Rate limiting de la API sin token")
    print("\n   📋 Próximos pasos manuales:")
    print("   - AGROSAVIA: https://www.datos.gov.co/browse?q=AGROSAVIA")
    print("   - IDEAM: https://www.datos.gov.co/browse?q=IDEAM")
    print("   - Registrar app token en https://www.datos.gov.co/profile/edit/developer_settings")
