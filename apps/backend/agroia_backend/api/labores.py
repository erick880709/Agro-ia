"""API de labores / órdenes de trabajo (ejecución del plan agronómico).

Convierte las acciones del diagnóstico en tareas individuales con
trazabilidad completa: estado, responsable, fechas programada/ejecución
y observaciones del operario.
"""

import uuid as uuid_mod
from datetime import date, datetime, timezone

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.finca import Finca
from agroia_backend.models.labor import Labor
from agroia_backend.models.lote import Lote
from agroia_backend.models.recomendacion import Recomendacion
from agroia_backend.services.acceso import verificar_acceso_finca
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["labores"])

ROL_ADMIN = {"admin", "administrador"}
ROL_EXPERTOS = {"admin", "administrador", "agronomo", "agrónomo"}

_PALABRAS = {
    "Enmienda": ("cal", "encalado", "yeso", "enmienda", "dolomit"),
    "Riego": ("riego", "agua", "lavar", "humedad"),
    "Control Fitosanitario": ("fungicida", "plaga", "insecticida", "herbicida", "enfermedad", "fitosanitario"),
}


def _inferir_tipo(texto: str) -> str:
    t = (texto or "").lower()
    for tipo, palabras in _PALABRAS.items():
        if any(p in t for p in palabras):
            return tipo
    return "Fertilización"


class GenerarLaboresRequest(BaseModel):
    acciones: list[dict] = Field(..., min_length=1, max_length=50)
    fecha_programada: date | None = None
    responsable_id: str | None = None


class ActualizarLaborRequest(BaseModel):
    estado: str | None = Field(None, pattern="^(Pendiente|En Progreso|Completada|Cancelada)$")
    fecha_programada: date | None = None
    fecha_ejecucion: date | None = None
    responsable_id: str | None = None
    observaciones_ejecucion: str | None = Field(None, max_length=4000)


def _exigir_rol(rol: str | None, permitidos: set[str], mensaje: str) -> str:
    rol_norm = (rol or "").strip().lower()
    if rol_norm not in permitidos:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE", "message": mensaje,
        })
    return rol_norm


def _labor_a_dict(labor) -> dict:
    return {
        "id": str(labor.id),
        "lote_id": str(labor.lote_id),
        "recomendacion_id": str(labor.recomendacion_id) if labor.recomendacion_id else None,
        "titulo": labor.titulo,
        "tipo": labor.tipo,
        "producto": labor.producto,
        "dosis_kg_ha": labor.dosis_kg_ha,
        "fecha_programada": labor.fecha_programada.isoformat() if labor.fecha_programada else None,
        "fecha_ejecucion": labor.fecha_ejecucion.isoformat() if labor.fecha_ejecucion else None,
        "responsable_id": str(labor.responsable_id) if labor.responsable_id else None,
        "estado": labor.estado,
        "observaciones_ejecucion": labor.observaciones_ejecucion,
        "created_at": labor.created_at.isoformat() if labor.created_at else None,
    }


async def _lote_principal(db, finca_uuid) -> Lote | None:
    return (
        await db.execute(
            select(Lote)
            .where(Lote.finca_id == finca_uuid, Lote.activo.is_(True))
            .order_by(Lote.created_at)
            .limit(1)
        )
    ).scalars().first()


