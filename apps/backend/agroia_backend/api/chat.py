"""Chat con el asesor agronómico experto (explica reportes y da consejos).

Disponible para administrador, agrónomo y cliente. El acceso se limita a
las fincas que el rol puede ver (`verificar_acceso_finca`).

Sin OPENAI_API_KEY responde el motor experto local (reglas + lectura);
con la key configurada, responde el LLM con el mismo contexto real.
"""

import uuid as uuid_mod
from datetime import datetime, timezone

from agroia.database import get_db
from agroia.errors import AgroIAError
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.chat_memoria import ChatMemoria
from agroia_backend.models.cultivo import Cultivo, FichaTecnica
from agroia_backend.models.finca import Finca
from agroia_backend.models.regla_agronomica import ReglaAgronomica
from agroia_backend.models.sensor_reading import SensorReading
from agroia_backend.services.acceso import verificar_acceso_finca
from agroia_backend.services.agronomo_chat import (
    consultar_experto,
    construir_contexto,
    contexto_resumido,
    respuesta_orquestada,
    vision_disponible,
)
from agroia_backend.services.agronomo_kb import (
    contexto_climatico,
    contexto_conocimiento,
    resumen_climatico,
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
    imagen_base64: str | None = Field(
        None,
        max_length=6_000_000,
        description="Foto del cultivo en base64 (JPG/PNG, sin prefijo data:)",
    )

    @field_validator("imagen_base64")
    @classmethod
    def _limpiar_imagen(cls, v):
        if not v:
            return None
        v = v.strip()
        if v.startswith("data:image/"):
            v = v.split(",", 1)[1]
        if len(v) > 6_000_000:  # ~4,5 MB máx.
            raise ValueError("La imagen supera el tamaño máximo (4,5 MB).")
        return v or None


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

    # ── Clima disponible (época del año + sensores ambientales; sin inventar) ──
    clima = contexto_climatico(
        finca=finca,
        lectura=lectura,
        fecha=datetime.now(timezone.utc),
    )

    ctx = {
        "recomendaciones": recomendaciones,
        "reglas": list(reglas),
        "sugerencias": sugerencias,
        "clasificacion": (uc2.clasificacion_upra if uc2 else (uc1.clasificacion_upra if uc1 else None)),
        "lectura": lectura,
        "rol": x_user_role or "cliente",
        "clima": clima,
        "cultivo": cultivo.nombre if cultivo else None,
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
    contexto_texto += (
        "\n\nINFORMACIÓN CLIMÁTICA DISPONIBLE:\n" + resumen_climatico(clima)
        + "\n\nBASE DE CONOCIMIENTO AGRONÓMICO (general, con fuentes):\n"
        + contexto_conocimiento()
    )

    # ── Imagen adjunta: visión si el modelo la soporta; si no, referencia ──
    imagen = body.imagen_base64
    vision = imagen is not None and vision_disponible()
    mensaje_efectivo = body.mensaje
    if imagen and not vision:
        mensaje_efectivo = (
            body.mensaje
            + "\n\nNOTA: El usuario adjuntó una imagen del cultivo (hojas, "
            "planta o síntoma). No hay análisis visual disponible: quedó "
            "guardada como referencia en la memoria de la finca y el "
            "diagnóstico se basa en la descripción textual."
        )

    resultado = await consultar_experto(
        mensaje=mensaje_efectivo,
        historial=body.historial or [],
        contexto=contexto_texto,
        rol=x_user_role or "cliente",
        imagen_base64=imagen if vision else None,
    )

    if resultado["modo"] == "llm" and resultado["respuesta"]:
        respuesta = resultado["respuesta"]
        modo = "llm"
        fuentes = ["Base de conocimiento AgroIA (Agrosavia/Cenicafé/UPRA/ICA/IDEAM)"]
        confianza = None
        falta = None
        datos_utilizados = ["contexto de la finca", "análisis del motor", "clima disponible"]
    else:
        orquestado = respuesta_orquestada(mensaje_efectivo, contexto_resumido(ctx))
        respuesta = orquestado["respuesta"] or ""
        modo = "experto-local"
        fuentes = orquestado.get("fuentes") or []
        confianza = orquestado.get("confianza")
        falta = orquestado.get("falta")
        datos_utilizados = orquestado.get("datos_utilizados") or []

    # ── Memoria de finca (el usuario puede volver después) ──
    db.add(ChatMemoria(
        finca_id=finca_uuid,
        usuario_email=x_user_email,
        rol=x_user_role,
        pregunta=body.mensaje,
        respuesta=respuesta,
        fuentes="; ".join(fuentes) if fuentes else None,
        confianza=confianza,
        imagen_base64=imagen,
    ))
    await db.commit()

    return {
        "respuesta": respuesta,
        "modo": modo,
        "finca_id": body.finca_id,
        "cultivo_id": str(cultivo_uuid) if cultivo_uuid else None,
        "cultivo": cultivo.nombre if cultivo else None,
        "clasificacion_upra": ctx["clasificacion"],
        "fuentes": fuentes,
        "confianza": confianza,
        "datos_utilizados": datos_utilizados,
        "falta": falta,
        "clima": resumen_climatico(clima),
        "imagen_analizada": bool(imagen and vision),
        "imagen_guardada": bool(imagen),
        "nota": (
            "Respuesta generada por el sistema experto local."
            if modo == "experto-local" else None
        ),
    }


@router.get("/memoria/{finca_id}")
async def memoria_chat(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Memoria conversacional de la finca (últimas consultas y respuestas)."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })
    registros = (
        await db.execute(
            select(ChatMemoria)
            .where(ChatMemoria.finca_id == finca_uuid)
            .order_by(ChatMemoria.ts.desc())
            .limit(20)
        )
    ).scalars().all()
    return {
        "finca_id": finca_id,
        "total": len(registros),
        "registros": [
            {
                "pregunta": r.pregunta,
                "respuesta": r.respuesta,
                "fuentes": r.fuentes,
                "confianza": r.confianza,
                "ts": r.ts.isoformat() if r.ts else None,
            }
            for r in registros
        ],
    }
