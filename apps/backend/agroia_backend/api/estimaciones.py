"""API AGC-COST (F3/F6/F7) — estimaciones: cotizador, ciclo de vida y tablero.

POST /estimaciones (borrador) · PATCH · emitir · aceptar · rechazar ·
recalcular con snapshot (CA-07) · convertir en comisión (RF-20) ·
export HTML/PDF por audiencia (RF-21/26) · tablero (RF-25) ·
sugerencia de puntos por densidad (RF-05/06) y de km (RF-07).
"""

import math
import uuid as uuid_mod
from datetime import date, datetime, timezone
from decimal import Decimal

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.cobros import CobroDocumento
from agroia_backend.models.comision import Comision
from agroia_backend.models.costeo import CosteoConjunto
from agroia_backend.models.costeo_fases import CosteoIdentidad, CosteoTelefono
from agroia_backend.models.estimaciones import (
    Estimacion,
    EstimacionEvento,
    EstimacionLinea,
    EstimacionSnapshot,
)
from agroia_backend.models.finca import Finca
from agroia_backend.models.lote import Lote
from agroia_backend.services.auth_contexto import (
    ROLES_ADMIN,
    ROLES_ADMIN_AGRONOMO,
    contexto_usuario,
)
from agroia_backend.services.auditoria import registrar_auditoria
from agroia_backend.services.documentos_costeo import (
    html_cobro,
    html_cotizacion,
    pdf_cobro,
    pdf_cotizacion,
)
from agroia_backend.services.estimaciones import (
    EstimacionError,
    _marcar_vencidas,
    convertir_a_comision,
    emitir as _emitir,
    recalcular as _recalcular,
    recalcular_desde_snapshot,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["estimaciones"])

ROLES_CLIENTE = {"admin", "administrador", "agronomo", "agrónomo", "cliente"}
ROLES_EXT = {"admin", "administrador", "extensionista"}


def _err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _uuid(valor: str | None) -> uuid_mod.UUID | None:
    if not valor:
        return None
    try:
        return uuid_mod.UUID(str(valor))
    except ValueError:
        return None


def _n(v):
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, date):
        return v.isoformat()
    return v


async def _serializador_conjunto(db, conjunto) -> dict:
    from agroia_backend.api.costeo import _conjunto_a_dict
    return await _conjunto_a_dict(db, conjunto)


async def _estimacion_a_dict(db, e: Estimacion, con_detalle: bool = True) -> dict:
    finca = (
        await db.execute(select(Finca).where(Finca.id == e.finca_id))
    ).scalars().one_or_none()
    lineas = []
    if con_detalle:
        lineas = (
            await db.execute(
                select(EstimacionLinea).where(EstimacionLinea.estimacion_id == e.id)
                .order_by(EstimacionLinea.creado_en)
            )
        ).scalars().all()
    snapshot = (
        await db.execute(
            select(EstimacionSnapshot).where(EstimacionSnapshot.estimacion_id == e.id)
        )
    ).scalars().one_or_none()
    cobro = (
        await db.execute(
            select(CobroDocumento).where(
                CobroDocumento.estimacion_id == e.id,
                CobroDocumento.estado != "anulado",
            )
        )
    ).scalars().first()
    return {
        "id": str(e.id),
        "consecutivo": e.consecutivo,
        "estado": e.estado,
        "finca_id": str(e.finca_id),
        "finca": finca.nombre if finca else None,
        "municipio": finca.municipio if finca else None,
        "departamento": finca.departamento if finca else None,
        "cliente_id": str(e.cliente_id) if e.cliente_id else None,
        "conjunto_id": str(e.conjunto_id) if e.conjunto_id else None,
        "fecha_referencia": e.fecha_referencia.isoformat(),
        "area_total_ha": _n(e.area_total_ha),
        "total_directo": _n(e.total_directo),
        "total_ajustado": _n(e.total_ajustado),
        "precio_lista": _n(e.precio_lista),
        "descuento_aplicado": _n(e.descuento_aplicado),
        "total_final": _n(e.total_final),
        "margen_pct": _n(e.margen_pct),
        "vence_en": e.vence_en.isoformat() if e.vence_en else None,
        "emitida_en": e.emitido_en.isoformat() if e.emitido_en else None,
        "motivo_excepcion": e.motivo_excepcion,
        "notas": e.notas,
        "hash_snapshot": snapshot.hash_sha256 if snapshot else None,
        "cobro": {"id": str(cobro.id), "numero": f"{cobro.prefijo}-{cobro.consecutivo}",
                  "estado": cobro.estado} if cobro else None,
        "lineas": [
            {
                "lote_id": str(ln.lote_id) if ln.lote_id else None,
                "lote": None,
                "descripcion": ln.descripcion,
                "cantidad": _n(ln.cantidad),
                "unidad": ln.unidad,
                "valor_unitario": _n(ln.valor_unitario),
                "valor": _n(ln.valor),
                "componente_codigo": ln.componente_codigo,
            }
            for ln in lineas
        ],
    }


class ServicioSel(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=40)
    cantidad: Decimal = Field(Decimal("1"), ge=0)


class LoteSel(BaseModel):
    lote_id: str | None = None
    area_ha: Decimal = Field(..., gt=0)
    puntos: int | None = Field(None, ge=0)
    km: Decimal = Field(Decimal("0"), ge=0)
    servicios: list[ServicioSel] = Field(default_factory=list)


