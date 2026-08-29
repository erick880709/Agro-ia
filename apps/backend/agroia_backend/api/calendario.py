"""API del Almanaque Bristol — calendario lunar y preferencias (v3.4)."""

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.preferencia_bristol import PreferenciaBristol
from agroia_backend.models.usuario import Usuario
from agroia_backend.services.auditoria import registrar_auditoria
from agroia_backend.services.calendario_lunar import (
    BRISTOL_ACTIVADO,
    calendario_mes,
    estado_bristol,
    pronostico_lunar,
    resumen_bristol,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["calendario-lunar"])


async def _usuario_por_email(db: AsyncSession, email: str | None) -> Usuario | None:
    if not email:
        return None
    return (
        await db.execute(select(Usuario).where(Usuario.email == email.lower()))
    ).scalar_one_or_none()


async def _preferencias(db: AsyncSession, usuario_id) -> PreferenciaBristol | None:
    return (
        await db.execute(
            select(PreferenciaBristol).where(PreferenciaBristol.usuario_id == usuario_id)
        )
    ).scalar_one_or_none()


@router.get("/calendario-lunar/actual")
async def calendario_lunar_actual(
    lat: float = Query(0.0, ge=-90, le=90),
    lon: float = Query(0.0, ge=-180, le=180),
):
    """Fase lunar actual y recomendación Bristol (todos los roles)."""
    return resumen_bristol(None, lat, lon)


@router.get("/calendario-lunar/pronostico")
async def calendario_lunar_pronostico(
    dias: int = Query(7, ge=1, le=30),
    lat: float = Query(0.0, ge=-90, le=90),
    lon: float = Query(0.0, ge=-180, le=180),
):
    """Fases de los próximos `dias` días con recomendación y favorabilidad."""
    return {"data": pronostico_lunar(dias, lat, lon), "total": dias}


@router.get("/calendario-lunar/mes")
async def calendario_lunar_mes(
    anio: int = Query(..., ge=1900, le=2200),
    mes: int = Query(..., ge=1, le=12),
):
    """Fases lunares de todos los días de un mes (calendario navegable)."""
    return calendario_mes(anio, mes)


@router.get("/calendario-lunar/estado")
async def calendario_lunar_estado(
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Fuente activa del cálculo lunar (solo Admin)."""
    rol = (x_user_role or "").strip().lower()
    if rol not in {"admin", "administrador"}:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol administrador puede consultar el estado del módulo.",
        })
    return estado_bristol()


class PreferenciaBristolBody(BaseModel):
    mostrar_en_reportes: bool | None = Field(None, description="Incluir sección lunar en reportes")
    generar_alertas_siembra: bool | None = Field(None, description="Generar alertas de siembra lunar")


@router.get("/usuarios/preferencias-bristol")
async def obtener_preferencias_bristol(
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Preferencias Bristol del usuario autenticado."""
    usuario = await _usuario_por_email(db, x_user_email)
    if usuario is None:
        raise HTTPException(status_code=404, detail={
            "code": "USUARIO_NOT_FOUND", "message": "Usuario no registrado.",
        })
    pref = await _preferencias(db, usuario.id)
    return {
        "modulo_activado": BRISTOL_ACTIVADO,
        "mostrar_en_reportes": pref.mostrar_en_reportes if pref else True,
        "generar_alertas_siembra": pref.generar_alertas_siembra if pref else True,
    }


@router.put("/usuarios/preferencias-bristol")
async def actualizar_preferencias_bristol(
    body: PreferenciaBristolBody,
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Activa/desactiva alertas de siembra y visibilidad en reportes (toggle)."""
    usuario = await _usuario_por_email(db, x_user_email)
    if usuario is None:
        raise HTTPException(status_code=404, detail={
            "code": "USUARIO_NOT_FOUND", "message": "Usuario no registrado.",
        })
    pref = await _preferencias(db, usuario.id)
    if pref is None:
        pref = PreferenciaBristol(usuario_id=usuario.id)
        db.add(pref)
    if body.mostrar_en_reportes is not None:
        pref.mostrar_en_reportes = body.mostrar_en_reportes
    if body.generar_alertas_siembra is not None:
        pref.generar_alertas_siembra = body.generar_alertas_siembra
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        rol=None,
        accion="bristol.actualizar_preferencias",
        entidad="preferencias_bristol",
        entidad_id=str(usuario.id),
        detalle={
            "mostrar_en_reportes": pref.mostrar_en_reportes,
            "generar_alertas_siembra": pref.generar_alertas_siembra,
        },
    )
    await db.commit()
    logger.info(
        "bristol_preferencias_actualizadas",
        usuario_id=str(usuario.id),
        generar_alertas_siembra=pref.generar_alertas_siembra,
        mostrar_en_reportes=pref.mostrar_en_reportes,
    )
    return {
        "status": "ok",
        "mostrar_en_reportes": pref.mostrar_en_reportes,
        "generar_alertas_siembra": pref.generar_alertas_siembra,
    }
