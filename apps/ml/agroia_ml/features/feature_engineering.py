"""Feature engineering for crop recommendation.

Prepares features from raw soil + climate data for ML model input.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


def prepare_features(df: pd.DataFrame, target_col: str = "label") -> tuple:
    """Prepare features and target for ML training.

    Args:
        df: DataFrame with soil/climate columns
        target_col: Name of target column (crop name)

    Returns:
        (X, y, label_encoder, scaler) tuple
    """
    # Feature columns
    feature_cols = ["n", "p", "k", "temperature", "humidity", "ph", "rainfall"]

    # Ensure all feature columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        available = [c for c in feature_cols if c in df.columns]
        print(f"⚠️  Columnas faltantes: {missing}. Usando: {available}")
        feature_cols = available

    X = df[feature_cols].copy()

    # Handle missing values — simple median imputation
    for col in X.columns:
        X[col] = X[col].fillna(X[col].median())

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Encode target
    y = df[target_col].copy()
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    return X_scaled, y_encoded, label_encoder, scaler


def get_soil_ranges() -> dict:
    """Return soil variable ranges for validation (Colombia reference).

    These are REFERENCE values — not used for training.
    Actual thresholds come from UPRA/Cenicafé rules.
    """
    return {
        "ph": (4.0, 8.5),
        "n": (0, 400),
        "p": (0, 200),
        "k": (0, 400),
        "temperature": (10, 35),
        "humidity": (30, 100),
        "rainfall": (50, 300),
    }


def validate_features(X: np.ndarray, ranges: dict = None) -> list[str]:
    """Validate feature values against expected ranges.

    Returns list of warnings for out-of-range values.
    """
    if ranges is None:
        ranges = get_soil_ranges()
    warnings = []
    feature_names = list(ranges.keys())
    for i, name in enumerate(feature_names):
        if i < X.shape[1]:
            col = X[:, i]
            lo, hi = ranges[name]
            out = (col < lo) | (col > hi)
            if out.any():
                warnings.append(f"{name}: {out.sum()} valores fuera de rango [{lo}-{hi}]")
    return warnings
