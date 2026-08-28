"""API de comisiones de trabajo por finca (Admin) — órdenes de trabajo de campo."""

import uuid as uuid_mod
from datetime import date, datetime, timezone

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.comision import ESTADOS_COMISION, Comision, ComisionMiembro
from agroia_backend.models.equipo_trabajo import ROLES_EQUIPO, EquipoTrabajo
from agroia_backend.models.finca import Finca
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["comisiones"])

SERVICIOS_SUGERIDOS = (
    "muestreo_suelos", "recomendacion_siembra", "reporte_completo",
    "balance_hidrico", "trazabilidad_bpa", "otro",
)


def _exigir_admin(rol: str | None) -> str:
    rol_norm = (rol or "").strip().lower()
    if rol_norm != "admin":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol administrador puede gestionar comisiones.",
        })
    return rol_norm


class MiembroIn(BaseModel):
    empleado_id: str
    rol_en_comision: str = Field(..., description="instrumentador | cadenero_sensorista | chofer | agronomo")


class ComisionCreate(BaseModel):
    finca_id: str
    servicio: str | None = Field(None, max_length=60)
    fecha_asignacion: date
    fecha_inicio_tomas: date | None = None
    miembros: list[MiembroIn] = Field(..., min_length=2, max_length=30)
    valor_comision_cop: float | None = Field(None, ge=0)
    valor_cobro_servicio_cop: float | None = Field(None, ge=0)
    valor_validacion_cop: float | None = Field(None, ge=0)
    valor_plataforma_cop: float | None = Field(None, ge=0)
    observaciones: str | None = None


class ComisionUpdate(BaseModel):
    servicio: str | None = Field(None, max_length=60)
    fecha_asignacion: date | None = None
    fecha_inicio_tomas: date | None = None
    miembros: list[MiembroIn] | None = None
    valor_comision_cop: float | None = Field(None, ge=0)
    valor_cobro_servicio_cop: float | None = Field(None, ge=0)
    valor_validacion_cop: float | None = Field(None, ge=0)
    valor_plataforma_cop: float | None = Field(None, ge=0)
    observaciones: str | None = None


async def _obtener_comision(db, comision_id: str) -> Comision:
    try:
        cid = uuid_mod.UUID(comision_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "COMISION_INVALIDA", "message": "comision_id no es un UUID válido.",
        })
    comision = (
        await db.execute(select(Comision).where(Comision.id == cid))
    ).scalar_one_or_none()
    if comision is None:
        raise HTTPException(status_code=404, detail={
            "code": "COMISION_NOT_FOUND", "message": "La comisión no está registrada.",
        })
    return comision


async def _miembros_dict(db, comision_id) -> list[dict]:
    miembros = (
        await db.execute(
            select(ComisionMiembro, EquipoTrabajo)
            .join(EquipoTrabajo, EquipoTrabajo.id == ComisionMiembro.empleado_id)
            .where(ComisionMiembro.comision_id == comision_id, ComisionMiembro.activo.is_(True))
        )
    ).all()
    return [{
        "id": str(m[0].id),
        "empleado_id": str(m[0].empleado_id),
        "nombre": f"{m[1].nombres} {m[1].apellidos}".strip(),
        "rol_en_comision": m[0].rol_en_comision,
        "valor_dia_cop": float(m[1].valor_dia_cop) if m[1].valor_dia_cop is not None else None,
    } for m in miembros]


