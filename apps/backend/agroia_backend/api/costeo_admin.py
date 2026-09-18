"""API AGC-COST (F2) — administración de parámetros de costeo.

CRUD admin de conjuntos, servicios, componentes, tramos, factores, opciones,
densidad, zonas, impuestos, política y descuentos (RF-01 a RF-05, RF-14,
RF-15, RF-18). Doble control, validación previa, clonación con reajuste
masivo e import/export JSON (RF-23). Toda mutación queda en auditoría (RF-22).
"""

import uuid as uuid_mod
from datetime import date, datetime, timezone
from decimal import Decimal

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.costeo import (
    CosteoComponente,
    CosteoConjunto,
    CosteoDensidad,
    CosteoDescuento,
    CosteoFactor,
    CosteoFactorOpcion,
    CosteoImpuesto,
    CosteoPolitica,
    CosteoServicio,
    CosteoTramo,
    CosteoZona,
)
from agroia_backend.services.auth_contexto import ROLES_ADMIN, contexto_usuario
from agroia_backend.services.auditoria import registrar_auditoria
from agroia_backend.services.costeo_validacion import validar_conjunto

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/costeo", tags=["costeo-admin"])

_ESTADOS_EDITABLES = {"borrador", "en_revision"}


def _err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _uuid(valor: str | None) -> uuid_mod.UUID | None:
    if not valor:
        return None
    try:
        return uuid_mod.UUID(str(valor))
    except ValueError:
        return None


async def _conjunto_o_404(db: AsyncSession, conjunto_id: str) -> CosteoConjunto:
    cid = _uuid(conjunto_id)
    if cid is None:
        raise _err(422, "CONJUNTO_INVALIDO", "conjunto_id no es un UUID válido.")
    conjunto = (
        await db.execute(select(CosteoConjunto).where(CosteoConjunto.id == cid))
    ).scalars().one_or_none()
    if conjunto is None:
        raise _err(404, "CONJUNTO_NOT_FOUND", "El conjunto no está registrado.")
    return conjunto


async def _exigir_editable(db: AsyncSession, conjunto: CosteoConjunto) -> None:
    if conjunto.estado not in _ESTADOS_EDITABLES:
        raise _err(
            422,
            "CONJUNTO_NO_EDITABLE",
            f"El conjunto está en estado «{conjunto.estado}»; solo se editan "
            "borradores o conjuntos en revisión.",
        )


def _json_detalle(valor):
    """Convierte Decimal/date a tipos JSON para auditoria.detalle (JSONB)."""
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {k: _json_detalle(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_json_detalle(v) for v in valor]
    return valor


async def _auditar(request: Request, db, *, accion: str, entidad_id: str | None, detalle: dict) -> None:
    usuario = contexto_usuario(request, ROLES_ADMIN)
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion=accion,
        entidad="costeo",
        entidad_id=entidad_id,
        detalle=_json_detalle(detalle),
    )


def _json_conjunto(db_conjunto, db) -> dict:
    """(Reservado) Serializador de conjunto para import/export."""

    return None  # pragma: no cover — se usa _conjunto_a_dict directamente


# ─────────────────────────── Conjuntos ───────────────────────────────────────

class ConjuntoIn(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150)
    notas: str | None = Field(None, max_length=2000)
    moneda: str = Field("COP", max_length=5)
    vigencia_desde: date | None = None


class ClonarIn(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=150)
    reajuste_pct: Decimal | None = Field(None, ge=-100, le=1000)


