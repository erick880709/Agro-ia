"""Valida que los datasets descargados sean legibles y tengan la estructura esperada."""

import os
import pandas as pd

DATASETS_DIR = os.path.dirname(__file__)

expected = {
    "crop-recommendation/Crop_recommendation.csv": {
        "min_rows": 2000,
        "expected_cols": ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "label"],
    },
    "crops-npk/sensor_Crop_Dataset (1).csv": {
        "min_rows": 15000,
        "expected_cols": None,  # validar solo que tenga columnas razonables
    },
}

exit_code = 0

for rel_path, checks in expected.items():
    full_path = os.path.join(DATASETS_DIR, rel_path)
    print(f"🔍 {rel_path} ...", end=" ")
    if not os.path.exists(full_path):
        print("❌ NO ENCONTRADO")
        exit_code = 1
        continue
    try:
        df = pd.read_csv(full_path)
        print(f"✅ {len(df):,} filas × {len(df.columns)} columnas", end="")
        if checks["min_rows"] and len(df) < checks["min_rows"]:
            print(f" ⚠️ Menos filas de las esperadas (mín {checks['min_rows']})")
            exit_code = 1
        elif checks["expected_cols"]:
            missing = [c for c in checks["expected_cols"] if c not in df.columns]
            if missing:
                print(f" ⚠️ Columnas faltantes: {missing}")
                exit_code = 1
            else:
                print(" — columnas OK")
        else:
            print(f" — columnas: {list(df.columns[:8])}...")
    except Exception as e:
        print(f"❌ Error al leer: {e}")
        exit_code = 1

print()
if exit_code == 0:
    print("✅ Todos los datasets validados correctamente.")
else:
    print("⚠️ Algunos datasets requieren atención.")

exit(exit_code)
