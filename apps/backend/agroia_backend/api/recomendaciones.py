"""API endpoints del motor de recomendaciones."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agroia.database import get_db
from agroia.errors import InsufficientDataError
from agroia.logging import get_logger
from agroia_backend.services.orchestrator import (
    RecommendationOrchestrator,
    RecommendationRequest,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/recomendaciones", tags=["recomendaciones"])


# ── Schemas ──

class RecommendRequest(BaseModel):
    finca_id: str = Field(..., description="UUID de la finca a analizar")
    cultivo_id: Optional[str] = Field(None, description="UUID del cultivo objetivo (opcional, para sugerir el mejor)")


class RecommendResponse(BaseModel):
    cultivo: str
    clasificacion_upra: str
    confianza: float
    recomendaciones: list[dict]
    justificacion: dict
    advertencia: Optional[str] = None
    discordancia: Optional[dict] = None
    tiempo_respuesta_ms: float


# ── Endpoints ──

@router.post("/analyze", response_model=RecommendResponse)
async def analizar_aptitud(request: RecommendRequest, db: AsyncSession = Depends(get_db)):
    """Analiza la aptitud del suelo de una finca para un cultivo.

    Pipeline completo: datos de suelo → ML → reglas → discordancia → respuesta.
    Tiempo objetivo: < 5s (p95).
    """
    orch = RecommendationOrchestrator(
        db_session=db,
    )
    try:
        result = await orch.analyze(
            RecommendationRequest(
                finca_id=request.finca_id,
                cultivo_id=request.cultivo_id,
            )
        )
        return RecommendResponse(
            cultivo=result.cultivo,
            clasificacion_upra=result.clasificacion_upra,
            confianza=result.confianza,
            recomendaciones=result.recomendaciones,
            justificacion=result.justificacion,
            advertencia=result.advertencia,
            discordancia=result.discordancia,
            tiempo_respuesta_ms=result.tiempo_respuesta_ms,
        )
    except InsufficientDataError as e:
        raise HTTPException(status_code=422, detail={
            "code": "INSUFFICIENT_DATA",
            "message": f"Datos insuficientes. Variables faltantes: {', '.join(e.missing_vars)}",
            "missing_variables": e.missing_vars,
        })


@router.get("/historial/{finca_id}")
async def historial_recomendaciones(
    finca_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    cultivo_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Historial de recomendaciones de una finca."""
    from sqlalchemy import select, func
    from agroia_backend.models.recomendacion import Recomendacion

    stmt = select(Recomendacion).where(Recomendacion.finca_id == finca_id)
    count_stmt = select(func.count()).select_from(Recomendacion).where(Recomendacion.finca_id == finca_id)
    if cultivo_id:
        stmt = stmt.where(Recomendacion.cultivo_id == cultivo_id)
        count_stmt = count_stmt.where(Recomendacion.cultivo_id == cultivo_id)

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.offset((page - 1) * page_size).limit(page_size).order_by(Recomendacion.created_at.desc())
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "data": [{"id": str(r.id), "cultivo_id": str(r.cultivo_id), "clasificacion_upra": r.clasificacion_upra.value if r.clasificacion_upra else None,
                  "confianza": r.confianza, "estado": r.estado.value if r.estado else None, "created_at": str(r.created_at)} for r in items],
        "meta": {"page": page, "page_size": page_size, "total": total, "total_pages": max(1, (total + page_size - 1) // page_size)},
    }
