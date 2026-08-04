"""MLflow tracking configuration for AgroIA ML service.

Local development: uses file-based store (SQLite + local artifacts).
Production: uses PostgreSQL backend + S3 artifact store.
"""

import mlflow
from agroia.config import get_settings

settings = get_settings()


def init_mlflow():
    """Initialize MLflow tracking for the current environment."""
    if settings.environment == "development":
        mlflow.set_tracking_uri("http://localhost:5000")
    else:
        mlflow.set_tracking_uri(f"postgresql://{settings.database_url}")

    mlflow.set_experiment("agroia-motor-recomendaciones")
    return mlflow


def log_model_metrics(
    model_name: str,
    model_type: str,
    f1_score: float,
    precision: float,
    recall: float,
    params: dict,
    artifact_path: str = "model",
):
    """Log model training results to MLflow."""
    mlflow.set_tag("model_name", model_name)
    mlflow.set_tag("model_type", model_type)

    mlflow.log_params(params)
    mlflow.log_metric("f1_score", f1_score)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
