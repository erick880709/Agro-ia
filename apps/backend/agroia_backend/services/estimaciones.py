"""Servicio de dominio AGC-COST — estimaciones (F3) y conversión (F6).

Ciclo de vida: borrador → emitida → aceptada/rechazada/vencida.
Al emitir se congela el snapshot de parámetros con hash SHA-256 para
reproducibilidad dígito a dígito (RF-17 / CA-07).
"""

import hashlib
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.comision import Comision, ComisionMiembro
from agroia_backend.models.costeo import CosteoConjunto
from agroia_backend.models.estimaciones import (
    Estimacion,
    EstimacionEvento,
    EstimacionLinea,
    EstimacionSnapshot,
)
from agroia_backend.models.equipo_trabajo import EquipoTrabajo
from agroia_backend.models.finca import Finca
from agroia_backend.services.costeo_motor import CosteoError, calcular

_ESTADOS = {"borrador", "emitida", "aceptada", "rechazada", "vencida"}


class EstimacionError(Exception):
    """Error de negocio del flujo de estimaciones."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _dec(v) -> Decimal:
    if v is None:
        return Decimal("0")
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _hash_snapshot(parametros: dict) -> str:
    """Hash SHA-256 del snapshot canónico (Decimal→str, claves ordenadas)."""
    canonico = json.dumps(
        parametros, sort_keys=True, ensure_ascii=False,
        default=lambda o: str(o) if isinstance(o, Decimal) else o,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


async def _conjunto_para_estimacion(
    db: AsyncSession, conjunto: CosteoConjunto, serializador
) -> dict:
    """Snapshot dict del conjunto (reutiliza el serializador de la API)."""
    return await serializador(db, conjunto)


def _contexto_lote(
    lote: dict,
    fecha_ref: date,
    rol: str,
    zona: dict | None,
    factores: dict,
) -> tuple[dict, dict]:
    """Construye contexto y selección del motor para un lote."""
    puntos = int(lote.get("puntos") or 0)
    contexto = {
        "fecha_referencia": fecha_ref,
        "area_ha": _dec(lote.get("area_ha") or 0),
        "puntos": puntos,
        "km": _dec(lote.get("km") or 0),
        "rol": rol,
        "departamento": lote.get("departamento"),
        "municipio": lote.get("municipio"),
        "zona": zona or {},
    }
    seleccion = {
        "servicios": [
            {"codigo": s.get("codigo"), "cantidad": _dec(s.get("cantidad") or 0)}
            for s in lote.get("servicios") or []
        ],
        "factores": factores or {},
        "descuento_pct": lote.get("descuento_pct"),
    }
    return contexto, seleccion


def _consolidar(resultados: list[dict], lineas_por_lote: list[list[dict]]) -> dict:
    """Consolida múltiples resultados del motor en uno solo (multi-lote)."""
    if not resultados:
        raise EstimacionError("SIN_LOTES", "La estimación no tiene lotes ni servicios.")
    claves = (
        "subtotal_directo", "subtotal_ajustado", "precio_lista",
        "descuento_aplicado", "total_final",
    )
    totales = {k: sum((_dec(r.get(k)) for r in resultados), Decimal("0")) for k in claves}
    ajuste_redondeo = sum((_dec(r.get("ajuste_redondeo")) for r in resultados), Decimal("0"))
    indicadores_consolidados = {
        "costo_directo": totales["subtotal_directo"],
        "costo_por_ha": (
            (totales["total_final"] / _dec(resultados[0].get("area_total_ha") or 1))
            if len(resultados) == 1 else None
        ),
    }
    return {
        **totales,
        "ajuste_redondeo": ajuste_redondeo,
        "lineas": [ln for grupo in lineas_por_lote for ln in grupo],
        "factores_aplicados": resultados[0].get("factores_aplicados", []),
        "impuestos_informativos": resultados[0].get("impuestos_informativos", []),
        "impuestos_incluidos": resultados[0].get("impuestos_incluidos", []),
        "advertencias": [a for r in resultados for a in r.get("advertencias", [])],
        "indicadores": {
            **resultados[0].get("indicadores", {}),
            **indicadores_consolidados,
        },
    }


async def _guardar_lineas(db: AsyncSession, estimacion_id, consolidado, lotes_map) -> None:
    """Reemplaza las líneas de la estimación con el desglose consolidado."""
    await db.execute(delete(EstimacionLinea).where(EstimacionLinea.estimacion_id == estimacion_id))
    for i, ln in enumerate(consolidado.get("lineas") or []):
        db.add(EstimacionLinea(
            estimacion_id=estimacion_id,
            lote_id=lotes_map.get(i),
            servicio_id=None,
            componente_codigo=ln.get("componente_codigo"),
            descripcion=(
                f"{ln.get('servicio_nombre') or ln.get('servicio_codigo')} — "
                f"{ln.get('descripcion') or ln.get('componente_nombre')}"
            )[:250],
            cantidad=_dec(ln.get("cantidad")),
            unidad=ln.get("unidad"),
            valor_unitario=_dec(ln.get("valor_unitario")),
            valor=_dec(ln.get("valor")),
            parametro_ref=ln.get("parametro_ref"),
        ))
    await db.flush()


async def _registrar_evento(db: AsyncSession, estimacion_id, evento, usuario_id, comentario=None) -> None:
    db.add(EstimacionEvento(
        estimacion_id=estimacion_id,
        evento=evento,
        usuario_id=usuario_id,
        comentario=comentario,
    ))
    await db.flush()


async def _marcar_vencidas(db: AsyncSession) -> None:
    """Pasa a vencidas las estimaciones emitidas cuya vigencia expiró."""
    hoy = date.today()
    vencidas = (
        await db.execute(
            select(Estimacion).where(
                Estimacion.estado == "emitida",
                Estimacion.vence_en.is_not(None),
                Estimacion.vence_en < hoy,
            )
        )
    ).scalars().all()
    for e in vencidas:
        e.estado = "vencida"
        await _registrar_evento(db, e.id, "vencida", None, "Vencimiento automático de la vigencia.")


async def recalcular(
    db: AsyncSession,
    estimacion: Estimacion,
    *,
    rol: str,
    lotes: list[dict],
    factores: dict,
    descuento_pct: Decimal | None,
    serializador,
) -> dict:
    """Recalcula líneas y totales de una estimación en borrador."""
    conjunto = (
        await db.execute(select(CosteoConjunto).where(CosteoConjunto.id == estimacion.conjunto_id))
    ).scalars().one_or_none()
    if conjunto is None:
        raise EstimacionError("CONJUNTO_NOT_FOUND", "El conjunto de la estimación no existe.")
    conjunto_dict = await serializador(db, conjunto)
    return await recalcular_con_dict(
        db, estimacion, conjunto_dict, rol=rol, lotes=lotes,
        factores=factores, descuento_pct=descuento_pct,
    )


async def recalcular_con_dict(
    db: AsyncSession,
    estimacion: Estimacion,
    conjunto_dict: dict,
    *,
    rol: str,
    lotes: list[dict],
    factores: dict,
    descuento_pct: Decimal | None,
) -> dict:
    """Recalcula usando un conjunto ya resuelto y persiste líneas/totales."""
    consolidado, lotes_map = _motor_para_lotes(
        conjunto_dict,
        fecha_ref=estimacion.fecha_referencia,
        rol=rol,
        lotes=lotes,
        factores=factores,
        descuento_pct=descuento_pct,
    )
    area_total = sum((_dec(lot.get("area_ha") or 0) for lot in lotes), Decimal("0"))
    consolidado["indicadores"]["costo_por_ha"] = (
        consolidado["total_final"] / area_total
    ).quantize(Decimal("1"), rounding="ROUND_HALF_UP") if area_total > 0 else None
    puntos_totales = sum(int(lot.get("puntos") or 0) for lot in lotes)
    if puntos_totales:
        consolidado["indicadores"]["costo_por_punto"] = (
            consolidado["total_final"] / Decimal(str(puntos_totales))
        ).quantize(Decimal("1"), rounding="ROUND_HALF_UP")

    estimacion.area_total_ha = area_total
    estimacion.total_directo = consolidado["subtotal_directo"]
    estimacion.total_ajustado = consolidado["subtotal_ajustado"]
    estimacion.precio_lista = consolidado["precio_lista"]
    estimacion.descuento_aplicado = consolidado["descuento_aplicado"]
    estimacion.total_final = consolidado["total_final"]
    margen_pct = (consolidado["precio_lista"] - consolidado["total_final"]) / consolidado["precio_lista"] * 100 \
        if consolidado["precio_lista"] else Decimal("0")
    estimacion.margen_pct = margen_pct.quantize(Decimal("0.0001"))
    await db.flush()
    await _guardar_lineas(db, estimacion.id, consolidado, lotes_map)
    return consolidado


def _motor_para_lotes(
    conjunto_dict: dict,
    *,
    fecha_ref,
    rol: str,
    lotes: list[dict],
    factores: dict,
    descuento_pct: Decimal | None,
) -> tuple[dict, dict]:
    """Ejecuta el motor por lote y consolida sin tocar la base de datos."""
    zona = None
    for lote in lotes:
        zona = next(
            (z for z in conjunto_dict.get("zonas", [])
             if z.get("departamento") == lote.get("departamento")
             and (z.get("municipio") == lote.get("municipio") or z.get("municipio") is None)),
            zona,
        )

    resultados = []
    grupos_lineas = []
    lotes_map: dict[int, uuid.UUID | None] = {}
    idx_linea = 0
    for lote in lotes:
        lote_id = lote.get("lote_id")
        try:
            lote_uuid = uuid.UUID(str(lote_id)) if lote_id else None
        except ValueError:
            lote_uuid = None
        # El descuento es de la estimación completa; si el lote no lo trae
        # explícito, se propaga (multi-lote consolidado).
        lote_con_descuento = dict(lote)
        if "descuento_pct" not in lote_con_descuento or lote_con_descuento.get("descuento_pct") is None:
            lote_con_descuento["descuento_pct"] = descuento_pct
        contexto, seleccion = _contexto_lote(lote_con_descuento, fecha_ref, rol, zona, factores)
        try:
            res = calcular(contexto, conjunto_dict, seleccion)
        except CosteoError as e:
            raise EstimacionError(e.code, e.message)
        res["area_total_ha"] = _dec(lote.get("area_ha") or 0)
        resultados.append(res)
        for _ in res.get("lineas") or []:
            lotes_map[idx_linea] = lote_uuid
            idx_linea += 1
        grupos_lineas.append(res.get("lineas") or [])

    consolidado = _consolidar(resultados, grupos_lineas)
    return consolidado, lotes_map


async def emitir(
    db: AsyncSession,
    estimacion: Estimacion,
    *,
    usuario_id,
    rol: str,
    autorizar_bajo_piso: bool,
    motivo_excepcion: str | None,
    serializador,
) -> Estimacion:
    """Emite la estimación: congela snapshot, valida piso y asigna consecutivo."""
    if estimacion.estado != "borrador":
        raise EstimacionError(
            "ESTIMACION_NO_EDITABLE", "Solo una estimación en borrador puede emitirse."
        )
    conjunto = (
        await db.execute(select(CosteoConjunto).where(CosteoConjunto.id == estimacion.conjunto_id))
    ).scalars().one_or_none()
    if conjunto is None:
        raise EstimacionError("CONJUNTO_NOT_FOUND", "El conjunto de la estimación no existe.")
    conjunto_dict = await serializador(db, conjunto)

    politica = conjunto_dict.get("politica") or {}
    piso = _dec(politica.get("piso_visita") or 0)
    rol_norm = (rol or "").lower()
    if estimacion.total_final < piso:
        if not (rol_norm in ("admin", "administrador") and autorizar_bajo_piso and motivo_excepcion):
            raise EstimacionError(
                "BAJO_PISO_RENTABILIDAD",
                f"El total (${estimacion.total_final:,.0f}) está por debajo del piso de "
                f"rentabilidad (${piso:,.0f}). Solo un administrador puede autorizar con justificación.",
            )
        estimacion.motivo_excepcion = motivo_excepcion

    snapshot = {"conjunto": conjunto_dict, "seleccion": estimacion.seleccion}
    estimacion.emitido_por = usuario_id
    estimacion.emitido_en = datetime.now(timezone.utc)
    estimacion.estado = "emitida"
    estimacion.vence_en = date.today() + timedelta(
        days=int(politica.get("vigencia_cotizacion_dias") or 30)
    )
    estimacion.consecutivo = await _siguiente_consecutivo(db)
    await db.flush()

    hash_snapshot = _hash_snapshot(snapshot)
    anterior = (
        await db.execute(
            select(EstimacionSnapshot).where(EstimacionSnapshot.estimacion_id == estimacion.id)
        )
    ).scalars().one_or_none()
    if anterior is None:
        db.add(EstimacionSnapshot(
            estimacion_id=estimacion.id,
            parametros=snapshot,
            hash_sha256=hash_snapshot,
        ))
    else:
        anterior.parametros = snapshot
        anterior.hash_sha256 = hash_snapshot
    await _registrar_evento(
        db, estimacion.id, "emitida", usuario_id,
        f"Snapshot {hash_snapshot[:12]}… · conjunto {conjunto.nombre} v{conjunto.version}",
    )
    await db.flush()
    return estimacion


async def recalcular_desde_snapshot(
    db: AsyncSession,
    estimacion: Estimacion,
    *,
    rol: str,
) -> Decimal:
    """Recalcula el total usando el snapshot congelado y devuelve el total (CA-07)."""
    snapshot = (
        await db.execute(
            select(EstimacionSnapshot).where(EstimacionSnapshot.estimacion_id == estimacion.id)
        )
    ).scalars().one_or_none()
    if snapshot is None:
        raise EstimacionError(
            "SNAPSHOT_AUSENTE",
            "La estimación no tiene snapshot (solo se congela al emitir).",
        )
    if _hash_snapshot(snapshot.parametros) != snapshot.hash_sha256:
        raise EstimacionError(
            "SNAPSHOT_INCONSISTENTE",
            "El hash del snapshot no coincide: los parámetros fueron alterados.",
        )
    conjunto_dict = snapshot.parametros.get("conjunto") or {}
    seleccion = snapshot.parametros.get("seleccion") or {}
    lotes = seleccion.get("lotes") or []
    factores = seleccion.get("factores") or {}
    descuento_pct = _dec(seleccion.get("descuento_pct")) or None

    consolidado, _ = _motor_para_lotes(
        conjunto_dict,
        fecha_ref=estimacion.fecha_referencia,
        rol=rol,
        lotes=lotes,
        factores=factores,
        descuento_pct=descuento_pct,
    )
    return consolidado["total_final"]


async def _siguiente_consecutivo(db: AsyncSession) -> str:
    """COT-{año}-{5 dígitos} único (contador por año)."""
    anio = date.today().year
    prefijo = f"COT-{anio}-"
    ultimo = (
        await db.execute(
            select(func.max(Estimacion.consecutivo)).where(
                Estimacion.consecutivo.like(f"{prefijo}%")
            )
        )
    ).scalar_one_or_none()
    secuencia = int(str(ultimo).split("-")[-1]) + 1 if ultimo else 1
    return f"{prefijo}{secuencia:05d}"


async def convertir_a_comision(
    db: AsyncSession,
    estimacion: Estimacion,
    *,
    usuario_id,
    usuario_email: str,
    usuario_nombre: str | None,
    rol: str | None,
    auditor,
) -> Comision:
    """Convierte una estimación aceptada en comisión (RF-20 / F6)."""
    if estimacion.estado != "aceptada":
        raise EstimacionError(
            "ESTIMACION_NO_ACEPTADA",
            "Solo una estimación aceptada puede convertirse en comisión.",
        )
    finca = (
        await db.execute(select(Finca).where(Finca.id == estimacion.finca_id))
    ).scalars().one_or_none()
    if finca is None:
        raise EstimacionError("FINCA_NOT_FOUND", "La finca de la estimación no existe.")

    existente = (
        await db.execute(
            select(Comision).where(
                Comision.origen_estimacion_id == estimacion.id,
                Comision.estado != "cancelada",
            )
        )
    ).scalars().first()
    if existente is not None:
        raise EstimacionError(
            "COMISION_YA_CREADA",
            "La estimación ya tiene una comisión asociada.",
        )

    comision = Comision(
        finca_id=estimacion.finca_id,
        servicio="Toma de muestras de suelo",
        fecha_asignacion=date.today(),
        estado="asignada",
        valor_comision_cop=estimacion.total_final,
        valor_cobro_servicio_cop=estimacion.total_final,
        observaciones=(
            f"Generada desde la estimación {estimacion.consecutivo or estimacion.id} "
            f"(AGC-COST). Valor de referencia: ${estimacion.total_final:,.0f} COP."
        ),
        origen_estimacion_id=estimacion.id,
    )
    db.add(comision)
    await db.flush()

    equipo = (
        await db.execute(
            select(EquipoTrabajo).where(
                EquipoTrabajo.estado == "activo"
            ).order_by(EquipoTrabajo.rol, EquipoTrabajo.apellidos)
        )
    ).scalars().all()
    for miembro in equipo:
        db.add(ComisionMiembro(
            comision_id=comision.id,
            empleado_id=miembro.id,
            rol_en_comision=miembro.rol,
            activo=True,
        ))

    await _registrar_evento(
        db, estimacion.id, "convertida_comision", usuario_id,
        f"Comisión {comision.id} creada desde la estimación.",
    )
    if auditor is not None:
        await auditor(
            db,
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            rol=rol,
            accion="estimacion.convertir_comision",
            entidad="estimacion",
            entidad_id=str(estimacion.id),
            detalle={"comision_id": str(comision.id), "consecutivo": estimacion.consecutivo},
        )
    await db.flush()
    return comision