@router.post("/fincas/{finca_id}/labores/generar", status_code=201)
async def generar_labores(
    finca_id: str,
    body: GenerarLaboresRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Convierte las acciones del diagnóstico en órdenes de trabajo.

    Cada acción se vuelve una labor sobre el lote principal, con tipo
    inferido (Fertilización/Enmienda/Riego/Control Fitosanitario) y
    fecha programada (hoy por defecto). Se vincula a la recomendación
    más reciente de la finca si existe.
    """
    rol = _exigir_rol(
        x_user_role, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden generar órdenes de trabajo.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })
    finca = (
        await db.execute(select(Finca).where(Finca.id == finca_uuid))
    ).scalar_one_or_none()
    if finca is None:
        raise HTTPException(status_code=404, detail={
            "code": "FINCA_NOT_FOUND", "message": "La finca no está registrada.",
        })
    lote = await _lote_principal(db, finca_uuid)
    if lote is None:
        raise HTTPException(status_code=422, detail={
            "code": "NO_LOTES", "message": "La finca no tiene un lote activo.",
        })

    recomendacion = (
        await db.execute(
            select(Recomendacion)
            .where(Recomendacion.finca_id == finca_uuid)
            .order_by(Recomendacion.created_at.desc())
            .limit(1)
        )
    ).scalars().first()

    responsable_id = None
    if body.responsable_id:
        try:
            responsable_id = uuid_mod.UUID(body.responsable_id)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "RESPONSABLE_INVALIDO", "message": "responsable_id no es un UUID válido.",
            })

    fecha_programada = body.fecha_programada or datetime.now(timezone.utc).date()
    creadas = []
    for accion in body.acciones:
        variable = str(accion.get("variable") or accion.get("titulo") or "Labor").strip()
        detalle = str(accion.get("accion") or accion.get("detalle") or "").strip()
        titulo = f"{variable}: {detalle}" if detalle else variable
        labor = Labor(
            lote_id=lote.id,
            recomendacion_id=recomendacion.id if recomendacion else None,
            titulo=titulo[:200],
            tipo=_inferir_tipo(f"{variable} {detalle}"),
            fecha_programada=fecha_programada,
            responsable_id=responsable_id,
            estado="Pendiente",
        )
        db.add(labor)
        creadas.append(labor)
    await db.flush()

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="labor.generar",
        entidad="labor",
        detalle={
            "finca_id": str(finca.id),
            "finca": finca.nombre,
            "lote_id": str(lote.id),
            "creadas": len(creadas),
            "fecha_programada": fecha_programada.isoformat(),
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    logger.info("labores_generadas", finca_id=str(finca.id), creadas=len(creadas), rol=rol)
    return {
        "status": "created",
        "creadas": len(creadas),
        "labores": [_labor_a_dict(labor) for labor in creadas],
    }


@router.get("/fincas/{finca_id}/labores")
async def labores_de_finca(
    finca_id: str,
    estado: str | None = Query(None, pattern="^(Pendiente|En Progreso|Completada|Cancelada)$"),
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Lista las labores de la finca (más recientes primero)."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })
    lotes = (
        await db.execute(select(Lote.id).where(Lote.finca_id == finca_uuid))
    ).scalars().all()
    stmt = select(Labor).where(Labor.lote_id.in_(lotes)).order_by(
        Labor.fecha_programada.desc(), Labor.created_at.desc()
    )
    if estado:
        stmt = stmt.where(Labor.estado == estado)
    labores = (await db.execute(stmt.limit(100))).scalars().all()
    return {"data": [_labor_a_dict(labor) for labor in labores], "total": len(labores)}


@router.get("/fincas/{finca_id}/labores/pendientes-hoy")
async def labores_pendientes(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Tareas pendientes (hoy o vencidas) para el widget del Dashboard."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })
    hoy = datetime.now(timezone.utc).date()
    lotes = (
        await db.execute(select(Lote.id).where(Lote.finca_id == finca_uuid))
    ).scalars().all()
    labores = (
        await db.execute(
            select(Labor)
            .where(
                Labor.lote_id.in_(lotes),
                Labor.estado.in_(["Pendiente", "En Progreso"]),
                Labor.fecha_programada <= hoy,
            )
            .order_by(Labor.fecha_programada, Labor.created_at)
            .limit(10)
        )
    ).scalars().all()
    return {"data": [_labor_a_dict(labor) for labor in labores], "total": len(labores)}


@router.patch("/labores/{labor_id}")
async def actualizar_labor(
    labor_id: str,
    body: ActualizarLaborRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Actualiza estado/ejecución de una labor. Admin/Agrónomo."""
    rol = _exigir_rol(
        x_user_role, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden actualizar labores.",
    )
    try:
        labor_uuid = uuid_mod.UUID(labor_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "LABOR_INVALIDA", "message": "labor_id no es un UUID válido.",
        })
    labor = (
        await db.execute(select(Labor).where(Labor.id == labor_uuid))
    ).scalar_one_or_none()
    if labor is None:
        raise HTTPException(status_code=404, detail={
            "code": "LABOR_NOT_FOUND", "message": "La labor no existe.",
        })

    cambios = body.model_dump(exclude_unset=True)
    if "responsable_id" in cambios and cambios["responsable_id"]:
        try:
            cambios["responsable_id"] = uuid_mod.UUID(cambios["responsable_id"])
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "RESPONSABLE_INVALIDO", "message": "responsable_id no es un UUID válido.",
            })
    if cambios.get("estado") == "Completada" and labor.fecha_ejecucion is None:
        labor.fecha_ejecucion = datetime.now(timezone.utc).date()
        cambios.pop("fecha_ejecucion", None)
    for campo, valor in cambios.items():
        setattr(labor, campo, valor)

    accion_audit = "labor.actualizar"
    if body.estado == "Completada":
        accion_audit = "labor.completar"
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion=accion_audit,
        entidad="labor",
        entidad_id=str(labor.id),
        detalle={
            "titulo": labor.titulo,
            "estado": labor.estado,
            "fecha_ejecucion": labor.fecha_ejecucion.isoformat() if labor.fecha_ejecucion else None,
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    await db.refresh(labor)
    logger.info("labor_actualizada", labor_id=str(labor.id), estado=labor.estado, rol=rol)
    return {"status": "updated", "labor": _labor_a_dict(labor)}


@router.delete("/labores/{labor_id}")
async def eliminar_labor(
    labor_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Elimina una orden de trabajo. Solo administrador."""
    rol = _exigir_rol(
        x_user_role, ROL_ADMIN,
        "Solo el rol administrador puede eliminar labores.",
    )
    try:
        labor_uuid = uuid_mod.UUID(labor_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "LABOR_INVALIDA", "message": "labor_id no es un UUID válido.",
        })
    labor = (
        await db.execute(select(Labor).where(Labor.id == labor_uuid))
    ).scalar_one_or_none()
    if labor is None:
        raise HTTPException(status_code=404, detail={
            "code": "LABOR_NOT_FOUND", "message": "La labor no existe.",
        })
    detalle = {"titulo": labor.titulo, "estado": labor.estado}
    await db.delete(labor)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="labor.eliminar",
        entidad="labor",
        entidad_id=str(labor_uuid),
        detalle=detalle,
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    logger.info("labor_eliminada", labor_id=str(labor_uuid), rol=rol)
    return {"status": "deleted", "labor_id": str(labor_uuid)}
