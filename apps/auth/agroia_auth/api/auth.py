"""API endpoints de autenticación y usuarios."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from agroia.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    nombre: str = Field(..., min_length=2, max_length=200)
    consentimiento_datos: bool = Field(..., description="Consentimiento Ley 1581/2012")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """Autentica un usuario y retorna JWT access + refresh tokens."""
    from agroia_auth.auth_service import create_access_token, create_refresh_token

    # TODO: validar credenciales contra BD de usuarios (épica 008)
    logger.info("login_attempt", email=body.email)

    # Placeholder — usuarios reales en épica 008
    access = create_access_token("user-id", "tenant-id", "Cliente")
    refresh = create_refresh_token("user-id")

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    """Registra un nuevo usuario con consentimiento Ley 1581."""
    if not body.consentimiento_datos:
        raise HTTPException(
            status_code=422,
            detail={"code": "CONSENT_REQUIRED", "message": "Se requiere consentimiento para el tratamiento de datos personales (Ley 1581/2012)"},
        )
    logger.info("user_registered", email=body.email)
    return {"status": "registered", "email": body.email, "message": "Usuario registrado. Verifique su correo."}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str = Field(...)):
    """Renueva un access token usando un refresh token válido."""
    from agroia_auth.auth_service import create_access_token, decode_token

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Token inválido"})
        access = create_access_token(payload["sub"], "tenant-id", "Cliente")
        return TokenResponse(access_token=access, refresh_token=refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Refresh token inválido o expirado"})


@router.get("/me")
async def me():
    """Retorna información del usuario autenticado."""
    return {"id": "user-id", "email": "usuario@ejemplo.com", "rol": "Cliente", "tenant_id": "tenant-id"}