class EstimacionIn(BaseModel):
    finca_id: str = Field(...)
    fecha_referencia: date | None = None
    lotes: list[LoteSel] = Field(default_factory=list)
    servicios: list[ServicioSel] = Field(default_factory=list, description="Servicios sin lote")
    factores: dict = Field(default_factory=dict)
    descuento_pct: Decimal | None = Field(None, ge=0, le=100)
    notas: str | None = None


def _json_safe(valor):
    """Convierte Decimal/date a tipos JSON (la columna seleccion es JSONB)."""
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {k: _json_safe(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_json_safe(v) for v in valor]
    return valor


def _lotes_normalizados(body: EstimacionIn, finca: Finca, db_lotes: list[Lote],
                        conjunto_dict: dict | None = None) -> list[dict]:
    lotes = [lot.model_dump() for lot in body.lotes]
    if body.servicios:
        lotes.append({
            "lote_id": None,
            "area_ha": Decimal("0"),
            "puntos": None,
            "km": Decimal("0"),
            "servicios": [s.model_dump() for s in body.servicios],
        })
    # Área por defecto desde el lote registrado.
    area_por_lote = {str(lot.id): Decimal(str(lot.area_ha or 0)) for lot in db_lotes}
    for lot in lotes:
        if lot.get("lote_id") and lot.get("area_ha") is None:
            lot["area_ha"] = area_por_lote.get(lot["lote_id"], Decimal("1"))
        if lot.get("area_ha") is None:
            lot["area_ha"] = Decimal("1")
        lot["departamento"] = finca.departamento
        lot["municipio"] = finca.municipio
        # Sugerencia de puntos por densidad del conjunto vigente (RF-05) si no viene explícita.
        if lot.get("puntos") is None and lot["lote_id"]:
            sugeridos = _sugerir_puntos_por_densidad(conjunto_dict, float(lot["area_ha"] or 1))
            if sugeridos:
                lot["puntos"] = sugeridos
    return lotes


def _sugerir_puntos_por_densidad(conjunto_dict: dict | None, area_ha: float) -> int | None:
    """Sugerencia por regla de densidad del conjunto (fallback heurístico §2)."""
    for regla in (conjunto_dict or {}).get("densidad") or []:
        area_min = float(regla.get("area_min") or 0)
        area_max = regla.get("area_max")
        if area_ha >= area_min and (area_max is None or area_ha <= float(area_max)):
            sugerido = int(round(float(regla.get("puntos_por_ha") or 1) * area_ha))
            sugerido = max(int(regla.get("puntos_min") or 0),
                           min(int(regla.get("puntos_max") or sugerido), sugerido))
            return sugerido
    return max(5, min(60, int(round(area_ha))))


@router.get("/estimaciones/sugerencia-puntos")
async def sugerencia_puntos(
    request: Request,
    db: AsyncSession = Depends(get_db),
    area_ha: float = Query(..., gt=0, le=10000),
    finca_id: str | None = Query(None),
):
    """Sugerencia de puntos según la regla de densidad vigente (RF-05/06)."""
    contexto_usuario(request, ROLES_ADMIN_AGRONOMO)
    from agroia_backend.api.costeo import _conjunto_vigente
    conjunto = await _conjunto_vigente(db, date.today())
    if conjunto is None:
        raise _err(404, "CONJUNTO_SIN_VIGENCIA", "No hay conjunto vigente.")
    conjunto_dict = await _serializador_conjunto(db, conjunto)
    minimo = None
    for regla in conjunto_dict.get("densidad") or []:
        area_min = float(regla.get("area_min") or 0)
        area_max = regla.get("area_max")
        if area_ha >= area_min and (area_max is None or area_ha <= float(area_max)):
            minimo = int(regla.get("puntos_min") or 0)
            break
    sugerido = _sugerir_puntos_por_densidad(conjunto_dict, area_ha)
    return {
        "puntos_sugeridos": sugerido,
        "puntos_minimos": minimo,
        "fuente": "densidad",
        "advertencia": (
            f"Bajar de {minimo} puntos en {area_ha:g} ha puede restar "
            "representatividad agronómica al muestreo."
            if minimo else None
        ),
    }


@router.get("/estimaciones/sugerencia-km")
async def sugerencia_km(
    request: Request,
    db: AsyncSession = Depends(get_db),
    finca_id: str = Query(...),
):
    """Distancia geodésica desde la sede configurada hasta la finca (RF-07)."""
    contexto_usuario(request, ROLES_ADMIN_AGRONOMO)
    finca = (
        await db.execute(select(Finca).where(Finca.id == _uuid(finca_id)))
    ).scalars().one_or_none()
    if finca is None:
        raise _err(404, "FINCA_NOT_FOUND", "La finca no existe.")
    identidad = (
        await db.execute(select(CosteoIdentidad).order_by(CosteoIdentidad.creado_en.desc()))
    ).scalars().first()
    if identidad is None or identidad.sede_latitud is None or identidad.sede_longitud is None:
        return {"km": None, "mensaje": "La sede de la empresa no tiene coordenadas configuradas."}
    if finca.latitud is None or finca.longitud is None:
        return {"km": None, "mensaje": "La finca no tiene coordenadas registradas."}
    km = _haversine(identidad.sede_latitud, identidad.sede_longitud,
                    finca.latitud, finca.longitud)
    return {"km": round(km, 1), "editable": True}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_tierra_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r_tierra_km * math.asin(math.sqrt(a))


@router.post("/estimaciones", status_code=201)
async def crear_estimacion(
    body: EstimacionIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_ADMIN_AGRONOMO)
    finca = (
        await db.execute(select(Finca).where(Finca.id == _uuid(body.finca_id)))
    ).scalars().one_or_none()
    if finca is None:
        raise _err(404, "FINCA_NOT_FOUND", "La finca no existe.")
    db_lotes = (
        await db.execute(select(Lote).where(Lote.finca_id == finca.id))
    ).scalars().all()

    from agroia_backend.api.costeo import _conjunto_vigente
    fecha_ref = body.fecha_referencia or datetime.now(timezone.utc).date()
    conjunto = await _conjunto_vigente(db, fecha_ref)
    if conjunto is None:
        raise _err(404, "CONJUNTO_SIN_VIGENCIA",
                   "No hay un conjunto de parámetros publicado vigente.")
    conjunto_dict = await _serializador_conjunto(db, conjunto)

    estimacion = Estimacion(
        finca_id=finca.id,
        cliente_id=finca.usuario_id,
        conjunto_id=conjunto.id,
        estado="borrador",
        fecha_referencia=fecha_ref,
        notas=body.notas,
        creado_por=usuario["uid"],
    )
    db.add(estimacion)
    await db.flush()

    lotes = _lotes_normalizados(body, finca, db_lotes, conjunto_dict)
    estimacion.seleccion = _json_safe({
        "lotes": lotes,
        "factores": body.factores,
        "descuento_pct": str(body.descuento_pct) if body.descuento_pct is not None else None,
    })
    try:
        await _recalcular(
            db, estimacion,
            rol=usuario["rol"],
            lotes=lotes,
            factores=body.factores,
            descuento_pct=body.descuento_pct,
            serializador=lambda db, c: _serializador_conjunto(db, c),
        )
    except EstimacionError as e:
        raise _err(422, e.code, e.message)

    from agroia_backend.models.estimaciones import EstimacionEvento
    db.add(EstimacionEvento(estimacion_id=estimacion.id, evento="creada", usuario_id=usuario["uid"]))
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion="estimacion.crear",
        entidad="estimacion",
        entidad_id=str(estimacion.id),
        detalle={"finca_id": body.finca_id, "total": str(estimacion.total_final)},
    )
    await db.commit()
    return {"estimacion": await _estimacion_a_dict(db, estimacion)}


