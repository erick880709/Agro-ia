"""Middleware de seguridad OWASP + logging de auditoría.

Aplica cabeceras HTTP de seguridad, registra operaciones sensibles
en logs de auditoría para cumplimiento Ley 1581/2012.
"""

import time
import uuid
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from agroia.logging import get_logger

logger = get_logger(__name__)

# ── Cabeceras de seguridad OWASP ──
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(self)",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Agrega cabeceras de seguridad OWASP a todas las respuestas."""

    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Registra operaciones sensibles en logs de auditoría.

    Cumple con Ley 1581/2012: trazabilidad de acceso a datos personales.
    """

    SENSITIVE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    SENSITIVE_PATHS = {"/api/v1/recomendaciones", "/api/v1/iot/ingest"}

    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed = time.time() - start

        # Solo auditar operaciones sensibles
        if request.method in self.SENSITIVE_METHODS and any(
            request.url.path.startswith(p) for p in self.SENSITIVE_PATHS
        ):
            logger.info(
                "audit",
                event="api_access",
                method=request.method,
                path=request.url.path,
                client_ip=request.client.host if request.client else "unknown",
                status_code=response.status_code,
                elapsed_ms=round(elapsed * 1000),
                timestamp=datetime.now(timezone.utc).isoformat(),
                audit_id=uuid.uuid4().hex,
            )

        return response
