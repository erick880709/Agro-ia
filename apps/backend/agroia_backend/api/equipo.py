"""API del equipo de trabajo: empleados, tarifas por rol y novedades (Admin).

Todo auditable (auditoria) y con fechas de registro/modificación (created_at/
updated_at en las tablas).
"""

import uuid as uuid_mod
from datetime import date

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.equipo_trabajo import (
    ROLES_EQUIPO,
    ROLES_EQUIPO_ETIQUETA,
    EquipoTrabajo,
    TarifaRol,
)
from agroia_backend.models.novedad_equipo import NovedadEquipo
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["equipo-trabajo"])


def _exigir_admin(rol: str | None) -> str:
    rol_norm = (rol or "").strip().lower()
    if rol_norm != "admin":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol administrador puede gestionar el equipo de trabajo.",
        })
    return rol_norm


# ══════════════════ Empleados ══════════════════

class EmpleadoCreate(BaseModel):
    nombres: str = Field(..., min_length=2, max_length=120)
    apellidos: str = Field(..., min_length=2, max_length=120)
    tipo_documento: str = Field("CC", pattern="^(CC|CE|TI|PASAPORTE|NIT)$")
    numero_documento: str = Field(..., min_length=3, max_length=20)
    lugar_domicilio: str | None = Field(None, max_length=200)
    numero_contacto: str | None = Field(None, max_length=20)
    contacto_emergencia_nombre: str | None = Field(None, max_length=200)
    contacto_emergencia_telefono: str | None = Field(None, max_length=20)
    rol: str = Field(..., description="instrumentador | cadenero_sensorista | chofer | agronomo")
    fecha_ingreso: date
    estado: str = Field("activo", pattern="^(activo|desvinculado)$")
    valor_dia_cop: float | None = Field(None, ge=0)


class EmpleadoUpdate(BaseModel):
    nombres: str | None = Field(None, min_length=2, max_length=120)
    apellidos: str | None = Field(None, min_length=2, max_length=120)
    tipo_documento: str | None = Field(None, pattern="^(CC|CE|TI|PASAPORTE|NIT)$")
    numero_documento: str | None = Field(None, min_length=3, max_length=20)
    lugar_domicilio: str | None = Field(None, max_length=200)
    numero_contacto: str | None = Field(None, max_length=20)
    contacto_emergencia_nombre: str | None = Field(None, max_length=200)
    contacto_emergencia_telefono: str | None = Field(None, max_length=20)
    rol: str | None = None
    fecha_ingreso: date | None = None
    estado: str | None = Field(None, pattern="^(activo|desvinculado)$")
    valor_dia_cop: float | None = Field(None, ge=0)


def _empleado_a_dict(e: EquipoTrabajo) -> dict:
    return {
        "id": str(e.id),
        "nombres": e.nombres,
        "apellidos": e.apellidos,
        "nombre_completo": f"{e.nombres} {e.apellidos}".strip(),
        "tipo_documento": e.tipo_documento,
        "numero_documento": e.numero_documento,
        "lugar_domicilio": e.lugar_domicilio,
        "numero_contacto": e.numero_contacto,
        "contacto_emergencia_nombre": e.contacto_emergencia_nombre,
        "contacto_emergencia_telefono": e.contacto_emergencia_telefono,
        "rol": e.rol,
        "rol_etiqueta": ROLES_EQUIPO_ETIQUETA.get(e.rol, e.rol),
        "fecha_ingreso": e.fecha_ingreso.isoformat(),
        "estado": e.estado,
        "valor_dia_cop": float(e.valor_dia_cop) if e.valor_dia_cop is not None else None,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    }


async def _obtener_empleado(db, empleado_id: str) -> EquipoTrabajo:
    try:
        eid = uuid_mod.UUID(empleado_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "EMPLEADO_INVALIDO", "message": "empleado_id no es un UUID válido.",
        })
    empleado = (
        await db.execute(select(EquipoTrabajo).where(EquipoTrabajo.id == eid))
    ).scalar_one_or_none()
    if empleado is None:
        raise HTTPException(status_code=404, detail={
            "code": "EMPLEADO_NOT_FOUND", "message": "El empleado no está registrado.",
        })
    return empleado


