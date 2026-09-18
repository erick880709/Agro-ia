"""API AGC-COST (F1) — parámetros vigentes y simulación de cálculo.

RFP AgroIA v4 §10: `GET /costeo/parametros/vigentes` y `POST /costeo/simular`
(roles Admin y Agrónomo). La simulación no persiste nada; el cálculo lo
ejecuta el motor puro `services/costeo_motor.py` con el conjunto de
parámetros resuelto desde la base de datos.
"""

import uuid as uuid_mod
from datetime import date, datetime, timezone
from decimal import Decimal

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.costeo import (
    CosteoComponente,
    CosteoConjunto,
    CosteoDescuento,
    CosteoDensidad,
    CosteoFactor,
    CosteoFactorOpcion,
    CosteoImpuesto,
    CosteoPolitica,
    CosteoServicio,
    CosteoTramo,
    CosteoZona,
)
from agroia_backend.services.costeo_motor import CosteoError, calcular

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["costeo"])

ROLES_PERMITIDOS = {"admin", "administrador", "agronomo", "agrónomo"}


def _exigir_rol(rol: str | None) -> str:
    rol_norm = (rol or "").strip().lower()
    if rol_norm not in ROLES_PERMITIDOS:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo los roles administrador y agrónomo pueden usar el costeo.",
        })
    return rol_norm


def _n(v) -> float | None:
    """Decimal → float para la respuesta JSON (el cálculo ya fue exacto)."""
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    return v


async def _conjunto_vigente(db: AsyncSession, fecha: date) -> CosteoConjunto | None:
    return (
        await db.execute(
            select(CosteoConjunto)
            .where(
                CosteoConjunto.estado == "publicado",
                CosteoConjunto.vigencia_desde.is_not(None),
                CosteoConjunto.vigencia_desde <= fecha,
            )
            .order_by(CosteoConjunto.vigencia_desde.desc(), CosteoConjunto.version.desc())
            .limit(1)
        )
    ).scalars().first()


