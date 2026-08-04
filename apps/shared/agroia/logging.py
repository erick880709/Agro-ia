"""Configuración de logging estructurado con structlog.

Formato JSON en producción, formato legible (console) en desarrollo.
Integrable con CloudWatch en AWS.
"""

import logging
import sys

import structlog

from agroia.config import get_settings


def setup_logging() -> None:
    """Configura structlog para toda la aplicación."""
    settings = get_settings()

    # Configurar nivel base de logging estándar
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # En desarrollo: consola legible; en producción: JSON
            structlog.dev.ConsoleRenderer()
            if settings.environment == "development"
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__):
    """Retorna un logger estructurado."""
    return structlog.get_logger(name)
