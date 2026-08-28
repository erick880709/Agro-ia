"""API de ciclos productivos por lote (`historial_ciclos_lote`).

Cada lote acumula un historial de ciclos (siembra → cosecha) con fechas,
resultados productivos, manejo agronómico estructurado (aplicaciones e
incidencias JSONB) y observaciones. Gestión: Admin/Agrónomo (crear/editar),
Admin (eliminar). Consulta: cualquier rol con acceso a la finca.
"""

import csv
import io
import re
import uuid as uuid_mod
from datetime import date, datetime

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.ciclo_lote import CicloLote
from agroia_backend.models.cultivo import Cultivo
from agroia_backend.models.finca import Finca
from agroia_backend.models.lote import Lote
from agroia_backend.services.acceso import verificar_acceso_finca
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ciclos"])

ROL_ADMIN = {"admin", "administrador"}
ROL_EXPERTOS = {"admin", "administrador", "agronomo", "agrónomo"}
CALIDADES = {"Premium", "Estándar", "Rechazo"}
RIEGOS = {"Goteo", "Gravedad", "Aspersión", "Secano"}


class CicloCreate(BaseModel):
    cultivo_id: str = Field(..., description="UUID del cultivo del catálogo")
    fecha_siembra: date
    fecha_cosecha: date | None = None
    variedad: str | None = Field(None, max_length=100, description="Variedad sembrada (opcional)")
    densidad_siembra_plantas_ha: float | None = Field(None, ge=0, le=1_000_000, description="Plantas por hectárea (opcional)")
    rendimiento_tn_ha: float | None = Field(None, ge=0, le=1_000, description="t/ha")
    calidad_cosecha: str | None = Field(None, max_length=20, description="Premium | Estándar | Rechazo")
    aplicaciones: list[dict] | None = Field(None, description="[{producto, dosis_kg_ha, fecha, tipo}, …]")
    incidencias: list[dict] | None = Field(None, description="[{plaga, severidad, fecha, control}, …]")
    practicas_riego: str | None = Field(None, max_length=50, description="Goteo | Gravedad | Aspersión | Secano")
    observaciones: str | None = Field(None, max_length=4000)


class CicloUpdate(BaseModel):
    cultivo_id: str | None = None
    fecha_siembra: date | None = None
    fecha_cosecha: date | None = None
    variedad: str | None = Field(None, max_length=100)
    densidad_siembra_plantas_ha: float | None = Field(None, ge=0, le=1_000_000)
    rendimiento_tn_ha: float | None = Field(None, ge=0, le=1_000)
    calidad_cosecha: str | None = Field(None, max_length=20)
    aplicaciones: list[dict] | None = None
    incidencias: list[dict] | None = None
    practicas_riego: str | None = Field(None, max_length=50)
    observaciones: str | None = Field(None, max_length=4000)


class IniciarCicloRequest(BaseModel):
    """Flujo rápido desde Recomendaciones: registra el ciclo y actualiza la finca/lote."""

    cultivo_id: str = Field(..., description="UUID del cultivo (preseleccionado en la UI)")
    fecha_siembra: date = Field(..., description="Fecha de siembra (obligatoria)")
    variedad: str | None = Field(None, max_length=100, description="Variedad (opcional)")
    densidad_siembra_plantas_ha: float | None = Field(None, ge=0, le=1_000_000, description="Plantas/ha (opcional)")


class CosecharCicloRequest(BaseModel):
    """Cierre del ciclo activo: cosecha, rendimiento y resumen de aplicaciones."""

    fecha_cosecha: date = Field(..., description="Fecha de cosecha (la UI la precarga con hoy)")
    rendimiento: float = Field(..., gt=0, le=1_000_000, description="Rendimiento obtenido (obligatorio para el ROI futuro)")
    unidad_rendimiento: str = Field("t_ha", pattern="^(kg_ha|t_ha)$", description="kg_ha | t_ha")
    calidad_cosecha: str | None = Field(None, max_length=20, description="Premium | Estándar | Rechazo (opcional)")
    resumen_aplicaciones: str | None = Field(
        None, max_length=4000,
        description="Texto libre: «Urea 150kg, DAP 80kg» — un parser simple lo convierte a JSONB",
    )


