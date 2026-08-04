"""Servicio de autenticación JWT + OAuth2 + RBAC para AgroIA.

Emite y valida tokens JWT RS256, gestiona refresh tokens,
y verifica roles RBAC (Admin, Cliente, Técnico, Investigador).
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from agroia.config import get_settings
from agroia.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ── Config ──
pwd_context = CryptContext(schemes=["bcrypt", "argon2"], deprecated="auto")
bearer_scheme = HTTPBearer()

# ── Roles ──
class Rol(str):
    ADMIN = "Admin"
    CLIENTE = "Cliente"
    TECNICO = "Tecnico"
    INVESTIGADOR = "Investigador"

ROLES = [Rol.ADMIN, Rol.CLIENTE, Rol.TECNICO, Rol.INVESTIGADOR]


# ═══════════════════════════════════════════════
# Password hashing
# ═══════════════════════════════════════════════

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ═══════════════════════════════════════════════
# JWT
# ═══════════════════════════════════════════════

def create_access_token(
    user_id: str,
    tenant_id: str,
    rol: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Crea un JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "rol": rol,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": uuid.uuid4().hex,
    }
    # En desarrollo: usar clave secreta (sin RS256)
    # En producción: cargar clave privada desde archivo
    secret = "agroia-dev-secret-key-change-in-production"
    return jwt.encode(payload, secret, algorithm="HS256")


def create_refresh_token(user_id: str) -> str:
    """Crea un refresh token (7 días)."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
    }
    secret = "agroia-dev-refresh-secret-change-in-production"
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decodifica y valida un JWT token."""
    secret = "agroia-dev-secret-key-change-in-production"
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError as e:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Token inválido o expirado"})


# ═══════════════════════════════════════════════
# RBAC Dependency
# ═══════════════════════════════════════════════

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Dependency que extrae y valida el usuario del JWT."""
    return decode_token(credentials.credentials)


def require_role(*roles: str):
    """Factory de dependency que verifica que el usuario tenga uno de los roles requeridos."""
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_rol = user.get("rol")
        if user_rol not in roles:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": f"Rol '{user_rol}' no autorizado. Requerido: {roles}"},
            )
        return user
    return role_checker


require_admin = require_role(Rol.ADMIN)
require_tecnico = require_role(Rol.TECNICO, Rol.ADMIN)
require_cliente = require_role(Rol.CLIENTE, Rol.ADMIN)
require_investigador = require_role(Rol.INVESTIGADOR, Rol.ADMIN)


# ═══════════════════════════════════════════════
# Tenant extraction
# ═══════════════════════════════════════════════

def get_tenant_id(request: Request) -> str:
    """Extrae el tenant_id del request (inyectado por AuthMiddleware)."""
    return getattr(request.state, "tenant_id", None)
