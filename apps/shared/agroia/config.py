"""Configuración centralizada desde variables de entorno.

Usa pydantic-settings para cargar y validar toda la configuración
de la aplicación desde variables de entorno y archivos .env.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada de AgroIA."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Base de datos ──
    database_url: str = "postgresql+asyncpg://agroia:agroia_dev@localhost:5432/agroia"
    database_url_sync: str = "postgresql://agroia:agroia_dev@localhost:5432/agroia"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── RabbitMQ ──
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_queue_iot: str = "sensor.data.received"

    # ── JWT ──
    jwt_private_key_path: str = "./keys/private.pem"
    jwt_public_key_path: str = "./keys/public.pem"
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ── OpenAI ──
    openai_api_key: str = ""
    openai_model: str = "gpt-4"

    # ── AWS ──
    aws_region: str = "sa-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket: str = "agroia-reports-dev"

    # ── APIs externas ──
    ideam_api_url: str = ""
    ideam_api_key: str = ""
    copernicus_api_url: str = ""
    google_maps_api_key: str = ""

    # ── Observabilidad ──
    log_level: str = "INFO"
    environment: str = "development"


@lru_cache()
def get_settings() -> Settings:
    """Retorna la configuración cacheada (singleton)."""
    return Settings()