async def _comision_a_dict(db, c: Comision, con_miembros: bool = True) -> dict:
    finca = (
        await db.execute(select(Finca).where(Finca.id == c.finca_id))
    ).scalar_one_or_none()
    miembros = await _miembros_dict(db, c.id) if con_miembros else []
    dias = None
    if c.fecha_inicio_tomas and c.fecha_fin_tomas:
        dias = max(0, (c.fecha_fin_tomas - c.fecha_inicio_tomas).days + 1)
    costo_equipo = None
    if dias:
        suma = sum(m.get("valor_dia_cop") or 0 for m in miembros)
        if suma:
            costo_equipo = round(suma * dias, 2)
    return {
        "id": str(c.id),
        "finca_id": str(c.finca_id),
        "finca_nombre": finca.nombre if finca else None,
        "servicio": c.servicio,
        "fecha_asignacion": c.fecha_asignacion.isoformat(),
        "fecha_inicio_tomas": c.fecha_inicio_tomas.isoformat() if c.fecha_inicio_tomas else None,
        "fecha_fin_tomas": c.fecha_fin_tomas.isoformat() if c.fecha_fin_tomas else None,
        "estado": c.estado,
        "valor_comision_cop": float(c.valor_comision_cop) if c.valor_comision_cop is not None else None,
        "valor_cobro_servicio_cop": float(c.valor_cobro_servicio_cop) if c.valor_cobro_servicio_cop is not None else None,
        "valor_validacion_cop": float(c.valor_validacion_cop) if c.valor_validacion_cop is not None else None,
        "valor_plataforma_cop": float(c.valor_plataforma_cop) if c.valor_plataforma_cop is not None else None,
        "observaciones": c.observaciones,
        "dias_programados": dias,
        "costo_equipo_estimado_cop": costo_equipo,
        "miembros": miembros,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


async def _validar_miembros(db, miembros: list[MiembroIn]) -> list[EquipoTrabajo]:
    """Valida roles de comisión y que los empleados estén activos y libres."""
    instrumentadores = [m for m in miembros if m.rol_en_comision == "instrumentador"]
    cadeneros = [m for m in miembros if m.rol_en_comision == "cadenero_sensorista"]
    if len(instrumentadores) != 1:
        raise HTTPException(status_code=422, detail={
            "code": "INSTRUMENTADOR_REQUERIDO",
            "message": "La comisión debe tener exactamente un instrumentador.",
        })
    if not cadeneros:
        raise HTTPException(status_code=422, detail={
            "code": "CADENERO_REQUERIDO",
            "message": "La comisión debe tener al menos un cadenero sensorista.",
        })
    for m in miembros:
        if m.rol_en_comision not in ROLES_EQUIPO:
            raise HTTPException(status_code=422, detail={
                "code": "ROL_INVALIDO", "message": f"Rol inválido en comisión: {m.rol_en_comision}.",
            })
    ids = {uuid_mod.UUID(m.empleado_id) for m in miembros}
    empleados = (
        await db.execute(select(EquipoTrabajo).where(EquipoTrabajo.id.in_(ids)))
    ).scalars().all()
    if len(empleados) != len(ids):
        raise HTTPException(status_code=422, detail={
            "code": "EMPLEADO_NOT_FOUND",
            "message": "Uno o más empleados indicados no existen.",
        })
    for e in empleados:
        if e.estado != "activo":
            raise HTTPException(status_code=422, detail={
                "code": "EMPLEADO_INACTIVO",
                "message": f"El empleado '{e.nombres} {e.apellidos}' está desvinculado.",
            })
    # Empleados en otra comisión activa (asignada/en_campo) no pueden duplicarse
    ocupados = (
        await db.execute(
            select(ComisionMiembro.empleado_id)
            .join(Comision, Comision.id == ComisionMiembro.comision_id)
            .where(
                ComisionMiembro.empleado_id.in_(ids),
                ComisionMiembro.activo.is_(True),
                Comision.estado.in_(["asignada", "en_campo"]),
            )
        )
    ).scalars().all()
    if ocupados:
        nombres = {e.id: f"{e.nombres} {e.apellidos}" for e in empleados}
        raise HTTPException(status_code=409, detail={
            "code": "EMPLEADO_OCUPADO",
            "message": "Los siguientes empleados ya están en otra comisión activa: "
                       + ", ".join(nombres.get(oid, str(oid)) for oid in ocupados)
                       + ". Finalice su comisión actual antes de asignarlos.",
        })
    return empleados


@router.get("/comisiones")
async def listar_comisiones(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    finca_id: str | None = Query(None),
    estado: str | None = Query(None),
):
    """Lista las comisiones (filtros por finca y estado)."""
    _exigir_admin(x_user_role)
    q = select(Comision).order_by(Comision.fecha_asignacion.desc(), Comision.created_at.desc())
    if finca_id:
        try:
            fid = uuid_mod.UUID(finca_id)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
            })
        q = q.where(Comision.finca_id == fid)
    if estado:
        if estado not in ESTADOS_COMISION:
            raise HTTPException(status_code=422, detail={
                "code": "ESTADO_INVALIDO", "message": f"Estado inválido. Use: {', '.join(ESTADOS_COMISION)}.",
            })
        q = q.where(Comision.estado == estado)
    comisiones = (await db.execute(q)).scalars().all()
    data = [await _comision_a_dict(db, c) for c in comisiones]
    return {"data": data, "total": len(data)}