@router.get("/estimaciones")
async def listar_estimaciones(
    request: Request,
    db: AsyncSession = Depends(get_db),
    finca_id: str | None = Query(None),
    estado: str | None = Query(None),
    limite: int = Query(50, ge=1, le=200),
):
    usuario = contexto_usuario(request, ROLES_CLIENTE)
    await _marcar_vencidas(db)
    await db.commit()

    stmt = select(Estimacion).order_by(Estimacion.creado_en.desc()).limit(limite)
    if finca_id:
        stmt = stmt.where(Estimacion.finca_id == _uuid(finca_id))
    if estado:
        stmt = stmt.where(Estimacion.estado == estado)
    if usuario["rol"] == "cliente":
        fincas_propias = (
            await db.execute(select(Finca.id).where(Finca.usuario_id == usuario["uid"]))
        ).scalars().all()
        if not fincas_propias:
            return {"data": [], "total": 0}
        stmt = stmt.where(Estimacion.finca_id.in_(fincas_propias))
    estimaciones = (await db.execute(stmt)).scalars().all()
    return {"data": [await _estimacion_a_dict(db, e, con_detalle=False) for e in estimaciones],
            "total": len(estimaciones)}


@router.get("/estimaciones/tablero")
async def tablero_estimaciones(
    request: Request,
    db: AsyncSession = Depends(get_db),
    desde: date | None = Query(None),
    hasta: date | None = Query(None),
    municipio: str | None = Query(None),
):
    """Tablero de estimaciones: emitidas, aceptadas, conversión y ticket (RF-25)."""
    contexto_usuario(request, ROLES_ADMIN)
    await _marcar_vencidas(db)
    await db.commit()
    stmt = select(Estimacion)
    if desde:
        stmt = stmt.where(Estimacion.creado_en >= datetime.combine(desde, datetime.min.time()))
    if hasta:
        stmt = stmt.where(Estimacion.creado_en <= datetime.combine(hasta, datetime.max.time()))
    estimaciones = (await db.execute(stmt)).scalars().all()
    fincas = {f.id: f for f in (await db.execute(
        select(Finca).where(Finca.id.in_({e.finca_id for e in estimaciones}))
    )).scalars().all()}
    if municipio:
        estimaciones = [e for e in estimaciones
                        if fincas.get(e.finca_id) and fincas[e.finca_id].municipio == municipio]

    totales = {"total": 0, "emitidas": 0, "aceptadas": 0, "convertidas": 0}
    por_servicio: dict[str, dict] = {}
    comisiones = (
        await db.execute(
            select(Comision.origen_estimacion_id).where(
                Comision.origen_estimacion_id.in_([e.id for e in estimaciones])
            )
        )
    ).scalars().all()
    convertidas = set(comisiones)

    for e in estimaciones:
        totales["total"] += 1
        totales["emitidas"] += int(e.estado in ("emitida", "aceptada"))
        totales["aceptadas"] += int(e.estado == "aceptada")
        totales["convertidas"] += int(e.id in convertidas)
        for ln in await _lineas(db, e.id):
            codigo = ln.componente_codigo or "—"
            item = por_servicio.setdefault(codigo, {"cantidad": 0, "valor": Decimal("0")})
            item["cantidad"] += 1
            item["valor"] += ln.valor
    tasa = (totales["convertidas"] / totales["aceptadas"]) if totales["aceptadas"] else 0
    return {
        "totales": totales,
        "tasa_conversion": round(tasa, 4),
        "ticket_promedio_por_servicio": {
            k: float(v["valor"] / v["cantidad"]) if v["cantidad"] else 0
            for k, v in por_servicio.items()
        },
    }


