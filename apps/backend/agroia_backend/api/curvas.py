"""API de curvas de extracción nutricional por etapa fenológica (1.B)."""

import uuid as uuid_mod

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.curva_extraccion import CurvaExtraccion

logger = get_logger(__name__)
router = APIRouter(tags=["curvas-extraccion"])

ROL_ESCRITURA = {"admin", "administrador", "agronomo", "agrónomo"}
ETAPAS = {"Vegetativo", "Floración", "Fructificación", "Cosecha"}
NUTRIENTES = {"N", "P", "K", "Ca", "Mg", "S"}


class PuntoCurva(BaseModel):
    etapa_fenologica: str = Field(..., max_length=30)
    nutriente: str = Field(..., max_length=10)
    pct_extraccion_acumulado: float = Field(..., ge=0, le=100)
    fuente: str | None = None


class CurvaRequest(BaseModel):
    puntos: list[PuntoCurva] = Field(..., min_length=1, max_length=200)


def _a_dict(p: CurvaExtraccion) -> dict:
    return {
        "id": str(p.id),
        "cultivo_id": str(p.cultivo_id),
        "etapa_fenologica": p.etapa_fenologica,
        "nutriente": p.nutriente,
        "pct_extraccion_acumulado": float(p.pct_extraccion_acumulado),
        "fuente": p.fuente,
    }


@router.get("/cultivos/{cultivo_id}/curva-extraccion")
async def curva_extraccion(
    cultivo_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Curva de extracción completa por etapa/nutriente del cultivo."""
    try:
        cultivo_uuid = uuid_mod.UUID(cultivo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "CULTIVO_INVALIDO", "message": "cultivo_id no es un UUID válido.",
        })
    puntos = (
        await db.execute(
            select(CurvaExtraccion)
            .where(CurvaExtraccion.cultivo_id == cultivo_uuid)
            .order_by(CurvaExtraccion.etapa_fenologica, CurvaExtraccion.nutriente)
        )
    ).scalars().all()
    return {"data": [_a_dict(p) for p in puntos], "total": len(puntos)}


@router.put("/cultivos/{cultivo_id}/curva-extraccion")
async def cargar_curva_extraccion(
    cultivo_id: str,
    body: CurvaRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Carga o reemplaza puntos de la curva (upsert por etapa+nutriente)."""
    rol = (x_user_role or "").strip().lower()
    if rol not in ROL_ESCRITURA:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo Admin o Agrónomo pueden cargar curvas de extracción.",
        })
    try:
        cultivo_uuid = uuid_mod.UUID(cultivo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "CULTIVO_INVALIDO", "message": "cultivo_id no es un UUID válido.",
        })

    existentes = {
        (p.etapa_fenologica, p.nutriente): p
        for p in (
            await db.execute(select(CurvaExtraccion).where(CurvaExtraccion.cultivo_id == cultivo_uuid))
        ).scalars().all()
    }
    for punto in body.puntos:
        if punto.etapa_fenologica not in ETAPAS:
            raise HTTPException(status_code=422, detail={
                "code": "ETAPA_INVALIDA",
                "message": f"Etapa '{punto.etapa_fenologica}' inválida. Use: {', '.join(sorted(ETAPAS))}.",
            })
        if punto.nutriente not in NUTRIENTES:
            raise HTTPException(status_code=422, detail={
                "code": "NUTRIENTE_INVALIDO",
                "message": f"Nutriente '{punto.nutriente}' inválido. Use: {', '.join(sorted(NUTRIENTES))}.",
            })
        clave = (punto.etapa_fenologica, punto.nutriente)
        if clave in existentes:
            existentes[clave].pct_extraccion_acumulado = punto.pct_extraccion_acumulado
            existentes[clave].fuente = punto.fuente
        else:
            db.add(CurvaExtraccion(
                cultivo_id=cultivo_uuid,
                etapa_fenologica=punto.etapa_fenologica,
                nutriente=punto.nutriente,
                pct_extraccion_acumulado=punto.pct_extraccion_acumulado,
                fuente=punto.fuente,
            ))
    await db.commit()
    puntos = (
        await db.execute(
            select(CurvaExtraccion).where(CurvaExtraccion.cultivo_id == cultivo_uuid)
        )
    ).scalars().all()
    logger.info("curva_extraccion_actualizada", cultivo_id=cultivo_id, puntos=len(puntos), rol=rol)
    return {"status": "updated", "total": len(puntos), "data": [_a_dict(p) for p in puntos]}
