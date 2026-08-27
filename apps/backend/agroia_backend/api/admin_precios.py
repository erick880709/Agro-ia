"""API admin de precios de insumos (COP/kg) — ROI dinámico."""

from datetime import date

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.precio_insumo import PrecioInsumo
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin-precios"])

ROL_ADMIN = {"admin", "administrador"}


def _exigir_admin(rol: str | None) -> str:
    rol = (rol or "").strip().lower()
    if rol not in ROL_ADMIN:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el administrador puede gestionar los precios de insumos.",
        })
    return rol


class PrecioInsumoItem(BaseModel):
    producto: str = Field(..., min_length=2, max_length=100)
    precio_kg_cop: float = Field(..., gt=0, le=1_000_000)
    fuente: str | None = Field(None, max_length=255)


class PreciosInsumosUpdate(BaseModel):
    precios: list[PrecioInsumoItem] = Field(..., min_length=1, max_length=100)


@router.get("/precios-insumos")
async def listar_precios_insumos(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Precios vigentes de insumos (producto, COP/kg, fecha de actualización)."""
    _exigir_admin(x_user_role)
    filas = (
        await db.execute(select(PrecioInsumo).order_by(PrecioInsumo.producto))
    ).scalars().all()
    return {
        "data": [
            {
                "producto": p.producto,
                "precio_kg_cop": p.precio_kg_cop,
                "fecha_actualizacion": p.fecha_actualizacion.isoformat(),
                "fuente": p.fuente,
            }
            for p in filas
        ],
        "total": len(filas),
    }


@router.put("/precios-insumos")
async def actualizar_precios_insumos(
    body: PreciosInsumosUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Upsert de precios: `{precios: [{producto, precio_kg_cop, fuente?}]}`.

    La fecha de actualización queda en hoy para cada producto; el plan
    económico (`calcular_plan_economico`) lee esta tabla en cada análisis.
    """
    _exigir_admin(x_user_role)
    hoy = date.today()
    actualizados: list[str] = []
    for item in body.precios:
        existente = (
            await db.execute(
                select(PrecioInsumo).where(PrecioInsumo.producto == item.producto.strip())
            )
        ).scalar_one_or_none()
        if existente is not None:
            existente.precio_kg_cop = item.precio_kg_cop
            existente.fecha_actualizacion = hoy
            existente.fuente = item.fuente
        else:
            db.add(PrecioInsumo(
                producto=item.producto.strip(),
                precio_kg_cop=item.precio_kg_cop,
                fecha_actualizacion=hoy,
                fuente=item.fuente,
            ))
        actualizados.append(item.producto.strip())
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="precios.actualizar",
        entidad="precios_insumos",
        detalle={"productos": actualizados, "fecha": hoy.isoformat()},
    )
    await db.commit()
    logger.info("precios_insumos_actualizados", productos=len(actualizados))
    return {
        "status": "updated",
        "actualizados": actualizados,
        "fecha_actualizacion": hoy.isoformat(),
        "mensaje": (
            "Precios actualizados: el ROI y el plan económico usarán estas "
            "cotizaciones desde el próximo análisis."
        ),
    }
