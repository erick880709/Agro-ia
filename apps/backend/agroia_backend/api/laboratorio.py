"""API de análisis de laboratorio ICA — ingesta de resultados de suelo.

- POST /fincas/{id}/lab/ingestar (Admin/Agrónomo/Extensionista en su zona)
- GET  /fincas/{id}/lab/analisis (fincas visibles)
- DELETE /fincas/{id}/lab/analisis/{analisis_id} (solo Admin)
"""

import uuid as uuid_mod
from datetime import date

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.analisis_laboratorio import AnalisisLaboratorio
from agroia_backend.models.finca import Finca
from agroia_backend.services.acceso import (
    exigir_no_cliente,
    verificar_acceso_finca,
)
from agroia_backend.services.analisis_laboratorio import normalizar_resultados
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["laboratorio-ica"])

VARIABLES_VALIDADORAS = {"nitrogeno", "fosforo", "potasio", "ph", "materia_organica"}


class IngestaLabRequest(BaseModel):
    laboratorio_nombre: str | None = Field(None, max_length=200)
    lote_id: str | None = None
    fecha_muestreo: date
    fecha_resultado: date
    resultados: dict = Field(..., description="Pares variable -> valor (pH, N, P, K, MO…)")


def _a_dict(a: AnalisisLaboratorio) -> dict:
    return {
        "id": str(a.id),
        "finca_id": str(a.finca_id),
        "lote_id": str(a.lote_id) if a.lote_id else None,
        "laboratorio_nombre": a.laboratorio_nombre,
        "fecha_muestreo": a.fecha_muestreo.isoformat() if a.fecha_muestreo else None,
        "fecha_resultado": a.fecha_resultado.isoformat() if a.fecha_resultado else None,
        "resultados": a.resultados,
        "fuente": a.fuente,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.post("/fincas/{finca_id}/lab/ingestar", status_code=201)
async def ingestar_analisis(
    finca_id: str,
    body: IngestaLabRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Ingesta de resultados de laboratorio; valida rangos y prioriza sobre el sensor."""
    rol = (x_user_role or "").strip().lower()
    exigir_no_cliente(rol)
    finca = (
        await db.execute(select(Finca).where(Finca.id == uuid_mod.UUID(finca_id)))
    ).scalar_one_or_none() if _es_uuid(finca_id) else None
    if finca is None:
        raise HTTPException(status_code=404, detail={
            "code": "FINCA_NOT_FOUND", "message": "La finca no está registrada.",
        })
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)

    resultados, rechazadas = normalizar_resultados(body.resultados)
    if not resultados:
        raise HTTPException(status_code=422, detail={
            "code": "LAB_SIN_VARIABLES_VALIDAS",
            "message": "Ninguna variable válida. Rechazadas: " + ", ".join(rechazadas),
        })

    lote_uuid = None
    if body.lote_id and _es_uuid(body.lote_id):
        lote_uuid = uuid_mod.UUID(body.lote_id)

    analisis = AnalisisLaboratorio(
        finca_id=uuid_mod.UUID(finca_id),
        lote_id=lote_uuid,
        laboratorio_nombre=body.laboratorio_nombre,
        fecha_muestreo=body.fecha_muestreo,
        fecha_resultado=body.fecha_resultado,
        resultados=resultados,
        fuente="ingreso_manual",
    )
    db.add(analisis)

    # Si cubre variables validadoras → la finca queda con validación de laboratorio
    if VARIABLES_VALIDADORAS & set(resultados):
        finca.validacion_laboratorio = True

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        rol=x_user_role,
        accion="laboratorio.ingestar",
        entidad="finca",
        entidad_id=finca_id,
        detalle={
            "laboratorio": body.laboratorio_nombre,
            "variables": sorted(resultados),
            "rechazadas": rechazadas,
        },
    )
    await db.commit()
    await db.refresh(analisis)
    logger.info(
        "lab_ingesta_ok", finca_id=finca_id,
        variables=sorted(resultados), rechazadas=rechazadas,
    )
    return {"data": _a_dict(analisis), "rechazadas": rechazadas}


@router.get("/fincas/{finca_id}/lab/analisis")
async def historial_analisis(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Historial de análisis de laboratorio de la finca."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    if not _es_uuid(finca_id):
        return {"data": [], "total": 0}
    analisis = (
        await db.execute(
            select(AnalisisLaboratorio)
            .where(AnalisisLaboratorio.finca_id == uuid_mod.UUID(finca_id))
            .order_by(AnalisisLaboratorio.fecha_resultado.desc())
            .limit(50)
        )
    ).scalars().all()
    return {"data": [_a_dict(a) for a in analisis], "total": len(analisis)}


@router.delete("/fincas/{finca_id}/lab/analisis/{analisis_id}")
async def eliminar_analisis(
    finca_id: str,
    analisis_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Elimina un análisis erróneo (solo Admin)."""
    rol = (x_user_role or "").strip().lower()
    if rol not in {"admin", "administrador"}:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE", "message": "Solo el rol administrador.",
        })
    if not (_es_uuid(finca_id) and _es_uuid(analisis_id)):
        raise HTTPException(status_code=422, detail={
            "code": "ID_INVALIDO", "message": "IDs inválidos.",
        })
    analisis = (
        await db.execute(
            select(AnalisisLaboratorio).where(
                AnalisisLaboratorio.id == uuid_mod.UUID(analisis_id),
                AnalisisLaboratorio.finca_id == uuid_mod.UUID(finca_id),
            )
        )
    ).scalar_one_or_none()
    if analisis is None:
        raise HTTPException(status_code=404, detail={
            "code": "ANALISIS_NOT_FOUND", "message": "Análisis no encontrado.",
        })
    await registrar_auditoria(
        db,
        usuario_email="admin@agroia.co",
        rol=x_user_role,
        accion="laboratorio.eliminar",
        entidad="finca",
        entidad_id=finca_id,
        detalle={"analisis_id": analisis_id},
    )
    await db.delete(analisis)
    await db.commit()
    return {"status": "ok"}


def _es_uuid(s: str | None) -> bool:
    try:
        uuid_mod.UUID(str(s))
        return True
    except (ValueError, TypeError, AttributeError):
        return False
