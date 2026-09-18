"""Validación integral de un conjunto de parámetros AGC-COST (RFP §13).

Validación previa obligatoria antes de publicar: rechaza tramos con huecos
o traslapes, factores sin opciones, servicios sin componentes y política
sin margen. Devuelve errores bloqueantes y advertencias no bloqueantes.
"""

from decimal import Decimal


def validar_conjunto(conjunto: dict) -> dict:
    """Valida la estructura resuelta de un conjunto (formato `_conjunto_a_dict`).

    Devuelve {"valido": bool, "errores": [...], "advertencias": [...]}.
    Cada entrada es {"codigo", "mensaje"}.
    """
    errores: list[dict] = []
    advertencias: list[dict] = []

    politica = conjunto.get("politica") or {}
    servicios = conjunto.get("servicios") or []
    factores = conjunto.get("factores") or []
    impuestos = conjunto.get("impuestos") or []
    descuentos = conjunto.get("descuentos") or []
    densidad = conjunto.get("densidad") or []

    # ── Servicios ──────────────────────────────────────────────────────────
    codigos_s = [s.get("codigo") for s in servicios if s.get("codigo")]
    if not servicios:
        errores.append({
            "codigo": "SIN_SERVICIOS",
            "mensaje": "El conjunto no tiene servicios cotizables.",
        })
    if len(codigos_s) != len(set(codigos_s)):
        errores.append({
            "codigo": "CODIGOS_SERVICIO_DUPLICADOS",
            "mensaje": "Hay códigos de servicio duplicados.",
        })
    for s in servicios:
        componentes = s.get("componentes") or []
        if not componentes:
            errores.append({
                "codigo": "SERVICIO_SIN_COMPONENTES",
                "mensaje": f"El servicio «{s.get('nombre', s.get('codigo'))}» no tiene componentes.",
            })
        codigos_c = [c.get("codigo") for c in componentes if c.get("codigo")]
        if len(codigos_c) != len(set(codigos_c)):
            errores.append({
                "codigo": "CODIGOS_COMPONENTE_DUPLICADOS",
                "mensaje": f"El servicio «{s.get('codigo')}» tiene componentes con código duplicado.",
            })
        for c in componentes:
            tipo = c.get("tipo")
            if tipo == "escalonado":
                tramos = c.get("tramos") or []
                if not tramos:
                    errores.append({
                        "codigo": "TRAMOS_VACIOS",
                        "mensaje": f"El componente «{c.get('codigo')}» es escalonado y no tiene tramos.",
                    })
                    continue
                _validar_tramos(tramos, c.get("codigo"), errores)
            elif tipo not in (
                "fijo", "por_unidad", "por_distancia", "por_jornada",
                "porcentual", "condicional",
            ):
                errores.append({
                    "codigo": "TIPO_COMPONENTE_INVALIDO",
                    "mensaje": f"Tipo de componente desconocido en «{c.get('codigo')}»: {tipo}.",
                })

    # ── Factores ───────────────────────────────────────────────────────────
    codigos_f = [f.get("codigo") for f in factores if f.get("codigo")]
    if len(codigos_f) != len(set(codigos_f)):
        errores.append({
            "codigo": "CODIGOS_FACTOR_DUPLICADOS",
            "mensaje": "Hay códigos de factor duplicados.",
        })
    for f in factores:
        opciones = f.get("opciones") or []
        if not opciones:
            errores.append({
                "codigo": "FACTOR_SIN_OPCIONES",
                "mensaje": f"El factor «{f.get('nombre', f.get('codigo'))}» no tiene opciones.",
            })
        for o in opciones:
            pct = o.get("porcentaje")
            if pct is None or Decimal(str(pct)) < -100 or Decimal(str(pct)) > 1000:
                errores.append({
                    "codigo": "OPCION_PORCENTAJE_INVALIDO",
                    "mensaje": f"Porcentaje inválido en la opción «{o.get('codigo')}» del factor «{f.get('codigo')}».",
                })

    # ── Política comercial ─────────────────────────────────────────────────
    margen = Decimal(str(politica.get("margen_objetivo") or 0))
    if margen < 0:
        errores.append({
            "codigo": "POLITICA_SIN_MARGEN",
            "mensaje": "La política comercial no define un margen objetivo válido (≥ 0).",
        })
    piso = Decimal(str(politica.get("piso_visita") or 0))
    if piso < 0:
        errores.append({
            "codigo": "PISO_NEGATIVO",
            "mensaje": "El piso de rentabilidad no puede ser negativo.",
        })
    redondeo = politica.get("redondeo_modo")
    if redondeo not in (None, "ninguno", "mitad_superior", "techo", "piso"):
        errores.append({
            "codigo": "REDONDEO_INVALIDO",
            "mensaje": f"Modo de redondeo desconocido: {redondeo}.",
        })

    # ── Impuestos ──────────────────────────────────────────────────────────
    for i in impuestos:
        pct = i.get("porcentaje")
        if pct is None or Decimal(str(pct)) < 0 or Decimal(str(pct)) > 100:
            errores.append({
                "codigo": "IMPUESTO_PORCENTAJE_INVALIDO",
                "mensaje": f"Porcentaje inválido en el impuesto «{i.get('codigo')}».",
            })

    # ── Descuentos ─────────────────────────────────────────────────────────
    for d in descuentos:
        pct = d.get("porcentaje")
        if pct is None or Decimal(str(pct)) < 0 or Decimal(str(pct)) > 100:
            errores.append({
                "codigo": "DESCUENTO_PORCENTAJE_INVALIDO",
                "mensaje": f"Porcentaje inválido en el descuento «{d.get('codigo')}».",
            })

    # ── Densidad ───────────────────────────────────────────────────────────
    rangos = [
        (Decimal(str(d.get("area_min") or 0)), Decimal(str(d.get("area_max") or 0)), d)
        for d in densidad
    ]
    for (area_min, area_max, d) in rangos:
        if area_min >= area_max:
            errores.append({
                "codigo": "DENSIDAD_RANGO_INVALIDO",
                "mensaje": "Un rango de densidad tiene area_min ≥ area_max.",
            })
    for i in range(len(rangos)):
        for j in range(i + 1, len(rangos)):
            (a1, b1, _), (a2, b2, _) = rangos[i], rangos[j]
            if a1 < b2 and a2 < b1:
                errores.append({
                    "codigo": "DENSIDAD_TRASLAPE",
                    "mensaje": "Hay rangos de densidad de muestreo que se traslapan.",
                })

    # ── Advertencias no bloqueantes ────────────────────────────────────────
    if not politica:
        advertencias.append({
            "codigo": "SIN_POLITICA",
            "mensaje": "El conjunto no define política comercial (usa valores por defecto).",
        })
    if not impuestos:
        advertencias.append({
            "codigo": "SIN_IMPUESTOS",
            "mensaje": "El conjunto no define impuestos; la cotización saldrá sin ellos.",
        })

    return {
        "valido": not errores,
        "errores": errores,
        "advertencias": advertencias,
    }


