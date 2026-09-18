"""Motor de cálculo AGC-COST — puro, determinista y sin estado (RFP AgroIA v4 §8).

La capa de cálculo **no conoce ningún valor de negocio**: solo interpreta el
conjunto de parámetros que recibe (componentes ordenados con tipo conocido,
factores, política e impuestos) y un contexto de lote. Toda la aritmética
monetaria usa `Decimal` (NUMERIC(18,4) en base); nunca coma flotante. El
redondeo ocurre una sola vez, en el paso 8, con modo y múltiplo parametrizados.

Orden de resolución (no negociable):
  1. Conjunto publicado y vigente en `fecha_referencia`.
  2. Contexto (área, puntos, km, dificultad, zona, cliente).
  3. Componentes en su orden → subtotal directo.
  4. Factores sobre líneas afectables → subtotal ajustado.
  5. Margen objetivo → precio de lista.
  6. Descuentos (con tope por rol).
  7. Piso de rentabilidad y margen mínimo → advertencias.
  8. Redondeo único.
  9. Impuestos y retenciones (informativos o incluidos).
  10. Indicadores derivados y traza completa.
"""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from typing import Any

# ──────────────────────────────────────────────────────────────
# Errores de negocio
# ──────────────────────────────────────────────────────────────


class CosteoError(Exception):
    """Error de negocio del motor con código estable (contrato RFP §10)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# ──────────────────────────────────────────────────────────────
# Utilidades decimales
# ──────────────────────────────────────────────────────────────

_CUATRO = Decimal("0.0001")
_CERO = Decimal("0")


def _dec(valor: Any, default: Decimal | None = None) -> Decimal | None:
    """Convierte a Decimal vía cadena (nunca vía flotante binario)."""
    if valor is None or valor == "":
        return default
    if isinstance(valor, Decimal):
        return valor
    try:
        return Decimal(str(valor))
    except Exception:  # noqa: BLE001 — degradación controlada del llamador
        return default


def _moneda(valor: Decimal | None) -> Decimal:
    return (_dec(valor) or _CERO).quantize(_CUATRO, rounding=ROUND_HALF_UP)


def _pct_a_factor(pct: Decimal | None) -> Decimal:
    """Porcentaje → factor multiplicativo (15% → 1.15)."""
    return Decimal("1") + (_dec(pct) or _CERO) / Decimal("100")


def _condicion_se_cumple(contexto: dict, cond: dict) -> bool:
    """Evalúa una condición declarativa sobre el contexto (sin eval())."""
    campo = str(cond.get("campo") or "")
    op = str(cond.get("op") or "eq").lower()
    esperado = cond.get("valor")
    actual = contexto.get(campo)
    if op in ("eq", "="):
        return str(actual) == str(esperado)
    if op == "ne":
        return str(actual) != str(esperado)
    if op in ("gt", ">"):
        return _dec(actual, _CERO) > _dec(esperado, _CERO)
    if op in ("gte", ">="):
        return _dec(actual, _CERO) >= _dec(esperado, _CERO)
    if op in ("lt", "<"):
        return _dec(actual, _CERO) < _dec(esperado, _CERO)
    if op in ("lte", "<="):
        return _dec(actual, _CERO) <= _dec(esperado, _CERO)
    if op == "in":
        opciones = esperado if isinstance(esperado, list) else str(esperado).split(",")
        return str(actual) in {str(o) for o in opciones}
    raise CosteoError("CONDICION_INVALIDA", f"Operador desconocido en componente condicional: {op}")


# ──────────────────────────────────────────────────────────────
# Tramos escalonados
# ──────────────────────────────────────────────────────────────


def validar_tramos(tramos: list[dict]) -> list[dict]:
    """Ordena y valida tramos: sin huecos ni traslapes (RF-03 / CA-08).

    Cada tramo: {desde: Decimal|str, hasta: Decimal|str|None, valor, modo}.
    """
    ordenados: list[dict] = []
    for t in tramos or []:
        desde = _dec(t.get("desde"))
        hasta = _dec(t.get("hasta"))
        if desde is None:
            raise CosteoError(
                "TRAMOS_INCONSISTENTES",
                f"Tramo sin límite inferior: {t.get('desde')!r}.",
            )
        ordenados.append({**t, "desde": desde, "hasta": hasta})
    ordenados.sort(key=lambda t: t["desde"])

    esperado = None
    for i, t in enumerate(ordenados):
        desde, hasta = t["desde"], t["hasta"]
        if hasta is not None and hasta < desde:
            raise CosteoError(
                "TRAMOS_INCONSISTENTES",
                f"Tramo invertido ({desde}–{hasta}): el límite superior es menor que el inferior.",
            )
        if i > 0:
            anterior = ordenados[i - 1]
            if desde <= (anterior["hasta"] or Decimal("inf")):
                raise CosteoError(
                    "TRAMOS_INCONSISTENTES",
                    f"Traslape de tramos: {anterior['desde']}–{anterior['hasta']} y {desde}–{hasta}.",
                )
            if esperado is not None and desde != esperado:
                raise CosteoError(
                    "TRAMOS_INCONSISTENTES",
                    f"Hueco entre tramos: se esperaba continuidad en {esperado} y el siguiente "
                    f"tramo inicia en {desde}.",
                )
        esperado = (hasta + Decimal("1")) if hasta is not None else None
    if esperado is not None and ordenados[-1]["hasta"] is None:
        raise CosteoError(
            "TRAMOS_INCONSISTENTES",
            "Hay un tramo intermedio sin límite superior: el tramo abierto debe ser el último.",
        )
    return ordenados


def calcular_escalonado(tramos: list[dict], cantidad: Decimal) -> tuple[list[dict], Decimal]:
    """Recorre tramos marginales o completos sobre `cantidad`.

    - Si todos los tramos son `marginal`: se factura tramo a tramo.
    - Si existe al menos un tramo `completo`: toda la cantidad se factura
      con el valor del tramo que la contiene (una sola línea).

    Devuelve (filas aplicadas, total).
    """
    validos = validar_tramos(tramos)
    cantidad = _moneda(cantidad)

    if any(str(t.get("modo") or "marginal").lower() == "completo" for t in validos):
        for t in validos:
            desde = t["desde"]
            hasta = t["hasta"]
            if cantidad >= desde and (hasta is None or cantidad <= hasta):
                valor_unitario = _moneda(t["valor"])
                valor = (cantidad * valor_unitario).quantize(_CUATRO, rounding=ROUND_HALF_UP)
                return (
                    [{
                        "tramo": t,
                        "cantidad_tramo": cantidad,
                        "valor_unitario": valor_unitario,
                        "valor": valor,
                    }],
                    valor,
                )
        raise CosteoError(
            "TRAMOS_INSUFICIENTES",
            f"Ningún tramo contiene la cantidad {cantidad}.",
        )

    filas: list[dict] = []
    total = _CERO
    restante = cantidad
    for t in validos:
        desde = t["desde"]
        hasta = t["hasta"]
        valor_unitario = _moneda(t["valor"])
        if hasta is None:
            alcance = restante
        else:
            alcance = min(restante, max(_CERO, hasta - desde + Decimal("1")))
        if alcance <= 0:
            continue
        valor = (alcance * valor_unitario).quantize(_CUATRO, rounding=ROUND_HALF_UP)
        total += valor
        filas.append({
            "tramo": t,
            "cantidad_tramo": alcance,
            "valor_unitario": valor_unitario,
            "valor": valor,
        })
        restante -= alcance
        if restante <= 0:
            break
    if restante > 0:
        raise CosteoError(
            "TRAMOS_INSUFICIENTES",
            f"Los tramos no cubren la cantidad solicitada: quedan {restante} unidades sin tarifa.",
        )
    return filas, total.quantize(_CUATRO, rounding=ROUND_HALF_UP)


# ──────────────────────────────────────────────────────────────
# Componentes
# ──────────────────────────────────────────────────────────────


def _aplicar_componente(
    comp: dict,
    contexto: dict,
    cantidad_servicio: Decimal,
    lineas: list[dict],
    subtotal_directo: Decimal,
    subtotal_ajustado: Decimal,
) -> tuple[Decimal, str]:
    """Ejecuta un componente según su tipo y devuelve (valor, detalle)."""
    tipo = str(comp.get("tipo") or "").lower()
    cfg = comp.get("config") or {}
    cantidad = _moneda(cantidad_servicio)

    if tipo == "fijo":
        valor = _moneda(cfg.get("valor"))
        return valor, f"tarifa fija {valor}"

    if tipo == "escalonado":
        tramos = comp.get("tramos") or []
        filas, total = calcular_escalonado(tramos, cantidad)
        detalle = "; ".join(
            f"tramo {f['tramo']['desde']}–{f['tramo']['hasta']}: "
            f"{f['cantidad_tramo']} × {f['valor_unitario']} = {f['valor']}"
            for f in filas
        )
        return total, detalle or "sin tramos aplicables"

    if tipo == "por_unidad":
        unitario = _moneda(cfg.get("valor_unitario"))
        return (cantidad * unitario).quantize(_CUATRO, rounding=ROUND_HALF_UP), \
            f"{cantidad} × {unitario}"

    if tipo == "por_distancia":
        km = _moneda(contexto.get("km"))
        zona = contexto.get("zona") or {}
        km_incluidos = _moneda(zona.get("km_incluidos")) or _CERO
        tarifa_km = _moneda(zona.get("tarifa_km")) or _CERO
        peajes = _moneda(zona.get("peajes_estimados")) or _CERO
        excedente = max(_CERO, km - km_incluidos)
        valor = (excedente * tarifa_km + peajes).quantize(_CUATRO, rounding=ROUND_HALF_UP)
        return valor, f"{km} km (incluidos {km_incluidos}) × {tarifa_km} + peajes {peajes}"

    if tipo == "por_jornada":
        rendimiento = _moneda(cfg.get("rendimiento")) or Decimal("1")
        personas = _dec(cfg.get("personas")) or Decimal("1")
        tarifa_dia = _moneda(cfg.get("tarifa_dia"))
        prestacional = _dec(cfg.get("factor_prestacional")) or _CERO
        jornadas = (cantidad / rendimiento).to_integral_value(rounding=ROUND_CEILING)
        valor = (jornadas * personas * tarifa_dia * (Decimal("1") + prestacional / Decimal("100")))
        valor = valor.quantize(_CUATRO, rounding=ROUND_HALF_UP)
        return valor, f"{jornadas} jornadas × {personas} personas × {tarifa_dia} " \
            f"(prestacional {prestacional}%)"

    if tipo == "porcentual":
        pct = _dec(cfg.get("porcentaje")) or _CERO
        base_txt = str(cfg.get("base") or "directo").lower()
        if base_txt == "directo":
            base = subtotal_directo
        elif base_txt == "ajustado":
            base = subtotal_ajustado
        elif base_txt.startswith("linea:"):
            codigo = base_txt.split(":", 1)[1]
            linea = next((ln for ln in lineas if ln["componente_codigo"] == codigo), None)
            base = _moneda(linea["valor"]) if linea else _CERO
        else:
            raise CosteoError(
                "BASE_INVALIDA",
                f"Base desconocida en componente porcentual: {base_txt}.",
            )
        valor = (base * pct / Decimal("100")).quantize(_CUATRO, rounding=ROUND_HALF_UP)
        return valor, f"{pct}% sobre {base_txt} ({base})"

    if tipo == "condicional":
        cond = cfg.get("si") or {}
        if not _condicion_se_cumple(contexto, cond):
            return _CERO, "condición no cumplida"
        sub = dict(cfg.get("componente") or {})
        if not sub:
            raise CosteoError(
                "CONDICIONAL_SIN_COMPONENTE",
                f"El componente condicional {comp.get('codigo')} no declara componente hijo.",
            )
        valor, detalle = _aplicar_componente(
            sub, contexto, cantidad_servicio, lineas, subtotal_directo, subtotal_ajustado
        )
        return valor, f"condicional: {detalle}"

    raise CosteoError(
        "TIPO_COMPONENTE_DESCONOCIDO",
        f"Tipo de componente desconocido: {tipo}.",
    )


# ──────────────────────────────────────────────────────────────
# Redondeo único (paso 8)
# ──────────────────────────────────────────────────────────────


def aplicar_redondeo(valor: Decimal, multiplo: Decimal, modo: str) -> Decimal:
    """Redondeo único parametrizado. `modo`: ninguno | mitad_superior | techo | piso."""
    valor = _moneda(valor)
    multiplo = _dec(multiplo) or Decimal("1")
    modo = str(modo or "ninguno").lower()
    if modo == "ninguno" or multiplo <= 0:
        return valor
    if modo == "mitad_superior":
        redondeado = (valor / multiplo).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * multiplo
    elif modo == "techo":
        redondeado = (valor / multiplo).quantize(Decimal("1"), rounding=ROUND_CEILING) * multiplo
    elif modo == "piso":
        redondeado = (valor / multiplo).quantize(Decimal("1"), rounding=ROUND_FLOOR) * multiplo
    else:
        raise CosteoError("REDONDEO_DESCONOCIDO", f"Modo de redondeo desconocido: {modo}.")
    return _moneda(redondeado)


# ──────────────────────────────────────────────────────────────
# Motor principal
# ──────────────────────────────────────────────────────────────


def calcular(contexto: dict, conjunto: dict, seleccion: dict) -> dict:
    """Ejecuta la tubería de cálculo y devuelve el desglose completo.

    Parámetros:
      contexto:  {fecha_referencia, area_ha, puntos, km, rol, departamento,
                  municipio, dificultad, zona?: {...}}
      conjunto:  {id, nombre, version, estado, vigencia_desde, vigencia_hasta,
                  moneda, politica, servicios[], factores[], impuestos[], descuentos[]}
      seleccion: {servicios: [{codigo, cantidad}], factores: {codigo: opcion},
                  descuento_pct}
    """
    traza: list[str] = []
    advertencias: list[dict] = []

    # ── 1. Vigencia del conjunto ──
    fecha_ref = contexto.get("fecha_referencia")
    if conjunto.get("estado") != "publicado":
        raise CosteoError(
            "CONJUNTO_NO_PUBLICADO",
            f"El conjunto {conjunto.get('nombre')} no está publicado.",
        )
    vdesde = conjunto.get("vigencia_desde")
    vhasta = conjunto.get("vigencia_hasta")
    if vdesde and fecha_ref and str(fecha_ref) < str(vdesde):
        raise CosteoError("CONJUNTO_SIN_VIGENCIA", "El conjunto no está vigente para la fecha.")
    if vhasta and fecha_ref and str(fecha_ref) > str(vhasta):
        raise CosteoError("CONJUNTO_SIN_VIGENCIA", "El conjunto venció para la fecha.")
    traza.append(f"Conjunto {conjunto.get('nombre')} v{conjunto.get('version')} vigente.")

    politica = conjunto.get("politica") or {}

    # ── 2. Contexto ──
    area_ha = _moneda(contexto.get("area_ha"))
    puntos = int(contexto.get("puntos") or 0)
    traza.append(f"Contexto: {area_ha} ha · {puntos} puntos · {_moneda(contexto.get('km'))} km.")

    # ── 3. Componentes en orden → subtotal directo ──
    lineas: list[dict] = []
    subtotal_directo = _CERO
    for sel in seleccion.get("servicios") or []:
        servicio = next(
            (s for s in conjunto.get("servicios") or []
             if s.get("codigo") == sel.get("codigo")),
            None,
        )
        if servicio is None:
            raise CosteoError(
                "SERVICIO_NO_ENCONTRADO",
                f"El servicio '{sel.get('codigo')}' no existe en el conjunto vigente.",
            )
        cantidad = _moneda(sel.get("cantidad")) or _CERO
        componentes = sorted(
            (c for c in servicio.get("componentes") or []),
            key=lambda c: int(c.get("orden") or 0),
        )
        if not componentes:
            raise CosteoError(
                "SERVICIO_SIN_COMPONENTES",
                f"El servicio '{servicio.get('codigo')}' no tiene componentes de costo.",
            )
        for comp in componentes:
            valor, detalle = _aplicar_componente(
                comp, contexto, cantidad, lineas, subtotal_directo, _CERO
            )
            subtotal_directo += valor
            linea = {
                "servicio_codigo": servicio.get("codigo"),
                "servicio_nombre": servicio.get("nombre"),
                "componente_codigo": comp.get("codigo"),
                "componente_nombre": comp.get("nombre"),
                "tipo": comp.get("tipo"),
                "descripcion": detalle,
                "cantidad": cantidad if comp.get("tipo") != "fijo" else Decimal("1"),
                "unidad": servicio.get("unidad"),
                "valor_unitario": None,
                "valor": valor,
                "afectable": bool(comp.get("afectable_por_factores")),
                "parametro_ref": {
                    "componente_id": comp.get("id"),
                    "config": comp.get("config"),
                },
            }
            lineas.append(linea)
            traza.append(f"Línea {servicio.get('codigo')}/{comp.get('codigo')}: {valor} ({detalle})")
    subtotal_directo = _moneda(subtotal_directo)

    # ── 4. Factores sobre líneas afectables → subtotal ajustado ──
    base_afectable = _moneda(sum((ln["valor"] for ln in lineas if ln["afectable"]), _CERO))
    subtotal_ajustado = subtotal_directo
    factores_aplicados: list[dict] = []
    acumulador_multiplica = Decimal("1")
    pendientes_multiplica: list[dict] = []
    seleccion_factores = seleccion.get("factores") or {}
    for factor in conjunto.get("factores") or []:
        codigo_factor = factor.get("codigo")
        opcion_codigo = seleccion_factores.get(codigo_factor)
        if opcion_codigo is None:
            continue
        opcion = next(
            (o for o in factor.get("opciones") or [] if o.get("codigo") == opcion_codigo),
            None,
        )
        if opcion is None:
            raise CosteoError(
                "FACTOR_OPCION_INVALIDA",
                f"Opción '{opcion_codigo}' inexistente en el factor '{codigo_factor}'.",
            )
        pct = _dec(opcion.get("porcentaje")) or _CERO
        detalle_factor = {
            "factor_codigo": codigo_factor,
            "factor_nombre": factor.get("nombre"),
            "opcion_codigo": opcion_codigo,
            "opcion_etiqueta": opcion.get("etiqueta"),
            "porcentaje": pct,
        }
        if str(factor.get("combinacion") or "suma").lower() == "multiplica":
            acumulador_multiplica *= _pct_a_factor(pct)
            pendientes_multiplica.append(detalle_factor)
            continue
        # combinación «suma»: cada factor agrega su porcentaje sobre la base afectable
        incremento = (base_afectable * pct / Decimal("100")).quantize(
            _CUATRO, rounding=ROUND_HALF_UP
        )
        subtotal_ajustado += incremento
        detalle_factor["valor"] = incremento
        factores_aplicados.append(detalle_factor)
        traza.append(
            f"Factor {codigo_factor}/{opcion_codigo} {pct}% sobre {base_afectable} → +{incremento}"
        )
    if pendientes_multiplica:
        factor_multi = (acumulador_multiplica - Decimal("1"))
        incremento = (base_afectable * factor_multi).quantize(_CUATRO, rounding=ROUND_HALF_UP)
        subtotal_ajustado += incremento
        detalle = {
            "factor_codigo": ",".join(p["factor_codigo"] for p in pendientes_multiplica),
            "factor_nombre": "combinación multiplicativa",
            "porcentaje": ((acumulador_multiplica - Decimal("1")) * Decimal("100")).quantize(_CUATRO),
            "valor": incremento,
        }
        factores_aplicados.append(detalle)
        traza.append(f"Factores multiplicativos → +{incremento}")
    subtotal_ajustado = _moneda(subtotal_ajustado)

    # ── 5. Margen objetivo → precio de lista ──
    margen = _dec(politica.get("margen_objetivo")) or _CERO
    precio_lista = _moneda(subtotal_ajustado * _pct_a_factor(margen))

    # ── 6. Descuento comercial con tope por rol ──
    descuento_pct = _dec(seleccion.get("descuento_pct")) or _CERO
    if descuento_pct > 0:
        rol = str(contexto.get("rol") or "").lower()
        tope = None
        for regla in conjunto.get("descuentos") or []:
            if str(regla.get("criterio") or "").lower() == "manual":
                tope_rol = regla.get("tope_rol") or {}
                tope = _dec(tope_rol.get(rol)) if isinstance(tope_rol, dict) else None
                break
        if tope is not None and descuento_pct > tope:
            raise CosteoError(
                "DESCUENTO_EXCEDE_TOPE",
                f"El descuento {descuento_pct}% excede el tope del rol ({tope}%).",
            )
    descuento_valor = (precio_lista * descuento_pct / Decimal("100")).quantize(
        _CUATRO, rounding=ROUND_HALF_UP
    )
    total_con_descuento = _moneda(precio_lista - descuento_valor)

    # ── 7. Piso de rentabilidad y margen mínimo ──
    piso = _dec(politica.get("piso_visita")) or _CERO
    if piso > 0 and total_con_descuento < piso:
        advertencias.append({
            "codigo": "BAJO_PISO_RENTABILIDAD",
            "mensaje": (
                f"El total {total_con_descuento} está por debajo del piso de "
                f"rentabilidad {piso}. Se requiere autorización para emitir."
            ),
        })
    margen_minimo = _dec(politica.get("margen_minimo")) or _CERO
    margen_efectivo = (
        ((total_con_descuento - subtotal_ajustado) / total_con_descuento * Decimal("100"))
        .quantize(_CUATRO, rounding=ROUND_HALF_UP)
        if total_con_descuento > 0 else _CERO
    )
    if margen_minimo > 0 and margen_efectivo < margen_minimo:
        advertencias.append({
            "codigo": "MARGEN_BAJO_MINIMO",
            "mensaje": (
                f"El margen efectivo {margen_efectivo}% está por debajo del mínimo "
                f"{margen_minimo}%."
            ),
        })

    # ── 8. Redondeo único ──
    redondeo = aplicar_redondeo(
        total_con_descuento,
        _dec(politica.get("redondeo_multiplo")) or Decimal("1"),
        politica.get("redondeo_modo") or "ninguno",
    )
    ajuste_redondeo = _moneda(redondeo - total_con_descuento)
    total_final = redondeo

    # ── 9. Impuestos y retenciones ──
    bases = {
        "directo": subtotal_directo,
        "ajustado": subtotal_ajustado,
        "lista": precio_lista,
    }
    impuestos_informativos: list[dict] = []
    impuestos_incluidos: list[dict] = []
    for imp in conjunto.get("impuestos") or []:
        pct = _dec(imp.get("porcentaje")) or _CERO
        base_val = bases.get(str(imp.get("base") or "subtotal").lower(), subtotal_ajustado)
        valor_imp = (base_val * pct / Decimal("100")).quantize(_CUATRO, rounding=ROUND_HALF_UP)
        item = {
            "codigo": imp.get("codigo"),
            "nombre": imp.get("nombre"),
            "porcentaje": pct,
            "base": imp.get("base"),
            "base_valor": base_val,
            "valor": valor_imp,
        }
        if imp.get("informativo"):
            impuestos_informativos.append(item)
        else:
            impuestos_incluidos.append(item)
            total_final += valor_imp
    total_final = _moneda(total_final)

    # ── 10. Indicadores derivados y traza ──
    indicadores = {
        "costo_por_punto": (
            (total_final / Decimal(str(puntos))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            if puntos > 0 else None
        ),
        "costo_por_ha": (
            (total_final / area_ha).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            if area_ha > 0 else None
        ),
        "costo_directo": subtotal_directo,
        "margen_cop": _moneda(precio_lista - subtotal_ajustado),
        "margen_pct": margen,
    }
    traza.append(f"Subtotal directo {subtotal_directo} → ajustado {subtotal_ajustado} → "
                 f"lista {precio_lista} → descuento {descuento_valor} → final {total_final}.")

    return {
        "conjunto": {
            "id": conjunto.get("id"),
            "nombre": conjunto.get("nombre"),
            "version": conjunto.get("version"),
        },
        "fecha_referencia": str(fecha_ref) if fecha_ref else None,
        "moneda": conjunto.get("moneda") or "COP",
        "subtotal_directo": subtotal_directo,
        "subtotal_ajustado": subtotal_ajustado,
        "precio_lista": precio_lista,
        "descuento_aplicado": descuento_valor,
        "descuento_pct": descuento_pct,
        "total_sin_redondeo": total_con_descuento,
        "ajuste_redondeo": ajuste_redondeo,
        "total_final": total_final,
        "lineas": lineas,
        "factores_aplicados": factores_aplicados,
        "impuestos_informativos": impuestos_informativos,
        "impuestos_incluidos": impuestos_incluidos,
        "advertencias": advertencias,
        "indicadores": indicadores,
        "traza": traza,
    }