@router.get("/equipo-trabajo")
async def listar_empleados(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    rol: str | None = Query(None),
    estado: str | None = Query(None),
    search: str | None = Query(None),
):
    """Lista los empleados del equipo de trabajo (filtros por rol/estado/búsqueda)."""
    _exigir_admin(x_user_role)
    q = select(EquipoTrabajo).order_by(EquipoTrabajo.apellidos, EquipoTrabajo.nombres)
    if rol:
        q = q.where(EquipoTrabajo.rol == rol)
    if estado:
        q = q.where(EquipoTrabajo.estado == estado)
    if search:
        termino = f"%{search.strip()}%"
        q = q.where(
            (EquipoTrabajo.nombres.ilike(termino))
            | (EquipoTrabajo.apellidos.ilike(termino))
            | (EquipoTrabajo.numero_documento.ilike(termino))
        )
    empleados = (await db.execute(q)).scalars().all()
    return {"data": [_empleado_a_dict(e) for e in empleados], "total": len(empleados)}


@router.post("/equipo-trabajo", status_code=201)
async def crear_empleado(
    body: EmpleadoCreate,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Registra un empleado del equipo de trabajo."""
    _exigir_admin(x_user_role)
    if body.rol not in ROLES_EQUIPO:
        raise HTTPException(status_code=422, detail={
            "code": "ROL_INVALIDO", "message": f"Rol inválido. Use: {', '.join(ROLES_EQUIPO)}.",
        })
    existente = (
        await db.execute(
            select(EquipoTrabajo).where(EquipoTrabajo.numero_documento == body.numero_documento)
        )
    ).scalar_one_or_none()
    if existente is not None:
        raise HTTPException(status_code=409, detail={
            "code": "DOCUMENTO_EXISTENTE",
            "message": f"Ya existe un empleado con el documento '{body.numero_documento}'.",
        })
    empleado = EquipoTrabajo(
        nombres=body.nombres.strip(),
        apellidos=body.apellidos.strip(),
        tipo_documento=body.tipo_documento,
        numero_documento=body.numero_documento.strip(),
        lugar_domicilio=body.lugar_domicilio,
        numero_contacto=body.numero_contacto,
        contacto_emergencia_nombre=body.contacto_emergencia_nombre,
        contacto_emergencia_telefono=body.contacto_emergencia_telefono,
        rol=body.rol,
        fecha_ingreso=body.fecha_ingreso,
        estado=body.estado,
        valor_dia_cop=body.valor_dia_cop,
    )
    db.add(empleado)
    await db.flush()
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="equipo.crear", entidad="equipo_trabajo", entidad_id=str(empleado.id),
        detalle={"nombre": f"{body.nombres} {body.apellidos}", "rol": body.rol,
                 "documento": body.numero_documento},
    )
    await db.commit()
    await db.refresh(empleado)
    logger.info("equipo_crear", empleado_id=str(empleado.id), rol=body.rol)
    return _empleado_a_dict(empleado)


@router.put("/equipo-trabajo/{empleado_id}")
async def editar_empleado(
    empleado_id: str,
    body: EmpleadoUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Edita un empleado (incluida la desvinculación vía estado)."""
    _exigir_admin(x_user_role)
    empleado = await _obtener_empleado(db, empleado_id)
    cambios = body.model_dump(exclude_unset=True)
    if "rol" in cambios and cambios["rol"] not in ROLES_EQUIPO:
        raise HTTPException(status_code=422, detail={
            "code": "ROL_INVALIDO", "message": f"Rol inválido. Use: {', '.join(ROLES_EQUIPO)}.",
        })
    for campo, valor in cambios.items():
        setattr(empleado, campo, valor)
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="equipo.editar", entidad="equipo_trabajo", entidad_id=empleado_id,
        detalle={"campos": sorted(cambios)},
    )
    await db.commit()
    await db.refresh(empleado)
    logger.info("equipo_editar", empleado_id=empleado_id)
    return _empleado_a_dict(empleado)