def _validar_tramos(tramos: list[dict], codigo: str, errores: list[dict]) -> None:
    """Rechaza huecos y traslapes en tramos escalonados (RF-03 / CA-08).

    Misma semántica del motor: traslape si desde ≤ hasta_anterior; hueco si
    el siguiente tramo no inicia en hasta_anterior + 1; el tramo abierto
    (hasta=None) debe ser el último.
    """
    ordenados = sorted(
        tramos, key=lambda t: Decimal(str(t.get("desde") or 0))
    )
    esperado: Decimal | None = None
    for i, t in enumerate(ordenados):
        desde = Decimal(str(t.get("desde") or 0))
        hasta_raw = t.get("hasta")
        hasta = Decimal(str(hasta_raw)) if hasta_raw is not None else None
        if hasta is not None and hasta < desde:
            errores.append({
                "codigo": "TRAMOS_INCONSISTENTES",
                "mensaje": (
                    f"El componente «{codigo}» tiene un tramo invertido "
                    f"({t.get('desde')}–{hasta_raw})."
                ),
            })
        if i > 0:
            anterior = ordenados[i - 1]
            hasta_ant_raw = anterior.get("hasta")
            hasta_ant = (
                Decimal(str(hasta_ant_raw)) if hasta_ant_raw is not None else None
            )
            if hasta_ant is not None and desde <= hasta_ant:
                errores.append({
                    "codigo": "TRAMOS_INCONSISTENTES",
                    "mensaje": (
                        f"El componente «{codigo}» tiene tramos que se traslapan: "
                        f"{anterior.get('desde')}–{hasta_ant_raw} y {t.get('desde')}–{hasta_raw}."
                    ),
                })
            if esperado is not None and desde != esperado:
                errores.append({
                    "codigo": "TRAMOS_INCONSISTENTES",
                    "mensaje": (
                        f"El componente «{codigo}» deja un hueco: se esperaba "
                        f"continuidad en {esperado} y el siguiente tramo inicia en {t.get('desde')}."
                    ),
                })
        esperado = (hasta + Decimal("1")) if hasta is not None else None
        # Tramo abierto intermedio: siempre inconsistente.
        if esperado is None and i < len(ordenados) - 1:
            errores.append({
                "codigo": "TRAMOS_INCONSISTENTES",
                "mensaje": (
                    f"El componente «{codigo}» tiene un tramo abierto "
                    f"({t.get('desde')}–∞) que no es el último."
                ),
            })
            break
