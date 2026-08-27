"""API de enriquecimiento SIG (IGAC/UPRA) — capas oficiales de suelos."""

import uuid as uuid_mod

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.finca import Finca
from agroia_backend.services.auditoria import registrar_auditoria
from agroia_backend.services.sig_suelos import enriquecer_finca_sig, ultima_lectura_sig

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["sig"])

ROL_EXPERTOS = {"admin", "administrador", "agronomo", "agrónomo"}


def _exigir_rol(rol: str | None) -> str:
    rol = (rol or "").strip().lower()
    if rol not in ROL_EXPERTOS:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el administrador o el agrónomo pueden enriquecer con SIG.",
        })
    return rol


async def _obtener_finca(db, finca_id: str) -> Finca:
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
    return finca


@router.post("/fincas/{finca_id}/enriquecer-sig")
async def enriquecer_sig(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Precarga textura/MO/CIC oficiales (IGAC/UPRA) para la finca.

    El polígono GeoJSON se intersecta (centroide) con las zonas de
    referencia del Estudio General de Suelos; la estimación se guarda en
    `sensor_readings` con `calidad = estimado_por_sig`. Si el sensor envía
    datos reales de esas variables, sobreescriben la estimación.
    """
    _exigir_rol(x_user_role)
    finca = await _obtener_finca(db, finca_id)
    resultado = await enriquecer_finca_sig(db, finca)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="sig.enriquecer",
        entidad="finca",
        entidad_id=str(finca.id),
        detalle={
            "estado": resultado.get("estado"),
            "region": (resultado.get("zona") or {}).get("region"),
            "textura": (resultado.get("zona") or {}).get("textura"),
        },
    )
    await db.commit()
    return {"status": "ok", **resultado}


@router.get("/fincas/{finca_id}/enriquecimiento-sig")
async def consultar_enriquecimiento(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Última estimación SIG registrada para la finca (o null)."""
    _exigir_rol(x_user_role)
    await _obtener_finca(db, finca_id)
    return {"data": await ultima_lectura_sig(db, uuid_mod.UUID(finca_id))}
