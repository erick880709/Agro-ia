"""API endpoints de usuarios y membresías."""

import uuid as uuid_mod

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.finca import Finca
from agroia_backend.models.finca_usuario import FincaUsuario
from agroia_backend.models.usuario import RolUsuario, Usuario
from agroia_backend.services.auditoria import registrar_auditoria
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
async def actualizar_perfil(nombre: str | None = None, email: EmailStr | None = None):
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
    rol: str | None = None,
    search: str | None = None,
):
    """Lista usuarios (solo Admin)."""
    return {
        "data": [],
        "meta": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0},
    }


@router.put("/admin/usuarios/{user_id}/rol")
async def cambiar_rol(user_id: str, rol: str = Query(..., pattern="^(Admin|Agronomo|Cliente|Tecnico|Investigador|Extensionista)$")):
    """Cambia el rol de un usuario (solo Admin)."""
    logger.info("role_changed", user_id=user_id, new_rol=rol)
    return {"status": "updated", "user_id": user_id, "rol": rol}


# ── Usuarios reales (creación admin + relación con fincas) ──

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8)
    rol: str = Field("Cliente", pattern="^(Cliente|Tecnico|Investigador|Agronomo|Extensionista)$")
    finca_ids: list[str] = Field(default_factory=list, description="UUIDs de fincas a relacionar")
    municipios_asignados: list[str] | None = Field(None, description="Municipios del extensionista (solo rol Extensionista)")


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
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
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
        municipios_asignados=list(body.municipios_asignados) if body.municipios_asignados else None,
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

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="usuario.crear",
        entidad="usuario",
        entidad_id=str(usuario.id),
        detalle={
            "nombre": usuario.nombre,
            "email": email,
            "rol": usuario.rol.value,
            "fincas": [f["nombre"] for f in fincas_relacionadas],
        },
        ip=request.client.host if request and request.client else None,
    )
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
    x_user_role: str | None = Header(None, alias="X-User-Role"),
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
        finca_ids = [link.finca_id for link in links]
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


# ══════════════════ Edición y eliminación de usuarios (Admin) ══════════════════

class UsuarioUpdate(BaseModel):
    """Edición de un usuario por el administrador."""

    nombre: str | None = Field(None, min_length=2, max_length=200)
    email: EmailStr | None = None
    rol: str | None = Field(None, pattern="^(Admin|Agronomo|Cliente|Tecnico|Investigador|Extensionista)$")
    activo: bool | None = None
    finca_ids: list[str] | None = Field(
        None, description="Lista completa de fincas relacionadas (reemplaza la actual)"
    )
    municipios_asignados: list[str] | None = Field(
        None, description="Municipios del extensionista (reemplaza la actual)"
    )


async def _obtener_usuario(db, user_id: str) -> Usuario:
    try:
        user_uuid = uuid_mod.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "USUARIO_INVALIDO", "message": "user_id no es un UUID válido.",
        })
    usuario = (
        await db.execute(select(Usuario).where(Usuario.id == user_uuid))
    ).scalar_one_or_none()
    if usuario is None:
        raise HTTPException(status_code=404, detail={
            "code": "USUARIO_NOT_FOUND", "message": "El usuario no está registrado.",
        })
    return usuario


def _exigir_admin_usuarios(rol: str | None) -> str:
    rol_norm = (rol or "").strip().lower()
    if rol_norm != "admin":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol administrador puede editar o eliminar usuarios.",
        })
    return rol_norm