@router.delete("/equipo-trabajo/{empleado_id}")
async def desvincular_empleado(
    empleado_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Desvincula un empleado (borrado lógico conservando la trazabilidad)."""
    _exigir_admin(x_user_role)
    empleado = await _obtener_empleado(db, empleado_id)
    empleado.estado = "desvinculado"
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="equipo.desvincular", entidad="equipo_trabajo", entidad_id=empleado_id,
        detalle={"nombre": f"{empleado.nombres} {empleado.apellidos}"},
    )
    await db.commit()
    logger.info("equipo_desvincular", empleado_id=empleado_id)
    return {"status": "desvinculado", "empleado_id": empleado_id}


# ══════════════════ Tarifas por rol ══════════════════

class TarifaUpdate(BaseModel):
    valor_dia_cop: float = Field(..., ge=0)


@router.get("/equipo-trabajo/tarifas")
async def get_tarifas(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Valor por día de trabajo por rol."""
    _exigir_admin(x_user_role)
    tarifas = (await db.execute(select(TarifaRol))).scalars().all()
    mapa = {t.rol: float(t.valor_dia_cop) for t in tarifas}
    return {
        "data": [
            {"rol": r, "rol_etiqueta": ROLES_EQUIPO_ETIQUETA.get(r, r),
             "valor_dia_cop": mapa.get(r)}
            for r in ROLES_EQUIPO
        ],
    }


@router.put("/equipo-trabajo/tarifas/{rol}")
async def put_tarifa(
    rol: str,
    body: TarifaUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Actualiza el valor por día de trabajo de un rol."""
    _exigir_admin(x_user_role)
    if rol not in ROLES_EQUIPO:
        raise HTTPException(status_code=422, detail={
            "code": "ROL_INVALIDO", "message": f"Rol inválido. Use: {', '.join(ROLES_EQUIPO)}.",
        })
    tarifa = (
        await db.execute(select(TarifaRol).where(TarifaRol.rol == rol))
    ).scalar_one_or_none()
    if tarifa is None:
        tarifa = TarifaRol(rol=rol, valor_dia_cop=body.valor_dia_cop)
        db.add(tarifa)
    else:
        tarifa.valor_dia_cop = body.valor_dia_cop
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="equipo.tarifa", entidad="tarifas_rol", entidad_id=rol,
        detalle={"valor_dia_cop": body.valor_dia_cop},
    )
    await db.commit()
    logger.info("equipo_tarifa", rol=rol, valor=body.valor_dia_cop)
    return {"status": "updated", "rol": rol, "valor_dia_cop": body.valor_dia_cop}


# ══════════════════ Novedades (incapacidades/ausencias) ══════════════════

class NovedadCreate(BaseModel):
    tipo: str = Field(..., pattern="^(incapacidad|ausencia|otro)$")
    descripcion: str | None = None
    fecha_inicio: date
    fecha_fin: date | None = None
    comision_id: str | None = None
    reemplazo_empleado_id: str | None = None


def _novedad_a_dict(n: NovedadEquipo) -> dict:
    return {
        "id": str(n.id),
        "empleado_id": str(n.empleado_id),
        "comision_id": str(n.comision_id) if n.comision_id else None,
        "tipo": n.tipo,
        "descripcion": n.descripcion,
        "fecha_inicio": n.fecha_inicio.isoformat(),
        "fecha_fin": n.fecha_fin.isoformat() if n.fecha_fin else None,
        "reemplazo_empleado_id": str(n.reemplazo_empleado_id) if n.reemplazo_empleado_id else None,
        "estado": n.estado,
        "created_at": n.created_at.isoformat() if n.created_at else None,
        "updated_at": n.updated_at.isoformat() if n.updated_at else None,
    }


@router.get("/equipo-trabajo/novedades")
async def listar_novedades(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    estado: str | None = Query(None),
    empleado_id: str | None = Query(None),
):
    """Lista de novedades del equipo (filtro por estado y empleado)."""
    _exigir_admin(x_user_role)
    q = select(NovedadEquipo).order_by(NovedadEquipo.fecha_inicio.desc())
    if estado:
        q = q.where(NovedadEquipo.estado == estado)
    if empleado_id:
        try:
            eid = uuid_mod.UUID(empleado_id)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "EMPLEADO_INVALIDO", "message": "empleado_id no es un UUID válido.",
            })
        q = q.where(NovedadEquipo.empleado_id == eid)
    novedades = (await db.execute(q)).scalars().all()
    data = []
    for n in novedades:
        empleado = (
            await db.execute(select(EquipoTrabajo).where(EquipoTrabajo.id == n.empleado_id))
        ).scalar_one_or_none()
        reemplazo = None
        if n.reemplazo_empleado_id:
            r = (
                await db.execute(select(EquipoTrabajo).where(EquipoTrabajo.id == n.reemplazo_empleado_id))
            ).scalar_one_or_none()
            if r:
                reemplazo = {"id": str(r.id), "nombre": f"{r.nombres} {r.apellidos}".strip()}
        item = _novedad_a_dict(n)
        item["empleado_nombre"] = f"{empleado.nombres} {empleado.apellidos}".strip() if empleado else "—"
        item["reemplazo_nombre"] = reemplazo["nombre"] if reemplazo else None
        data.append(item)
    return {"data": data, "total": len(data)}


@router.post("/equipo-trabajo/{empleado_id}/novedades", status_code=201)
async def registrar_novedad(
    empleado_id: str,
    body: NovedadCreate,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Registra una novedad (incapacidad/ausencia) y, si se indica, asigna reemplazo
    a la comisión activa del empleado (mismo rol)."""
    _exigir_admin(x_user_role)
    empleado = await _obtener_empleado(db, empleado_id)
    comision_id_uuid = None
    if body.comision_id:
        try:
            comision_id_uuid = uuid_mod.UUID(body.comision_id)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "COMISION_INVALIDA", "message": "comision_id no es un UUID válido.",
            })
        from agroia_backend.models.comision import Comision

        comision = (
            await db.execute(select(Comision).where(Comision.id == comision_id_uuid))
        ).scalar_one_or_none()
        if comision is None:
            raise HTTPException(status_code=404, detail={
                "code": "COMISION_NOT_FOUND", "message": "La comisión no está registrada.",
            })
    reemplazo_uuid = None
    if body.reemplazo_empleado_id:
        try:
            reemplazo_uuid = uuid_mod.UUID(body.reemplazo_empleado_id)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "EMPLEADO_INVALIDO", "message": "reemplazo_empleado_id no es un UUID válido.",
            })
        reemplazo = await _obtener_empleado(db, body.reemplazo_empleado_id)
        if reemplazo.estado != "activo":
            raise HTTPException(status_code=422, detail={
                "code": "REEMPLAZO_INACTIVO",
                "message": "El reemplazo debe ser un empleado activo.",
            })
        if comision_id_uuid:
            from agroia_backend.models.comision import ComisionMiembro

            db.add(ComisionMiembro(
                comision_id=comision_id_uuid,
                empleado_id=reemplazo_uuid,
                rol_en_comision=empleado.rol,
            ))
    novedad = NovedadEquipo(
        empleado_id=uuid_mod.UUID(empleado_id),
        comision_id=comision_id_uuid,
        tipo=body.tipo,
        descripcion=body.descripcion,
        fecha_inicio=body.fecha_inicio,
        fecha_fin=body.fecha_fin,
        reemplazo_empleado_id=reemplazo_uuid,
    )
    db.add(novedad)
    await db.flush()
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="equipo.novedad", entidad="novedades_equipo", entidad_id=str(novedad.id),
        detalle={"empleado": f"{empleado.nombres} {empleado.apellidos}", "tipo": body.tipo,
                 "comision_id": body.comision_id,
                 "reemplazo": body.reemplazo_empleado_id},
    )
    await db.commit()
    await db.refresh(novedad)
    logger.info("equipo_novedad", novedad_id=str(novedad.id), tipo=body.tipo)
    return _novedad_a_dict(novedad)


@router.put("/equipo-trabajo/novedades/{novedad_id}/cerrar")
async def cerrar_novedad(
    novedad_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Cierra una novedad (el empleado se reintegra)."""
    _exigir_admin(x_user_role)
    try:
        nid = uuid_mod.UUID(novedad_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "NOVEDAD_INVALIDA", "message": "novedad_id no es un UUID válido.",
        })
    novedad = (
        await db.execute(select(NovedadEquipo).where(NovedadEquipo.id == nid))
    ).scalar_one_or_none()
    if novedad is None:
        raise HTTPException(status_code=404, detail={
            "code": "NOVEDAD_NOT_FOUND", "message": "La novedad no está registrada.",
        })
    novedad.estado = "cerrada"
    await registrar_auditoria(
        db, usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre, rol=x_user_role,
        accion="equipo.novedad.cerrar", entidad="novedades_equipo", entidad_id=novedad_id,
    )
    await db.commit()
    logger.info("equipo_novedad_cerrada", novedad_id=novedad_id)
    return {"status": "cerrada", "novedad_id": novedad_id}
