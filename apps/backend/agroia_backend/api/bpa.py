"""API de trazabilidad BPA / certificación (1.G): checklist + reporte."""

import uuid as uuid_mod
from datetime import date, datetime, timezone

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.checklist_bpa import ChecklistBpa, PeriodoCarencia
from agroia_backend.models.finca import Finca
from agroia_backend.models.labor import Labor
from agroia_backend.models.lote import Lote
from agroia_backend.models.visita_bpa import VisitaBpa
from agroia_backend.services.acceso import verificar_acceso_finca
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["bpa"])

ROL_ESCRITURA = {"admin", "administrador", "agronomo", "agrónomo", "extensionista"}

# Checklist estático versionado (Res. ICA 30021/2017) — categorías base
CHECKLIST_BASE = [
    ("suelo_agua", "Fuente de agua para riego identificada y sin riesgo de contaminación"),
    ("suelo_agua", "Análisis de agua vigente (≤ 1 año) cuando aplica"),
    ("suelo_agua", "Análisis de suelo vigente (≤ 2 años)"),
    ("agroquimicos", "Registro de aplicaciones de agroquímicos con producto, dosis y fecha"),
    ("agroquimicos", "Respeto del período de carencia antes de cosecha"),
    ("agroquimicos", "Almacenamiento seguro de agroquímicos (bodega cerrada y señalizada)"),
    ("agroquimicos", "Equipo de protección personal disponible y en uso"),
    ("trabajadores", "Registro de capacitación en manejo seguro de agroquímicos"),
    ("trabajadores", "Agua potable disponible para trabajadores"),
    ("poscosecha", "Registro de trazabilidad lote → cosecha → destino"),
    ("poscosecha", "Instalaciones de poscosecha limpias y desinfectadas"),
]


class ChecklistItem(BaseModel):
    item: str = Field(..., max_length=200)
    categoria: str | None = Field(None, max_length=60)
    cumple: bool | None = None
    evidencia_url: str | None = Field(None, max_length=500)


class ChecklistRequest(BaseModel):
    items: list[ChecklistItem] = Field(..., min_length=1, max_length=100)


class VisitaItemModel(BaseModel):
    item: str = Field(..., max_length=200)
    categoria: str | None = Field(None, max_length=60)
    cumple: bool
    evidencia_url: str | None = Field(None, max_length=500)


class VisitaRequest(BaseModel):
    fecha: date
    items: list[VisitaItemModel] = Field(..., min_length=1, max_length=100)


def _a_dict(c: ChecklistBpa) -> dict:
    return {
        "id": str(c.id),
        "item": c.item,
        "categoria": c.categoria,
        "cumple": c.cumple,
        "evidencia_url": c.evidencia_url,
        "fecha_verificacion": c.fecha_verificacion.isoformat() if c.fecha_verificacion else None,
    }


def _visita_a_dict(v: VisitaBpa) -> dict:
    return {
        "id": str(v.id),
        "finca_id": str(v.finca_id),
        "fecha": v.fecha.isoformat(),
        "items": v.items or [],
        "verificado_por_email": v.verificado_por_email,
        "verificado_por_nombre": v.verificado_por_nombre,
        "verificado_rol": v.verificado_rol,
        "creado_en": v.creado_en.isoformat() if v.creado_en else None,
    }


@router.get("/fincas/{finca_id}/bpa/checklist")
async def get_checklist(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Checklist BPA de la finca (si está vacío, devuelve la base por categoría)."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })
    items = (
        await db.execute(select(ChecklistBpa).where(ChecklistBpa.finca_id == finca_uuid))
    ).scalars().all()
    data = [_a_dict(c) for c in items]
    if not data:
        data = [
            {"id": None, "item": item, "categoria": cat, "cumple": None,
             "evidencia_url": None, "fecha_verificacion": None}
            for cat, item in CHECKLIST_BASE
        ]
    return {"data": data, "total": len(data), "pendiente_diligenciar": not items}


@router.put("/fincas/{finca_id}/bpa/checklist")
async def put_checklist(
    finca_id: str,
    body: ChecklistRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Diligencia el checklist BPA (upsert por item)."""
    rol = (x_user_role or "").strip().lower()
    if rol not in ROL_ESCRITURA:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo Admin, Agrónomo o Extensionista pueden diligenciar el checklist BPA.",
        })
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })

    hoy = datetime.now(timezone.utc).date()
    existentes = {
        c.item: c
        for c in (
            await db.execute(select(ChecklistBpa).where(ChecklistBpa.finca_id == finca_uuid))
        ).scalars().all()
    }
    for it in body.items:
        if it.item in existentes:
            existentes[it.item].cumple = it.cumple
            existentes[it.item].categoria = it.categoria
            existentes[it.item].evidencia_url = it.evidencia_url
            existentes[it.item].fecha_verificacion = hoy
        else:
            db.add(ChecklistBpa(
                finca_id=finca_uuid,
                item=it.item,
                categoria=it.categoria,
                cumple=it.cumple,
                evidencia_url=it.evidencia_url,
                fecha_verificacion=hoy,
            ))
    await db.commit()
    logger.info("bpa_checklist_actualizado", finca_id=finca_id, items=len(body.items), rol=rol)
    return {"status": "updated", "items": len(body.items)}


@router.get("/fincas/{finca_id}/bpa/visitas")
async def get_visitas(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Historial de visitas de verificación BPA (línea de tiempo de trazabilidad)."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })
    visitas = (
        await db.execute(
            select(VisitaBpa)
            .where(VisitaBpa.finca_id == finca_uuid)
            .order_by(VisitaBpa.fecha.desc(), VisitaBpa.creado_en.desc())
        )
    ).scalars().all()
    return {"data": [_visita_a_dict(v) for v in visitas], "total": len(visitas)}


@router.post("/fincas/{finca_id}/bpa/visitas", status_code=201)
async def registrar_visita(
    finca_id: str,
    body: VisitaRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Registra una visita/medición BPA: guarda los ítems evaluados y actualiza
    el checklist vigente de la finca (fecha_verificacion = fecha de la visita)."""
    rol = (x_user_role or "").strip().lower()
    if rol not in ROL_ESCRITURA:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo Admin, Agrónomo o Extensionista pueden registrar visitas BPA.",
        })
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })

    visita = VisitaBpa(
        finca_id=finca_uuid,
        fecha=body.fecha,
        items=[it.model_dump() for it in body.items],
        verificado_por_email=(x_user_email or "").strip().lower() or None,
        verificado_por_nombre=x_user_nombre,
        verificado_rol=x_user_role,
    )
    db.add(visita)
    await db.flush()

    # ── Actualiza el checklist vigente con lo evaluado en esta visita ──
    existentes = {
        c.item: c
        for c in (
            await db.execute(select(ChecklistBpa).where(ChecklistBpa.finca_id == finca_uuid))
        ).scalars().all()
    }
    for it in body.items:
        if it.item in existentes:
            existentes[it.item].cumple = it.cumple
            if it.categoria:
                existentes[it.item].categoria = it.categoria
            existentes[it.item].evidencia_url = it.evidencia_url
            existentes[it.item].fecha_verificacion = body.fecha
        else:
            db.add(ChecklistBpa(
                finca_id=finca_uuid,
                item=it.item,
                categoria=it.categoria,
                cumple=it.cumple,
                evidencia_url=it.evidencia_url,
                fecha_verificacion=body.fecha,
            ))

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="bpa.visita.registrar",
        entidad="visita_bpa",
        entidad_id=str(visita.id),
        detalle={"finca_id": finca_id, "fecha": body.fecha.isoformat(), "items": len(body.items)},
    )
    await db.commit()
    await db.refresh(visita)
    logger.info("bpa_visita_registrada", finca_id=finca_id, fecha=body.fecha.isoformat(), items=len(body.items), rol=rol)
    return _visita_a_dict(visita)


