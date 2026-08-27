"""API de ciclos productivos por lote (`historial_ciclos_lote`).

Cada lote acumula un historial de ciclos (siembra → cosecha) con fechas,
resultados productivos, manejo agronómico estructurado (aplicaciones e
incidencias JSONB) y observaciones. Gestión: Admin/Agrónomo (crear/editar),
Admin (eliminar). Consulta: cualquier rol con acceso a la finca.
"""

import uuid as uuid_mod
from datetime import date

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.ciclo_lote import CicloLote
from agroia_backend.models.cultivo import Cultivo
from agroia_backend.models.lote import Lote
from agroia_backend.services.acceso import verificar_acceso_finca
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ciclos"])

ROL_ADMIN = {"admin", "administrador"}
ROL_EXPERTOS = {"admin", "administrador", "agronomo", "agrónomo"}
CALIDADES = {"Premium", "Estándar", "Rechazo"}
RIEGOS = {"Goteo", "Gravedad", "Aspersión", "Secano"}


class CicloCreate(BaseModel):
    cultivo_id: str = Field(..., description="UUID del cultivo del catálogo")
    fecha_siembra: date
    fecha_cosecha: date | None = None
    rendimiento_tn_ha: float | None = Field(None, ge=0, le=1_000, description="t/ha")
    calidad_cosecha: str | None = Field(None, max_length=20, description="Premium | Estándar | Rechazo")
    aplicaciones: list[dict] | None = Field(None, description="[{producto, dosis_kg_ha, fecha, tipo}, …]")
    incidencias: list[dict] | None = Field(None, description="[{plaga, severidad, fecha, control}, …]")
    practicas_riego: str | None = Field(None, max_length=50, description="Goteo | Gravedad | Aspersión | Secano")
    observaciones: str | None = Field(None, max_length=4000)


class CicloUpdate(BaseModel):
    cultivo_id: str | None = None
    fecha_siembra: date | None = None
    fecha_cosecha: date | None = None
    rendimiento_tn_ha: float | None = Field(None, ge=0, le=1_000)
    calidad_cosecha: str | None = Field(None, max_length=20)
    aplicaciones: list[dict] | None = None
    incidencias: list[dict] | None = None
    practicas_riego: str | None = Field(None, max_length=50)
    observaciones: str | None = Field(None, max_length=4000)


def _exigir_rol(rol: str | None, permitidos: set[str], mensaje: str) -> str:
    rol_norm = (rol or "").strip().lower()
    if rol_norm not in permitidos:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE", "message": mensaje,
        })
    return rol_norm


async def _obtener_lote(db, finca_id: str, lote_id: str) -> Lote:
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
        lote_uuid = uuid_mod.UUID(lote_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "LOTE_INVALIDO", "message": "finca_id o lote_id no es un UUID válido.",
        })
    lote = (
        await db.execute(
            select(Lote).where(Lote.id == lote_uuid, Lote.finca_id == finca_uuid)
        )
    ).scalar_one_or_none()
    if lote is None:
        raise HTTPException(status_code=404, detail={
            "code": "LOTE_NOT_FOUND",
            "message": "El lote no pertenece a esta finca o no existe.",
        })
    return lote


async def _cultivo_nombre(db, cultivo_id) -> str:
    try:
        cultivo_uuid = uuid_mod.UUID(str(cultivo_id))
    except ValueError:
        return str(cultivo_id)
    cultivo = (
        await db.execute(select(Cultivo).where(Cultivo.id == cultivo_uuid))
    ).scalar_one_or_none()
    return cultivo.nombre if cultivo is not None else str(cultivo_id)


def _ciclo_a_dict(c, cultivo_nombre: str | None = None) -> dict:
    return {
        "id": str(c.id),
        "lote_id": str(c.lote_id),
        "cultivo_id": str(c.cultivo_id),
        "cultivo_nombre": cultivo_nombre,
        "fecha_siembra": c.fecha_siembra.isoformat() if c.fecha_siembra else None,
        "fecha_cosecha": c.fecha_cosecha.isoformat() if c.fecha_cosecha else None,
        "rendimiento_tn_ha": float(c.rendimiento_tn_ha) if c.rendimiento_tn_ha is not None else None,
        "calidad_cosecha": c.calidad_cosecha,
        "aplicaciones": c.aplicaciones or [],
        "incidencias": c.incidencias or [],
        "practicas_riego": c.practicas_riego,
        "observaciones": c.observaciones,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


async def _validar_cultivo(db, cultivo_id: str) -> None:
    try:
        cultivo_uuid = uuid_mod.UUID(cultivo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "CULTIVO_INVALIDO", "message": "cultivo_id no es un UUID válido.",
        })
    cultivo = (
        await db.execute(select(Cultivo).where(Cultivo.id == cultivo_uuid))
    ).scalar_one_or_none()
    if cultivo is None:
        raise HTTPException(status_code=404, detail={
            "code": "CULTIVO_NOT_FOUND", "message": "El cultivo no está registrado en el catálogo.",
        })