class CargaCiclosCsvRequest(BaseModel):
    """Carga masiva: CSV con el historial de ciclos (últimos 5 años).

    Columnas esperadas: lote, cultivo, fecha_siembra, fecha_cosecha,
    rendimiento, aplicaciones_texto.
    """

    csv_texto: str = Field(..., min_length=1, max_length=2_000_000, description="Contenido del CSV")


COLUMNAS_CICLOS_CSV = {
    "lote", "cultivo", "fecha_siembra", "fecha_cosecha", "rendimiento", "aplicaciones_texto",
}


def _parsear_fecha_csv(valor: str) -> date | None:
    """Acepta ISO (YYYY-MM-DD) o DD/MM/YYYY."""
    v = (valor or "").strip()
    if not v:
        return None
    try:
        return date.fromisoformat(v)
    except ValueError:
        pass
    try:
        return datetime.strptime(v, "%d/%m/%Y").date()
    except ValueError:
        return None


_RE_APLICACION = re.compile(
    r"([A-Za-zÀ-ÿ0-9\.\-\+/ ]+?)\s+(\d+(?:[.,]\d+)?)\s*(g|gr|kg|l|ml|t)?",
    re.UNICODE,
)


def parsear_resumen_aplicaciones(texto: str | None) -> list[dict] | None:
    """Convierte «Urea 150kg, DAP 80kg» en JSONB [{producto, dosis_kg_ha, unidad, tipo}].

    Separa por coma/punto y coma/salto de línea y extrae producto + dosis;
    los gramos se normalizan a kg (÷1000). Sin unidad se asume kg.
    """
    if not texto or not texto.strip():
        return None
    aplicaciones: list[dict] = []
    for parte in re.split(r"[,;\n]+", texto):
        parte = parte.strip()
        if not parte:
            continue
        m = _RE_APLICACION.match(parte)
        if not m:
            continue
        producto = m.group(1).strip()
        dosis = float(m.group(2).replace(",", "."))
        unidad = (m.group(3) or "kg").lower()
        if unidad in {"g", "gr"}:
            dosis = round(dosis / 1000.0, 3)
            unidad = "kg"
        aplicaciones.append({
            "producto": producto,
            "dosis_kg_ha": dosis,
            "unidad": unidad,
            "tipo": "Fertilizante",
        })
    return aplicaciones or None


def _exigir_rol(rol: str | None, permitidos: set[str], mensaje: str) -> str:
    rol_norm = (rol or "").strip().lower()
    if rol_norm not in permitidos:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE", "message": mensaje,
        })
    return rol_norm


async def _obtener_lote(db, finca_id: str, lote_id: str) -> Lote:
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
        lote_uuid = uuid_mod.UUID(lote_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "LOTE_INVALIDO", "message": "finca_id o lote_id no es un UUID válido.",
        })
    lote = (
        await db.execute(
            select(Lote).where(Lote.id == lote_uuid, Lote.finca_id == finca_uuid)
        )
    ).scalar_one_or_none()
    if lote is None:
        raise HTTPException(status_code=404, detail={
            "code": "LOTE_NOT_FOUND",
            "message": "El lote no pertenece a esta finca o no existe.",
        })
    return lote


async def _cultivo_nombre(db, cultivo_id) -> str:
    try:
        cultivo_uuid = uuid_mod.UUID(str(cultivo_id))
    except ValueError:
        return str(cultivo_id)
    cultivo = (
        await db.execute(select(Cultivo).where(Cultivo.id == cultivo_uuid))
    ).scalar_one_or_none()
    return cultivo.nombre if cultivo is not None else str(cultivo_id)