@router.delete("/fincas/{finca_id}/bpa/visitas/{visita_id}")
async def quitar_visita(
    finca_id: str,
    visita_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Quita una visita de la trazabilidad (el checklist vigente no se modifica)."""
    rol = (x_user_role or "").strip().lower()
    if rol not in ROL_ESCRITURA:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo Admin, Agrónomo o Extensionista pueden quitar visitas BPA.",
        })
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        visita_uuid = uuid_mod.UUID(visita_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "VISITA_INVALIDA", "message": "visita_id no es un UUID válido.",
        })
    visita = (
        await db.execute(
            select(VisitaBpa).where(
                VisitaBpa.id == visita_uuid, VisitaBpa.finca_id == uuid_mod.UUID(finca_id)
            )
        )
    ).scalar_one_or_none()
    if visita is None:
        raise HTTPException(status_code=404, detail={
            "code": "VISITA_NOT_FOUND", "message": "La visita no está registrada para esta finca.",
        })
    await db.delete(visita)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="bpa.visita.quitar",
        entidad="visita_bpa",
        entidad_id=visita_id,
        detalle={"finca_id": finca_id, "fecha": visita.fecha.isoformat()},
    )
    await db.commit()
    logger.info("bpa_visita_quitada", finca_id=finca_id, visita_id=visita_id, rol=rol)
    return {"status": "deleted", "visita_id": visita_id}


@router.get("/fincas/{finca_id}/bpa/reporte-trazabilidad")
async def reporte_trazabilidad(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Reporte de trazabilidad: labores + períodos de carencia + checklist."""
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
    lotes = (
        await db.execute(select(Lote.id).where(Lote.finca_id == finca_uuid))
    ).scalars().all()

    labores = (
        await db.execute(
            select(Labor).where(Labor.lote_id.in_(lotes)).order_by(Labor.fecha_programada.desc())
        )
    ).scalars().all() if lotes else []

    periodos = {
        p.producto.lower(): p.dias_carencia
        for p in (await db.execute(select(PeriodoCarencia))).scalars().all()
    }

    aplicaciones = []
    for labor in labores:
        producto = labor.producto or ""
        dias = periodos.get(producto.lower())
        aplicacion = {
            "fecha": labor.fecha_ejecucion.isoformat() if labor.fecha_ejecucion else None,
            "producto": producto,
            "dosis_kg_ha": float(labor.dosis_kg_ha) if labor.dosis_kg_ha is not None else None,
            "periodo_carencia_dias": dias,
            "estado": labor.estado,
        }
        if labor.fecha_ejecucion and dias:
            aplicacion["cosecha_segura_desde"] = (
                date.fromordinal(labor.fecha_ejecucion.toordinal() + dias).isoformat()
            )
        aplicaciones.append(aplicacion)

    checklist = (
        await db.execute(select(ChecklistBpa).where(ChecklistBpa.finca_id == finca_uuid))
    ).scalars().all()
    total_items = len(checklist)
    cumplidos = sum(1 for c in checklist if c.cumple)

    return {
        "finca": finca.nombre if finca else None,
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "aplicaciones": aplicaciones,
        "checklist": {
            "total": total_items,
            "cumplidos": cumplidos,
            "pct_avance": round(cumplidos * 100 / total_items, 1) if total_items else 0,
            "pendientes": [c.item for c in checklist if not c.cumple][:50],
        },
    }
