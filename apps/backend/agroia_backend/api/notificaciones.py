"""API de preferencias de notificación (1.I)."""

import uuid as uuid_mod

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.preferencia_notificacion import PreferenciaNotificacion
from agroia_backend.models.usuario import Usuario
from agroia_backend.services.acceso import verificar_acceso_finca

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["notificaciones"])


class PreferenciasRequest(BaseModel):
    canal: str = Field(..., pattern="^(whatsapp|sms|email|ninguno)$")
    telefono: str | None = Field(None, max_length=20)
    activo: bool = True


@router.put("/fincas/{finca_id}/notificaciones/preferencias")
async def preferencias_notificacion(
    finca_id: str,
    body: PreferenciasRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Configura el canal de notificación de una finca (upsert por finca)."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    rol = (x_user_role or "").strip().lower()
    if rol == "cliente" and body.canal != "ninguno":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "El rol Cliente no puede activar canales de notificación masivos.",
        })
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })

    usuario = None
    if x_user_email:
        usuario = (
            await db.execute(select(Usuario).where(Usuario.email == (x_user_email or "").lower()))
        ).scalar_one_or_none()

    pref = (
        await db.execute(
            select(PreferenciaNotificacion).where(PreferenciaNotificacion.finca_id == finca_uuid)
        )
    ).scalar_one_or_none()
    if pref is None:
        pref = PreferenciaNotificacion(finca_id=finca_uuid)
        db.add(pref)
    pref.canal = body.canal
    pref.telefono = body.telefono
    pref.activo = body.activo
    if usuario:
        pref.usuario_id = usuario.id
    await db.commit()
    await db.refresh(pref)
    logger.info("preferencias_notificacion", finca_id=finca_id, canal=body.canal, rol=rol)
    return {
        "status": "saved",
        "finca_id": str(pref.finca_id),
        "canal": pref.canal,
        "telefono": pref.telefono,
        "activo": pref.activo,
    }


@router.get("/fincas/{finca_id}/notificaciones/preferencias")
async def get_preferencias(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Preferencia de notificación actual de la finca."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })
    pref = (
        await db.execute(
            select(PreferenciaNotificacion).where(PreferenciaNotificacion.finca_id == finca_uuid)
        )
    ).scalar_one_or_none()
    if pref is None:
        return {"canal": "ninguno", "telefono": None, "activo": True}
    return {"canal": pref.canal, "telefono": pref.telefono, "activo": pref.activo}