async def _lineas(db, estimacion_id) -> list[EstimacionLinea]:
    return (await db.execute(
        select(EstimacionLinea).where(EstimacionLinea.estimacion_id == estimacion_id)
    )).scalars().all()


@router.get("/estimaciones/{estimacion_id}")
async def ver_estimacion(
    estimacion_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_CLIENTE)
    e = (
        await db.execute(select(Estimacion).where(Estimacion.id == _uuid(estimacion_id)))
    ).scalars().one_or_none()
    if e is None:
        raise _err(404, "ESTIMACION_NOT_FOUND", "La estimación no existe.")
    await _exigir_acceso(request, db, e, usuario)
    await _marcar_vencidas(db)
    await db.commit()
    dict_e = await _estimacion_a_dict(db, e)
    lotes = (
        await db.execute(select(Lote).where(Lote.finca_id == e.finca_id))
    ).scalars().all()
    nombres_lotes = {str(lot.id): lot.nombre for lot in lotes}
    for ln in dict_e["lineas"]:
        ln["lote"] = nombres_lotes.get(ln["lote_id"]) if ln["lote_id"] else None
    eventos = (
        await db.execute(
            select(EstimacionEvento).where(EstimacionEvento.estimacion_id == e.id)
            .order_by(EstimacionEvento.created_at.desc())
        )
    ).scalars().all()
    dict_e["eventos"] = [
        {"evento": ev.evento, "comentario": ev.comentario,
         "fecha": ev.created_at.isoformat()} for ev in eventos
    ]
    return {"estimacion": dict_e}


async def _exigir_acceso(request: Request, db, e: Estimacion, usuario: dict) -> None:
    if usuario["rol"] in ("admin", "administrador", "agronomo", "agrónomo"):
        return
    if usuario["rol"] == "cliente":
        finca = (
            await db.execute(select(Finca).where(Finca.id == e.finca_id))
        ).scalars().one_or_none()
        if finca and finca.usuario_id == usuario["uid"]:
            return
        raise _err(403, "FORBIDDEN_ROLE",
                   "El cliente solo ve las estimaciones de sus fincas.")
    raise _err(403, "FORBIDDEN_ROLE", "Rol sin permiso para ver estimaciones.")


class EditarIn(BaseModel):
    lotes: list[LoteSel] | None = None
    servicios: list[ServicioSel] | None = None
    factores: dict | None = None
    descuento_pct: Decimal | None = Field(None, ge=0, le=100)
    notas: str | None = None


