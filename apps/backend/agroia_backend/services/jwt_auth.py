"""Autenticación JWT (HS256/RS256) + middleware que protege la API.

Reemplaza el esquema demo de cabeceras confiadas por tokens:
- `POST /auth/login` emite `access_token` (8 h) y `refresh_token` (30 días).
- El middleware valida el Bearer en cada request (excepto rutas públicas) y
  **sobrescribe** las cabeceras X-User-Role/X-User-Email/X-User-Nombre con las
  claims del token, de modo que los 35 routers siguen funcionando sin cambios.
- Fuera de producción (o con `AUTH_ALLOW_LEGACY_HEADERS=true`) se mantiene el
  esquema demo de cabeceras para desarrollo local.
"""

import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

from agroia.config import get_settings
from agroia.database import async_session_factory
from agroia.logging import get_logger
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt as jose_jwt
from jose.exceptions import ExpiredSignatureError, JWTError as JoseJWTError

from agroia_backend.models.token_auth import RefreshToken, TokenBlacklist

logger = get_logger(__name__)

settings = get_settings()

# Clave de desarrollo SOLO cuando no hay JWT_SECRET configurado (entornos locales).
_DEV_SECRET_FALLBACK = "agroia-dev-secret-2026-solo-entornos-locales-no-produccion"

RUTAS_PUBLICAS = {
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/sensor",
}
PREFIJOS_PUBLICOS = ("/docs", "/openapi.json", "/redoc", "/media")


