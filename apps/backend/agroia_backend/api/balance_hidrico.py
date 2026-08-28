"""API de balance hídrico ETo/Kc (1.C) — solo lectura."""

import uuid as uuid_mod

from agroia.database import get_db
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.finca import Finca
from agroia_backend.services.acceso import verificar_acceso_finca
from agroia_backend.services.balance_hidrico import calcular_balance_hidrico

router = APIRouter(prefix="/api/v1", tags=["balance-hidrico"])


@router.get("/fincas/{finca_id}/balance-hidrico")
async def balance_hidrico(
    finca_id: str,
    lote_id: str | None = Query(None),
    dias: int = Query(7, ge=1, le=14),
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Necesidad de riego de los próximos días (ETo × Kc − lluvia)."""
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
    resultado = await calcular_balance_hidrico(db, finca, lote_id=lote_id, dias=dias)
    if resultado is None:
        raise HTTPException(status_code=422, detail={
            "code": "SIN_COORDENADAS",
            "message": "La finca no tiene coordenadas registradas para calcular el balance hídrico.",
        })
    return resultado
