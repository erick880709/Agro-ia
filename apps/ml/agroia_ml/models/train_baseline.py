"""Baseline model training for crop recommendation.

Trains Random Forest and XGBoost classifiers on the combined Kaggle
datasets. These models serve as a METHODOLOGICAL BASELINE only —
they MUST be recalibrated with Colombian data before production use.

⚠️  ADVERTENCIA: Estos modelos fueron entrenados con datos de India.
    NO usar para generar recomendaciones a agricultores colombianos.
    Solo sirven para validar que el pipeline de ML funciona.
"""

import os
import pickle
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import cross_val_score, train_test_split

# Fix random seed for reproducibility
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# ── Output directory for model artifacts ──
MODELS_DIR = Path(__file__).parent.parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


def train_random_forest(X, y, label_encoder) -> dict:
    """Train Random Forest baseline for crop classification.

    Args:
        X: Feature matrix (scaled)
        y: Encoded labels
        label_encoder: Fitted LabelEncoder

    Returns:
        dict with model, metrics, and metadata
    """
    print("🌲 Entrenando Random Forest baseline...")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    # Train
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    f1 = f1_score(y_test, y_pred, average="weighted")
    precision = precision_score(y_test, y_pred, average="weighted")
    recall = recall_score(y_test, y_pred, average="weighted")

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="f1_weighted")

    print(f"   F1-score: {f1:.4f} (CV mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f})")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall: {recall:.4f}")

    # Check if meets AgroIA quality gate
    meets_target = f1 >= 0.80
    if meets_target:
        print("   ✅ F1 cumple meta AgroIA (≥ 0.80)")
    else:
        print(f"   ⚠️  F1 NO cumple meta AgroIA (≥ 0.80). Diferencia: {0.80 - f1:.4f}")

    return {
        "model": model,
        "f1_score": f1,
        "precision": precision,
        "recall": recall,
        "cv_mean": cv_scores.mean(),
        "cv_std": cv_scores.std(),
        "meets_target": meets_target,
        "label_encoder": label_encoder,
        "n_classes": len(label_encoder.classes_),
        "classes": label_encoder.classes_.tolist(),
    }


def save_model(result: dict, name: str = "rf_baseline"):
    """Save trained model and metadata to disk."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    versioned_name = f"{name}_{timestamp}"

    # Save model
    model_path = MODELS_DIR / f"{versioned_name}.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(result["model"], f)

    # Save metadata (without model object)
    meta = {k: v for k, v in result.items() if k != "model"}
    meta["model_path"] = str(model_path)
    meta["timestamp"] = timestamp
    meta["dataset"] = "Kaggle: Crop Recommendation + Crops NPK (India)"
    meta["warning"] = "⚠️ BASELINE ONLY — NOT FOR PRODUCTION USE IN COLOMBIA"

    meta_path = MODELS_DIR / f"{versioned_name}_meta.json"
    import json
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False, default=str)

    print(f"   💾 Modelo guardado: {model_path}")
    print(f"   📋 Metadata: {meta_path}")

    return model_path


def main():
    """Full training pipeline."""
    print("=" * 60)
    print("  AgroIA — Entrenamiento Baseline (Cold Start)")
    print("  ⚠️  Datos de India — SOLO para validación del pipeline")
    print("=" * 60)

    from agroia_ml.data.load_datasets import get_combined_dataset
    from agroia_ml.features.feature_engineering import prepare_features

    # Load data
    print("\n📥 Cargando datasets...")
    df = get_combined_dataset()
    print(f"   {len(df):,} registros combinados")

    # Prepare features
    print("\n🔧 Preparando features...")
    X, y, label_encoder, scaler = prepare_features(df)
    print(f"   Features: {X.shape[1]} | Clases: {len(label_encoder.classes_)}")

    # Train Random Forest
    result = train_random_forest(X, y, label_encoder)

    # Save model
    print("\n💾 Guardando modelo...")
    save_model(result, "rf_baseline")

    # Summary
    print("\n" + "=" * 60)
    print("  RESUMEN DE ENTRENAMIENTO")
    print("=" * 60)
    print(f"  Modelo: Random Forest (baseline)")
    print(f"  Datos: {len(df):,} registros (Kaggle, India)")
    print(f"  Cultivos: {result['n_classes']}")
    print(f"  F1-score: {result['f1_score']:.4f}")
    print(f"  Cross-val (5-fold): {result['cv_mean']:.4f} ± {result['cv_std']:.4f}")
    print(f"  ¿Cumple meta AgroIA (F1 ≥ 0.80)? {'✅ Sí' if result['meets_target'] else '❌ No'}")
    print("=" * 60)
    print("\n⚠️  RECORDATORIO: Este modelo usa datos de India.")
    print("   NO desplegar en producción sin recalibrar con datos colombianos.")
    print("   Fuentes requeridas: AGROSAVIA + IDEAM + sensores IoT Quindío.")

    return result


if __name__ == "__main__":
    main()