def _ciclo_a_dict(c, cultivo_nombre: str | None = None) -> dict:
    return {
        "id": str(c.id),
        "lote_id": str(c.lote_id),
        "cultivo_id": str(c.cultivo_id),
        "cultivo_nombre": cultivo_nombre,
        "fecha_siembra": c.fecha_siembra.isoformat() if c.fecha_siembra else None,
        "fecha_cosecha": c.fecha_cosecha.isoformat() if c.fecha_cosecha else None,
        "variedad": c.variedad,
        "densidad_siembra_plantas_ha": (
            float(c.densidad_siembra_plantas_ha)
            if c.densidad_siembra_plantas_ha is not None else None
        ),
        "rendimiento_tn_ha": float(c.rendimiento_tn_ha) if c.rendimiento_tn_ha is not None else None,
        "rendimiento_atipico": bool(c.rendimiento_atipico),
        "calidad_cosecha": c.calidad_cosecha,
        "aplicaciones": c.aplicaciones or [],
        "incidencias": c.incidencias or [],
        "practicas_riego": c.practicas_riego,
        "observaciones": c.observaciones,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


async def _validar_cultivo(db, cultivo_id: str) -> None:
    try:
        cultivo_uuid = uuid_mod.UUID(cultivo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "CULTIVO_INVALIDO", "message": "cultivo_id no es un UUID válido.",
        })
    cultivo = (
        await db.execute(select(Cultivo).where(Cultivo.id == cultivo_uuid))
    ).scalar_one_or_none()
    if cultivo is None:
        raise HTTPException(status_code=404, detail={
            "code": "CULTIVO_NOT_FOUND", "message": "El cultivo no está registrado en el catálogo.",
        })


