"""API de monitoreo integrado de plagas (1.D) con enriquecimiento GBIF."""

import asyncio
import json
import urllib.parse
import urllib.request
import uuid as uuid_mod
from datetime import date

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.monitoreo_plaga import MonitoreoPlaga
from agroia_backend.services.acceso import verificar_acceso_finca

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["monitoreo-plagas"])

ROL_ESCRITURA = {"admin", "administrador", "agronomo", "agrónomo", "extensionista"}


class MonitoreoRequest(BaseModel):
    cultivo_id: str | None = None
    fecha: date
    plaga_nombre: str = Field(..., min_length=2, max_length=120)
    plaga_nombre_cientifico: str | None = Field(None, max_length=150)
    metodo: str | None = Field(None, max_length=30)
    severidad: str | None = Field(None, pattern="^(Baja|Media|Alta)$")
    incidencia_pct: float | None = Field(None, ge=0, le=100)
    observaciones: str | None = None
    foto_url: str | None = Field(None, max_length=500)


def _gbif_ocurencias(nombre_cientifico: str | None) -> dict | None:
    """Conteo de ocurrencias reportadas en Colombia (GBIF, sin API key)."""
    if not nombre_cientifico:
        return None
    params = urllib.parse.urlencode({
        "scientificName": nombre_cientifico,
        "country": "CO",
        "limit": 1,
    })
    url = f"https://api.gbif.org/v1/occurrence/search?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgroIA/0.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        return {"total_ocurencias_co": int(data.get("count") or 0)}
    except Exception as e:  # noqa: BLE001 — enriquecimiento informativo
        logger.warning("gbif_no_disponible", error=str(e))
        return None


def _a_dict(m: MonitoreoPlaga) -> dict:
    return {
        "id": str(m.id),
        "finca_id": str(m.finca_id),
        "lote_id": str(m.lote_id) if m.lote_id else None,
        "cultivo_id": str(m.cultivo_id) if m.cultivo_id else None,
        "fecha": m.fecha.isoformat(),
        "plaga_nombre": m.plaga_nombre,
        "plaga_nombre_cientifico": m.plaga_nombre_cientifico,
        "metodo": m.metodo,
        "severidad": m.severidad,
        "incidencia_pct": float(m.incidencia_pct) if m.incidencia_pct is not None else None,
        "observaciones": m.observaciones,
        "foto_url": m.foto_url,
        "creado_en": m.creado_en.isoformat() if m.creado_en else None,
    }


@router.post("/fincas/{finca_id}/lotes/{lote_id}/monitoreo-plagas", status_code=201)
async def registrar_monitoreo(
    finca_id: str,
    lote_id: str,
    body: MonitoreoRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Registra una observación de campo de plagas (MIP)."""
    rol = (x_user_role or "").strip().lower()
    if rol not in ROL_ESCRITURA:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo Admin, Agrónomo o Extensionista pueden registrar monitoreo de plagas.",
        })
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
        lote_uuid = uuid_mod.UUID(lote_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "UUID_INVALIDO", "message": "finca_id o lote_id no son UUID válidos.",
        })

    registro = MonitoreoPlaga(
        finca_id=finca_uuid,
        lote_id=lote_uuid,
        cultivo_id=uuid_mod.UUID(body.cultivo_id) if body.cultivo_id else None,
        fecha=body.fecha,
        plaga_nombre=body.plaga_nombre,
        plaga_nombre_cientifico=body.plaga_nombre_cientifico,
        metodo=body.metodo,
        severidad=body.severidad,
        incidencia_pct=body.incidencia_pct,
        observaciones=body.observaciones,
        foto_url=body.foto_url,
    )
    db.add(registro)
    await db.commit()
    await db.refresh(registro)

    enriquecimiento = await asyncio.to_thread(_gbif_ocurencias, body.plaga_nombre_cientifico)
    logger.info("monitoreo_plaga_registrado", finca_id=finca_id, plaga=body.plaga_nombre, rol=rol)
    return {
        **{k: v for k, v in _a_dict(registro).items()},
        "enriquecimiento_gbif": enriquecimiento,
    }


@router.get("/fincas/{finca_id}/lotes/{lote_id}/monitoreo-plagas")
async def historial_monitoreo(
    finca_id: str,
    lote_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Historial de monitoreos de plagas del lote."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
        lote_uuid = uuid_mod.UUID(lote_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "UUID_INVALIDO", "message": "finca_id o lote_id no son UUID válidos.",
        })
    registros = (
        await db.execute(
            select(MonitoreoPlaga)
            .where(MonitoreoPlaga.finca_id == finca_uuid, MonitoreoPlaga.lote_id == lote_uuid)
            .order_by(MonitoreoPlaga.fecha.desc())
            .limit(100)
        )
    ).scalars().all()
    return {"data": [_a_dict(r) for r in registros], "total": len(registros)}