@router.patch("/estimaciones/{estimacion_id}")
async def editar_estimacion(
    estimacion_id: str,
    body: EditarIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Edita cantidades, factores y descuentos de un borrador (RFP §10)."""
    usuario = contexto_usuario(request, ROLES_ADMIN_AGRONOMO)
    e = await _buscar(db, estimacion_id)
    if e.estado != "borrador":
        raise _err(422, "ESTIMACION_NO_EDITABLE",
                   "Solo una estimación en borrador puede editarse.")
    finca = (
        await db.execute(select(Finca).where(Finca.id == e.finca_id))
    ).scalars().one_or_none()
    db_lotes = (
        await db.execute(select(Lote).where(Lote.finca_id == e.finca_id))
    ).scalars().all()
    conjunto = (
        await db.execute(select(CosteoConjunto).where(CosteoConjunto.id == e.conjunto_id))
    ).scalars().one_or_none()
    if conjunto is None:
        raise _err(404, "CONJUNTO_NOT_FOUND", "El conjunto de la estimación no existe.")
    conjunto_dict = await _serializador_conjunto(db, conjunto)

    base = EstimacionIn(
        finca_id=str(e.finca_id),
        lotes=body.lotes or [],
        servicios=body.servicios or [],
        factores=body.factores or {},
        descuento_pct=body.descuento_pct,
        notas=body.notas if body.notas is not None else e.notas,
    )
    lotes = _lotes_normalizados(base, finca, db_lotes, conjunto_dict)
    e.seleccion = _json_safe({
        "lotes": lotes,
        "factores": body.factores or {},
        "descuento_pct": str(body.descuento_pct) if body.descuento_pct is not None else None,
    })
    try:
        await _recalcular(
            db, e,
            rol=usuario["rol"],
            lotes=lotes,
            factores=body.factores or {},
            descuento_pct=body.descuento_pct,
            serializador=lambda db, c: _serializador_conjunto(db, c),
        )
    except EstimacionError as err:
        raise _err(422, err.code, err.message)
    db.add(EstimacionEvento(estimacion_id=e.id, evento="editada", usuario_id=usuario["uid"]))
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion="estimacion.editar",
        entidad="estimacion",
        entidad_id=str(e.id),
        detalle={"total": str(e.total_final)},
    )
    await db.commit()
    return {"estimacion": await _estimacion_a_dict(db, e)}


class EmitirIn(BaseModel):
    autorizar_bajo_piso: bool = False
    motivo_excepcion: str | None = None


@router.post("/estimaciones/{estimacion_id}/emitir")
async def emitir_estimacion(
    estimacion_id: str,
    body: EmitirIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_ADMIN_AGRONOMO)
    e = await _buscar(db, estimacion_id)
    try:
        await _emitir(
            db, e,
            usuario_id=usuario["uid"],
            rol=usuario["rol"],
            autorizar_bajo_piso=body.autorizar_bajo_piso,
            motivo_excepcion=body.motivo_excepcion,
            serializador=lambda db, c: _serializador_conjunto(db, c),
        )
    except EstimacionError as err:
        raise _err(422, err.code, err.message)
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion="estimacion.emitir",
        entidad="estimacion",
        entidad_id=str(e.id),
        detalle={"consecutivo": e.consecutivo, "total": str(e.total_final)},
    )
    await db.commit()
    return {"estimacion": await _estimacion_a_dict(db, e)}


async def _buscar(db, estimacion_id: str) -> Estimacion:
    e = (
        await db.execute(select(Estimacion).where(Estimacion.id == _uuid(estimacion_id)))
    ).scalars().one_or_none()
    if e is None:
        raise _err(404, "ESTIMACION_NOT_FOUND", "La estimación no existe.")
    return e


class DecisionIn(BaseModel):
    comentario: str | None = None


@router.post("/estimaciones/{estimacion_id}/aceptar")
async def aceptar_estimacion(
    estimacion_id: str,
    body: DecisionIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_CLIENTE)
    e = await _buscar(db, estimacion_id)
    await _exigir_acceso(request, db, e, usuario)
    if e.estado != "emitida":
        raise _err(422, "ESTIMACION_NO_ACEPTABLE",
                   "Solo una estimación emitida puede aceptarse.")
    if e.vence_en and e.vence_en < date.today():
        raise _err(422, "ESTIMACION_VENCIDA",
                   "La cotización venció y ya no puede aceptarse.")
    e.estado = "aceptada"
    db.add(EstimacionEvento(
        estimacion_id=e.id, evento="aceptada", usuario_id=usuario["uid"],
        comentario=body.comentario,
    ))
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion="estimacion.aceptar",
        entidad="estimacion",
        entidad_id=str(e.id),
        detalle={},
    )
    await db.commit()
    return {"estimacion": await _estimacion_a_dict(db, e)}


@router.post("/estimaciones/{estimacion_id}/rechazar")
async def rechazar_estimacion(
    estimacion_id: str,
    body: DecisionIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_CLIENTE)
    e = await _buscar(db, estimacion_id)
    await _exigir_acceso(request, db, e, usuario)
    if e.estado != "emitida":
        raise _err(422, "ESTIMACION_NO_RECHAZABLE",
                   "Solo una estimación emitida puede rechazarse.")
    e.estado = "rechazada"
    db.add(EstimacionEvento(
        estimacion_id=e.id, evento="rechazada", usuario_id=usuario["uid"],
        comentario=body.comentario or "Rechazada por el cliente.",
    ))
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion="estimacion.rechazar",
        entidad="estimacion",
        entidad_id=str(e.id),
        detalle={"comentario": body.comentario},
    )
    await db.commit()
    return {"estimacion": await _estimacion_a_dict(db, e)}


@router.post("/estimaciones/{estimacion_id}/recalcular")
async def recalcular_con_snapshot(
    estimacion_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Recalcula con el snapshot congelado y verifica reproducibilidad (CA-07)."""
    usuario = contexto_usuario(request, ROLES_ADMIN_AGRONOMO)
    e = await _buscar(db, estimacion_id)
    try:
        total_snapshot = await recalcular_desde_snapshot(db, e, rol=usuario["rol"])
    except EstimacionError as err:
        raise _err(422, err.code, err.message)
    coincidencia = (
        Decimal(str(total_snapshot)).quantize(Decimal("0.0001"))
        == Decimal(str(e.total_final)).quantize(Decimal("0.0001"))
    )
    return {
        "coincide": coincidencia,
        "total_guardado": _n(e.total_final),
        "total_snapshot": _n(total_snapshot),
        "hash_verificado": True,
    }


@router.post("/estimaciones/{estimacion_id}/convertir-comision")
async def convertir_en_comision(
    estimacion_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_ADMIN)
    e = await _buscar(db, estimacion_id)
    try:
        comision = await convertir_a_comision(
            db, e,
            usuario_id=usuario["uid"],
            usuario_email=usuario["email"],
            usuario_nombre=usuario["nombre"],
            rol=usuario["rol"],
            auditor=registrar_auditoria,
        )
    except EstimacionError as err:
        raise _err(422, err.code, err.message)
    await db.commit()
    return {"comision": {
        "id": str(comision.id),
        "finca_id": str(comision.finca_id),
        "valor_comision_cop": _n(comision.valor_comision_cop),
        "estado": comision.estado,
    }}


@router.get("/estimaciones/{estimacion_id}/export")
async def exportar_estimacion(
    estimacion_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    formato: str = Query("html", pattern="^(html|pdf)$"),
    audiencia: str = Query("agricultor", pattern="^(agricultor|tecnico)$"),
):
    """Descarga la cotización HTML/PDF con la identidad vigente (RF-21/26)."""
    usuario = contexto_usuario(request, ROLES_CLIENTE)
    e = await _buscar(db, estimacion_id)
    await _exigir_acceso(request, db, e, usuario)
    identidad, telefonos = await _identidad_con_telefonos(db)
    dict_e = await _estimacion_a_dict(db, e)
    finca = (
        await db.execute(select(Finca).where(Finca.id == e.finca_id))
    ).scalars().one_or_none()
    cliente_nombre = None
    if finca and finca.usuario_id:
        from agroia_backend.models.usuario import Usuario
        cliente = (
            await db.execute(select(Usuario).where(Usuario.id == finca.usuario_id))
        ).scalars().one_or_none()
        cliente_nombre = cliente.nombre if cliente else finca.propietario
    lotes = (
        await db.execute(select(Lote).where(Lote.finca_id == e.finca_id))
    ).scalars().all()
    nombres_lotes = {str(lot.id): lot.nombre for lot in lotes}
    for ln in dict_e["lineas"]:
        ln["lote"] = nombres_lotes.get(ln["lote_id"]) if ln["lote_id"] else None

    identidad_dict = {
        "nombre_comercial": identidad.nombre_comercial,
        "razon_social": identidad.razon_social,
        "nit": identidad.nit,
        "regimen": identidad.regimen,
        "sitio_web": identidad.sitio_web,
        "correo": identidad.correo,
        "direccion": identidad.direccion,
        "ciudad": identidad.ciudad,
        "logo_url": _logo_absoluto(request, identidad.logo_url),
        "color_acento": identidad.color_acento,
        "pie_legal": identidad.pie_legal,
        "terminos_condiciones": identidad.terminos_condiciones,
        "telefonos": [
            {"etiqueta": t.etiqueta, "numero": t.numero, "whatsapp": t.whatsapp, "orden": t.orden}
            for t in telefonos
        ],
    }
    # El cliente no ve costos internos (RFP §12): sin desglose de márgenes.
    es_interno = usuario["rol"] in ("admin", "administrador", "agronomo", "agrónomo")
    if not es_interno:
        audiencia = "agricultor"
        dict_e["total_directo"] = None
        dict_e["total_ajustado"] = None
        dict_e["precio_lista"] = None
        dict_e["margen_pct"] = None

    payload = {
        **dict_e,
        "cliente": cliente_nombre or finca.propietario if finca else None,
        "finca": finca.nombre if finca else None,
        "municipio": finca.municipio if finca else None,
        "area_ha": dict_e["area_total_ha"],
        "emitida": dict_e["emitida_en"] or dict_e["fecha_referencia"],
        "vence": dict_e["vence_en"],
        "asesor": usuario["nombre"] if es_interno else None,
        "terminos": identidad.terminos_condiciones,
    }

    if formato == "html":
        return HTMLResponse(html_cotizacion(payload, identidad_dict, audiencia))
    pdf_bytes = pdf_cotizacion(payload, identidad_dict)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="cotizacion-{e.consecutivo or e.id}.pdf"'
            )
        },
    )


