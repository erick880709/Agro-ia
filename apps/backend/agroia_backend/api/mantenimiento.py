"""API admin de mantenimiento (limpieza de imágenes y otros jobs)."""

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.services.auditoria import registrar_auditoria
from agroia_backend.services.mantenimiento import limpiar_imagenes_chat

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin-mantenimiento"])

ROL_ADMIN = {"admin", "administrador"}


@router.post("/chat/limpiar-imagenes")
async def limpiar_imagenes(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Limpia las imágenes Base64 del chat con más de 90 días (solo Admin).

    El mismo job corre automáticamente cada 24 h en el lifespan; este
    endpoint permite dispararlo manualmente.
    """
    rol = (x_user_role or "").strip().lower()
    if rol not in ROL_ADMIN:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el administrador puede ejecutar mantenimiento.",
        })
    liberadas = await limpiar_imagenes_chat(db, dias=90)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="mantenimiento.chat_imagenes",
        entidad="chat_memoria",
        detalle={"liberadas": liberadas, "dias": 90},
    )
    await db.commit()
    return {
        "status": "ok",
        "liberadas": liberadas,
        "mensaje": f"Se liberaron {liberadas} imagen(es) Base64 del chat (más de 90 días).",
    }
