"""API de variedades/cultivares por cultivo (1.E) — filtro por altitud."""

import uuid as uuid_mod

from agroia.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.cultivo import Cultivo
from agroia_backend.models.variedad_cultivo import VariedadCultivo

router = APIRouter(tags=["variedades"])


def _a_dict(v: VariedadCultivo) -> dict:
    return {
        "id": str(v.id),
        "cultivo_id": str(v.cultivo_id),
        "nombre_variedad": v.nombre_variedad,
        "resistencias": v.resistencias,
        "altitud_min_msnm": v.altitud_min_msnm,
        "altitud_max_msnm": v.altitud_max_msnm,
        "mercado_objetivo": v.mercado_objetivo,
        "fuente": v.fuente,
    }


@router.get("/cultivos/{cultivo_id}/variedades")
async def variedades_cultivo(
    cultivo_id: str,
    altitud_msnm: int | None = Query(None, ge=0, le=6000),
    db: AsyncSession = Depends(get_db),
):
    """Variedades del cultivo; si se pasa altitud, filtra compatibles."""
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
            "code": "CULTIVO_NOT_FOUND", "message": "El cultivo no existe.",
        })
    variedades = (
        await db.execute(
            select(VariedadCultivo).where(VariedadCultivo.cultivo_id == cultivo_uuid)
        )
    ).scalars().all()

    compatibles = []
    for v in variedades:
        if altitud_msnm is not None:
            if v.altitud_min_msnm is not None and altitud_msnm < v.altitud_min_msnm:
                continue
            if v.altitud_max_msnm is not None and altitud_msnm > v.altitud_max_msnm:
                continue
        compatibles.append(_a_dict(v))

    return {
        "cultivo": cultivo.nombre,
        "variedades_compatibles": compatibles,
        "total": len(compatibles),
    }
