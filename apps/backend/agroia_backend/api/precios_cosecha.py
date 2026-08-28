"""API de precios de cosecha — inteligencia de mercado de venta (UC1).

- GET  /api/v1/cultivos/precios?departamento= — precios por departamento.
- PUT  /api/v1/admin/precios-cosecha — (Admin) actualiza el precio de un cultivo.
"""

import uuid as uuid_mod
from datetime import date

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.cultivo import Cultivo
from agroia_backend.models.precio_cosecha import PrecioCosecha
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["precios-cosecha"])


class PrecioRequest(BaseModel):
    cultivo_id: str
    departamento: str = Field(..., min_length=2, max_length=100)
    precio_promedio_cop_kg: float = Field(..., gt=0, le=1_000_000)
    rendimiento_promedio_t_ha: float | None = Field(None, gt=0, le=200)
    fuente: str = Field("Ingreso manual", max_length=100)


def _a_dict(p: PrecioCosecha, nombre_cultivo: str | None = None) -> dict:
    return {
        "id": str(p.id),
        "cultivo_id": str(p.cultivo_id),
        "cultivo": nombre_cultivo,
        "departamento": p.departamento,
        "precio_promedio_cop_kg": p.precio_promedio_cop_kg,
        "rendimiento_promedio_t_ha": p.rendimiento_promedio_t_ha,
        "fecha_actualizacion": (
            p.fecha_actualizacion.isoformat() if p.fecha_actualizacion else None
        ),
        "fuente": p.fuente,
    }


@router.get("/cultivos/precios")
async def precios_por_departamento(
    departamento: str | None = None,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Precios de cosecha vigentes (opcionalmente filtrados por departamento)."""
    if not x_user_role:
        raise HTTPException(status_code=401, detail={
            "code": "UNAUTHORIZED", "message": "Autenticación requerida.",
        })
    query = select(PrecioCosecha).order_by(
        PrecioCosecha.departamento, PrecioCosecha.fecha_actualizacion.desc()
    )
    if departamento:
        query = query.where(PrecioCosecha.departamento == departamento.strip())
    filas = (await db.execute(query.limit(500))).scalars().all()
    cultivos = {
        c.id: c.nombre
        for c in (await db.execute(select(Cultivo))).scalars().all()
    }
    return {
        "data": [_a_dict(p, cultivos.get(p.cultivo_id)) for p in filas],
        "total": len(filas),
    }


@router.put("/admin/precios-cosecha")
async def actualizar_precio(
    body: PrecioRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """(Admin) Actualiza el precio de cosecha de un cultivo en un departamento."""
    rol = (x_user_role or "").strip().lower()
    if rol not in {"admin", "administrador"}:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE", "message": "Solo el rol administrador.",
        })
    try:
        cultivo_uuid = uuid_mod.UUID(body.cultivo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "CULTIVO_INVALIDO", "message": "cultivo_id no es un UUID.",
        }) from None

    cultivo = (
        await db.execute(select(Cultivo).where(Cultivo.id == cultivo_uuid))
    ).scalar_one_or_none()
    if cultivo is None:
        raise HTTPException(status_code=404, detail={
            "code": "CULTIVO_NOT_FOUND", "message": "Cultivo no registrado.",
        })

    # Un solo precio vigente por (cultivo, departamento)
    precio = (
        await db.execute(
            select(PrecioCosecha).where(
                PrecioCosecha.cultivo_id == cultivo_uuid,
                PrecioCosecha.departamento == body.departamento.strip(),
            )
        )
    ).scalar_one_or_none()
    if precio is None:
        precio = PrecioCosecha(
            cultivo_id=cultivo_uuid,
            departamento=body.departamento.strip(),
            precio_promedio_cop_kg=body.precio_promedio_cop_kg,
            rendimiento_promedio_t_ha=body.rendimiento_promedio_t_ha,
            fecha_actualizacion=date.today(),
            fuente=body.fuente,
        )
        db.add(precio)
    else:
        precio.precio_promedio_cop_kg = body.precio_promedio_cop_kg
        precio.rendimiento_promedio_t_ha = body.rendimiento_promedio_t_ha
        precio.fecha_actualizacion = date.today()
        precio.fuente = body.fuente

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        rol=x_user_role,
        accion="precio_cosecha.actualizar",
        entidad="cultivo",
        entidad_id=str(cultivo_uuid),
        detalle={
            "departamento": body.departamento,
            "precio_cop_kg": body.precio_promedio_cop_kg,
            "fuente": body.fuente,
        },
    )
    await db.commit()
    await db.refresh(precio)
    logger.info(
        "precio_cosecha_ok", cultivo=cultivo.nombre,
        departamento=body.departamento,
    )
    return {"data": _a_dict(precio, cultivo.nombre)}
