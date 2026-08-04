"""Middleware de tenant (multi-tenancy) para RLS en PostgreSQL.

Inyecta el tenant_id del usuario autenticado en la configuración
de sesión de PostgreSQL para que las políticas RLS funcionen.
"""

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware que configura el tenant_id en la sesión de BD."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extraer tenant_id del token JWT (inyectado por AuthMiddleware)
        tenant_id = getattr(request.state, "tenant_id", None)

        if tenant_id:
            # Guardar en request state para uso en la app
            request.state.tenant_id = tenant_id

        response = await call_next(request)
        return response


async def set_tenant_context(db: AsyncSession, tenant_id: str) -> None:
    """Configura el tenant_id en la sesión PostgreSQL para RLS."""
    await db.execute(
        text("SELECT set_config('app.current_tenant', :tenant_id, false)"),
        {"tenant_id": str(tenant_id)},
    )
