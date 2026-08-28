"""API de recomendación de rotación de cultivos (1.F)."""

import uuid as uuid_mod

from agroia.database import get_db
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.ciclo_lote import CicloLote
from agroia_backend.models.compatibilidad_rotacion import CompatibilidadRotacion
from agroia_backend.models.cultivo import Cultivo
from agroia_backend.models.lote import Lote
from agroia_backend.services.acceso import verificar_acceso_finca

router = APIRouter(prefix="/api/v1", tags=["rotacion"])

_BENEFICIO_TEXTO = {
    "fijacion_n": "Leguminosa: aporta N al suelo tras un cultivo exigente en nitrógeno",
    "ruptura_plaga": "Rompe el ciclo de plagas/enfermedades al cambiar de familia botánica",
    "recuperacion_estructura": "Ayuda a recuperar estructura y materia orgánica del suelo",
}


async def calcular_rotacion(db, finca_uuid) -> dict:
    """Sugerencia de rotación según el último ciclo cerrado. Compartido con el reporte."""
    lotes = (
        await db.execute(select(Lote.id).where(Lote.finca_id == finca_uuid))
    ).scalars().all()

    ciclo = (
        await db.execute(
            select(CicloLote)
            .where(
                CicloLote.lote_id.in_(lotes),
                CicloLote.fecha_cosecha.isnot(None),
            )
            .order_by(CicloLote.fecha_cosecha.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if ciclo is None or ciclo.cultivo_id is None:
        # Regla de degradación: sin historial, el bloque se omite
        return {"cultivo_actual": None, "sugerencias": [], "nota": "Sin ciclos cerrados registrados."}

    cultivo_actual = (
        await db.execute(
            select(Cultivo).where(Cultivo.id == ciclo.cultivo_id)
        )
    ).scalar_one_or_none()
    if cultivo_actual is None:
        return {"cultivo_actual": None, "sugerencias": [], "nota": "Cultivo sin reglas de rotación cargadas."}

    reglas = (
        await db.execute(
            select(CompatibilidadRotacion).where(
                CompatibilidadRotacion.cultivo_actual_id == cultivo_actual.id
            )
        )
    ).scalars().all()
    sugerencias = []
    for regla in reglas:
        siguiente = (
            await db.execute(
                select(Cultivo).where(Cultivo.id == regla.cultivo_siguiente_id)
            )
        ).scalar_one_or_none()
        if siguiente is None:
            continue
        sugerencias.append({
            "cultivo": siguiente.nombre,
            "beneficio": regla.beneficio,
            "motivo": regla.motivo or _BENEFICIO_TEXTO.get(regla.beneficio or "", "Rotación recomendada"),
        })

    return {
        "cultivo_actual": cultivo_actual.nombre,
        "sugerencias": sugerencias,
    }


@router.get("/fincas/{finca_id}/recomendacion-rotacion")
async def recomendacion_rotacion(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Sugerencia de rotación según el último ciclo cerrado y reglas internas."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })

    return await calcular_rotacion(db, finca_uuid)