@router.get("/fincas/{finca_id}/lotes/{lote_id}/ciclos")
async def ciclos_de_lote(
    finca_id: str,
    lote_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Historial de ciclos productivos de un lote (más reciente primero)."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    lote = await _obtener_lote(db, finca_id, lote_id)

    ciclos = (
        await db.execute(
            select(CicloLote)
            .where(CicloLote.lote_id == lote.id)
            .order_by(CicloLote.fecha_siembra.desc(), CicloLote.created_at.desc())
        )
    ).scalars().all()

    nombres: dict[str, str] = {}
    data = []
    for c in ciclos:
        key = str(c.cultivo_id)
        if key not in nombres:
            nombres[key] = await _cultivo_nombre(db, c.cultivo_id)
        data.append(_ciclo_a_dict(c, nombres[key]))
    return {"data": data, "total": len(data)}


@router.post("/fincas/{finca_id}/lotes/{lote_id}/ciclos", status_code=201)
async def crear_ciclo(
    finca_id: str,
    lote_id: str,
    body: CicloCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Registra un ciclo productivo en el lote. Admin/Agrónomo."""
    rol = _exigir_rol(
        x_user_role, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden registrar ciclos.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    lote = await _obtener_lote(db, finca_id, lote_id)
    await _validar_cultivo(db, body.cultivo_id)

    if body.fecha_cosecha and body.fecha_cosecha < body.fecha_siembra:
        raise HTTPException(status_code=422, detail={
            "code": "FECHAS_INVALIDAS",
            "message": "La fecha de cosecha no puede ser anterior a la de siembra.",
        })
    if body.calidad_cosecha and body.calidad_cosecha not in CALIDADES:
        raise HTTPException(status_code=422, detail={
            "code": "CALIDAD_INVALIDA",
            "message": f"Calidad debe ser una de: {', '.join(sorted(CALIDADES))}.",
        })
    if body.practicas_riego and body.practicas_riego not in RIEGOS:
        raise HTTPException(status_code=422, detail={
            "code": "RIEGO_INVALIDO",
            "message": f"Prácticas de riego debe ser una de: {', '.join(sorted(RIEGOS))}.",
        })

    ciclo = CicloLote(
        lote_id=lote.id,
        cultivo_id=uuid_mod.UUID(body.cultivo_id),
        fecha_siembra=body.fecha_siembra,
        fecha_cosecha=body.fecha_cosecha,
        rendimiento_tn_ha=body.rendimiento_tn_ha,
        calidad_cosecha=body.calidad_cosecha,
        aplicaciones=body.aplicaciones or [],
        incidencias=body.incidencias or [],
        practicas_riego=body.practicas_riego,
        observaciones=body.observaciones,
    )
    db.add(ciclo)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="ciclo.crear",
        entidad="ciclo",
        entidad_id=str(ciclo.id),
        detalle={
            "lote_id": str(lote.id),
            "lote": lote.nombre,
            "cultivo": await _cultivo_nombre(db, body.cultivo_id),
            "fecha_siembra": body.fecha_siembra.isoformat(),
            "rendimiento_tn_ha": body.rendimiento_tn_ha,
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    await db.refresh(ciclo)
    logger.info("ciclo_creado", ciclo_id=str(ciclo.id), lote_id=str(lote.id), rol=rol)
    return {
        "status": "created",
        "ciclo": _ciclo_a_dict(ciclo, await _cultivo_nombre(db, ciclo.cultivo_id)),
    }


@router.patch("/fincas/{finca_id}/lotes/{lote_id}/ciclos/{ciclo_id}")
async def editar_ciclo(
    finca_id: str,
    lote_id: str,
    ciclo_id: str,
    body: CicloUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Edita un ciclo productivo. Admin/Agrónomo."""
    rol = _exigir_rol(
        x_user_role, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden editar ciclos.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    lote = await _obtener_lote(db, finca_id, lote_id)

    try:
        ciclo_uuid = uuid_mod.UUID(ciclo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "CICLO_INVALIDO", "message": "ciclo_id no es un UUID válido.",
        })
    ciclo = (
        await db.execute(
            select(CicloLote).where(CicloLote.id == ciclo_uuid, CicloLote.lote_id == lote.id)
        )
    ).scalar_one_or_none()
    if ciclo is None:
        raise HTTPException(status_code=404, detail={
            "code": "CICLO_NOT_FOUND", "message": "El ciclo no pertenece a este lote o no existe.",
        })

    cambios = body.model_dump(exclude_unset=True)
    if "cultivo_id" in cambios and cambios["cultivo_id"]:
        await _validar_cultivo(db, cambios["cultivo_id"])
        cambios["cultivo_id"] = uuid_mod.UUID(cambios["cultivo_id"])
    if "fecha_siembra" in cambios and cambios["fecha_siembra"]:
        nueva_siembra = cambios["fecha_siembra"]
        cosecha = cambios.get("fecha_cosecha", ciclo.fecha_cosecha)
        if cosecha and cosecha < nueva_siembra:
            raise HTTPException(status_code=422, detail={
                "code": "FECHAS_INVALIDAS",
                "message": "La fecha de cosecha no puede ser anterior a la de siembra.",
            })
    if cambios.get("calidad_cosecha") and cambios["calidad_cosecha"] not in CALIDADES:
        raise HTTPException(status_code=422, detail={
            "code": "CALIDAD_INVALIDA",
            "message": f"Calidad debe ser una de: {', '.join(sorted(CALIDADES))}.",
        })
    if cambios.get("practicas_riego") and cambios["practicas_riego"] not in RIEGOS:
        raise HTTPException(status_code=422, detail={
            "code": "RIEGO_INVALIDO",
            "message": f"Prácticas de riego debe ser una de: {', '.join(sorted(RIEGOS))}.",
        })
    for campo, valor in cambios.items():
        setattr(ciclo, campo, valor)

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="ciclo.actualizar",
        entidad="ciclo",
        entidad_id=str(ciclo.id),
        detalle={
            "lote_id": str(lote.id),
            "lote": lote.nombre,
            "fecha_siembra": ciclo.fecha_siembra.isoformat(),
            "campos": sorted(cambios),
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    await db.refresh(ciclo)
    logger.info("ciclo_editado", ciclo_id=str(ciclo.id), lote_id=str(lote.id), rol=rol)
    return {
        "status": "updated",
        "ciclo": _ciclo_a_dict(ciclo, await _cultivo_nombre(db, ciclo.cultivo_id)),
    }


@router.delete("/fincas/{finca_id}/lotes/{lote_id}/ciclos/{ciclo_id}")
async def eliminar_ciclo(
    finca_id: str,
    lote_id: str,
    ciclo_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Elimina un ciclo del historial del lote. Solo administrador."""
    rol = _exigir_rol(
        x_user_role, ROL_ADMIN,
        "Solo el rol administrador puede eliminar ciclos.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    lote = await _obtener_lote(db, finca_id, lote_id)

    try:
        ciclo_uuid = uuid_mod.UUID(ciclo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "CICLO_INVALIDO", "message": "ciclo_id no es un UUID válido.",
        })
    ciclo = (
        await db.execute(
            select(CicloLote).where(CicloLote.id == ciclo_uuid, CicloLote.lote_id == lote.id)
        )
    ).scalar_one_or_none()
    if ciclo is None:
        raise HTTPException(status_code=404, detail={
            "code": "CICLO_NOT_FOUND", "message": "El ciclo no pertenece a este lote o no existe.",
        })

    detalle = {
        "lote_id": str(lote.id),
        "lote": lote.nombre,
        "cultivo": await _cultivo_nombre(db, ciclo.cultivo_id),
        "fecha_siembra": ciclo.fecha_siembra.isoformat() if ciclo.fecha_siembra else None,
    }
    await db.delete(ciclo)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="ciclo.eliminar",
        entidad="ciclo",
        entidad_id=str(ciclo_uuid),
        detalle=detalle,
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    logger.info("ciclo_eliminado", ciclo_id=str(ciclo_uuid), lote_id=str(lote.id), rol=rol)
    return {"status": "deleted", "ciclo_id": str(ciclo_uuid)}
