"""Reglas de negocio de etapas de comisión (flujo recomendación → reporte).

Reglas (2026-08-31):
  1. Sin comisión asignada (o cancelada) NO se puede generar una
     recomendación para la finca.
  2. Al generar una recomendación, la comisión pasa a `en_recomendacion`.
  3. Para generar un reporte, la comisión DEBE haber pasado por la etapa de
     recomendación (`en_recomendacion` o posterior). Pueden generarse tantas
     recomendaciones como se necesiten.
  4. Al generar el reporte, la comisión pasa a
     `generacion_reporte_fin_etapa`.
"""

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.comision import Comision

# Estados en los que se considera que la comisión existe y está activa para
# el flujo de recomendaciones (todo menos cancelada).
_ESTADOS_VALIDOS = {
    "asignada", "en_campo", "en_recomendacion",
    "generacion_reporte_fin_etapa", "finalizada",
}

# Estados que habilitan la generación del reporte: haber pasado por la etapa
# de recomendación.
_ESTADOS_PARA_REPORTE = {"en_recomendacion", "generacion_reporte_fin_etapa"}


async def comision_reciente(db: AsyncSession, finca_id: str) -> Comision | None:
    """Última comisión asignada a la finca (por fecha de asignación)."""
    try:
        fid = uuid.UUID(str(finca_id))
    except ValueError:
        return None
    return (
        await db.execute(
            select(Comision)
            .where(Comision.finca_id == fid)
            .order_by(Comision.fecha_asignacion.desc(), Comision.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def exigir_comision_para_recomendacion(
    db: AsyncSession, finca_id: str
) -> Comision:
    """Regla 1: sin comisión activa no se puede generar recomendación."""
    comision = await comision_reciente(db, finca_id)
    if comision is None:
        raise HTTPException(status_code=409, detail={
            "code": "FINCA_SIN_COMISION",
            "message": (
                "La finca no tiene una comisión asignada. Asigne una comisión "
                "de trabajo antes de generar recomendaciones."
            ),
        })
    if comision.estado not in _ESTADOS_VALIDOS:
        raise HTTPException(status_code=409, detail={
            "code": "COMISION_CANCELADA",
            "message": (
                "La comisión de esta finca está cancelada. Asigne una nueva "
                "comisión antes de generar recomendaciones."
            ),
        })
    return comision


async def marcar_en_recomendacion(db: AsyncSession, comision: Comision) -> None:
    """Regla 2: la recomendación generada mueve la comisión a
    `en_recomendacion` (idempotente)."""
    if comision.estado != "en_recomendacion":
        comision.estado = "en_recomendacion"
        await db.flush()


async def exigir_etapa_recomendacion_para_reporte(
    db: AsyncSession, finca_id: str
) -> Comision:
    """Regla 3: el reporte exige haber pasado por la etapa de recomendación."""
    comision = await comision_reciente(db, finca_id)
    if comision is None:
        raise HTTPException(status_code=409, detail={
            "code": "FINCA_SIN_COMISION",
            "message": (
                "La finca no tiene una comisión asignada. Asigne una comisión "
                "y genere al menos una recomendación antes del reporte."
            ),
        })
    if comision.estado not in _ESTADOS_PARA_REPORTE:
        raise HTTPException(status_code=409, detail={
            "code": "REPORTE_SIN_RECOMENDACION",
            "message": (
                f"La comisión está en estado '{comision.estado}'. Para "
                "generar el reporte la finca debe haber pasado por la etapa "
                "de recomendación: genere una recomendación y vuelva a "
                "intentar."
            ),
        })
    return comision


async def marcar_reporte_fin_etapa(db: AsyncSession, comision: Comision) -> None:
    """Regla 4: el reporte generado mueve la comisión a
    `generacion_reporte_fin_etapa`."""
    if comision.estado != "generacion_reporte_fin_etapa":
        comision.estado = "generacion_reporte_fin_etapa"
        await db.flush()
