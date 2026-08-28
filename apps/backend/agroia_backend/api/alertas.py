"""API de alertas climáticas proactivas."""

from datetime import datetime, timezone

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.alerta_climatica import AlertaClimatica
from agroia_backend.models.finca import Finca
from agroia_backend.services.acceso import (
    fincas_permitidas_ids,
    verificar_acceso_finca,
)
from agroia_backend.services.clima_alertas import evaluar_alertas_finca, evaluar_todas_fincas

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["alertas-climaticas"])


def _alerta_a_dict(a) -> dict:
    return {
        "id": str(a.id),
        "finca_id": str(a.finca_id),
        "tipo": a.tipo,
        "severidad": a.severidad,
        "mensaje": a.mensaje,
        "fecha_alerta": a.fecha_alerta.isoformat() if a.fecha_alerta else None,
        "pronostico": a.pronostico,
        "activa": a.activa,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


class EvaluarRequest(BaseModel):
    finca_id: str | None = Field(None, description="Solo esta finca; vacío = todas")
    pronostico: list[dict] | None = Field(
        None, description="Pronóstico inyectado (para pruebas/demo determinista)"
    )


@router.get("/fincas/{finca_id}/alertas-climaticas/activas")
async def alertas_activas(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Alertas meteorológicas activas de la finca (banner del Dashboard)."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    hoy = datetime.now(timezone.utc).date()
    alertas = (
        await db.execute(
            select(AlertaClimatica)
            .where(
                AlertaClimatica.finca_id == finca_id,
                AlertaClimatica.activa.is_(True),
                AlertaClimatica.fecha_alerta == hoy,
            )
            .order_by(AlertaClimatica.created_at.desc())
        )
    ).scalars().all()
    return {"data": [_alerta_a_dict(a) for a in alertas], "total": len(alertas)}


@router.get("/alertas-climaticas")
async def alertas_globales(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Listado «⛅ Alertas clima»: alertas activas de las fincas visibles para el rol.

    - Cliente → solo sus fincas (según `fincas_permitidas_ids`).
    - Extensionista → solo fincas de sus municipios asignados.
    - Agrónomo / Admin → todas las fincas.
    Cada alerta incluye `finca_nombre`, `departamento`, `municipio`, `latitud` y
    `longitud` para que el frontend agrupe las fincas que comparten ubicación y
    muestre la alerta con el departamento y la ciudad.
    """

    query = (
        select(AlertaClimatica, Finca)
        .join(Finca, Finca.id == AlertaClimatica.finca_id)
        .where(AlertaClimatica.activa.is_(True))
        .order_by(
            AlertaClimatica.fecha_alerta.desc(),
            AlertaClimatica.created_at.desc(),
        )
    )

    permitidas = await fincas_permitidas_ids(db, x_user_role, x_user_email)
    if permitidas is not None:
        if not permitidas:
            return {"data": [], "total": 0}
        query = query.where(AlertaClimatica.finca_id.in_(permitidas))

    filas = (await db.execute(query)).all()
    data: list[dict] = []
    for alerta, finca in filas:
        item = _alerta_a_dict(alerta)
        item.update({
            "finca_nombre": finca.nombre,
            "departamento": finca.departamento,
            "municipio": finca.municipio,
            "latitud": float(finca.latitud) if finca.latitud is not None else None,
            "longitud": float(finca.longitud) if finca.longitud is not None else None,
        })
        data.append(item)
    return {"data": data, "total": len(data)}


@router.post("/alertas-climaticas/evaluar")
async def evaluar_alertas(
    body: EvaluarRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Dispara la evaluación de alertas (manual o con pronóstico inyectado)."""
    rol = (x_user_role or "").strip().lower()
    if rol not in {"admin", "administrador"}:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol administrador puede disparar la evaluación.",
        })
    if body.finca_id:
        import uuid as uuid_mod

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
        creadas = await evaluar_alertas_finca(db, finca, pronostico=body.pronostico)
        return {"status": "ok", "fincas_evaluadas": 1, "alertas_creadas": len(creadas), "alertas": creadas}

    resumen = await evaluar_todas_fincas(db)
    return {"status": "ok", **resumen}
