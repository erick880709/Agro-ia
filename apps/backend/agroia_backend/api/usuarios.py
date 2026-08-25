"""API endpoints de usuarios y membresías."""

import uuid as uuid_mod
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia.database import get_db
from agroia.logging import get_logger
from agroia_backend.models.finca import Finca
from agroia_backend.models.finca_usuario import FincaUsuario
from agroia_backend.models.usuario import RolUsuario, Usuario
from agroia_backend.services.auth_utils import hash_password

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


# ── Usuarios reales (creación admin + relación con fincas) ──

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8)
    rol: str = Field("Cliente", pattern="^(Cliente|Tecnico|Investigador)$")
    finca_ids: list[str] = Field(default_factory=list, description="UUIDs de fincas a relacionar")


class UsuarioAdminResponse(BaseModel):
    id: str
    nombre: str
    email: str
    rol: str
    activo: bool
    fincas: list[dict] = []

    @field_validator("id", mode="before")
    @classmethod
    def _coerce(cls, v: object) -> str:
        return str(v)


def _hash_password(password: str) -> str:
    # Delegado al helper compartido (mismo esquema que valida el login)
    return hash_password(password)


@router.post("/usuarios", status_code=201, response_model=UsuarioAdminResponse)
async def crear_usuario(
    body: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """Crea un usuario (cliente) relacionado a una o más fincas. Solo Admin."""
    rol = (x_user_role or "").strip().lower()
    if rol != "admin":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol administrador puede crear usuarios.",
        })

    email = body.email.lower()
    existente = (
        await db.execute(select(Usuario).where(Usuario.email == email))
    ).scalar_one_or_none()
    if existente is not None:
        raise HTTPException(status_code=409, detail={
            "code": "EMAIL_EXISTENTE",
            "message": f"Ya existe un usuario con el email '{email}'.",
        })

    usuario = Usuario(
        id=uuid_mod.uuid4(),
        tenant_id=uuid_mod.uuid4(),  # FIXME MVP: tenant del admin que crea
        email=email,
        password_hash=_hash_password(body.password),
        nombre=body.nombre,
        rol=RolUsuario[body.rol.upper()] if body.rol.upper() in RolUsuario.__members__ else RolUsuario.CLIENTE,
        activo=True,
        consentimiento_datos=True,
        email_verificado=False,
    )
    db.add(usuario)
    await db.flush()

    fincas_relacionadas: list[dict] = []
    for fid in body.finca_ids:
        try:
            finca_uuid = uuid_mod.UUID(fid)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "FINCA_INVALIDA",
                "message": f"'{fid}' no es un UUID válido.",
            })
        finca = (
            await db.execute(select(Finca).where(Finca.id == finca_uuid))
        ).scalar_one_or_none()
        if finca is None:
            raise HTTPException(status_code=404, detail={
                "code": "FINCA_NOT_FOUND",
                "message": f"La finca '{fid}' no está registrada.",
            })
        db.add(FincaUsuario(finca_id=finca_uuid, usuario_id=usuario.id))
        fincas_relacionadas.append({"id": str(finca.id), "nombre": finca.nombre})

    await db.commit()
    logger.info("usuario_creado", email=email, rol=body.rol, fincas=len(fincas_relacionadas))
    return UsuarioAdminResponse(
        id=str(usuario.id),
        nombre=usuario.nombre,
        email=usuario.email,
        rol=usuario.rol.value,
        activo=usuario.activo,
        fincas=fincas_relacionadas,
    )


@router.get("/usuarios", response_model=list[UsuarioAdminResponse])
async def listar_usuarios_reales(
    db: AsyncSession = Depends(get_db),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """Lista usuarios con sus fincas relacionadas. Solo Admin."""
    rol = (x_user_role or "").strip().lower()
    if rol != "admin":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol administrador puede listar usuarios.",
        })

    usuarios = (await db.execute(
        select(Usuario).order_by(Usuario.created_at)
    )).scalars().all()

    resultado = []
    for u in usuarios:
        links = (
            await db.execute(
                select(FincaUsuario).where(FincaUsuario.usuario_id == u.id)
            )
        ).scalars().all()
        finca_ids = [l.finca_id for l in links]
        fincas = []
        if finca_ids:
            fincas = (
                await db.execute(
                    select(Finca).where(Finca.id.in_(finca_ids)).order_by(Finca.nombre)
                )
            ).scalars().all()
        resultado.append(UsuarioAdminResponse(
            id=str(u.id),
            nombre=u.nombre,
            email=u.email,
            rol=u.rol.value,
            activo=u.activo,
            fincas=[{"id": str(f.id), "nombre": f.nombre} for f in fincas],
        ))
    return resultado
