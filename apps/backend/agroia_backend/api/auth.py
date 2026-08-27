"""Autenticación demo contra la tabla usuarios (MVP).

Login real contra los hashes de `usuarios.password_hash`. El Auth Service
(JWT/OAuth2) reemplazará este endpoint cuando se despliegue.
"""


from agroia.database import async_session_factory
from agroia.logging import get_logger
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from agroia_backend.models.usuario import Usuario
from agroia_backend.services.auditoria import auditar_y_commit
from agroia_backend.services.auth_utils import verify_password

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = ""


@router.post("/login")
async def login(
    body: LoginRequest,
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Valida email/contraseña y devuelve los datos de sesión del usuario."""
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

        await auditar_y_commit(
            db,
            usuario_email=email,
            usuario_nombre=usuario.nombre,
            rol=usuario.rol.value,
            accion="auth.login",
            entidad="auth",
            entidad_id=str(usuario.id),
        )

    logger.info("login_ok", email=email, rol=usuario.rol.value)
    return {
        "id": str(usuario.id),
        "nombre": usuario.nombre,
        "email": usuario.email,
        "rol": usuario.rol.value,
        "activo": usuario.activo,
    }
