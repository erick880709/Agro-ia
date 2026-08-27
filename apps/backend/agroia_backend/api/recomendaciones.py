"""API endpoints del motor de recomendaciones."""


from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.services.aptitud import AptitudService
from agroia_backend.services.data_adapters import SueloAdapter
from agroia_backend.services.ml_oracle import MLOracleService
from agroia_backend.services.orchestrator import (
    RecommendationOrchestrator,
    RecommendationRequest,
)
from agroia_backend.services.rules_engine import RulesEngine

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/recomendaciones", tags=["recomendaciones"])


# ── Schemas ──

class RecommendRequest(BaseModel):
    finca_id: str = Field(..., description="UUID de la finca a analizar")
    cultivo_id: str | None = Field(None, description="UUID del cultivo objetivo (opcional, para sugerir el mejor)")
    presupuesto_cop: float | None = Field(
        None, ge=0, description="Presupuesto de fertilización ($/ha) para el plan económico (opcional)"
    )
    rendimiento_actual_t_ha: float | None = Field(
        None, ge=0, description="Rendimiento actual declarado (t/ha) para el ROI realista (opcional)"
    )


class RecommendResponse(BaseModel):
    cultivo: str
    clasificacion_upra: str
    confianza: float
    recomendaciones: list[dict]
    justificacion: dict
    advertencia: str | None = None
    discordancia: dict | None = None
    tiempo_respuesta_ms: float
    sugerencias_cultivos: list[dict] | None = None
    modo: str = "analizar_cultivo"
    # ── Confianza real, validación y feedback humano (2026-08-27) ──
    confianza_real: float = 0.0
    estado_validacion: str = "pendiente_validacion"
    respaldos: int = 0
    variables_faltantes_fertilidad: list[str] = []
    variables_faltantes_esenciales: list[str] = []
    fenologia_ajustada: str | None = None
    plan_economico: dict | None = None
    rendimiento_actual_t_ha: float | None = None
    desglose_confianza: dict = {}
    # ── Validador ML (variables promovidas por aprendizaje activo) ──
    validacion_ml: dict | None = None


# ── Persistencia del historial ──

CLASIFICACION_A_ENUM = {
    "Apta": "ALTA",
    "Alta": "ALTA",
    "Moderadamente apta": "MEDIA",
    "Media": "MEDIA",
    "Marginalmente apta": "BAJA",
    "Baja": "BAJA",
    "No apta": "NO_APTA",
    "NoApta": "NO_APTA",
}


async def _persistir_recomendacion(
    db: AsyncSession, request: RecommendRequest, result
) -> None:
    """Persiste el análisis en el historial de la finca (UC1 y UC2).

    Un fallo aquí no rompe la respuesta del análisis: se registra en logs.
    """
    import uuid as uuid_mod

    from sqlalchemy import select, text

    from agroia_backend.models.finca import Finca
    from agroia_backend.models.recomendacion import Recomendacion

    try:
        # Endurecer contra search_path frágil (casts de enum en INSERT)
        await db.execute(text("SET LOCAL search_path TO public, agroia"))
        finca_uuid = uuid_mod.UUID(request.finca_id)

        # UC2: cultivo solicitado. UC1: cultivo top sugerido.
        cultivo_uuid = None
        if request.cultivo_id:
            cultivo_uuid = uuid_mod.UUID(request.cultivo_id)
        elif result.sugerencias_cultivos:
            top = result.sugerencias_cultivos[0]
            if top.get("cultivo_id"):
                cultivo_uuid = uuid_mod.UUID(top["cultivo_id"])

        if cultivo_uuid is None:
            logger.warning(
                "recomendacion_sin_cultivo_para_historial",
                finca_id=request.finca_id,
            )
            return

        finca = (
            await db.execute(select(Finca).where(Finca.id == finca_uuid))
        ).scalar_one_or_none()
        if finca is None:
            logger.warning(
                "finca_no_encontrada_para_historial", finca_id=request.finca_id
            )
            return

        estado = "ADVERTENCIA" if result.confianza < 0.8 else "PUBLICADA"

        db.add(Recomendacion(
            finca_id=finca_uuid,
            cultivo_id=cultivo_uuid,
            tenant_id=finca.tenant_id,
            clasificacion_upra=CLASIFICACION_A_ENUM.get(
                result.clasificacion_upra, "BAJA"
            ),
            confianza=result.confianza,
            justificacion=result.justificacion or {},
            estado=estado,
        ))
        await db.commit()
        logger.info(
            "recomendacion_persistida",
            finca_id=request.finca_id,
            cultivo_id=str(cultivo_uuid),
        )
    except Exception as e:
        await db.rollback()
        logger.error(
            "recomendacion_no_persistida",
            error=str(e),
            finca_id=request.finca_id,
        )


# ── Endpoints ──