async def _conjunto_a_dict(db: AsyncSession, conjunto: CosteoConjunto) -> dict:
    """Serializa el conjunto con sus hijos (servicios→componentes→tramos, etc.)."""
    servicios = (
        await db.execute(
            select(CosteoServicio)
            .where(CosteoServicio.conjunto_id == conjunto.id)
            .order_by(CosteoServicio.orden, CosteoServicio.codigo)
        )
    ).scalars().all()
    componentes = (
        await db.execute(
            select(CosteoComponente).where(
                CosteoComponente.servicio_id.in_([s.id for s in servicios])
            )
        )
    ).scalars().all() if servicios else []
    tramos = (
        await db.execute(
            select(CosteoTramo).where(
                CosteoTramo.componente_id.in_([c.id for c in componentes])
            ).order_by(CosteoTramo.desde)
        )
    ).scalars().all() if componentes else []
    factores = (
        await db.execute(
            select(CosteoFactor)
            .where(CosteoFactor.conjunto_id == conjunto.id)
            .order_by(CosteoFactor.codigo)
        )
    ).scalars().all()
    opciones = (
        await db.execute(
            select(CosteoFactorOpcion).where(
                CosteoFactorOpcion.factor_id.in_([f.id for f in factores])
            ).order_by(CosteoFactorOpcion.orden)
        )
    ).scalars().all() if factores else []

    por_componente: dict = {}
    for t in tramos:
        por_componente.setdefault(t.componente_id, []).append({
            "desde": _n(t.desde),
            "hasta": _n(t.hasta),
            "valor": _n(t.valor),
            "modo": t.modo,
        })
    por_servicio: dict = {}
    for c in componentes:
        por_servicio.setdefault(c.servicio_id, []).append({
            "id": str(c.id),
            "codigo": c.codigo,
            "nombre": c.nombre,
            "tipo": c.tipo,
            "orden": c.orden,
            "afectable_por_factores": c.afectable_por_factores,
            "config": c.config or {},
            "tramos": por_componente.get(c.id, []),
        })
    por_factor: dict = {}
    for o in opciones:
        por_factor.setdefault(o.factor_id, []).append({
            "codigo": o.codigo,
            "etiqueta": o.etiqueta,
            "porcentaje": _n(o.porcentaje),
            "orden": o.orden,
        })

    politica = (
        await db.execute(select(CosteoPolitica).where(CosteoPolitica.conjunto_id == conjunto.id))
    ).scalars().first()
    impuestos = (
        await db.execute(
            select(CosteoImpuesto).where(CosteoImpuesto.conjunto_id == conjunto.id)
        )
    ).scalars().all()
    descuentos = (
        await db.execute(
            select(CosteoDescuento).where(CosteoDescuento.conjunto_id == conjunto.id)
        )
    ).scalars().all()
    densidad = (
        await db.execute(
            select(CosteoDensidad).where(CosteoDensidad.conjunto_id == conjunto.id)
        )
    ).scalars().all()
    zonas = (
        await db.execute(
            select(CosteoZona).where(CosteoZona.conjunto_id == conjunto.id)
        )
    ).scalars().all()

    return {
        "id": str(conjunto.id),
        "nombre": conjunto.nombre,
        "version": conjunto.version,
        "estado": conjunto.estado,
        "vigencia_desde": conjunto.vigencia_desde.isoformat() if conjunto.vigencia_desde else None,
        "vigencia_hasta": conjunto.vigencia_hasta.isoformat() if conjunto.vigencia_hasta else None,
        "moneda": conjunto.moneda,
        "notas": conjunto.notas,
        "politica": {
            "margen_objetivo": _n(politica.margen_objetivo) if politica else 0.0,
            "margen_minimo": _n(politica.margen_minimo) if politica else 0.0,
            "piso_visita": _n(politica.piso_visita) if politica else 0.0,
            "vigencia_cotizacion_dias": politica.vigencia_cotizacion_dias if politica else 30,
            "redondeo_multiplo": _n(politica.redondeo_multiplo) if politica else 1.0,
            "redondeo_modo": politica.redondeo_modo if politica else "ninguno",
        },
        "servicios": [
            {
                "id": str(s.id),
                "codigo": s.codigo,
                "nombre": s.nombre,
                "unidad": s.unidad,
                "requiere_lote": s.requiere_lote,
                "activo": s.activo,
                "orden": s.orden,
                "componentes": sorted(
                    por_servicio.get(s.id, []), key=lambda c: c["orden"]
                ),
            }
            for s in servicios
        ],
        "factores": [
            {
                "id": str(f.id),
                "codigo": f.codigo,
                "nombre": f.nombre,
                "aplicacion": f.aplicacion,
                "combinacion": f.combinacion,
                "opciones": por_factor.get(f.id, []),
            }
            for f in factores
        ],
        "impuestos": [
            {
                "codigo": i.codigo,
                "nombre": i.nombre,
                "porcentaje": _n(i.porcentaje),
                "base": i.base,
                "informativo": i.informativo,
            }
            for i in impuestos
        ],
        "descuentos": [
            {
                "codigo": d.codigo,
                "criterio": d.criterio,
                "umbral": _n(d.umbral),
                "porcentaje": _n(d.porcentaje),
                "tope_rol": d.tope_rol or {},
            }
            for d in descuentos
        ],
        "densidad": [
            {
                "area_min": _n(d.area_min),
                "area_max": _n(d.area_max),
                "puntos_min": d.puntos_min,
                "puntos_max": d.puntos_max,
                "puntos_por_ha": _n(d.puntos_por_ha),
                "cultivo_id": str(d.cultivo_id) if d.cultivo_id else None,
            }
            for d in densidad
        ],
        "zonas": [
            {
                "departamento": z.departamento,
                "municipio": z.municipio,
                "factor": _n(z.factor),
                "km_incluidos": _n(z.km_incluidos),
                "tarifa_km": _n(z.tarifa_km),
                "peajes_estimados": _n(z.peajes_estimados),
            }
            for z in zonas
        ],
    }


def _serializar_resultado(res: dict) -> dict:
    """Convierte Decimales a float para la respuesta JSON."""
    salida = {k: v for k, v in res.items()}
    for clave in (
        "subtotal_directo", "subtotal_ajustado", "precio_lista",
        "descuento_aplicado", "descuento_pct", "total_sin_redondeo",
        "ajuste_redondeo", "total_final",
    ):
        salida[clave] = _n(res.get(clave))
    salida["lineas"] = [
        {**ln, "valor": _n(ln["valor"]), "cantidad": _n(ln["cantidad"]),
         "valor_unitario": _n(ln.get("valor_unitario"))}
        for ln in res.get("lineas", [])
    ]
    salida["factores_aplicados"] = [
        {**f, "porcentaje": _n(f.get("porcentaje")), "valor": _n(f.get("valor"))}
        for f in res.get("factores_aplicados", [])
    ]
    salida["impuestos_informativos"] = [
        {**i, "porcentaje": _n(i.get("porcentaje")), "base_valor": _n(i.get("base_valor")),
         "valor": _n(i.get("valor"))}
        for i in res.get("impuestos_informativos", [])
    ]
    salida["impuestos_incluidos"] = [
        {**i, "porcentaje": _n(i.get("porcentaje")), "base_valor": _n(i.get("base_valor")),
         "valor": _n(i.get("valor"))}
        for i in res.get("impuestos_incluidos", [])
    ]
    salida["indicadores"] = {k: _n(v) for k, v in res.get("indicadores", {}).items()}
    return salida


