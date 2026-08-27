"""Endpoint de mantenimiento demo (solo administrador).

Restablece los datos operativos conservando únicamente las lecturas del
sensor real y crea la finca demo completa. Uso: demostraciones.
"""

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.services.acceso import _normalizar
from agroia_backend.services.auditoria import auditar_y_commit
from agroia_backend.services.demo_reset import restablecer_demo

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.post("/reset")
async def reset_demo(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Restablece la BD de demostración (solo rol Admin)."""
    if _normalizar(x_user_role) != "admin":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol Admin puede restablecer los datos de demostración.",
        })
    resumen = await restablecer_demo(db)
    await auditar_y_commit(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        rol=x_user_role,
        accion="demo.reset",
        entidad="demo",
        detalle=resumen,
    )
    return {"status": "ok", **resumen}
