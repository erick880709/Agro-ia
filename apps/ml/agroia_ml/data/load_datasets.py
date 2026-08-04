"""Data loading utilities for AgroIA ML pipeline.

Loads the Kaggle datasets (Crop Recommendation + Crops NPK) for
baseline model training. These datasets are used ONLY for testing
the ML pipeline — NOT for generating real recommendations.
"""

import os
from pathlib import Path

import pandas as pd

# ── Paths ──
DATASETS_DIR = Path(__file__).parent.parent.parent.parent.parent / "datasets"
CROP_REC_PATH = DATASETS_DIR / "crop-recommendation" / "Crop_recommendation.csv"
CROPS_NPK_PATH = DATASETS_DIR / "crops-npk" / "sensor_Crop_Dataset (1).csv"


def load_crop_recommendation() -> pd.DataFrame:
    """Load the Crop Recommendation dataset (2,200 rows, India).

    Columns: N, P, K, temperature, humidity, ph, rainfall, label
    """
    if not CROP_REC_PATH.exists():
        raise FileNotFoundError(
            f"Dataset no encontrado: {CROP_REC_PATH}. "
            "Ejecuta primero 'python datasets/validate.py' para verificar."
        )
    df = pd.read_csv(CROP_REC_PATH)
    df.columns = df.columns.str.lower().str.strip()
    return df


def load_crops_npk() -> pd.DataFrame:
    """Load the Crops NPK dataset (20,000 rows, India).

    Columns: Nitrogen, Phosphorus, Potassium, Temperature,
             Humidity, pH_Value, Rainfall, Crop, Soil_Type, Variety
    """
    if not CROPS_NPK_PATH.exists():
        raise FileNotFoundError(
            f"Dataset no encontrado: {CROPS_NPK_PATH}. "
            "Ejecuta primero 'python datasets/validate.py' para verificar."
        )
    df = pd.read_csv(CROPS_NPK_PATH)
    df.columns = df.columns.str.lower().str.strip()
    return df


def get_combined_dataset() -> pd.DataFrame:
    """Combine and normalize both datasets into a unified format.

    Returns DataFrame with columns:
        n, p, k, temperature, humidity, ph, rainfall, crop
    """
    df1 = load_crop_recommendation()
    df2 = load_crops_npk()

    # Normalize column names
    col_map = {
        "nitrogen": "n",
        "phosphorus": "p",
        "potassium": "k",
        "ph_value": "ph",
        "temperature": "temperature",
        "humidity": "humidity",
        "rainfall": "rainfall",
        "label": "crop",
    }
    # df2 uses 'crop' as label column — normalize
    if "crop" in df2.columns and "label" not in df2.columns:
        df2 = df2.rename(columns={"crop": "label_temp"})
        # keep crop as the label
        pass

    # Standardize df1
    df1_std = df1[["n", "p", "k", "temperature", "humidity", "ph", "rainfall", "label"]].copy()
    df1_std["source"] = "crop_recommendation"

    # Standardize df2 — map columns
    df2_cols = {
        "nitrogen": "n", "phosphorus": "p", "potassium": "k",
        "temperature": "temperature", "humidity": "humidity",
        "ph_value": "ph", "rainfall": "rainfall", "crop": "label",
    }
    available = {k: v for k, v in df2_cols.items() if k in df2.columns}
    df2_std = df2[list(available.keys())].copy()
    df2_std = df2_std.rename(columns=available)
    df2_std["source"] = "crops_npk"

    combined = pd.concat([df1_std, df2_std], ignore_index=True)
    return combined