@router.get("/conjuntos")
async def listar_conjuntos(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    conjuntos = (
        await db.execute(
            select(CosteoConjunto).order_by(
                CosteoConjunto.version.desc(), CosteoConjunto.creado_en.desc()
            )
        )
    ).scalars().all()
    return {"data": [
        {
            "id": str(c.id),
            "nombre": c.nombre,
            "version": c.version,
            "estado": c.estado,
            "vigencia_desde": c.vigencia_desde.isoformat() if c.vigencia_desde else None,
            "vigencia_hasta": c.vigencia_hasta.isoformat() if c.vigencia_hasta else None,
            "moneda": c.moneda,
            "notas": c.notas,
            "aprobado_en": c.aprobado_en.isoformat() if c.aprobado_en else None,
        }
        for c in conjuntos
    ]}


@router.post("/conjuntos", status_code=201)
async def crear_conjunto(
    body: ConjuntoIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_ADMIN)
    ultima = (
        await db.execute(select(CosteoConjunto).order_by(CosteoConjunto.version.desc()).limit(1))
    ).scalars().one_or_none()
    version = (ultima.version + 1) if ultima else 1
    conjunto = CosteoConjunto(
        nombre=body.nombre,
        notas=body.notas,
        moneda=body.moneda,
        version=version,
        estado="borrador",
        vigencia_desde=body.vigencia_desde,
        creado_por=usuario["uid"],
    )
    db.add(conjunto)
    await db.flush()
    await _auditar(request, db, accion="costeo.conjunto.crear",
                  entidad_id=str(conjunto.id), detalle={"nombre": body.nombre})
    await db.commit()
    return {"id": str(conjunto.id), "version": version, "estado": "borrador"}


@router.get("/conjuntos/{conjunto_id}")
async def ver_conjunto(
    conjunto_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    from agroia_backend.api.costeo import _conjunto_a_dict
    return {"conjunto": await _conjunto_a_dict(db, conjunto)}


@router.patch("/conjuntos/{conjunto_id}")
async def actualizar_conjunto(
    conjunto_id: str,
    body: ConjuntoIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    await _exigir_editable(db, conjunto)
    cambios = {}
    if body.nombre and body.nombre != conjunto.nombre:
        cambios["nombre"] = {"anterior": conjunto.nombre, "nuevo": body.nombre}
        conjunto.nombre = body.nombre
    if body.notas != conjunto.notas:
        cambios["notas"] = {"anterior": conjunto.notas, "nuevo": body.notas}
        conjunto.notas = body.notas
    if body.vigencia_desde:
        cambios["vigencia_desde"] = {"anterior": str(conjunto.vigencia_desde),
                                     "nuevo": body.vigencia_desde.isoformat()}
        conjunto.vigencia_desde = body.vigencia_desde
    await _auditar(request, db, accion="costeo.conjunto.editar",
                  entidad_id=str(conjunto.id), detalle=cambios)
    await db.commit()
    return {"ok": True, "cambios": cambios}


@router.post("/conjuntos/{conjunto_id}/validar")
async def validar_conjunto_endpoint(
    conjunto_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    from agroia_backend.api.costeo import _conjunto_a_dict
    resultado = validar_conjunto(await _conjunto_a_dict(db, conjunto))
    return {
        "conjunto_id": str(conjunto.id),
        "valido": resultado["valido"],
        "errores": resultado["errores"],
        "advertencias": resultado["advertencias"],
    }


@router.post("/conjuntos/{conjunto_id}/publicar")
async def publicar_conjunto(
    conjunto_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Publica con doble control (RF-15) y validación previa (RF-14)."""
    usuario = contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    if conjunto.estado == "publicado":
        raise _err(422, "CONJUNTO_YA_PUBLICADO", "El conjunto ya está publicado.")

    # Doble control: quien edita no puede publicar (RF-15).
    if conjunto.creado_por and conjunto.creado_por == usuario["uid"]:
        raise _err(
            422,
            "APROBADOR_ES_EDITOR",
            "Doble control: el usuario que creó/editó el conjunto no puede publicarlo. "
            "La publicación debe hacerla otro administrador.",
        )

    from agroia_backend.api.costeo import _conjunto_a_dict
    dict_conjunto = await _conjunto_a_dict(db, conjunto)
    resultado = validar_conjunto(dict_conjunto)
    if not resultado["valido"]:
        raise _err(
            422,
            "CONJUNTO_INVALIDO",
            "Validación previa fallida: " + "; ".join(
                e["mensaje"] for e in resultado["errores"][:5]
            ),
        )

    # Simulación obligatoria (§13): exige al menos una simulación registrada
    # contra este conjunto en la bitácora.
    from agroia_backend.models.auditoria import Auditoria
    simulaciones = (
        await db.execute(
            select(Auditoria).where(
                Auditoria.accion == "costeo.simular",
                Auditoria.entidad_id == str(conjunto.id),
            ).limit(1)
        )
    ).scalars().first()
    if simulaciones is None:
        raise _err(
            422,
            "SIMULACION_REQUERIDA",
            "Antes de publicar debe correr al menos un caso en el simulador "
            "sobre este borrador (RFP §13).",
        )

    hoy = date.today()
    # Archiva el publicado vigente anterior sin borrarlo (RF-14).
    anterior = (
        await db.execute(
            select(CosteoConjunto).where(
                CosteoConjunto.estado == "publicado",
                CosteoConjunto.id != conjunto.id,
                CosteoConjunto.vigencia_hasta.is_(None),
            )
        )
    ).scalars().all()
    for c in anterior:
        c.estado = "archivado"
        c.vigencia_hasta = hoy

    conjunto.estado = "publicado"
    conjunto.vigencia_desde = conjunto.vigencia_desde or hoy
    conjunto.vigencia_hasta = None
    conjunto.aprobado_por = usuario["uid"]
    conjunto.aprobado_en = datetime.now(timezone.utc)
    await _auditar(request, db, accion="costeo.conjunto.publicar",
                  entidad_id=str(conjunto.id),
                  detalle={"version": conjunto.version, "archivados": len(anterior)})
    await db.commit()
    return {"ok": True, "estado": "publicado", "version": conjunto.version}


@router.post("/conjuntos/{conjunto_id}/archivar")
async def archivar_conjunto(
    conjunto_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    if conjunto.estado == "archivado":
        raise _err(422, "CONJUNTO_YA_ARCHIVADO", "El conjunto ya está archivado.")
    conjunto.estado = "archivado"
    conjunto.vigencia_hasta = date.today()
    await _auditar(request, db, accion="costeo.conjunto.archivar",
                  entidad_id=str(conjunto.id), detalle={})
    await db.commit()
    return {"ok": True, "estado": "archivado"}


@router.get("/conjuntos/{conjunto_id}/reajuste-previo")
async def reajuste_previo(
    conjunto_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    porcentaje: Decimal = Query(..., ge=-100, le=1000),
):
    """Vista previa del reajuste masivo sobre valores monetarios (RF-18)."""
    contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    factor = Decimal("1") + porcentaje / Decimal("100")
    cambios = []

    componentes = (
        await db.execute(
            select(CosteoComponente).join(
                CosteoServicio, CosteoComponente.servicio_id == CosteoServicio.id
            ).where(CosteoServicio.conjunto_id == conjunto.id)
        )
    ).scalars().all()
    for c in componentes:
        config = dict(c.config or {})
        if config.get("valor") is not None:
            nuevo = (Decimal(str(config["valor"])) * factor).quantize(Decimal("0.01"))
            cambios.append({"tipo": "componente", "codigo": c.codigo,
                            "anterior": float(config["valor"]), "nuevo": float(nuevo)})
    tramos = (
        await db.execute(
            select(CosteoTramo).join(
                CosteoComponente, CosteoTramo.componente_id == CosteoComponente.id
            ).join(
                CosteoServicio, CosteoComponente.servicio_id == CosteoServicio.id
            ).where(CosteoServicio.conjunto_id == conjunto.id)
        )
    ).scalars().all()
    for t in tramos:
        nuevo = (t.valor * factor).quantize(Decimal("0.01"))
        cambios.append({"tipo": "tramo", "desde": float(t.desde),
                        "anterior": float(t.valor), "nuevo": float(nuevo)})
    zonas = (
        await db.execute(
            select(CosteoZona).where(CosteoZona.conjunto_id == conjunto.id)
        )
    ).scalars().all()
    for z in zonas:
        cambios.append({"tipo": "zona", "municipio": z.municipio or z.departamento,
                        "anterior": float(z.tarifa_km), "nuevo": float((z.tarifa_km * factor).quantize(Decimal("0.01")))})
    return {"porcentaje": float(porcentaje), "cambios": cambios, "total_cambios": len(cambios)}


@router.post("/conjuntos/{conjunto_id}/clonar", status_code=201)
async def clonar_conjunto(
    conjunto_id: str,
    body: ClonarIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Clona un conjunto con reajuste masivo opcional (RF-18)."""
    contexto_usuario(request, ROLES_ADMIN)
    origen = await _conjunto_o_404(db, conjunto_id)
    factor = Decimal("1")
    if body.reajuste_pct is not None:
        factor += body.reajuste_pct / Decimal("100")

    ultima = (
        await db.execute(select(CosteoConjunto).order_by(CosteoConjunto.version.desc()).limit(1))
    ).scalars().one_or_none()
    clon = CosteoConjunto(
        nombre=body.nombre or f"{origen.nombre} (clon)",
        version=(ultima.version + 1) if ultima else origen.version + 1,
        estado="borrador",
        moneda=origen.moneda,
        notas=f"Clon de v{origen.version} «{origen.nombre}»"
              + (f" con reajuste del {body.reajuste_pct}%." if body.reajuste_pct is not None else "."),
    )
    db.add(clon)
    await db.flush()

    servicios = (
        await db.execute(select(CosteoServicio).where(CosteoServicio.conjunto_id == origen.id))
    ).scalars().all()
    mapa_servicios: dict = {}
    for s in servicios:
        copia = CosteoServicio(
            conjunto_id=clon.id, codigo=s.codigo, nombre=s.nombre, unidad=s.unidad,
            requiere_lote=s.requiere_lote, activo=s.activo, orden=s.orden,
        )
        db.add(copia)
        await db.flush()
        mapa_servicios[s.id] = copia.id

    componentes = (
        await db.execute(
            select(CosteoComponente).where(
                CosteoComponente.servicio_id.in_([s.id for s in servicios])
            )
        )
    ).scalars().all()
    mapa_componentes: dict = {}
    for c in componentes:
        config = dict(c.config or {})
        if config.get("valor") is not None:
            config["valor"] = float(
                (Decimal(str(config["valor"])) * factor).quantize(Decimal("0.01"))
            )
        copia = CosteoComponente(
            servicio_id=mapa_servicios[c.servicio_id], codigo=c.codigo, nombre=c.nombre,
            tipo=c.tipo, orden=c.orden, afectable_por_factores=c.afectable_por_factores,
            config=config,
        )
        db.add(copia)
        await db.flush()
        mapa_componentes[c.id] = copia.id

    tramos = (
        await db.execute(
            select(CosteoTramo).where(
                CosteoTramo.componente_id.in_([c.id for c in componentes])
            )
        )
    ).scalars().all()
    for t in tramos:
        db.add(CosteoTramo(
            componente_id=mapa_componentes[t.componente_id],
            desde=t.desde, hasta=t.hasta,
            valor=(t.valor * factor).quantize(Decimal("0.01")),
            modo=t.modo,
        ))

    for modelo, filtro in (
        (CosteoFactor, {"conjunto_id": origen.id}),
        (CosteoImpuesto, {"conjunto_id": origen.id}),
        (CosteoDescuento, {"conjunto_id": origen.id}),
        (CosteoDensidad, {"conjunto_id": origen.id}),
        (CosteoZona, {"conjunto_id": origen.id}),
    ):
        hijos = (await db.execute(select(modelo).where(*[
            getattr(modelo, k) == v for k, v in filtro.items()
        ]))).scalars().all()
        for h in hijos:
            datos = {col.name: getattr(h, col.name) for col in h.__table__.columns
                     if col.name not in ("id", "conjunto_id", "creado_en", "creado_por",
                                         "actualizado_en", "actualizado_por")}
            datos["conjunto_id"] = clon.id
            db.add(modelo(**datos))

    politica = (
        await db.execute(select(CosteoPolitica).where(CosteoPolitica.conjunto_id == origen.id))
    ).scalars().one_or_none()
    if politica:
        db.add(CosteoPolitica(
            conjunto_id=clon.id,
            margen_objetivo=politica.margen_objetivo,
            margen_minimo=politica.margen_minimo,
            piso_visita=(politica.piso_visita * factor).quantize(Decimal("0.01")),
            vigencia_cotizacion_dias=politica.vigencia_cotizacion_dias,
            redondeo_multiplo=politica.redondeo_multiplo,
            redondeo_modo=politica.redondeo_modo,
        ))

    # Factores → opciones
    factores_origen = (
        await db.execute(select(CosteoFactor).where(CosteoFactor.conjunto_id == origen.id))
    ).scalars().all()
    for f in factores_origen:
        copia = (
            await db.execute(
                select(CosteoFactor).where(
                    CosteoFactor.conjunto_id == clon.id, CosteoFactor.codigo == f.codigo
                )
            )
        ).scalars().one_or_none()
        if copia is None:
            continue
        opciones = (
            await db.execute(
                select(CosteoFactorOpcion).where(CosteoFactorOpcion.factor_id == f.id)
            )
        ).scalars().all()
        for o in opciones:
            db.add(CosteoFactorOpcion(
                factor_id=copia.id, codigo=o.codigo, etiqueta=o.etiqueta,
                porcentaje=o.porcentaje, orden=o.orden,
            ))

    await _auditar(request, db, accion="costeo.conjunto.clonar",
                  entidad_id=str(clon.id),
                  detalle={"origen": str(origen.id), "reajuste_pct": str(body.reajuste_pct)})
    await db.commit()
    return {"id": str(clon.id), "nombre": clon.nombre, "version": clon.version}


# ─────────────────────────── Servicios ───────────────────────────────────────

class ServicioIn(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=40)
    nombre: str = Field(..., min_length=2, max_length=150)
    unidad: str = Field("punto", max_length=20)
    requiere_lote: bool = True
    activo: bool = True
    orden: int = 0


@router.post("/conjuntos/{conjunto_id}/servicios", status_code=201)
async def crear_servicio(
    conjunto_id: str, body: ServicioIn, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    await _exigir_editable(db, conjunto)
    servicio = CosteoServicio(conjunto_id=conjunto.id, **body.model_dump())
    db.add(servicio)
    await db.flush()
    await _auditar(request, db, accion="costeo.servicio.crear",
                  entidad_id=str(conjunto.id), detalle={"codigo": body.codigo})
    await db.commit()
    return {"id": str(servicio.id)}


@router.put("/servicios/{servicio_id}")
async def actualizar_servicio(
    servicio_id: str, body: ServicioIn, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    servicio = (
        await db.execute(select(CosteoServicio).where(CosteoServicio.id == _uuid(servicio_id)))
    ).scalars().one_or_none()
    if servicio is None:
        raise _err(404, "SERVICIO_NOT_FOUND", "El servicio no existe.")
    conjunto = await _conjunto_o_404(db, str(servicio.conjunto_id))
    await _exigir_editable(db, conjunto)
    for campo, valor in body.model_dump().items():
        setattr(servicio, campo, valor)
    await _auditar(request, db, accion="costeo.servicio.editar",
                  entidad_id=str(conjunto.id), detalle={"codigo": servicio.codigo})
    await db.commit()
    return {"ok": True}


@router.delete("/servicios/{servicio_id}")
async def eliminar_servicio(
    servicio_id: str, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    servicio = (
        await db.execute(select(CosteoServicio).where(CosteoServicio.id == _uuid(servicio_id)))
    ).scalars().one_or_none()
    if servicio is None:
        raise _err(404, "SERVICIO_NOT_FOUND", "El servicio no existe.")
    conjunto = await _conjunto_o_404(db, str(servicio.conjunto_id))
    await _exigir_editable(db, conjunto)
    await _auditar(request, db, accion="costeo.servicio.eliminar",
                  entidad_id=str(conjunto.id), detalle={"codigo": servicio.codigo})
    await db.execute(delete(CosteoServicio).where(CosteoServicio.id == servicio.id))
    await db.commit()
    return {"ok": True}


# ─────────────────────────── Componentes ─────────────────────────────────────

class ComponenteIn(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=40)
    nombre: str = Field(..., min_length=2, max_length=150)
    tipo: str = Field(..., pattern="^(fijo|escalonado|por_unidad|por_distancia|por_jornada|porcentual|condicional)$")
    orden: int = 0
    afectable_por_factores: bool = False
    config: dict = Field(default_factory=dict)


@router.post("/servicios/{servicio_id}/componentes", status_code=201)
async def crear_componente(
    servicio_id: str, body: ComponenteIn, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    servicio = (
        await db.execute(select(CosteoServicio).where(CosteoServicio.id == _uuid(servicio_id)))
    ).scalars().one_or_none()
    if servicio is None:
        raise _err(404, "SERVICIO_NOT_FOUND", "El servicio no existe.")
    conjunto = await _conjunto_o_404(db, str(servicio.conjunto_id))
    await _exigir_editable(db, conjunto)
    componente = CosteoComponente(servicio_id=servicio.id, **body.model_dump())
    db.add(componente)
    await db.flush()
    await _auditar(request, db, accion="costeo.componente.crear",
                  entidad_id=str(conjunto.id), detalle={"codigo": body.codigo})
    await db.commit()
    return {"id": str(componente.id)}


@router.put("/componentes/{componente_id}")
async def actualizar_componente(
    componente_id: str, body: ComponenteIn, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    componente = (
        await db.execute(
            select(CosteoComponente).where(CosteoComponente.id == _uuid(componente_id))
        )
    ).scalars().one_or_none()
    if componente is None:
        raise _err(404, "COMPONENTE_NOT_FOUND", "El componente no existe.")
    servicio = (
        await db.execute(select(CosteoServicio).where(CosteoServicio.id == componente.servicio_id))
    ).scalars().one()
    conjunto = await _conjunto_o_404(db, str(servicio.conjunto_id))
    await _exigir_editable(db, conjunto)
    for campo, valor in body.model_dump().items():
        setattr(componente, campo, valor)
    await _auditar(request, db, accion="costeo.componente.editar",
                  entidad_id=str(conjunto.id), detalle={"codigo": componente.codigo})
    await db.commit()
    return {"ok": True}


@router.delete("/componentes/{componente_id}")
async def eliminar_componente(
    componente_id: str, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    componente = (
        await db.execute(
            select(CosteoComponente).where(CosteoComponente.id == _uuid(componente_id))
        )
    ).scalars().one_or_none()
    if componente is None:
        raise _err(404, "COMPONENTE_NOT_FOUND", "El componente no existe.")
    servicio = (
        await db.execute(select(CosteoServicio).where(CosteoServicio.id == componente.servicio_id))
    ).scalars().one()
    conjunto = await _conjunto_o_404(db, str(servicio.conjunto_id))
    await _exigir_editable(db, conjunto)
    await _auditar(request, db, accion="costeo.componente.eliminar",
                  entidad_id=str(conjunto.id), detalle={"codigo": componente.codigo})
    await db.execute(delete(CosteoComponente).where(CosteoComponente.id == componente.id))
    await db.commit()
    return {"ok": True}


# ─────────────────────────── Tramos ──────────────────────────────────────────

class TramoIn(BaseModel):
    desde: Decimal = Field(..., ge=0)
    hasta: Decimal | None = Field(None)
    valor: Decimal = Field(..., gt=0)
    modo: str = Field("marginal", pattern="^(marginal|completo)$")


@router.post("/componentes/{componente_id}/tramos", status_code=201)
async def crear_tramo(
    componente_id: str, body: TramoIn, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    componente = (
        await db.execute(
            select(CosteoComponente).where(CosteoComponente.id == _uuid(componente_id))
        )
    ).scalars().one_or_none()
    if componente is None:
        raise _err(404, "COMPONENTE_NOT_FOUND", "El componente no existe.")
    servicio = (
        await db.execute(select(CosteoServicio).where(CosteoServicio.id == componente.servicio_id))
    ).scalars().one()
    conjunto = await _conjunto_o_404(db, str(servicio.conjunto_id))
    await _exigir_editable(db, conjunto)
    tramo = CosteoTramo(componente_id=componente.id, **body.model_dump())
    db.add(tramo)
    await db.flush()
    await _auditar(request, db, accion="costeo.tramo.crear",
                  entidad_id=str(conjunto.id), detalle={"desde": str(body.desde)})
    await db.commit()
    return {"id": str(tramo.id)}


@router.put("/tramos/{tramo_id}")
async def actualizar_tramo(
    tramo_id: str, body: TramoIn, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    tramo = (
        await db.execute(select(CosteoTramo).where(CosteoTramo.id == _uuid(tramo_id)))
    ).scalars().one_or_none()
    if tramo is None:
        raise _err(404, "TRAMO_NOT_FOUND", "El tramo no existe.")
    componente = (
        await db.execute(select(CosteoComponente).where(CosteoComponente.id == tramo.componente_id))
    ).scalars().one()
    servicio = (
        await db.execute(select(CosteoServicio).where(CosteoServicio.id == componente.servicio_id))
    ).scalars().one()
    conjunto = await _conjunto_o_404(db, str(servicio.conjunto_id))
    await _exigir_editable(db, conjunto)
    for campo, valor in body.model_dump().items():
        setattr(tramo, campo, valor)
    await _auditar(request, db, accion="costeo.tramo.editar",
                  entidad_id=str(conjunto.id), detalle={"tramo_id": tramo_id})
    await db.commit()
    return {"ok": True}


@router.delete("/tramos/{tramo_id}")
async def eliminar_tramo(
    tramo_id: str, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    tramo = (
        await db.execute(select(CosteoTramo).where(CosteoTramo.id == _uuid(tramo_id)))
    ).scalars().one_or_none()
    if tramo is None:
        raise _err(404, "TRAMO_NOT_FOUND", "El tramo no existe.")
    componente = (
        await db.execute(select(CosteoComponente).where(CosteoComponente.id == tramo.componente_id))
    ).scalars().one()
    servicio = (
        await db.execute(select(CosteoServicio).where(CosteoServicio.id == componente.servicio_id))
    ).scalars().one()
    conjunto = await _conjunto_o_404(db, str(servicio.conjunto_id))
    await _exigir_editable(db, conjunto)
    await _auditar(request, db, accion="costeo.tramo.eliminar",
                  entidad_id=str(conjunto.id), detalle={"tramo_id": tramo_id})
    await db.execute(delete(CosteoTramo).where(CosteoTramo.id == tramo.id))
    await db.commit()
    return {"ok": True}


# ─────────────────────────── Factores y opciones ─────────────────────────────

class FactorIn(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=40)
    nombre: str = Field(..., min_length=2, max_length=150)
    aplicacion: str = Field("porcentual", pattern="^(porcentual|multiplicativo)$")
    combinacion: str = Field("suma", pattern="^(suma|multiplica)$")


class OpcionIn(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=40)
    etiqueta: str = Field(..., min_length=1, max_length=150)
    porcentaje: Decimal = Field(..., ge=-100, le=1000)
    orden: int = 0


@router.post("/conjuntos/{conjunto_id}/factores", status_code=201)
async def crear_factor(
    conjunto_id: str, body: FactorIn, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    await _exigir_editable(db, conjunto)
    factor = CosteoFactor(conjunto_id=conjunto.id, **body.model_dump())
    db.add(factor)
    await db.flush()
    await _auditar(request, db, accion="costeo.factor.crear",
                  entidad_id=str(conjunto.id), detalle={"codigo": body.codigo})
    await db.commit()
    return {"id": str(factor.id)}


@router.post("/factores/{factor_id}/opciones", status_code=201)
async def crear_opcion(
    factor_id: str, body: OpcionIn, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    factor = (
        await db.execute(select(CosteoFactor).where(CosteoFactor.id == _uuid(factor_id)))
    ).scalars().one_or_none()
    if factor is None:
        raise _err(404, "FACTOR_NOT_FOUND", "El factor no existe.")
    conjunto = await _conjunto_o_404(db, str(factor.conjunto_id))
    await _exigir_editable(db, conjunto)
    opcion = CosteoFactorOpcion(factor_id=factor.id, **body.model_dump())
    db.add(opcion)
    await db.flush()
    await _auditar(request, db, accion="costeo.factor.opcion.crear",
                  entidad_id=str(conjunto.id), detalle={"codigo": body.codigo})
    await db.commit()
    return {"id": str(opcion.id)}


@router.put("/factor-opciones/{opcion_id}")
async def actualizar_opcion(
    opcion_id: str, body: OpcionIn, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    opcion = (
        await db.execute(
            select(CosteoFactorOpcion).where(CosteoFactorOpcion.id == _uuid(opcion_id))
        )
    ).scalars().one_or_none()
    if opcion is None:
        raise _err(404, "OPCION_NOT_FOUND", "La opción no existe.")
    factor = (
        await db.execute(select(CosteoFactor).where(CosteoFactor.id == opcion.factor_id))
    ).scalars().one()
    conjunto = await _conjunto_o_404(db, str(factor.conjunto_id))
    await _exigir_editable(db, conjunto)
    for campo, valor in body.model_dump().items():
        setattr(opcion, campo, valor)
    await _auditar(request, db, accion="costeo.factor.opcion.editar",
                  entidad_id=str(conjunto.id), detalle={"codigo": opcion.codigo})
    await db.commit()
    return {"ok": True}


@router.delete("/factor-opciones/{opcion_id}")
async def eliminar_opcion(
    opcion_id: str, request: Request, db: AsyncSession = Depends(get_db),
):
    contexto_usuario(request, ROLES_ADMIN)
    opcion = (
        await db.execute(
            select(CosteoFactorOpcion).where(CosteoFactorOpcion.id == _uuid(opcion_id))
        )
    ).scalars().one_or_none()
    if opcion is None:
        raise _err(404, "OPCION_NOT_FOUND", "La opción no existe.")
    factor = (
        await db.execute(select(CosteoFactor).where(CosteoFactor.id == opcion.factor_id))
    ).scalars().one()
    conjunto = await _conjunto_o_404(db, str(factor.conjunto_id))
    await _exigir_editable(db, conjunto)
    await _auditar(request, db, accion="costeo.factor.opcion.eliminar",
                  entidad_id=str(conjunto.id), detalle={"codigo": opcion.codigo})
    await db.execute(delete(CosteoFactorOpcion).where(CosteoFactorOpcion.id == opcion.id))
    await db.commit()
    return {"ok": True}


# ─────────────────────────── Densidad, zonas, impuestos, política, descuentos ─

class DensidadIn(BaseModel):
    area_min: Decimal = Field(..., ge=0)
    area_max: Decimal | None = None
    puntos_min: int = Field(0, ge=0)
    puntos_max: int = Field(0, ge=0)
    puntos_por_ha: Decimal | None = Field(None, ge=0)
    cultivo_id: str | None = None


class ZonaIn(BaseModel):
    departamento: str = Field(..., min_length=2, max_length=60)
    municipio: str | None = Field(None, max_length=80)
    factor: Decimal = Field(0, ge=-100, le=1000)
    km_incluidos: Decimal = Field(0, ge=0)
    tarifa_km: Decimal = Field(0, ge=0)
    peajes_estimados: Decimal = Field(0, ge=0)


class ImpuestoIn(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=40)
    nombre: str = Field(..., min_length=2, max_length=150)
    porcentaje: Decimal = Field(..., ge=0, le=100)
    base: str = Field("subtotal", pattern="^(directo|ajustado|lista)$")
    informativo: bool = False


class PoliticaIn(BaseModel):
    margen_objetivo: Decimal = Field(..., ge=0, le=1000)
    margen_minimo: Decimal = Field(0, ge=0, le=1000)
    piso_visita: Decimal = Field(0, ge=0)
    vigencia_cotizacion_dias: int = Field(30, ge=1, le=3650)
    redondeo_multiplo: Decimal = Field(Decimal("1"), gt=0)
    redondeo_modo: str = Field("ninguno", pattern="^(ninguno|mitad_superior|techo|piso)$")


class DescuentoIn(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=40)
    criterio: str = Field("manual", max_length=40)
    umbral: Decimal = Field(0, ge=0)
    porcentaje: Decimal = Field(..., ge=0, le=100)
    tope_rol: dict = Field(default_factory=dict)


async def _hijos_simples(modelo_clase, conjunto_id: str, request: Request, db, body, accion: str):
    """Crea un hijo directo de conjunto y audita."""
    usuario = contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    await _exigir_editable(db, conjunto)
    hijo = modelo_clase(conjunto_id=conjunto.id, **body.model_dump())
    db.add(hijo)
    await db.flush()
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion=accion,
        entidad="costeo",
        entidad_id=str(conjunto.id),
        detalle=_json_detalle(body.model_dump()),
    )
    return hijo


@router.post("/conjuntos/{conjunto_id}/densidad", status_code=201)
async def crear_densidad(conjunto_id: str, body: DensidadIn, request: Request,
                         db: AsyncSession = Depends(get_db)):
    hijo = await _hijos_simples(CosteoDensidad, conjunto_id, request, db, body, "costeo.densidad.crear")
    await db.commit()
    return {"id": str(hijo.id)}


@router.post("/conjuntos/{conjunto_id}/zonas", status_code=201)
async def crear_zona(conjunto_id: str, body: ZonaIn, request: Request,
                     db: AsyncSession = Depends(get_db)):
    hijo = await _hijos_simples(CosteoZona, conjunto_id, request, db, body, "costeo.zona.crear")
    await db.commit()
    return {"id": str(hijo.id)}


@router.post("/conjuntos/{conjunto_id}/impuestos", status_code=201)
async def crear_impuesto(conjunto_id: str, body: ImpuestoIn, request: Request,
                         db: AsyncSession = Depends(get_db)):
    hijo = await _hijos_simples(CosteoImpuesto, conjunto_id, request, db, body, "costeo.impuesto.crear")
    await db.commit()
    return {"id": str(hijo.id)}


@router.post("/conjuntos/{conjunto_id}/descuentos", status_code=201)
async def crear_descuento(conjunto_id: str, body: DescuentoIn, request: Request,
                          db: AsyncSession = Depends(get_db)):
    hijo = await _hijos_simples(CosteoDescuento, conjunto_id, request, db, body, "costeo.descuento.crear")
    await db.commit()
    return {"id": str(hijo.id)}


@router.put("/conjuntos/{conjunto_id}/politica")
async def actualizar_politica(conjunto_id: str, body: PoliticaIn, request: Request,
                              db: AsyncSession = Depends(get_db)):
    contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    await _exigir_editable(db, conjunto)
    politica = (
        await db.execute(select(CosteoPolitica).where(CosteoPolitica.conjunto_id == conjunto.id))
    ).scalars().one_or_none()
    if politica is None:
        politica = CosteoPolitica(conjunto_id=conjunto.id, **body.model_dump())
        db.add(politica)
    else:
        for campo, valor in body.model_dump().items():
            setattr(politica, campo, valor)
    await db.flush()
    await _auditar(request, db, accion="costeo.politica.editar",
                  entidad_id=str(conjunto.id), detalle=body.model_dump())
    await db.commit()
    return {"ok": True}


@router.delete("/densidad/{item_id}")
async def eliminar_densidad(item_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _eliminar_hijo(CosteoDensidad, item_id, request, db, "densidad")


@router.delete("/zonas/{item_id}")
async def eliminar_zona(item_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _eliminar_hijo(CosteoZona, item_id, request, db, "zona")


@router.delete("/impuestos/{item_id}")
async def eliminar_impuesto(item_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _eliminar_hijo(CosteoImpuesto, item_id, request, db, "impuesto")


@router.delete("/descuentos/{item_id}")
async def eliminar_descuento(item_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _eliminar_hijo(CosteoDescuento, item_id, request, db, "descuento")


async def _eliminar_hijo(modelo_clase, item_id: str, request: Request, db, etiqueta: str):
    contexto_usuario(request, ROLES_ADMIN)
    item = (
        await db.execute(select(modelo_clase).where(modelo_clase.id == _uuid(item_id)))
    ).scalars().one_or_none()
    if item is None:
        raise _err(404, f"{etiqueta.upper()}_NOT_FOUND", f"El elemento de {etiqueta} no existe.")
    conjunto = await _conjunto_o_404(db, str(item.conjunto_id))
    await _exigir_editable(db, conjunto)
    await _auditar(request, db, accion=f"costeo.{etiqueta}.eliminar",
                  entidad_id=str(conjunto.id), detalle={"item_id": item_id})
    await db.execute(delete(modelo_clase).where(modelo_clase.id == item.id))
    await db.commit()
    return {"ok": True}


# ─────────────────────────── Import / Export (F7 RF-23) ──────────────────────

@router.get("/conjuntos/{conjunto_id}/exportar")
async def exportar_conjunto(conjunto_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Exporta el conjunto completo en JSON (RF-23)."""
    contexto_usuario(request, ROLES_ADMIN)
    conjunto = await _conjunto_o_404(db, conjunto_id)
    from agroia_backend.api.costeo import _conjunto_a_dict
    return {"formato": "agroia-costeo-1.0", "conjunto": await _conjunto_a_dict(db, conjunto)}


@router.post("/importar", status_code=201)
async def importar_conjunto(request: Request, db: AsyncSession = Depends(get_db)):
    """Importa un conjunto JSON exportado y lo valida antes de guardar (RF-23)."""
    contexto_usuario(request, ROLES_ADMIN)
    import json

    raw = await request.body()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:  # noqa: BLE001
        raise _err(422, "IMPORT_JSON_INVALIDO", "El archivo no es un JSON válido.")
    conjunto_dict = payload.get("conjunto")
    if not isinstance(conjunto_dict, dict):
        raise _err(422, "IMPORT_FORMATO_INVALIDO",
                   "El JSON debe tener la estructura {\"conjunto\": {...}} del exportador.")

    resultado = validar_conjunto(conjunto_dict)
    if not resultado["valido"]:
        raise _err(
            422,
            "IMPORT_VALIDACION_FALLIDA",
            "El conjunto importado no pasó la validación: "
            + "; ".join(e["mensaje"] for e in resultado["errores"][:5]),
        )

    ultima = (
        await db.execute(select(CosteoConjunto).order_by(CosteoConjunto.version.desc()).limit(1))
    ).scalars().one_or_none()
    vigencia_desde = conjunto_dict.get("vigencia_desde")
    vigencia_hasta = conjunto_dict.get("vigencia_hasta")
    if isinstance(vigencia_desde, str):
        vigencia_desde = date.fromisoformat(vigencia_desde)
    if isinstance(vigencia_hasta, str):
        vigencia_hasta = date.fromisoformat(vigencia_hasta)
    nuevo = CosteoConjunto(
        nombre=conjunto_dict.get("nombre") or "Conjunto importado",
        version=(ultima.version + 1) if ultima else 1,
        estado="borrador",
        moneda=conjunto_dict.get("moneda") or "COP",
        notas="Importado desde JSON (RF-23).",
        vigencia_desde=vigencia_desde,
        vigencia_hasta=vigencia_hasta,
    )
    db.add(nuevo)
    await db.flush()

    politica = conjunto_dict.get("politica")
    if politica:
        db.add(CosteoPolitica(conjunto_id=nuevo.id, **{k: v for k, v in politica.items() if k != "id"}))
    for i in conjunto_dict.get("impuestos") or []:
        db.add(CosteoImpuesto(conjunto_id=nuevo.id, **{k: v for k, v in i.items() if k != "id"}))
    for d in conjunto_dict.get("descuentos") or []:
        db.add(CosteoDescuento(conjunto_id=nuevo.id, **{k: v for k, v in d.items() if k != "id"}))
    for dens in conjunto_dict.get("densidad") or []:
        db.add(CosteoDensidad(conjunto_id=nuevo.id, **{k: v for k, v in dens.items() if k != "id"}))
    for z in conjunto_dict.get("zonas") or []:
        db.add(CosteoZona(conjunto_id=nuevo.id, **{k: v for k, v in z.items() if k != "id"}))
    for f in conjunto_dict.get("factores") or []:
        factor = CosteoFactor(
            conjunto_id=nuevo.id,
            codigo=f["codigo"], nombre=f["nombre"],
            aplicacion=f.get("aplicacion") or "porcentual",
            combinacion=f.get("combinacion") or "suma",
        )
        db.add(factor)
        await db.flush()
        for o in f.get("opciones") or []:
            db.add(CosteoFactorOpcion(factor_id=factor.id, **{k: v for k, v in o.items() if k != "id"}))
    for s in conjunto_dict.get("servicios") or []:
        servicio = CosteoServicio(
            conjunto_id=nuevo.id,
            codigo=s["codigo"], nombre=s["nombre"], unidad=s.get("unidad") or "punto",
            requiere_lote=s.get("requiere_lote", True), activo=s.get("activo", True),
            orden=s.get("orden") or 0,
        )
        db.add(servicio)
        await db.flush()
        for c in s.get("componentes") or []:
            componente = CosteoComponente(
                servicio_id=servicio.id,
                codigo=c["codigo"], nombre=c["nombre"], tipo=c["tipo"],
                orden=c.get("orden") or 0,
                afectable_por_factores=c.get("afectable_por_factores", False),
                config=c.get("config") or {},
            )
            db.add(componente)
            await db.flush()
            for t in c.get("tramos") or []:
                db.add(CosteoTramo(componente_id=componente.id, **t))

    await _auditar(request, db, accion="costeo.conjunto.importar",
                  entidad_id=str(nuevo.id), detalle={"nombre": nuevo.nombre})
    await db.commit()
    return {"id": str(nuevo.id), "version": nuevo.version, "estado": "borrador"}
