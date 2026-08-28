"""Autenticación con JWT (v3) — login, refresh, logout y datos del usuario.

Reemplaza el esquema demo de cabeceras confiadas por tokens:
- Login valida bcrypt contra `usuarios.password_hash` y emite
  `access_token` (8 h) + `refresh_token` (30 días, persistido como hash).
- Las cuentas demo usan las mismas credenciales (compatibilidad total).
- Cada login/refresh/logout queda auditado con IP y user-agent.
"""

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from agroia.database import async_session_factory
from agroia.logging import get_logger
from agroia_backend.models.usuario import Usuario
from agroia_backend.services.auditoria import registrar_auditoria
from agroia_backend.services.auth_utils import verify_password
from agroia_backend.services.jwt_auth import (
    AuthError,
    crear_tokens,
    refresh_valido,
    revocar_refresh,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = ""


class RefreshRequest(BaseModel):
    refresh_token: str


def _auditar(request: Request, db, *, accion: str, email: str, nombre: str, rol: str) -> None:
    """Registra en auditoría con IP y user-agent (el endpoint commitea)."""
    return registrar_auditoria(
        db,
        usuario_email=email,
        usuario_nombre=nombre,
        rol=rol,
        accion=accion,
        entidad="auth",
        entidad_id=email,
        ip=request.client.host if request.client else None,
        detalle={"user_agent": (request.headers.get("user-agent") or "")[:300]},
    )


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    """Valida email/contraseña y devuelve usuario + tokens JWT."""
    email = body.email.lower()
    async with async_session_factory() as db:
        usuario = (
            await db.execute(select(Usuario).where(Usuario.email == email))
        ).scalar_one_or_none()

        if usuario is None or not verify_password(body.password, usuario.password_hash):
            raise HTTPException(status_code=401, detail={
                "code": "CREDENCIALES_INVALIDAS",
                "message": "Email o contraseña incorrectos.",
            })

        if not usuario.activo:
            raise HTTPException(status_code=403, detail={
                "code": "USUARIO_INACTIVO",
                "message": "La cuenta está inactiva. Contacte al administrador.",
            })

        tokens = await crear_tokens(db, usuario)
        await _auditar(
            request, db,
            accion="auth.login",
            email=email,
            nombre=usuario.nombre,
            rol=usuario.rol.value,
        )
        await db.commit()

    logger.info("login_ok", email=email, rol=usuario.rol.value)
    return {
        "id": str(usuario.id),
        "nombre": usuario.nombre,
        "email": usuario.email,
        "rol": usuario.rol.value,
        "activo": usuario.activo,
        **tokens,
    }


@router.post("/refresh")
async def refresh(body: RefreshRequest, request: Request):
    """Rotación de refresh token: emite un par nuevo y revoca el anterior."""
    async with async_session_factory() as db:
        try:
            claims = await refresh_valido(db, body.refresh_token)
        except AuthError as e:
            raise HTTPException(status_code=401, detail={
                "code": e.code, "message": e.message,
            }) from None
        usuario = (
            await db.execute(select(Usuario).where(Usuario.id == claims["uid"]))
        ).scalar_one_or_none()
        if usuario is None or not usuario.activo:
            raise HTTPException(status_code=401, detail={
                "code": "USUARIO_INACTIVO",
                "message": "Usuario no encontrado o inactivo.",
            })
        await revocar_refresh(db, body.refresh_token)
        tokens = await crear_tokens(db, usuario)
        await _auditar(
            request, db,
            accion="auth.refresh",
            email=usuario.email,
            nombre=usuario.nombre,
            rol=usuario.rol.value,
        )
        await db.commit()

    logger.info("refresh_ok", email=usuario.email)
    return {
        "id": str(usuario.id),
        "nombre": usuario.nombre,
        "email": usuario.email,
        "rol": usuario.rol.value,
        **tokens,
    }


@router.post("/logout")
async def logout(request: Request, body: RefreshRequest | None = None):
    """Invalida el access token actual y revoca el refresh token si se envía."""
    from datetime import datetime, timedelta, timezone

    from agroia_backend.models.token_auth import TokenBlacklist

    usuario_ctx = getattr(request.state, "usuario", {})
    email = usuario_ctx.get("email") or (request.headers.get("x-user-email") or "")
    rol = usuario_ctx.get("rol") or (request.headers.get("x-user-role") or "")
    nombre = usuario_ctx.get("nombre") or (request.headers.get("x-user-nombre") or "")

    async with async_session_factory() as db:
        jti = usuario_ctx.get("jti")
        if jti:
            db.add(TokenBlacklist(
                jti=jti,
                tipo="access",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
            ))
        if body and body.refresh_token:
            await revocar_refresh(db, body.refresh_token)
        if email:
            await _auditar(
                request, db,
                accion="auth.logout",
                email=email,
                nombre=nombre,
                rol=rol,
            )
        await db.commit()

    return {"status": "ok"}


@router.get("/me")
async def me(
    request: Request,
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Datos del usuario autenticado (claims del token vía middleware)."""
    ctx = getattr(request.state, "usuario", {})
    email = (ctx.get("email") or x_user_email or "").lower()
    rol = ctx.get("rol") or x_user_role
    if not email:
        raise HTTPException(status_code=401, detail={
            "code": "UNAUTHORIZED", "message": "Sin identidad autenticada.",
        })
    async with async_session_factory() as db:
        usuario = (
            await db.execute(select(Usuario).where(Usuario.email == email))
        ).scalar_one_or_none()
    if usuario is None:
        raise HTTPException(status_code=404, detail={
            "code": "USUARIO_NOT_FOUND", "message": "Usuario no encontrado.",
        })
    return {
        "id": str(usuario.id),
        "nombre": usuario.nombre,
        "email": usuario.email,
        "rol": usuario.rol.value if rol is None else rol,
        "activo": usuario.activo,
    }
