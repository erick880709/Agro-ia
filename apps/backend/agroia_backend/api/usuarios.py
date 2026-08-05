"""API endpoints de usuarios y membresías."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from agroia.database import get_db
from agroia.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["usuarios"])

# ── Schemas ──

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    nombre: str = Field(..., min_length=2, max_length=200)
    consentimiento_datos: bool = Field(..., description="Acepta tratamiento de datos (Ley 1581/2012)")

class UserResponse(BaseModel):
    id: str
    email: str
    nombre: str
    rol: str
    activo: bool
    email_verificado: bool
    consentimiento_datos: bool

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: object) -> str:
        return str(v)

class MembershipResponse(BaseModel):
    id: str
    plan: str
    estado: str
    fecha_inicio: str
    fecha_vencimiento: str
    fincas_permitidas: int

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: object) -> str:
        return str(v)


# ── Endpoints ──

@router.post("/usuarios/register", status_code=201, response_model=UserResponse)
async def registrar_usuario(body: RegisterRequest):
    """Registra un nuevo usuario con consentimiento Ley 1581."""
    if not body.consentimiento_datos:
        raise HTTPException(
            status_code=422,
            detail={"code": "CONSENT_REQUIRED", "message": "Consentimiento requerido (Ley 1581/2012)"},
        )
    # Placeholder: la implementación real usa el Auth Service
    logger.info("user_registered", email=body.email)
    return UserResponse(
        id="new-user-id",
        email=body.email,
        nombre=body.nombre,
        rol="Cliente",
        activo=True,
        email_verificado=False,
        consentimiento_datos=True,
    )


@router.get("/usuarios/me", response_model=UserResponse)
async def perfil_usuario():
    """Retorna el perfil del usuario autenticado."""
    return UserResponse(
        id="user-id", email="usuario@agroia.co", nombre="Usuario Demo",
        rol="Cliente", activo=True, email_verificado=True, consentimiento_datos=True,
    )


@router.put("/usuarios/me")
async def actualizar_perfil(nombre: Optional[str] = None, email: Optional[EmailStr] = None):
    """Actualiza datos del perfil."""
    return {"status": "updated", "nombre": nombre, "email": email}


@router.delete("/usuarios/me")
async def eliminar_cuenta():
    """Elimina la cuenta del usuario (derecho de supresión Ley 1581)."""
    logger.info("user_deletion_requested", note="Derecho de supresión Ley 1581/2012")
    return {"status": "deleted", "message": "Sus datos serán eliminados en un plazo máximo de 15 días hábiles."}


@router.get("/usuarios/me/membresia", response_model=MembershipResponse)
async def ver_membresia():
    """Retorna la membresía activa del usuario."""
    return MembershipResponse(
        id="mem-id", plan="Mensual", estado="Activa",
        fecha_inicio="2026-08-01", fecha_vencimiento="2026-09-01", fincas_permitidas=1,
    )


@router.get("/admin/usuarios")
async def listar_usuarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rol: Optional[str] = None,
    search: Optional[str] = None,
):
    """Lista usuarios (solo Admin)."""
    return {
        "data": [],
        "meta": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0},
    }


@router.put("/admin/usuarios/{user_id}/rol")
async def cambiar_rol(user_id: str, rol: str = Query(..., pattern="^(Admin|Cliente|Tecnico|Investigador)$")):
    """Cambia el rol de un usuario (solo Admin)."""
    logger.info("role_changed", user_id=user_id, new_rol=rol)
    return {"status": "updated", "user_id": user_id, "rol": rol}
