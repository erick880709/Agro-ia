"""API de sincronización offline (PWA) — tramas de sensores y labores en batch.

Cada item trae `idempotency_key`: los duplicados se detectan contra
`agroia.sync_registro` y se omiten (reintentos seguros tras cortes de red).
"""

import uuid as uuid_mod
from datetime import date, datetime, timezone

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.api.sensor_api import SensorFrame, ingesta_sensor
from agroia_backend.models.labor import Labor
from agroia_backend.models.sync_registro import SyncRegistro
from agroia_backend.services.acceso import exigir_no_cliente
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/sync", tags=["sync-offline"])


class ItemSensor(BaseModel):
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    trama: dict = Field(..., description="Trama igual a POST /api/sensor")


class BatchSensor(BaseModel):
    items: list[ItemSensor] = Field(..., min_length=1, max_length=200)


class ItemLabor(BaseModel):
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    labor_id: str
    estado: str = Field(..., max_length=40)
    observaciones_ejecucion: str | None = Field(None, max_length=2000)
    fecha_ejecucion: date | None = None


class BatchLabor(BaseModel):
    items: list[ItemLabor] = Field(..., min_length=1, max_length=200)


async def _ya_procesado(db, key: str) -> bool:
    fila = (
        await db.execute(
            select(SyncRegistro.idempotency_key).where(
                SyncRegistro.idempotency_key == key
            )
        )
    ).scalar_one_or_none()
    return fila is not None


@router.get("/estado")
async def estado_sync(
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Estado del servidor para la app offline (hora y salud)."""
    if not x_user_role:
        raise HTTPException(status_code=401, detail={
            "code": "UNAUTHORIZED", "message": "Autenticación requerida.",
        })
    return {
        "estado": "ok",
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/sensor-readings")
async def sync_sensores(
    body: BatchSensor,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Reenvía tramas de sensores capturadas offline (idempotente)."""
    exigir_no_cliente(x_user_role)
    aceptados, duplicados, errores = [], [], []
    for item in body.items:
        if await _ya_procesado(db, item.idempotency_key):
            duplicados.append(item.idempotency_key)
            continue
        try:
            frame = SensorFrame(**item.trama)
            await ingesta_sensor(frame)
            db.add(SyncRegistro(
                idempotency_key=item.idempotency_key,
                tipo="sensor",
                usuario_email=x_user_email,
                resultado="ok",
            ))
            await db.commit()
            aceptados.append(item.idempotency_key)
        except Exception as e:  # noqa: BLE001 — no romper el batch
            await db.rollback()
            logger.warning("sync_sensor_error", key=item.idempotency_key, error=str(e))
            errores.append({"idempotency_key": item.idempotency_key, "error": str(e)})
    return {
        "aceptados": len(aceptados),
        "duplicados": len(duplicados),
        "errores": errores,
    }


@router.post("/labores")
async def sync_labores(
    body: BatchLabor,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Actualiza labores completadas offline (idempotente)."""
    exigir_no_cliente(x_user_role)
    aceptados, duplicados, errores = [], [], []
    for item in body.items:
        if await _ya_procesado(db, item.idempotency_key):
            duplicados.append(item.idempotency_key)
            continue
        try:
            labor = (
                await db.execute(
                    select(Labor).where(Labor.id == uuid_mod.UUID(item.labor_id))
                )
            ).scalar_one_or_none()
            if labor is None:
                raise ValueError("labor no encontrada")
            labor.estado = item.estado
            if item.observaciones_ejecucion is not None:
                labor.observaciones_ejecucion = item.observaciones_ejecucion
            if item.fecha_ejecucion is not None:
                labor.fecha_ejecucion = item.fecha_ejecucion
            await registrar_auditoria(
                db,
                usuario_email=x_user_email or "desconocido@agroia.co",
                rol=x_user_role,
                accion="labor.actualizar_offline",
                entidad="labor",
                entidad_id=item.labor_id,
                detalle={"estado": item.estado, "sync": True},
            )
            db.add(SyncRegistro(
                idempotency_key=item.idempotency_key,
                tipo="labor",
                usuario_email=x_user_email,
                resultado="ok",
            ))
            await db.commit()
            aceptados.append(item.idempotency_key)
        except Exception as e:  # noqa: BLE001
            await db.rollback()
            logger.warning("sync_labor_error", key=item.idempotency_key, error=str(e))
            errores.append({"idempotency_key": item.idempotency_key, "error": str(e)})
    return {
        "aceptados": len(aceptados),
        "duplicados": len(duplicados),
        "errores": errores,
    }