def _logo_absoluto(request: Request, logo_url: str | None) -> str | None:
    if not logo_url:
        return None
    if logo_url.startswith("http"):
        return logo_url
    return f"{request.url.scheme}://{request.url.netloc}{logo_url}"


async def _identidad_con_telefonos(db):
    identidad = (
        await db.execute(select(CosteoIdentidad).order_by(CosteoIdentidad.creado_en.desc()))
    ).scalars().first()
    if identidad is None:
        identidad = CosteoIdentidad(nombre_comercial="AgroIA — AgroInteligente Colombia")
        db.add(identidad)
        await db.flush()
    telefonos = (
        await db.execute(
            select(CosteoTelefono).where(CosteoTelefono.identidad_id == identidad.id)
            .order_by(CosteoTelefono.orden)
        )
    ).scalars().all()
    return identidad, telefonos


# ─────────────────────── Documentos de cobro (F5) ────────────────────────────

class PagoIn(BaseModel):
    fecha: date | None = None
    valor: Decimal = Field(..., gt=0)
    medio: str | None = Field(None, max_length=40)
    referencia: str | None = Field(None, max_length=120)


class AnularIn(BaseModel):
    motivo: str = Field(..., min_length=5, max_length=500)


class EnviarIn(BaseModel):
    canal: str = Field("whatsapp", pattern="^(whatsapp|correo)$")
    destinatario: str = Field(..., min_length=3, max_length=120)


