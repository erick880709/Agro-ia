"""Chat con el asesor agronómico experto (explica reportes y da consejos).

Disponible para administrador, agrónomo y cliente. El acceso se limita a
las fincas que el rol puede ver (`verificar_acceso_finca`).

Sin OPENAI_API_KEY responde el motor experto local (reglas + lectura);
con la key configurada, responde el LLM con el mismo contexto real.
"""

import uuid as uuid_mod

from agroia.database import get_db
from agroia.errors import AgroIAError
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.cultivo import Cultivo, FichaTecnica
from agroia_backend.models.finca import Finca
from agroia_backend.models.regla_agronomica import ReglaAgronomica
from agroia_backend.models.sensor_reading import SensorReading
from agroia_backend.services.acceso import verificar_acceso_finca
from agroia_backend.services.agronomo_chat import (
    consultar_experto,
    construir_contexto,
    contexto_resumido,
    _respuesta_local,
)
from agroia_backend.services.aptitud import AptitudService
from agroia_backend.services.data_adapters import SueloAdapter
from agroia_backend.services.orchestrator import (
    RecommendationOrchestrator,
    RecommendationRequest,
)
from agroia_backend.services.rules_engine import RulesEngine

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    finca_id: str = Field(..., description="UUID de la finca sobre la que se consulta")
    mensaje: str = Field(..., min_length=1, max_length=2000)
    cultivo_id: str | None = Field(None, description="UUID del cultivo (opcional; si no, se usa el top sugerido)")
    historial: list[dict] | None = Field(None, description="Últimos mensajes [{rol, contenido}]")


@router.post("/consultar")
async def consultar_chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Responde una pregunta sobre la finca usando el contexto agronómico real."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, body.finca_id)

    try:
        finca_uuid = uuid_mod.UUID(body.finca_id)
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

    lectura = (
        await db.execute(
            select(SensorReading)
            .where(SensorReading.finca_id == finca_uuid)
            .order_by(SensorReading.ts.desc())
            .limit(1)
        )
    ).scalars().first()

    # ── Motor de recomendaciones (UC1: sugerencias; UC2: cultivo elegido) ──
    rules_engine = RulesEngine(db)
    orch = RecommendationOrchestrator(
        db_session=db,
        soil_adapter=SueloAdapter(db),
        rules_engine=rules_engine,
        aptitud_service=AptitudService(db, rules_engine),
    )

    uc1 = None
    if lectura is not None:
        try:
            uc1 = await orch.analyze(RecommendationRequest(
                finca_id=body.finca_id, cultivo_id=None,
            ))
        except (AgroIAError, ValueError):
            uc1 = None

    cultivo = None
    ficha = None
    cultivo_uuid = None
    if body.cultivo_id:
        try:
            cultivo_uuid = uuid_mod.UUID(body.cultivo_id)
        except ValueError:
            cultivo_uuid = None
    if cultivo_uuid is None and uc1 is not None and (uc1.sugerencias_cultivos or []):
        primer = uc1.sugerencias_cultivos[0].get("cultivo_id")
        if primer:
            try:
                cultivo_uuid = uuid_mod.UUID(str(primer))
            except ValueError:
                cultivo_uuid = None

    if cultivo_uuid is not None:
        cultivo = (
            await db.execute(select(Cultivo).where(Cultivo.id == cultivo_uuid))
        ).scalar_one_or_none()
        ficha = (
            await db.execute(
                select(FichaTecnica)
                .where(FichaTecnica.cultivo_id == cultivo_uuid)
                .order_by(FichaTecnica.created_at.desc())
                .limit(1)
            )
        ).scalars().first()

    # Reglas aplicables: universales + del cultivo elegido
    reglas = (
        await db.execute(
            select(ReglaAgronomica)
            .where(
                ReglaAgronomica.activa.is_(True),
                or_(
                    ReglaAgronomica.cultivo_id.is_(None),
                    ReglaAgronomica.cultivo_id == cultivo_uuid,
                ),
            )
        )
    ).scalars().all()

    # Análisis UC2 para el cultivo elegido (si hay cultivo y lectura)
    uc2 = None
    if lectura is not None and cultivo_uuid is not None:
        try:
            uc2 = await orch.analyze(RecommendationRequest(
                finca_id=body.finca_id, cultivo_id=str(cultivo_uuid),
            ))
        except (AgroIAError, ValueError):
            uc2 = None

    recomendaciones = [dict(r) for r in (uc2.recomendaciones if uc2 else [])]
    if not recomendaciones and uc1 is not None:
        recomendaciones = [dict(r) for r in (uc1.recomendaciones or [])]
    sugerencias = [dict(s) for s in (uc1.sugerencias_cultivos if uc1 else [])]

    ctx = {
        "recomendaciones": recomendaciones,
        "reglas": list(reglas),
        "sugerencias": sugerencias,
        "clasificacion": (uc2.clasificacion_upra if uc2 else (uc1.clasificacion_upra if uc1 else None)),
        "lectura": lectura,
    }

    contexto_texto = await construir_contexto(
        rol=x_user_role or "cliente",
        finca=finca,
        lectura=lectura,
        cultivo=cultivo,
        ficha=ficha,
        reglas=list(reglas),
        analisis=uc2 or uc1,
    )

    resultado = await consultar_experto(
        mensaje=body.mensaje,
        historial=body.historial or [],
        contexto=contexto_texto,
        rol=x_user_role or "cliente",
    )

    if resultado["modo"] == "llm" and resultado["respuesta"]:
        respuesta = resultado["respuesta"]
        modo = "llm"
    else:
        respuesta = _respuesta_local(body.mensaje, contexto_resumido(ctx))
        modo = "experto-local"

    return {
        "respuesta": respuesta,
        "modo": modo,
        "finca_id": body.finca_id,
        "cultivo_id": str(cultivo_uuid) if cultivo_uuid else None,
        "cultivo": cultivo.nombre if cultivo else None,
        "clasificacion_upra": ctx["clasificacion"],
        "nota": (
            "Respuesta generada por el sistema experto local."
            if modo == "experto-local" else None
        ),
    }
