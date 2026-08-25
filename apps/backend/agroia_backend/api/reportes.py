"""Generación de reportes de análisis de suelo (HTML + PDF vía navegador).

Tipos:
  - siembra:  recomendación de siembra (UC1).
  - cultivo:  recomendación para el cultivo sembrado (UC2).
  - completo: UC1 + UC2 en un solo documento.
"""

import uuid as uuid_mod
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia.database import get_db
from agroia.errors import InsufficientDataError
from agroia.logging import get_logger
from agroia_backend.models.dispositivo_iot import DispositivoIoT
from agroia_backend.models.finca import Finca
from agroia_backend.models.sensor_reading import SensorReading
from agroia_backend.services.acceso import verificar_acceso_finca
from agroia_backend.services.aptitud import AptitudService
from agroia_backend.services.data_adapters import SueloAdapter
from agroia_backend.services.orchestrator import (
    RecommendationOrchestrator,
    RecommendationRequest,
)
from agroia_backend.services.reportes_html import generar_reporte_html
from agroia_backend.services.rules_engine import RulesEngine

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/reportes", tags=["reportes"])


class ReporteRequest(BaseModel):
    finca_id: str = Field(..., description="UUID de la finca a reportar")
    tipo: str = Field("completo", pattern="^(siembra|cultivo|completo)$")
    cultivo_id: Optional[str] = Field(None, description="UUID del cultivo sembrado (obligatorio en tipo 'cultivo')")


@router.post("/generar")
async def generar_reporte(
    body: ReporteRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
):
    """Genera el HTML del reporte según el tipo solicitado."""
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

    dispositivo = (
        await db.execute(
            select(DispositivoIoT)
            .where(DispositivoIoT.finca_id == finca_uuid)
            .order_by(DispositivoIoT.created_at)
            .limit(1)
        )
    ).scalars().first()

    if lectura is None:
        raise HTTPException(status_code=422, detail={
            "code": "SIN_LECTURAS",
            "message": "La finca no tiene lecturas de sensores. Envíe una trama o cargue un archivo primero.",
        })

    # ── Ejecutar el motor según el tipo de reporte ──
    rules_engine = RulesEngine(db)
    orch = RecommendationOrchestrator(
        db_session=db,
        soil_adapter=SueloAdapter(db),
        rules_engine=rules_engine,
        aptitud_service=AptitudService(db, rules_engine),
    )

    def _analizar(cultivo_id):
        return orch.analyze(RecommendationRequest(
            finca_id=body.finca_id, cultivo_id=cultivo_id,
        ))

    uc1 = uc2 = None
    try:
        if body.tipo in ("siembra", "completo"):
            uc1 = await _analizar(None)
        if body.tipo in ("cultivo", "completo"):
            cultivo = body.cultivo_id
            if not cultivo and body.tipo == "completo" and uc1 and uc1.sugerencias_cultivos:
                cultivo = uc1.sugerencias_cultivos[0].get("cultivo_id")
            if body.tipo == "cultivo" and not cultivo:
                raise HTTPException(status_code=422, detail={
                    "code": "CULTIVO_REQUERIDO",
                    "message": "El tipo 'cultivo' requiere cultivo_id.",
                })
            if cultivo:
                uc2 = await _analizar(cultivo)
    except InsufficientDataError as e:
        raise HTTPException(status_code=422, detail={
            "code": "INSUFFICIENT_DATA",
            "message": "Datos insuficientes para el reporte. Variables faltantes: " + ", ".join(e.missing_vars),
            "missing_variables": e.missing_vars,
        })

    html = generar_reporte_html(
        finca={
            "nombre": finca.nombre,
            "departamento": finca.departamento,
            "municipio": finca.municipio,
            "propietario": finca.propietario,
            "contacto_telefono": finca.contacto_telefono,
            "area_hectareas": finca.area_hectareas,
            "latitud": finca.latitud,
            "longitud": finca.longitud,
        },
        lectura={
            "ts": lectura.ts.isoformat() if lectura.ts else None,
            "sensor_id": lectura.sensor_id,
            "ph": lectura.ph,
            "nitrogeno": lectura.nitrogeno,
            "fosforo": lectura.fosforo,
            "potasio": lectura.potasio,
            "conductividad_electrica": lectura.conductividad_electrica,
            "humedad_ambiental": lectura.humedad_ambiental,
            "temperatura_ambiental": lectura.temperatura_ambiental,
            "materia_organica": lectura.materia_organica,
            "calidad": lectura.calidad,
        },
        dispositivo={
            "device_id": dispositivo.device_id,
            "rssi": dispositivo.rssi,
            "uptime_s": dispositivo.uptime_s,
            "npk_calibrado": dispositivo.npk_calibrado,
        } if dispositivo else None,
        tipo=body.tipo,
        uc1=asdict(uc1) if uc1 else None,
        uc2=asdict(uc2) if uc2 else None,
    )

    titulo = {
        "siembra": "Reporte de recomendación de siembra",
        "cultivo": "Reporte de recomendación para el cultivo sembrado",
        "completo": "Reporte completo de análisis",
    }.get(body.tipo, "Reporte AgroIA")

    logger.info("reporte_generado", finca_id=body.finca_id, tipo=body.tipo, rol=(x_user_role or "?"))
    return {"titulo": titulo, "tipo": body.tipo, "html": html}