class ServicioIn(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=40)
    cantidad: Decimal = Field(Decimal("1"), ge=0)


class SimularRequest(BaseModel):
    conjunto_id: str | None = Field(None, description="UUID del conjunto; vacío = vigente a la fecha")
    fecha_referencia: date | None = Field(None, description="Fecha de referencia (hoy por defecto)")
    area_ha: Decimal = Field(..., gt=0, description="Área del lote en hectáreas")
    puntos: int | None = Field(None, ge=0, description="Puntos de muestreo (vacío = suma de cantidades)")
    km: Decimal = Field(Decimal("0"), ge=0, description="Distancia desde la sede (km)")
    dificultad: str | None = Field(None, description="Opción del factor 'dificultad'")
    departamento: str | None = Field(None, max_length=60)
    municipio: str | None = Field(None, max_length=80)
    descuento_pct: Decimal | None = Field(None, ge=0, le=100)
    servicios: list[ServicioIn] = Field(..., min_length=1)


@router.get("/costeo/parametros/vigentes")
async def parametros_vigentes(
    fecha: date | None = Query(None, description="Fecha de referencia (hoy por defecto)"),
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Conjunto de parámetros publicado y vigente (para cotizador y caché PWA)."""
    _exigir_rol(x_user_role)
    fecha_ref = fecha or datetime.now(timezone.utc).date()
    conjunto = await _conjunto_vigente(db, fecha_ref)
    if conjunto is None:
        raise HTTPException(status_code=404, detail={
            "code": "CONJUNTO_SIN_VIGENCIA",
            "message": "No hay un conjunto de parámetros publicado vigente para la fecha.",
        })
    return {"fecha_referencia": fecha_ref.isoformat(), "conjunto": await _conjunto_a_dict(db, conjunto)}


@router.post("/costeo/simular")
async def simular(
    body: SimularRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Cálculo de costeo sin persistir, contra el conjunto indicado o el vigente."""
    rol = _exigir_rol(x_user_role)
    fecha_ref = body.fecha_referencia or datetime.now(timezone.utc).date()

    if body.conjunto_id:
        try:
            cid = uuid_mod.UUID(body.conjunto_id)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "CONJUNTO_INVALIDO", "message": "conjunto_id no es un UUID válido.",
            })
        conjunto = (
            await db.execute(select(CosteoConjunto).where(CosteoConjunto.id == cid))
        ).scalars().one_or_none()
        if conjunto is None:
            raise HTTPException(status_code=404, detail={
                "code": "CONJUNTO_NOT_FOUND", "message": "El conjunto no está registrado.",
            })
    else:
        conjunto = await _conjunto_vigente(db, fecha_ref)
        if conjunto is None:
            raise HTTPException(status_code=404, detail={
                "code": "CONJUNTO_SIN_VIGENCIA",
                "message": "No hay un conjunto de parámetros publicado vigente para la fecha.",
            })

    conjunto_dict = await _conjunto_a_dict(db, conjunto)
    puntos = body.puntos if body.puntos is not None else sum(
        int(s.cantidad) for s in body.servicios
    )
    zona = next(
        (z for z in conjunto_dict.get("zonas", [])
         if z["departamento"] == body.departamento
         and (z["municipio"] == body.municipio or z["municipio"] is None)),
        {},
    )
    contexto = {
        "fecha_referencia": fecha_ref,
        "area_ha": body.area_ha,
        "puntos": puntos,
        "km": body.km,
        "rol": rol,
        "departamento": body.departamento,
        "municipio": body.municipio,
        "zona": zona,
    }
    seleccion = {
        "servicios": [{"codigo": s.codigo, "cantidad": s.cantidad} for s in body.servicios],
        "factores": {"dificultad": body.dificultad} if body.dificultad else {},
        "descuento_pct": body.descuento_pct,
    }

    try:
        resultado = calcular(contexto, conjunto_dict, seleccion)
    except CosteoError as e:
        raise HTTPException(status_code=422, detail={"code": e.code, "message": e.message})

    logger.info(
        "costeo_simulado",
        conjunto_id=str(conjunto.id),
        total=float(resultado["total_final"]),
        puntos=puntos,
        area_ha=float(body.area_ha),
    )
    return _serializar_resultado(resultado)
