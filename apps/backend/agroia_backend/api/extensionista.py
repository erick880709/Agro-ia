"""API del rol Extensionista (1.J) — dashboard de zona por municipios."""

from agroia.database import get_db
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.alerta_climatica import AlertaClimatica
from agroia_backend.models.finca import Finca
from agroia_backend.models.recomendacion import Recomendacion
from agroia_backend.services.acceso import get_usuario

router = APIRouter(prefix="/api/v1", tags=["extensionista"])


def _es_extensionista(rol: str | None) -> bool:
    return (rol or "").strip().lower() == "extensionista"


@router.get("/extensionista/dashboard-zona")
async def dashboard_zona(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Fincas de la zona del extensionista (por municipios asignados)."""
    if not _es_extensionista(x_user_role):
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Este endpoint es exclusivo del rol Extensionista.",
        })

    usuario = await get_usuario(db, x_user_email)
    municipios = list(usuario.municipios_asignados or []) if usuario else []
    if not municipios:
        return {
            "municipios": [],
            "fincas": [],
            "resumen": {"total_fincas": 0, "alertas_climaticas_activas": 0, "recomendaciones_pendientes_validacion": 0},
            "nota": "Sin municipios asignados: pida al administrador que los configure.",
        }

    fincas = (
        await db.execute(
            select(Finca).where(Finca.municipio.in_(municipios)).order_by(Finca.nombre)
        )
    ).scalars().all()

    filas = []
    for finca in fincas:
        rec = (
            await db.execute(
                select(Recomendacion)
                .where(Recomendacion.finca_id == finca.id)
                .order_by(Recomendacion.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        alertas = (
            await db.execute(
                select(AlertaClimatica.id)
                .where(AlertaClimatica.finca_id == finca.id, AlertaClimatica.activa.is_(True))
                .limit(5)
            )
        ).scalars().all()
        filas.append({
            "id": str(finca.id),
            "nombre": finca.nombre,
            "municipio": finca.municipio,
            "cultivo_sembrado": finca.cultivo_sembrado,
            "ultima_recomendacion": (
                {
                    "clasificacion": str(getattr(rec.clasificacion_upra, "value", rec.clasificacion_upra)),
                    "confianza": rec.confianza,
                }
                if rec else None
            ),
            "alertas_activas": len(alertas),
        })

    alertas_activas = sum(f["alertas_activas"] for f in filas)
    pendientes = 0
    for finca in fincas:
        rec = (
            await db.execute(
                select(Recomendacion)
                .where(Recomendacion.finca_id == finca.id)
                .order_by(Recomendacion.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if rec is not None and (rec.confianza or 0) < 0.80:
            pendientes += 1

    return {
        "municipios": municipios,
        "fincas": filas,
        "resumen": {
            "total_fincas": len(fincas),
            "alertas_climaticas_activas": alertas_activas,
            "recomendaciones_pendientes_validacion": pendientes,
        },
    }


@router.get("/extensionista/info")
async def info_extensionista(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Municipios asignados del extensionista actual."""
    if not _es_extensionista(x_user_role):
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Este endpoint es exclusivo del rol Extensionista.",
        })
    usuario = await get_usuario(db, x_user_email)
    return {
        "email": usuario.email if usuario else None,
        "rol": str(getattr(usuario.rol, "value", usuario.rol)) if usuario else None,
        "municipios_asignados": list(usuario.municipios_asignados or []) if usuario else [],
    }