@router.post("/cobros", status_code=201)
async def crear_cobro(
    request: Request,
    db: AsyncSession = Depends(get_db),
    estimacion_id: str = Query(...),
):
    usuario = contexto_usuario(request, ROLES_ADMIN)
    e = await _buscar(db, estimacion_id)
    from agroia_backend.services.cobros import CobroError, crear_desde_estimacion
    identidad, telefonos = await _identidad_con_telefonos(db)
    try:
        documento = await crear_desde_estimacion(
            db, e,
            usuario_id=usuario["uid"],
            identidad_snapshot={
                "nombre_comercial": identidad.nombre_comercial,
                "nit": identidad.nit,
                "telefonos": [{"etiqueta": t.etiqueta, "numero": t.numero} for t in telefonos],
            },
            usuario_email=usuario["email"],
            usuario_nombre=usuario["nombre"],
            rol=usuario["rol"],
            auditor=registrar_auditoria,
        )
    except CobroError as err:
        raise _err(422, err.code, err.message)
    await db.commit()
    return {"documento": await _cobro_a_dict(db, documento)}


@router.get("/cobros")
async def listar_cobros(
    request: Request,
    db: AsyncSession = Depends(get_db),
    limite: int = Query(50, ge=1, le=200),
):
    contexto_usuario(request, ROLES_ADMIN)
    documentos = (
        await db.execute(
            select(CobroDocumento).order_by(CobroDocumento.creado_en.desc()).limit(limite)
        )
    ).scalars().all()
    return {"data": [await _cobro_a_dict(db, d, con_detalle=False) for d in documentos]}


async def _cobro_a_dict(db, d: CobroDocumento, con_detalle: bool = True) -> dict:
    e = (
        await db.execute(select(Estimacion).where(Estimacion.id == d.estimacion_id))
    ).scalars().one_or_none()
    finca = (
        await db.execute(select(Finca).where(Finca.id == e.finca_id))
    ).scalars().one_or_none() if e else None
    lineas, pagos = [], []
    if con_detalle:
        from agroia_backend.models.cobros import CobroLinea, CobroPago
        lineas = (
            await db.execute(select(CobroLinea).where(CobroLinea.documento_id == d.id))
        ).scalars().all()
        pagos = (
            await db.execute(select(CobroPago).where(CobroPago.documento_id == d.id)
                             .order_by(CobroPago.fecha))
        ).scalars().all()
    return {
        "id": str(d.id),
        "numero": f"{d.prefijo}-{d.consecutivo}" if d.consecutivo else None,
        "tipo": d.tipo,
        "estado": d.estado,
        "estimacion_id": str(d.estimacion_id),
        "estimacion": e.consecutivo if e else None,
        "finca": finca.nombre if finca else None,
        "fecha_emision": d.fecha_emision.isoformat() if d.fecha_emision else None,
        "fecha_vencimiento": d.fecha_vencimiento.isoformat() if d.fecha_vencimiento else None,
        "subtotal": _n(d.subtotal),
        "impuestos": _n(d.impuestos),
        "total": _n(d.total),
        "saldo": _n(d.saldo),
        "motivo_anulacion": d.motivo_anulacion,
        "lineas": [
            {"descripcion": ln.descripcion, "cantidad": _n(ln.cantidad),
             "unidad": ln.unidad, "valor": _n(ln.valor)}
            for ln in lineas
        ],
        "pagos": [
            {"fecha": p.fecha.isoformat(), "valor": _n(p.valor), "medio": p.medio}
            for p in pagos
        ],
    }


async def _cobro_o_404(db, documento_id: str) -> CobroDocumento:
    d = (
        await db.execute(select(CobroDocumento).where(CobroDocumento.id == _uuid(documento_id)))
    ).scalars().one_or_none()
    if d is None:
        raise _err(404, "COBRO_NOT_FOUND", "El documento de cobro no existe.")
    return d


@router.post("/cobros/{documento_id}/emitir")
async def emitir_cobro(
    documento_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_ADMIN)
    d = await _cobro_o_404(db, documento_id)
    from agroia_backend.services.cobros import CobroError, emitir as emitir_cobro_srv
    try:
        await emitir_cobro_srv(
            db, d,
            usuario_id=usuario["uid"],
            usuario_email=usuario["email"],
            usuario_nombre=usuario["nombre"],
            rol=usuario["rol"],
            auditor=registrar_auditoria,
        )
    except CobroError as err:
        raise _err(422, err.code, err.message)
    await db.commit()
    return {"documento": await _cobro_a_dict(db, d)}


@router.post("/cobros/{documento_id}/pagos", status_code=201)
async def registrar_pago(
    documento_id: str,
    body: PagoIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_ADMIN)
    d = await _cobro_o_404(db, documento_id)
    from agroia_backend.services.cobros import CobroError, registrar_pago as registrar_pago_srv
    try:
        await registrar_pago_srv(
            db, d,
            usuario_id=usuario["uid"],
            fecha=body.fecha or date.today(),
            valor=body.valor,
            medio=body.medio,
            referencia=body.referencia,
            usuario_email=usuario["email"],
            usuario_nombre=usuario["nombre"],
            rol=usuario["rol"],
            auditor=registrar_auditoria,
        )
    except CobroError as err:
        raise _err(422, err.code, err.message)
    await db.commit()
    return {"documento": await _cobro_a_dict(db, d)}


@router.post("/cobros/{documento_id}/anular")
async def anular_cobro(
    documento_id: str,
    body: AnularIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_ADMIN)
    d = await _cobro_o_404(db, documento_id)
    from agroia_backend.services.cobros import CobroError, anular as anular_srv
    try:
        await anular_srv(
            db, d,
            usuario_id=usuario["uid"],
            motivo=body.motivo,
            usuario_email=usuario["email"],
            usuario_nombre=usuario["nombre"],
            rol=usuario["rol"],
            auditor=registrar_auditoria,
        )
    except CobroError as err:
        raise _err(422, err.code, err.message)
    await db.commit()
    return {"documento": await _cobro_a_dict(db, d)}


