"""Manejo centralizado de errores para la API.

Define excepciones de dominio y un handler global que las traduce
a respuestas HTTP estructuradas con el formato estándar de AgroIA.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class AgroIAError(Exception):
    """Excepción base de dominio de AgroIA."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AgroIAError):
    """Recurso no encontrado."""

    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, code="NOT_FOUND", status_code=404)


class ValidationError(AgroIAError):
    """Error de validación de negocio."""

    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422)


class UnauthorizedError(AgroIAError):
    """No autenticado."""

    def __init__(self, message: str = "No autenticado"):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)


class ForbiddenError(AgroIAError):
    """No autorizado (RBAC)."""

    def __init__(self, message: str = "Acceso denegado"):
        super().__init__(message, code="FORBIDDEN", status_code=403)


class ConflictError(AgroIAError):
    """Conflicto de estado (ej. recurso duplicado)."""

    def __init__(self, message: str):
        super().__init__(message, code="CONFLICT", status_code=409)


class InsufficientDataError(AgroIAError):
    """Datos insuficientes para generar una recomendación."""

    def __init__(self, missing_vars: list[str]):
        msg = f"Datos insuficientes. Variables faltantes: {', '.join(missing_vars)}"
        super().__init__(msg, code="INSUFFICIENT_DATA", status_code=422)
        self.missing_vars = missing_vars


# ── Mapeo de excepciones a HTTP ──

ERROR_MAP = {
    NotFoundError: HTTP_404_NOT_FOUND,
    ValidationError: HTTP_422_UNPROCESSABLE_ENTITY,
    UnauthorizedError: HTTP_401_UNAUTHORIZED,
    ForbiddenError: HTTP_403_FORBIDDEN,
    ConflictError: HTTP_409_CONFLICT,
    InsufficientDataError: HTTP_422_UNPROCESSABLE_ENTITY,
}


async def agroia_error_handler(request: Request, exc: AgroIAError) -> JSONResponse:
    """Handler global que convierte AgroIAError → JSONResponse estructurada."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


def register_error_handlers(app):
    """Registra todos los handlers de error de AgroIA en la app FastAPI."""
    for exc_class in ERROR_MAP:
        app.add_exception_handler(exc_class, agroia_error_handler)
    app.add_exception_handler(AgroIAError, agroia_error_handler)