@router.get("/fincas/{finca_id}/lotes/{lote_id}/ciclos")
async def ciclos_de_lote(
    finca_id: str,
    lote_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Historial de ciclos productivos de un lote (más reciente primero)."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    lote = await _obtener_lote(db, finca_id, lote_id)

    ciclos = (
        await db.execute(
            select(CicloLote)
            .where(CicloLote.lote_id == lote.id)
            .order_by(CicloLote.fecha_siembra.desc(), CicloLote.created_at.desc())
        )
    ).scalars().all()

    nombres: dict[str, str] = {}
    data = []
    for c in ciclos:
        key = str(c.cultivo_id)
        if key not in nombres:
            nombres[key] = await _cultivo_nombre(db, c.cultivo_id)
        data.append(_ciclo_a_dict(c, nombres[key]))
    return {"data": data, "total": len(data)}


@router.post("/fincas/{finca_id}/lotes/{lote_id}/ciclos", status_code=201)
async def crear_ciclo(
    finca_id: str,
    lote_id: str,
    body: CicloCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Registra un ciclo productivo en el lote. Admin/Agrónomo."""
    rol = _exigir_rol(
        x_user_role, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden registrar ciclos.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    lote = await _obtener_lote(db, finca_id, lote_id)
    await _validar_cultivo(db, body.cultivo_id)

    if body.fecha_cosecha and body.fecha_cosecha < body.fecha_siembra:
        raise HTTPException(status_code=422, detail={
            "code": "FECHAS_INVALIDAS",
            "message": "La fecha de cosecha no puede ser anterior a la de siembra.",
        })
    if body.calidad_cosecha and body.calidad_cosecha not in CALIDADES:
        raise HTTPException(status_code=422, detail={
            "code": "CALIDAD_INVALIDA",
            "message": f"Calidad debe ser una de: {', '.join(sorted(CALIDADES))}.",
        })
    if body.practicas_riego and body.practicas_riego not in RIEGOS:
        raise HTTPException(status_code=422, detail={
            "code": "RIEGO_INVALIDO",
            "message": f"Prácticas de riego debe ser una de: {', '.join(sorted(RIEGOS))}.",
        })

    ciclo = CicloLote(
        lote_id=lote.id,
        cultivo_id=uuid_mod.UUID(body.cultivo_id),
        fecha_siembra=body.fecha_siembra,
        fecha_cosecha=body.fecha_cosecha,
        variedad=body.variedad,
        densidad_siembra_plantas_ha=body.densidad_siembra_plantas_ha,
        rendimiento_tn_ha=body.rendimiento_tn_ha,
        calidad_cosecha=body.calidad_cosecha,
        aplicaciones=body.aplicaciones or [],
        incidencias=body.incidencias or [],
        practicas_riego=body.practicas_riego,
        observaciones=body.observaciones,
    )
    db.add(ciclo)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="ciclo.crear",
        entidad="ciclo",
        entidad_id=str(ciclo.id),
        detalle={
            "lote_id": str(lote.id),
            "lote": lote.nombre,
            "cultivo": await _cultivo_nombre(db, body.cultivo_id),
            "fecha_siembra": body.fecha_siembra.isoformat(),
            "rendimiento_tn_ha": body.rendimiento_tn_ha,
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    await db.refresh(ciclo)
    logger.info("ciclo_creado", ciclo_id=str(ciclo.id), lote_id=str(lote.id), rol=rol)
    return {
        "status": "created",
        "ciclo": _ciclo_a_dict(ciclo, await _cultivo_nombre(db, ciclo.cultivo_id)),
    }


@router.patch("/fincas/{finca_id}/lotes/{lote_id}/ciclos/{ciclo_id}")
async def editar_ciclo(
    finca_id: str,
    lote_id: str,
    ciclo_id: str,
    body: CicloUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Edita un ciclo productivo. Admin/Agrónomo."""
    rol = _exigir_rol(
        x_user_role, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden editar ciclos.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    lote = await _obtener_lote(db, finca_id, lote_id)

    try:
        ciclo_uuid = uuid_mod.UUID(ciclo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "CICLO_INVALIDO", "message": "ciclo_id no es un UUID válido.",
        })
    ciclo = (
        await db.execute(
            select(CicloLote).where(CicloLote.id == ciclo_uuid, CicloLote.lote_id == lote.id)
        )
    ).scalar_one_or_none()
    if ciclo is None:
        raise HTTPException(status_code=404, detail={
            "code": "CICLO_NOT_FOUND", "message": "El ciclo no pertenece a este lote o no existe.",
        })

    cambios = body.model_dump(exclude_unset=True)
    if "cultivo_id" in cambios and cambios["cultivo_id"]:
        await _validar_cultivo(db, cambios["cultivo_id"])
        cambios["cultivo_id"] = uuid_mod.UUID(cambios["cultivo_id"])
    if "fecha_siembra" in cambios and cambios["fecha_siembra"]:
        nueva_siembra = cambios["fecha_siembra"]
        cosecha = cambios.get("fecha_cosecha", ciclo.fecha_cosecha)
        if cosecha and cosecha < nueva_siembra:
            raise HTTPException(status_code=422, detail={
                "code": "FECHAS_INVALIDAS",
                "message": "La fecha de cosecha no puede ser anterior a la de siembra.",
            })
    if cambios.get("calidad_cosecha") and cambios["calidad_cosecha"] not in CALIDADES:
        raise HTTPException(status_code=422, detail={
            "code": "CALIDAD_INVALIDA",
            "message": f"Calidad debe ser una de: {', '.join(sorted(CALIDADES))}.",
        })
    if cambios.get("practicas_riego") and cambios["practicas_riego"] not in RIEGOS:
        raise HTTPException(status_code=422, detail={
            "code": "RIEGO_INVALIDO",
            "message": f"Prácticas de riego debe ser una de: {', '.join(sorted(RIEGOS))}.",
        })
    for campo, valor in cambios.items():
        setattr(ciclo, campo, valor)

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="ciclo.actualizar",
        entidad="ciclo",
        entidad_id=str(ciclo.id),
        detalle={
            "lote_id": str(lote.id),
            "lote": lote.nombre,
            "fecha_siembra": ciclo.fecha_siembra.isoformat(),
            "campos": sorted(cambios),
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    await db.refresh(ciclo)
    logger.info("ciclo_editado", ciclo_id=str(ciclo.id), lote_id=str(lote.id), rol=rol)
    return {
        "status": "updated",
        "ciclo": _ciclo_a_dict(ciclo, await _cultivo_nombre(db, ciclo.cultivo_id)),
    }


@router.delete("/fincas/{finca_id}/lotes/{lote_id}/ciclos/{ciclo_id}")
async def eliminar_ciclo(
    finca_id: str,
    lote_id: str,
    ciclo_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Elimina un ciclo del historial del lote. Solo administrador."""
    rol = _exigir_rol(
        x_user_role, ROL_ADMIN,
        "Solo el rol administrador puede eliminar ciclos.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    lote = await _obtener_lote(db, finca_id, lote_id)

    try:
        ciclo_uuid = uuid_mod.UUID(ciclo_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "CICLO_INVALIDO", "message": "ciclo_id no es un UUID válido.",
        })
    ciclo = (
        await db.execute(
            select(CicloLote).where(CicloLote.id == ciclo_uuid, CicloLote.lote_id == lote.id)
        )
    ).scalar_one_or_none()
    if ciclo is None:
        raise HTTPException(status_code=404, detail={
            "code": "CICLO_NOT_FOUND", "message": "El ciclo no pertenece a este lote o no existe.",
        })

    detalle = {
        "lote_id": str(lote.id),
        "lote": lote.nombre,
        "cultivo": await _cultivo_nombre(db, ciclo.cultivo_id),
        "fecha_siembra": ciclo.fecha_siembra.isoformat() if ciclo.fecha_siembra else None,
    }
    await db.delete(ciclo)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="ciclo.eliminar",
        entidad="ciclo",
        entidad_id=str(ciclo_uuid),
        detalle=detalle,
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    logger.info("ciclo_eliminado", ciclo_id=str(ciclo_uuid), lote_id=str(lote.id), rol=rol)
    return {"status": "deleted", "ciclo_id": str(ciclo_uuid)}


@router.post("/fincas/{finca_id}/ciclo/iniciar", status_code=201)
async def iniciar_ciclo(
    finca_id: str,
    body: IniciarCicloRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Inicia un nuevo ciclo productivo (flujo rápido de Recomendaciones).

    Crea el registro en `historial_ciclos_lote` sobre el lote principal y
    actualiza automáticamente la finca (`cultivo_sembrado`) y el lote
    (`fecha_siembra`, `variedad`, `densidad_siembra_plantas_ha`) para que
    el análisis actual use el cultivo recién sembrado.
    """
    rol = _exigir_rol(
        x_user_role, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden iniciar ciclos.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)

    try:
        finca_uuid = uuid_mod.UUID(finca_id)
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

    # Lote principal: el primero activo de la finca
    lote = (
        await db.execute(
            select(Lote)
            .where(Lote.finca_id == finca_uuid, Lote.activo.is_(True))
            .order_by(Lote.created_at)
            .limit(1)
        )
    ).scalars().first()
    if lote is None:
        raise HTTPException(status_code=422, detail={
            "code": "NO_LOTES",
            "message": "La finca no tiene un lote activo. Registre el lote antes de iniciar el ciclo.",
        })

    await _validar_cultivo(db, body.cultivo_id)
    cultivo = (
        await db.execute(
            select(Cultivo).where(Cultivo.id == uuid_mod.UUID(body.cultivo_id))
        )
    ).scalar_one()

    ciclo = CicloLote(
        lote_id=lote.id,
        cultivo_id=cultivo.id,
        fecha_siembra=body.fecha_siembra,
        variedad=body.variedad,
        densidad_siembra_plantas_ha=body.densidad_siembra_plantas_ha,
        practicas_riego=finca.tipo_riego.value if finca.tipo_riego else None,
        observaciones="Ciclo registrado desde Recomendaciones (flujo rápido de inicio).",
    )
    db.add(ciclo)
    await db.flush()

    # ── Actualizar finca/lote para el análisis actual ──
    finca.cultivo_sembrado = cultivo.nombre
    lote.fecha_siembra = body.fecha_siembra
    lote.variedad = body.variedad
    lote.densidad_siembra_plantas_ha = body.densidad_siembra_plantas_ha

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="ciclo.iniciar",
        entidad="ciclo",
        entidad_id=str(ciclo.id),
        detalle={
            "finca_id": str(finca.id),
            "finca": finca.nombre,
            "lote_id": str(lote.id),
            "lote": lote.nombre,
            "cultivo": cultivo.nombre,
            "fecha_siembra": body.fecha_siembra.isoformat(),
            "variedad": body.variedad,
            "densidad_plantas_ha": body.densidad_siembra_plantas_ha,
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    await db.refresh(ciclo)
    logger.info(
        "ciclo_iniciado", ciclo_id=str(ciclo.id), finca_id=str(finca.id),
        cultivo=cultivo.nombre, rol=rol,
    )
    return {
        "status": "started",
        "ciclo": _ciclo_a_dict(ciclo, cultivo.nombre),
        "finca": {"cultivo_sembrado": finca.cultivo_sembrado},
        "lote": {
            "id": str(lote.id),
            "nombre": lote.nombre,
            "fecha_siembra": lote.fecha_siembra.isoformat() if lote.fecha_siembra else None,
            "variedad": lote.variedad,
            "densidad_siembra_plantas_ha": (
                float(lote.densidad_siembra_plantas_ha)
                if lote.densidad_siembra_plantas_ha is not None else None
            ),
        },
    }


async def _ciclo_abierto(db, finca: Finca) -> tuple[Lote, CicloLote] | None:
    """Lote principal y ciclo abierto (sin cosecha) más reciente, o None."""
    lote = (
        await db.execute(
            select(Lote)
            .where(Lote.finca_id == finca.id, Lote.activo.is_(True))
            .order_by(Lote.created_at)
            .limit(1)
        )
    ).scalars().first()
    if lote is None:
        return None
    ciclo = (
        await db.execute(
            select(CicloLote)
            .where(CicloLote.lote_id == lote.id, CicloLote.fecha_cosecha.is_(None))
            .order_by(CicloLote.fecha_siembra.desc(), CicloLote.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if ciclo is None:
        return None
    return lote, ciclo


@router.get("/fincas/{finca_id}/ciclo/activo")
async def ciclo_activo(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Ciclo abierto (sin cosechar) de la finca — alimenta el botón «Cosechar ciclo»."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
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
    abierto = await _ciclo_abierto(db, finca)
    if abierto is None:
        return {"data": None}
    lote, ciclo = abierto
    return {
        "data": {
            "ciclo": _ciclo_a_dict(ciclo, await _cultivo_nombre(db, ciclo.cultivo_id)),
            "lote": {"id": str(lote.id), "nombre": lote.nombre},
        },
    }


@router.post("/fincas/{finca_id}/ciclo/cosechar")
async def cosechar_ciclo(
    finca_id: str,
    body: CosecharCicloRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Cierra el ciclo activo: cosecha, rendimiento (obligatorio) y aplicaciones.

    El rendimiento alimenta el ROI de ciclos futuros (se guarda en
    `historial_ciclos_lote.rendimiento_tn_ha`); el resumen de aplicaciones
    en texto plano se convierte a JSONB con un parser simple.
    """
    rol = _exigir_rol(
        x_user_role, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden cosechar el ciclo.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
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

    abierto = await _ciclo_abierto(db, finca)
    if abierto is None:
        raise HTTPException(status_code=422, detail={
            "code": "NO_CICLO_ACTIVO",
            "message": "No hay un ciclo activo en la finca. Inicie un ciclo (🌱 Registrar nuevo ciclo) antes de cosechar.",
        })
    lote, ciclo = abierto

    if body.fecha_cosecha < ciclo.fecha_siembra:
        raise HTTPException(status_code=422, detail={
            "code": "FECHAS_INVALIDAS",
            "message": "La fecha de cosecha no puede ser anterior a la de siembra.",
        })
    if body.calidad_cosecha and body.calidad_cosecha not in CALIDADES:
        raise HTTPException(status_code=422, detail={
            "code": "CALIDAD_INVALIDA",
            "message": f"Calidad debe ser una de: {', '.join(sorted(CALIDADES))}.",
        })

    # Rendimiento normalizado a t/ha (unidad t_ha directa; kg_ha ÷ 1000)
    rendimiento_tn_ha = body.rendimiento if body.unidad_rendimiento == "t_ha" else body.rendimiento / 1000.0

    # ── Protección del Ground Truth: rendimiento atípico vs. ficha técnica ──
    # No se bloquea el guardado, pero se marca el ciclo y se advierte en la
    # UI para que el usuario verifique antes de envenenar los modelos.
    from agroia_backend.services.ml_labels import (
        es_rendimiento_atipico,
        rendimiento_esperado_cultivo,
    )

    esperado = await rendimiento_esperado_cultivo(db, ciclo.cultivo_id)
    rendimiento_atipico = False
    advertencia_rendimiento = None
    if esperado:
        rendimiento_atipico = es_rendimiento_atipico(rendimiento_tn_ha, esperado)
        if rendimiento_atipico:
            advertencia_rendimiento = (
                f"Este rendimiento ({rendimiento_tn_ha:g} t/ha) es atípico para "
                f"este cultivo en Colombia (esperado ≈ {esperado:g} t/ha). "
                "Verifique el dato antes de guardar para no afectar los "
                "modelos predictivos."
            )
            logger.warning(
                "rendimiento_atipico_declarado", ciclo_id=str(ciclo.id),
                rendimiento=rendimiento_tn_ha, esperado=esperado,
            )

    aplicaciones = parsear_resumen_aplicaciones(body.resumen_aplicaciones)
    advertencias: list[str] = []
    if body.resumen_aplicaciones and body.resumen_aplicaciones.strip() and aplicaciones is None:
        advertencias.append(
            "No se pudieron interpretar las aplicaciones pegadas; se conservan las del ciclo."
        )

    ciclo.fecha_cosecha = body.fecha_cosecha
    ciclo.rendimiento_tn_ha = rendimiento_tn_ha
    ciclo.rendimiento_atipico = rendimiento_atipico
    ciclo.calidad_cosecha = body.calidad_cosecha
    if aplicaciones:
        ciclo.aplicaciones = aplicaciones

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="ciclo.cosechar",
        entidad="ciclo",
        entidad_id=str(ciclo.id),
        detalle={
            "finca_id": str(finca.id),
            "finca": finca.nombre,
            "lote_id": str(lote.id),
            "lote": lote.nombre,
            "cultivo": await _cultivo_nombre(db, ciclo.cultivo_id),
            "fecha_siembra": ciclo.fecha_siembra.isoformat(),
            "fecha_cosecha": body.fecha_cosecha.isoformat(),
            "rendimiento_tn_ha": rendimiento_tn_ha,
            "calidad": body.calidad_cosecha,
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    await db.refresh(ciclo)
    logger.info(
        "ciclo_cosechado", ciclo_id=str(ciclo.id), finca_id=str(finca.id),
        rendimiento_tn_ha=rendimiento_tn_ha, rol=rol,
    )
    return {
        "status": "harvested",
        "ciclo": _ciclo_a_dict(ciclo, await _cultivo_nombre(db, ciclo.cultivo_id)),
        "advertencias": advertencias,
        "rendimiento_atipico": rendimiento_atipico,
        "advertencia_rendimiento": advertencia_rendimiento,
    }


@router.post("/fincas/{finca_id}/ciclos/carga-csv")
async def carga_masiva_ciclos(
    finca_id: str,
    body: CargaCiclosCsvRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Ingesta en bloque del historial de ciclos (CSV de los últimos 5 años).

    Columnas: `lote, cultivo, fecha_siembra, fecha_cosecha, rendimiento,
    aplicaciones_texto`. El lote se busca por nombre entre los lotes de la
    finca y se crea si no existe; el cultivo se resuelve por nombre en el
    catálogo; el rendimiento va en t/ha y el texto de aplicaciones se
    convierte a JSONB. Las filas inválidas se reportan sin abortar la carga.
    """
    rol = _exigir_rol(
        x_user_role, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden cargar el historial de ciclos.",
    )
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
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

    # ── Parsear CSV ──
    try:
        filas = list(csv.DictReader(io.StringIO(body.csv_texto)))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=422, detail={
            "code": "CSV_INVALIDO",
            "message": f"No se pudo interpretar el CSV: {e}",
        })
    if not filas:
        raise HTTPException(status_code=422, detail={
            "code": "CSV_VACIO", "message": "El CSV no contiene filas de datos.",
        })
    faltantes = COLUMNAS_CICLOS_CSV - {c.strip().lower() for c in filas[0].keys()}
    if faltantes:
        raise HTTPException(status_code=422, detail={
            "code": "CSV_COLUMNAS",
            "message": "Faltan columnas: " + ", ".join(sorted(faltantes)),
        })

    # ── Contexto: lotes de la finca y catálogo de cultivos ──
    lotes_db = (
        await db.execute(
            select(Lote).where(Lote.finca_id == finca_uuid, Lote.activo.is_(True))
        )
    ).scalars().all()
    lotes_por_nombre = {lote.nombre.strip().lower(): lote for lote in lotes_db}
    cultivos = (await db.execute(select(Cultivo))).scalars().all()
    cultivos_por_nombre = {c.nombre.strip().lower(): c for c in cultivos}

    creados = 0
    lotes_creados = 0
    errores: list[dict] = []

    for idx, fila in enumerate(filas, start=2):  # fila 2 = primera fila de datos
        def celda(nombre: str) -> str:
            valor = fila.get(nombre) or fila.get(nombre.capitalize()) or ""
            return (valor or "").strip()

        nombre_lote = celda("lote")
        nombre_cultivo = celda("cultivo")
        siembra_txt = celda("fecha_siembra")
        cosecha_txt = celda("fecha_cosecha")
        rendimiento_txt = celda("rendimiento")
        aplicaciones_txt = celda("aplicaciones_texto")

        if not nombre_lote:
            errores.append({"fila": idx, "mensaje": "Columna 'lote' vacía."})
            continue
        lote = lotes_por_nombre.get(nombre_lote.lower())
        if lote is None:
            lote = Lote(finca_id=finca_uuid, nombre=nombre_lote[:100])
            db.add(lote)
            await db.flush()
            lotes_por_nombre[nombre_lote.lower()] = lote
            lotes_creados += 1

        cultivo = cultivos_por_nombre.get(nombre_cultivo.lower())
        if cultivo is None:
            errores.append({"fila": idx, "mensaje": f"Cultivo '{nombre_cultivo}' no está en el catálogo."})
            continue

        fecha_siembra = _parsear_fecha_csv(siembra_txt)
        if fecha_siembra is None:
            errores.append({"fila": idx, "mensaje": f"Fecha de siembra inválida: '{siembra_txt}'."})
            continue
        fecha_cosecha = _parsear_fecha_csv(cosecha_txt)
        if cosecha_txt and fecha_cosecha is None:
            errores.append({"fila": idx, "mensaje": f"Fecha de cosecha inválida: '{cosecha_txt}'."})
            continue
        if fecha_cosecha and fecha_cosecha < fecha_siembra:
            errores.append({"fila": idx, "mensaje": "La cosecha es anterior a la siembra."})
            continue

        rendimiento = None
        if rendimiento_txt:
            try:
                rendimiento = float(rendimiento_txt.replace(",", "."))
            except ValueError:
                errores.append({"fila": idx, "mensaje": f"Rendimiento inválido: '{rendimiento_txt}'."})
                continue

        aplicaciones = parsear_resumen_aplicaciones(aplicaciones_txt)

        db.add(CicloLote(
            lote_id=lote.id,
            cultivo_id=cultivo.id,
            fecha_siembra=fecha_siembra,
            fecha_cosecha=fecha_cosecha,
            rendimiento_tn_ha=rendimiento,
            aplicaciones=aplicaciones,
            observaciones="Ciclo histórico importado por carga masiva (CSV).",
        ))
        creados += 1

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="ciclo.carga_csv",
        entidad="ciclo",
        detalle={
            "finca_id": str(finca.id),
            "finca": finca.nombre,
            "total_filas": len(filas),
            "creados": creados,
            "errores": len(errores),
            "lotes_creados": lotes_creados,
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    logger.info(
        "ciclos_carga_csv", finca_id=str(finca.id), creados=creados,
        errores=len(errores), lotes_creados=lotes_creados, rol=rol,
    )
    return {
        "status": "ok",
        "total_filas": len(filas),
        "creados": creados,
        "lotes_creados": lotes_creados,
        "errores": errores,
    }