@router.get("/comisiones/{comision_id}")
async def detalle_comision(
    comision_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Detalle de una comisión con sus miembros y costos."""
    _exigir_admin(x_user_role)
    comision = await _obtener_comision(db, comision_id)
    return await _comision_a_dict(db, comision)


@router.post("/comisiones", status_code=201)
async def crear_comision(
    body: ComisionCreate,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Crea una comisión asignada a una finca con su equipo de trabajo."""
    _exigir_admin(x_user_role)
    try:
        finca_uuid = uuid_mod.UUID(body.finca_id)
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
    await _validar_miembros(db, body.miembros)

    comision = Comision(
        finca_id=finca_uuid,
        servicio=body.servicio,
        fecha_asignacion=body.fecha_asignacion,
        fecha_inicio_tomas=body.fecha_inicio_tomas,
        estado="asignada",
        valor_comision_cop=body.valor_comision_cop,
        valor_cobro_servicio_cop=body.valor_cobro_servicio_cop,
        valor_validacion_cop=body.valor_validacion_cop,
        valor_plataforma_cop=body.valor_plataforma_cop,
        observaciones=body.observaciones,
    )
    db.add(comision)
    await db.flush()
    for m in body.miembros:
        db.add(ComisionMiembro(
            comision_id=comision.id,
            empleado_id=uuid_mod.UUID(m.empleado_id),
            rol_en_comision=m.rol_en_comision,
        ))
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="comision.crear", entidad="comisiones", entidad_id=str(comision.id),
        detalle={"finca_id": body.finca_id, "finca": finca.nombre,
                 "servicio": body.servicio, "miembros": len(body.miembros)},
    )
    await db.commit()
    await db.refresh(comision)
    logger.info("comision_crear", comision_id=str(comision.id), finca_id=body.finca_id)
    return await _comision_a_dict(db, comision)


@router.put("/comisiones/{comision_id}")
async def editar_comision(
    comision_id: str,
    body: ComisionUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Edita una comisión (datos, fechas, valores y reemplazo completo de miembros)."""
    _exigir_admin(x_user_role)
    comision = await _obtener_comision(db, comision_id)
    cambios = body.model_dump(exclude_unset=True)
    if "miembros" in cambios and cambios["miembros"] is not None:
        await _validar_miembros(db, cambios["miembros"])
        await db.execute(
            ComisionMiembro.__table__.update()
            .where(ComisionMiembro.comision_id == comision.id)
            .values(activo=False)
        )
        for m in cambios["miembros"]:
            db.add(ComisionMiembro(
                comision_id=comision.id,
                empleado_id=uuid_mod.UUID(m.empleado_id),
                rol_en_comision=m.rol_en_comision,
            ))
        cambios.pop("miembros")
    for campo, valor in cambios.items():
        setattr(comision, campo, valor)
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="comision.editar", entidad="comisiones", entidad_id=comision_id,
        detalle={"campos": sorted(body.model_dump(exclude_unset=True))},
    )
    await db.commit()
    await db.refresh(comision)
    logger.info("comision_editar", comision_id=comision_id)
    return await _comision_a_dict(db, comision)


class FinalizarRequest(BaseModel):
    fecha_fin_tomas: date | None = None


@router.post("/comisiones/{comision_id}/finalizar")
async def finalizar_comision(
    comision_id: str,
    body: FinalizarRequest | None = None,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Registra el fin de la medición (obligatorio para liberar el equipo a otra finca)."""
    _exigir_admin(x_user_role)
    comision = await _obtener_comision(db, comision_id)
    if comision.estado == "finalizada":
        raise HTTPException(status_code=422, detail={
            "code": "COMISION_YA_FINALIZADA", "message": "La comisión ya está finalizada.",
        })
    fecha_fin = (body.fecha_fin_tomas if body else None) or datetime.now(timezone.utc).date()
    comision.fecha_fin_tomas = fecha_fin
    comision.estado = "finalizada"
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="comision.finalizar", entidad="comisiones", entidad_id=comision_id,
        detalle={"fecha_fin_tomas": fecha_fin.isoformat()},
    )
    await db.commit()
    await db.refresh(comision)
    logger.info("comision_finalizar", comision_id=comision_id, fecha=fecha_fin.isoformat())
    return await _comision_a_dict(db, comision)


@router.delete("/comisiones/{comision_id}")
async def cancelar_comision(
    comision_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Cancela una comisión (estado cancelada; los miembros quedan liberados)."""
    _exigir_admin(x_user_role)
    comision = await _obtener_comision(db, comision_id)
    if comision.estado == "finalizada":
        raise HTTPException(status_code=422, detail={
            "code": "COMISION_YA_FINALIZADA",
            "message": "Una comisión finalizada no se puede cancelar.",
        })
    comision.estado = "cancelada"
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="comision.cancelar", entidad="comisiones", entidad_id=comision_id,
    )
    await db.commit()
    logger.info("comision_cancelar", comision_id=comision_id)
    return {"status": "cancelada", "comision_id": comision_id}