class AuthError(Exception):
    """Token ausente, inválido o revocado."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _algoritmo_y_clave() -> tuple[str, str]:
    """Devuelve (algoritmo, clave). RS256 si existen las PEM; si no, HS256."""
    priv = settings.jwt_private_key_path
    pub = settings.jwt_public_key_path
    if priv and pub and os.path.isfile(priv) and os.path.isfile(pub):
        return "RS256", open(pub, encoding="utf-8").read()
    secret = settings.jwt_secret or os.getenv("JWT_SECRET") or ""
    if not secret:
        logger.warning(
            "jwt_sin_secreto_usando_dev_fallback",
            hint="Configurar JWT_SECRET (32+ caracteres) antes de producción.",
        )
        return "HS256", _DEV_SECRET_FALLBACK
    if len(secret) < 16:
        logger.warning("jwt_secret_corto", hint="Usar 32+ caracteres en producción.")
    return "HS256", secret


def _privada() -> str:
    """Clave privada para firmar (solo RS256)."""
    priv = settings.jwt_private_key_path
    if priv and os.path.isfile(priv):
        return open(priv, encoding="utf-8").read()
    return ""


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def _expiracion() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )


async def crear_tokens(db, usuario) -> dict:
    """Emite access + refresh para el usuario y persiste el refresh (hash)."""
    ahora = datetime.now(timezone.utc)
    access_exp = ahora + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    refresh_exp = ahora + timedelta(days=settings.jwt_refresh_token_expire_days)

    algoritmo, clave = _algoritmo_y_clave()
    if algoritmo == "RS256":
        clave = _privada()

    access_jti = uuid.uuid4().hex
    access_token = jose_jwt.encode(
        {
            "sub": usuario.email,
            "uid": str(usuario.id),
            "rol": usuario.rol.value,
            "nombre": usuario.nombre or "",
            "jti": access_jti,
            "type": "access",
            "exp": access_exp,
        },
        clave,
        algorithm=algoritmo,
    )

    refresh_jti = uuid.uuid4().hex
    refresh_token = jose_jwt.encode(
        {
            "sub": usuario.email,
            "uid": str(usuario.id),
            "jti": refresh_jti,
            "type": "refresh",
            "exp": refresh_exp,
        },
        clave,
        algorithm=algoritmo,
    )
    db.add(RefreshToken(
        usuario_id=usuario.id,
        token_hash=_hash_token(refresh_token),
        expires_at=refresh_exp,
    ))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
        "refresh_token": refresh_token,
        "access_jti": access_jti,
        "refresh_jti": refresh_jti,
    }


def decodificar_token(token: str, tipo: str = "access") -> dict:
    """Valida firma/expiración/type y devuelve las claims. Lanza AuthError."""
    algoritmo, clave = _algoritmo_y_clave()
    try:
        claims = jose_jwt.decode(token, clave, algorithms=[algoritmo])
    except ExpiredSignatureError:
        raise AuthError("TOKEN_EXPIRADO", "El token expiró. Use /auth/refresh.") from None
    except JoseJWTError:
        raise AuthError("TOKEN_INVALIDO", "Token inválido.") from None
    if claims.get("type") != tipo:
        raise AuthError("TIPO_TOKEN_INVALIDO", f"Se esperaba un token de tipo {tipo}.")
    return claims


async def token_revocado(db, jti: str) -> bool:
    from sqlalchemy import select

    fila = (
        await db.execute(select(TokenBlacklist.jti).where(TokenBlacklist.jti == jti))
    ).scalar_one_or_none()
    return fila is not None


async def refresh_valido(db, refresh_token: str) -> dict:
    """Valida refresh (firma, tipo, blacklist, hash en BD no revocado)."""
    from sqlalchemy import select

    claims = decodificar_token(refresh_token, tipo="refresh")
    hash_ = _hash_token(refresh_token)
    fila = (
        await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hash_))
    ).scalar_one_or_none()
    if fila is None or fila.revocado:
        raise AuthError("REFRESH_REVOCADO", "El refresh token fue revocado.")
    if await token_revocado(db, claims["jti"]):
        raise AuthError("REFRESH_REVOCADO", "El refresh token fue revocado.")
    return claims


async def revocar_refresh(db, refresh_token: str) -> None:
    """Revoca (hash en BD) y blacklistea el jti del refresh token."""
    from sqlalchemy import select

    try:
        claims = decodificar_token(refresh_token, tipo="refresh")
    except AuthError:
        return
    hash_ = _hash_token(refresh_token)
    fila = (
        await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hash_))
    ).scalar_one_or_none()
    if fila is not None and not fila.revocado:
        fila.revocado = True
    exp = datetime.fromtimestamp(claims.get("exp", 0), tz=timezone.utc)
    db.add(TokenBlacklist(
        jti=claims["jti"],
        tipo="refresh",
        expires_at=exp,
    ))


def _es_publica(path: str) -> bool:
    return path in RUTAS_PUBLICAS or path.startswith(PREFIJOS_PUBLICOS)


def _permitir_legacy() -> bool:
    if settings.auth_allow_legacy_headers is not None:
        return settings.auth_allow_legacy_headers
    return settings.environment != "production"


def _sobrescribir_cabeceras(scope: dict, rol: str | None, email: str | None, nombre: str | None) -> None:
    """Reemplaza las cabeceras de identidad en el scope (anti-suplantación)."""
    headers = [
        (k, v)
        for k, v in scope.get("headers", [])
        if k.decode("latin-1").lower()
        not in {"x-user-role", "x-user-email", "x-user-nombre"}
    ]
    if rol:
        headers.append((b"x-user-role", rol.encode("latin-1")))
    if email:
        headers.append((b"x-user-email", email.encode("latin-1")))
    if nombre:
        headers.append((b"x-user-nombre", nombre.encode("latin-1")))
    scope["headers"] = headers


async def middleware_autenticacion(request: Request, call_next):
    """Protege la API con JWT. Rutas públicas y estáticos pasan sin token."""
    path = request.url.path
    if request.method == "OPTIONS" or _es_publica(path) or not path.startswith("/api"):
        return await call_next(request)

    authz = request.headers.get("authorization") or ""
    if authz.lower().startswith("bearer "):
        token = authz[7:].strip()
        try:
            claims = decodificar_token(token, tipo="access")
        except AuthError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": {"code": e.code, "message": e.message}},
            )
        async with async_session_factory() as db:
            if await token_revocado(db, claims.get("jti", "")):
                return JSONResponse(
                    status_code=401,
                    content={"detail": {
                        "code": "UNAUTHORIZED",
                        "message": "El token fue revocado (logout).",
                    }},
                )
        request.state.usuario = {
            "email": claims.get("sub"),
            "uid": claims.get("uid"),
            "rol": claims.get("rol"),
            "nombre": claims.get("nombre"),
            "jti": claims.get("jti"),
        }
        _sobrescribir_cabeceras(
            request.scope,
            claims.get("rol"),
            claims.get("sub"),
            claims.get("nombre"),
        )
        return await call_next(request)

    # Sin Bearer: solo se permiten las cabeceras demo en entornos no-producción
    rol = request.headers.get("x-user-role")
    if _permitir_legacy() and rol:
        return await call_next(request)

    return JSONResponse(
        status_code=401,
        content={"detail": {
            "code": "UNAUTHORIZED",
            "message": "Autenticación requerida (Authorization: Bearer).",
        }},
    )


async def limpiar_tokens_expirados(db) -> int:
    """Elimina jtis vencidos y refresh tokens expirados (tarea diaria)."""
    from sqlalchemy import delete

    ahora = datetime.now(timezone.utc)
    r1 = await db.execute(
        delete(TokenBlacklist).where(TokenBlacklist.expires_at < ahora)
    )
    r2 = await db.execute(
        delete(RefreshToken).where(
            RefreshToken.expires_at < ahora - timedelta(days=1)
        )
    )
    return (r1.rowcount or 0) + (r2.rowcount or 0)