@router.post("/analyze", response_model=RecommendResponse)
async def analizar_aptitud(
    request: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Analiza la aptitud del suelo de una finca.

    Dos casos de uso:
      - Sin `cultivo_id` (UC1): recomienda los cultivos más aptos para sembrar.
      - Con `cultivo_id` (UC2): diagnostica qué falta/sobra al suelo para ese
        cultivo y devuelve las acciones correctivas (sistema experto UPRA/Cenicafé).

    Tiempo objetivo: < 5s (p95).
    """
    from agroia_backend.services.acceso import exigir_no_cliente, verificar_acceso_finca

    exigir_no_cliente(x_user_role)
    await verificar_acceso_finca(db, x_user_role, None, request.finca_id)

    rules_engine = RulesEngine(db)
    orch = RecommendationOrchestrator(
        db_session=db,
        soil_adapter=SueloAdapter(db),
        ml_service=MLOracleService(),
        rules_engine=rules_engine,
        aptitud_service=AptitudService(db, rules_engine),
    )
    try:
        result = await orch.analyze(
            RecommendationRequest(
                finca_id=request.finca_id,
                cultivo_id=request.cultivo_id,
                presupuesto_cop=request.presupuesto_cop,
                rendimiento_actual_t_ha=request.rendimiento_actual_t_ha,
            )
        )
        await _persistir_recomendacion(db, request, result)
        return RecommendResponse(
            cultivo=result.cultivo,
            clasificacion_upra=result.clasificacion_upra,
            confianza=result.confianza,
            recomendaciones=result.recomendaciones,
            justificacion=result.justificacion,
            advertencia=result.advertencia,
            discordancia=result.discordancia,
            tiempo_respuesta_ms=result.tiempo_respuesta_ms,
            sugerencias_cultivos=result.sugerencias_cultivos,
            modo=result.modo,
            confianza_real=result.confianza_real,
            estado_validacion=result.estado_validacion,
            respaldos=result.respaldos,
            variables_faltantes_fertilidad=result.variables_faltantes_fertilidad,
            variables_faltantes_esenciales=result.variables_faltantes_esenciales,
            fenologia_ajustada=result.fenologia_ajustada,
            plan_economico=result.plan_economico,
            rendimiento_actual_t_ha=result.rendimiento_actual_t_ha,
            desglose_confianza=result.desglose_confianza,
            validacion_ml=result.validacion_ml,
        )
    except Exception as e:
        logger.exception("orchestrator_unexpected_error", error=str(e), finca_id=request.finca_id)
        raise HTTPException(status_code=500, detail={
            "code": "INTERNAL_ERROR",
            "message": "Error interno al procesar la recomendación. Revise los logs del servicio.",
        })


class AceptarRequest(BaseModel):
    finca_id: str = Field(..., description="UUID de la finca")
    cultivo_id: str | None = Field(None, description="UUID del cultivo aceptado (opcional)")
    comentario: str | None = Field(None, max_length=4000, description="Ampliación/ajustes del experto")
    resumen: dict | None = Field(None, description="Resumen de la recomendación aceptada")
    clasificacion_previa: str | None = Field(None, max_length=50)
    confianza_previa: float | None = Field(None, ge=0, le=1)


@router.post("/aceptar")
async def aceptar_recomendacion(
    body: AceptarRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Aceptación explícita de una recomendación por Admin/Agrónomo.

    Cada aceptación alimenta la confianza del modelo (human-in-the-loop):
    el orquestador suma +0.02 de confianza por aceptación (máx +0.10) y
    el comentario queda registrado como feedback para futuros
    reentrenamientos.
    """
    import uuid as uuid_mod

    from sqlalchemy import func, select

    from agroia_backend.models.aceptacion_recomendacion import AceptacionRecomendacion
    from agroia_backend.services.acceso import exigir_no_cliente

    exigir_no_cliente(x_user_role)
    rol = (x_user_role or "").strip().lower()
    if rol not in {"admin", "administrador", "agronomo", "agrónomo"}:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el administrador o el agrónomo pueden aceptar recomendaciones.",
        })

    try:
        finca_uuid = uuid_mod.UUID(body.finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })

    cultivo_uuid = None
    if body.cultivo_id:
        try:
            cultivo_uuid = uuid_mod.UUID(body.cultivo_id)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "CULTIVO_INVALIDO", "message": "cultivo_id no es un UUID válido.",
            })

    db.add(AceptacionRecomendacion(
        finca_id=finca_uuid,
        cultivo_id=cultivo_uuid,
        rol=rol,
        comentario=body.comentario,
        resumen=body.resumen or {},
        clasificacion_previa=body.clasificacion_previa,
        confianza_previa=body.confianza_previa,
    ))
    await db.commit()

    total_finca = (await db.execute(
        select(func.count(AceptacionRecomendacion.id)).where(
            AceptacionRecomendacion.finca_id == finca_uuid
        )
    )).scalar_one() or 0
    total_cultivo = None
    if cultivo_uuid:
        total_cultivo = (await db.execute(
            select(func.count(AceptacionRecomendacion.id)).where(
                AceptacionRecomendacion.finca_id == finca_uuid,
                AceptacionRecomendacion.cultivo_id == cultivo_uuid,
            )
        )).scalar_one() or 0

    logger.info(
        "recomendacion_aceptada",
        finca_id=str(finca_uuid),
        cultivo_id=str(cultivo_uuid) if cultivo_uuid else None,
        rol=rol,
    )
    refuerzo = min(0.10, 0.02 * int(total_cultivo or total_finca))
    return {
        "status": "accepted",
        "total_aceptaciones_finca": int(total_finca),
        "total_aceptaciones_cultivo": int(total_cultivo) if total_cultivo is not None else None,
        "refuerzo_confianza": round(refuerzo, 2),
        "mensaje": (
            "Recomendación aceptada y registrada como feedback: el modelo "
            f"gana +{round(refuerzo, 2)} de confianza para este cultivo/finca."
        ),
    }


@router.get("/historial/{finca_id}")
async def historial_recomendaciones(
    finca_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    cultivo_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Historial de recomendaciones de una finca."""
    from sqlalchemy import func, select

    from agroia_backend.models.recomendacion import Recomendacion
    from agroia_backend.services.acceso import verificar_acceso_finca

    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)

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