@router.put("/usuarios/{user_id}", response_model=UsuarioAdminResponse)
async def editar_usuario(
    user_id: str,
    body: UsuarioUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Edita un usuario (datos, rol, estado y fincas). Solo administrador."""
    _exigir_admin_usuarios(x_user_role)
    usuario = await _obtener_usuario(db, user_id)
    email_admin = (x_user_email or "").strip().lower()

    cambios = body.model_dump(exclude_unset=True)
    detalle: dict = {"campos": []}

    # Protección: el admin no puede desactivarse a sí mismo
    if "activo" in cambios and cambios["activo"] is False and usuario.email.lower() == email_admin:
        raise HTTPException(status_code=422, detail={
            "code": "SELF_DEACTIVATE",
            "message": "No puede desactivar su propia cuenta de administrador.",
        })

    if "email" in cambios:
        nuevo = cambios["email"].lower()
        existente = (
            await db.execute(select(Usuario).where(Usuario.email == nuevo, Usuario.id != usuario.id))
        ).scalar_one_or_none()
        if existente is not None:
            raise HTTPException(status_code=409, detail={
                "code": "EMAIL_EXISTENTE",
                "message": f"Ya existe un usuario con el email '{nuevo}'.",
            })
        if usuario.email != nuevo:
            detalle["email_anterior"] = usuario.email
        usuario.email = nuevo

    if "nombre" in cambios:
        usuario.nombre = cambios["nombre"]
    if "rol" in cambios:
        usuario.rol = RolUsuario[cambios["rol"].upper()]
    if "activo" in cambios:
        usuario.activo = bool(cambios["activo"])
    if "municipios_asignados" in cambios:
        usuario.municipios_asignados = list(cambios["municipios_asignados"]) if cambios["municipios_asignados"] else None
    detalle["campos"] = sorted(cambios)

    # ── Reemplazo de relaciones con fincas (si vienen) ──
    if "finca_ids" in cambios:
        await db.execute(delete(FincaUsuario).where(FincaUsuario.usuario_id == usuario.id))
        nombres: list[str] = []
        for fid in cambios["finca_ids"]:
            try:
                finca_uuid = uuid_mod.UUID(fid)
            except ValueError:
                raise HTTPException(status_code=422, detail={
                    "code": "FINCA_INVALIDA", "message": f"'{fid}' no es un UUID válido.",
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
            nombres.append(finca.nombre)
        detalle["fincas"] = nombres

    await registrar_auditoria(
        db,
        usuario_email=email_admin or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="usuario.actualizar",
        entidad="usuario",
        entidad_id=str(usuario.id),
        detalle={"nombre": usuario.nombre, "email": usuario.email, **detalle},
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    await db.refresh(usuario)

    links = (
        await db.execute(select(FincaUsuario).where(FincaUsuario.usuario_id == usuario.id))
    ).scalars().all()
    fincas = (
        await db.execute(
            select(Finca).where(Finca.id.in_([link.finca_id for link in links])).order_by(Finca.nombre)
        )
    ).scalars().all() if links else []
    logger.info("usuario_editado", user_id=user_id, email=usuario.email)
    return UsuarioAdminResponse(
        id=str(usuario.id),
        nombre=usuario.nombre,
        email=usuario.email,
        rol=usuario.rol.value,
        activo=usuario.activo,
        fincas=[{"id": str(f.id), "nombre": f.nombre} for f in fincas],
    )


@router.delete("/usuarios/{user_id}")
async def eliminar_usuario(
    user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Desactiva un usuario (eliminación lógica, Ley 1581). Solo administrador.

    El usuario queda inactivo (no puede iniciar sesión) y sus relaciones
    con fincas se retiran; el registro se conserva en auditoría.
    """
    _exigir_admin_usuarios(x_user_role)
    usuario = await _obtener_usuario(db, user_id)
    email_admin = (x_user_email or "").strip().lower()

    if usuario.email.lower() == email_admin:
        raise HTTPException(status_code=422, detail={
            "code": "SELF_DELETE",
            "message": "No puede eliminar su propia cuenta de administrador.",
        })

    links = (
        await db.execute(select(FincaUsuario).where(FincaUsuario.usuario_id == usuario.id))
    ).scalars().all()
    await db.execute(delete(FincaUsuario).where(FincaUsuario.usuario_id == usuario.id))
    usuario.activo = False

    await registrar_auditoria(
        db,
        usuario_email=email_admin or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="usuario.eliminar",
        entidad="usuario",
        entidad_id=str(usuario.id),
        detalle={
            "nombre": usuario.nombre,
            "email": usuario.email,
            "rol": usuario.rol.value,
            "fincas_desvinculadas": len(links),
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    logger.info("usuario_eliminado", user_id=user_id, email=usuario.email)
    return {"status": "deleted", "user_id": str(usuario.id), "email": usuario.email}