@router.post("/cobros/{documento_id}/enviar")
async def enviar_cobro(
    documento_id: str,
    body: EnviarIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Marca el envío y usa el canal de notificaciones de la v4 (RF-33)."""
    usuario = contexto_usuario(request, ROLES_ADMIN)
    d = await _cobro_o_404(db, documento_id)
    from agroia_backend.services.cobros import CobroError, marcar_enviado
    try:
        await marcar_enviado(
            db, d,
            usuario_id=usuario["uid"],
            canal=body.canal,
            destinatario=body.destinatario,
        )
    except CobroError as err:
        raise _err(422, err.code, err.message)
    if body.canal == "whatsapp":
        try:
            from agroia_backend.services.notificaciones import enviar_whatsapp
            enviar_whatsapp(body.destinatario, "cobro_enviado",
                            [f"{d.prefijo}-{d.consecutivo}"])
        except Exception as exc:  # noqa: BLE001 — el envío no debe tumbar el endpoint
            logger.warning("cobro_whatsapp_fallo", error=str(exc))
    await db.commit()
    return {"documento": await _cobro_a_dict(db, d)}


@router.get("/cobros/{documento_id}/pdf")
async def pdf_documento_cobro(
    documento_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_CLIENTE)
    d = await _cobro_o_404(db, documento_id)
    if usuario["rol"] not in ("admin", "administrador"):
        e = (
            await db.execute(select(Estimacion).where(Estimacion.id == d.estimacion_id))
        ).scalars().one_or_none()
        if e is None:
            raise _err(403, "FORBIDDEN_ROLE", "Sin permiso para descargar el documento.")
        await _exigir_acceso(request, db, e, usuario)
    dict_d = await _cobro_a_dict(db, d)
    identidad, telefonos = await _identidad_con_telefonos(db)
    identidad_dict = {
        "nombre_comercial": identidad.nombre_comercial,
        "razon_social": identidad.razon_social,
        "nit": identidad.nit,
        "regimen": identidad.regimen,
        "sitio_web": identidad.sitio_web,
        "correo": identidad.correo,
        "direccion": identidad.direccion,
        "ciudad": identidad.ciudad,
        "logo_url": _logo_absoluto(request, identidad.logo_url),
        "color_acento": identidad.color_acento,
        "pie_legal": identidad.pie_legal,
        "terminos_condiciones": identidad.terminos_condiciones,
        "telefonos": [
            {"etiqueta": t.etiqueta, "numero": t.numero, "orden": t.orden} for t in telefonos
        ],
    }
    e = (
        await db.execute(select(Estimacion).where(Estimacion.id == d.estimacion_id))
    ).scalars().one_or_none()
    finca = (
        await db.execute(select(Finca).where(Finca.id == e.finca_id))
    ).scalars().one_or_none() if e else None
    payload = {
        **dict_d,
        "tipo_titulo": "Cuenta de cobro" if d.tipo == "cuenta_cobro" else "Factura de venta",
        "cliente": finca.propietario if finca else None,
        "finca": finca.nombre if finca else None,
        "estimacion": e.consecutivo if e else None,
        "textos_legales": "",
    }
    pdf_bytes = pdf_cobro(payload, identidad_dict)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="cobro-{d.prefijo}-{d.consecutivo}.pdf"'
        },
    )


@router.get("/cobros/{documento_id}/export")
async def exportar_cobro_html(
    documento_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    audiencia: str = Query("agricultor", pattern="^(agricultor|tecnico)$"),
):
    usuario = contexto_usuario(request, ROLES_CLIENTE)
    d = await _cobro_o_404(db, documento_id)
    e = (
        await db.execute(select(Estimacion).where(Estimacion.id == d.estimacion_id))
    ).scalars().one_or_none()
    if e is not None:
        await _exigir_acceso(request, db, e, usuario)
    identidad, telefonos = await _identidad_con_telefonos(db)
    identidad_dict = {
        "nombre_comercial": identidad.nombre_comercial,
        "nit": identidad.nit,
        "sitio_web": identidad.sitio_web,
        "correo": identidad.correo,
        "ciudad": identidad.ciudad,
        "logo_url": _logo_absoluto(request, identidad.logo_url),
        "color_acento": identidad.color_acento,
        "pie_legal": identidad.pie_legal,
        "terminos_condiciones": identidad.terminos_condiciones,
        "telefonos": [
            {"etiqueta": t.etiqueta, "numero": t.numero, "orden": t.orden} for t in telefonos
        ],
    }
    dict_d = await _cobro_a_dict(db, d)
    finca = (
        await db.execute(select(Finca).where(Finca.id == e.finca_id))
    ).scalars().one_or_none() if e else None
    payload = {
        **dict_d,
        "tipo_titulo": "Cuenta de cobro" if d.tipo == "cuenta_cobro" else "Factura de venta",
        "cliente": finca.propietario if finca else None,
        "finca": finca.nombre if finca else None,
        "estimacion": e.consecutivo if e else None,
        "textos_legales": "",
    }
    return HTMLResponse(html_cobro(payload, identidad_dict, audiencia))
