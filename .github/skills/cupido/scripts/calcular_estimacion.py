#!/usr/bin/env python3
"""
Motor de cálculo determinístico de effort-estimator.

Toda cifra que aparezca en el .md, .html y .pptx debe salir de este script,
no de aritmética hecha "a mano" por el modelo. Así los tres formatos coinciden.

Uso:
    python3 calcular_estimacion.py entrada.json [-o salida.json]
    python3 calcular_estimacion.py --self-test

Modos por ítem (se pueden mezclar en una misma propuesta):
    pf     -> Puntos de Función (IFPUG/COSMIC) x tasa de productividad (h/PF)
    sp     -> Story Points x horas por SP CALIBRADAS del equipo (obligatorio)
    epica  -> T-shirt sizing top-down (guía top-down)
    horas  -> horas de desarrollo ya estimadas por el senior

Ver examples/entrada-ejemplo.json para el formato completo.
"""
import argparse
import json
import math
import sys

# --------------------------------------------------------------------------
# Tablas por defecto (todas sobrescribibles desde entrada.json -> "tablas")
# --------------------------------------------------------------------------
DEFAULTS = {
    # PDR (h/PF) de ciclo completo, mediana de benchmarks públicos.
    # Ver references/evidencia-benchmarks.md. Usar SOLO hasta tener datos propios.
    "pdr_ciclo_completo": 10.0,
    # Fracción de la PDR que corresponde a gestión (PM). Se descuenta porque
    # el PM se calcula globalmente por duración (evita doble conteo).
    "pdr_fraccion_pm": 0.12,
    # Reparto del esfuerzo de equipo (sin PM) en modo PF.
    "reparto_pf": {"desarrollo": 0.51, "qa": 0.25, "arquitecto": 0.09, "ux_ui": 0.15},
    # Perfil de quien EJECUTA (no de quien estima). Aplica solo a desarrollo.
    "perfil": {"senior": 0.85, "semi_senior": 1.1, "junior": 1.45, "mixto": 1.0},
    # Modo épica: punto medio de los rangos de la guía top-down.
    "talla_dev_horas": {"XS": 30, "S": 60, "M": 120, "L": 240, "XL": 400},
    "arq_horas": {"Baja": 6, "Media": 14, "Alta": 30, "Muy alta": 48},
    "ux_horas": {"Ninguno": 0, "Bajo": 12, "Medio": 28, "Alto": 60},
    "qa_pct_dev": 0.25,
    "arq_pct_dev_sp": 0.10,
    # PM por duración total (meses) -> %
    "pm_por_duracion": [[1, 0.10], [3, 0.12], [6, 0.15], [9999, 0.18]],
    # Cono de incertidumbre: multiplicadores (optimista, pesimista) sobre el valor más probable.
    # Se interpretan como percentiles 5 y 95 de una distribución log-normal.
    "cono": {
        "concepto": [0.50, 2.00],        # necesidad cruda, sin epicureo
        "requerimientos": [0.67, 1.50],  # épica refinada por epicureo
        "diseno": [0.80, 1.25],          # backlog specter / HU con PF contados
        "listo": [0.90, 1.10],           # HU refinada, spec lista
    },
    # Factores SDD (especificación, generación, revisión+validación) — guía SDD sección 6.
    "sdd_factores": {
        "crud": [0.8, 0.3, 0.7],
        "logica_media": [1.0, 0.5, 0.9],
        "critica": [1.2, 0.7, 1.1],
        "integracion": [1.1, 0.8, 1.0],
        "refactor": [0.9, 0.4, 0.8],
        "ninguno": [1.0, 1.0, 1.0],
    },
    # Reparto de horas de desarrollo por fase SDD (espec, rev spec, gen, rev código, validación, integración)
    "sdd_fases": [0.17, 0.09, 0.26, 0.17, 0.17, 0.13],
    # Decaimiento de la efectividad del agente por tamaño del ítem (horas de desarrollo).
    # Heurística conservadora basada en la tendencia reportada por METR: el ahorro cae con el tamaño.
    "sdd_decaimiento": [[16, 1.0], [40, 0.8], [120, 0.6], [1e9, 0.4]],
}

Z80 = 0.8416
Z95_SPAN = 3.29  # distancia entre percentil 5 y 95 en desviaciones estándar


def merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def r1(x):
    return round(x + 1e-9, 1)


def factor_sdd(tipo, t):
    s, g, rv = t["sdd_factores"][tipo]
    f = t["sdd_fases"]
    return f[0] * s + f[1] + f[2] * g + f[3] * rv + f[4] * rv + f[5]


def decaimiento(horas_dev, t):
    for lim, d in t["sdd_decaimiento"]:
        if horas_dev <= lim:
            return d
    return t["sdd_decaimiento"][-1][1]


def prod(factores):
    p = 1.0
    for v in (factores or {}).values():
        p *= float(v)
    return p


def estimar_item(it, t, advertencias):
    modo = it["modo"]
    fx = prod(it.get("factores"))
    perfil = t["perfil"][it.get("perfil", "mixto")]
    roles = {"desarrollo": 0.0, "qa": 0.0, "arquitecto": 0.0, "ux_ui": 0.0}
    nota = []

    if modo == "pf":
        pdr = float(it.get("pdr", t["pdr_ciclo_completo"]))
        equipo = it["pf"] * pdr * (1 - t["pdr_fraccion_pm"]) * fx
        for rol, pct in t["reparto_pf"].items():
            roles[rol] = equipo * pct
        roles["desarrollo"] *= perfil
        nota.append(f"{it['pf']} PF x {pdr} h/PF x (1-{t['pdr_fraccion_pm']}) x factores {fx:.3f}")
        if it["pf"] < 5:
            advertencias.append(f"{it['id']}: menos de 5 PF — IFPUG pierde precisión; considerar COSMIC.")
    elif modo == "sp":
        if "horas_por_sp" not in it:
            raise ValueError(f"{it['id']}: modo 'sp' requiere 'horas_por_sp' calibradas del equipo. "
                             "Los SP son relativos a cada equipo; no existe una conversión universal.")
        roles["desarrollo"] = it["sp"] * it["horas_por_sp"] * fx * perfil
        roles["qa"] = roles["desarrollo"] * t["qa_pct_dev"]
        roles["arquitecto"] = it.get("arq_horas", roles["desarrollo"] * t["arq_pct_dev_sp"])
        roles["ux_ui"] = it.get("ux_horas", 0.0)
        nota.append(f"{it['sp']} SP x {it['horas_por_sp']} h/SP x factores {fx:.3f}")
        if it["sp"] >= 13:
            advertencias.append(f"{it['id']}: SP >= 13 — recomendar Spike o descomposición.")
    elif modo == "epica":
        dev = it.get("horas_dev", t["talla_dev_horas"][it["talla"]])
        roles["desarrollo"] = dev * fx * perfil
        roles["qa"] = it.get("qa_horas", roles["desarrollo"] * t["qa_pct_dev"])
        roles["arquitecto"] = it.get("arq_horas", t["arq_horas"][it.get("complejidad_arq", "Media")])
        roles["ux_ui"] = it.get("ux_horas", t["ux_horas"][it.get("ux", "Ninguno")])
        nota.append(f"Talla {it.get('talla', '-')}, dev {dev} h x factores {fx:.3f}")
        if it.get("talla") == "XL":
            advertencias.append(f"{it['id']}: talla XL — ROM preliminar, descomponer con specter antes de comprometer.")
    elif modo == "horas":
        roles["desarrollo"] = it["horas_dev"] * fx
        roles["qa"] = it.get("qa_horas", roles["desarrollo"] * t["qa_pct_dev"])
        roles["arquitecto"] = it.get("arq_horas", 0.0)
        roles["ux_ui"] = it.get("ux_horas", 0.0)
        nota.append(f"Horas dev directas {it['horas_dev']} x factores {fx:.3f}")
    else:
        raise ValueError(f"{it['id']}: modo desconocido '{modo}'")

    tipo = it.get("tipo_sdd", "ninguno")
    f_sdd = factor_sdd(tipo, t)
    ahorro_bruto = 1 - f_sdd
    dec = decaimiento(roles["desarrollo"], t)
    ahorro = ahorro_bruto * dec
    dev_ia = roles["desarrollo"] * (1 - ahorro)
    equipo_trad = sum(roles.values())
    equipo_ia = equipo_trad - roles["desarrollo"] + dev_ia

    return {
        "id": it["id"],
        "titulo": it.get("titulo", ""),
        "modo": modo,
        "prioridad": it.get("prioridad", "Sin priorizar"),
        "roles_horas": {k: r1(v) for k, v in roles.items()},
        "horas_equipo_tradicional": r1(equipo_trad),
        "tipo_sdd": tipo,
        "ahorro_sdd_pct_dev": r1(ahorro * 100),
        "horas_dev_con_ia": r1(dev_ia),
        "horas_equipo_con_ia": r1(equipo_ia),
        "calculo": "; ".join(nota),
    }


def pm_pct(meses, t):
    for lim, pct in t["pm_por_duracion"]:
        if meses <= lim:
            return pct
    return t["pm_por_duracion"][-1][1]


def rango(m, fase, t):
    lo, hi = t["cono"][fase]
    o, p = m * lo, m * hi
    mu = (math.log(o) + math.log(p)) / 2
    sigma = (math.log(p) - math.log(o)) / Z95_SPAN
    return {
        "optimista_p5": r1(o),
        "mas_probable": r1(m),
        "pesimista_p95": r1(p),
        "p50": r1(math.exp(mu)),
        "esperado_media": r1(math.exp(mu + sigma ** 2 / 2)),
        "comprometido_p80": r1(math.exp(mu + Z80 * sigma)),
        "buffer_implicito_p80_pct": r1((math.exp(mu + Z80 * sigma) / m - 1) * 100),
    }


def calcular(data):
    t = merge(DEFAULTS, data.get("tablas"))
    par = data.get("parametros", {})
    jornada = float(par.get("jornada_horas", 8.4))
    fprod = float(par.get("factor_productivo", 0.75))
    if par.get("horas_calibradas_con_timesheet_completo"):
        fprod = 1.0  # la tasa ya absorbe reuniones: no descontar dos veces
    h_ef = jornada * fprod
    dias_iter = par.get("dias_iteracion")
    n_dev = int(par.get("personas_desarrollo", 1))
    fase = par.get("fase_definicion", "requerimientos")
    advertencias = []

    items = [estimar_item(it, t, advertencias) for it in data["items"]]

    def totales(clave_equipo, clave_dev):
        equipo = sum(i[clave_equipo] for i in items)
        dev = sum(i[clave_dev] for i in items) if clave_dev != "_trad" else \
            sum(i["roles_horas"]["desarrollo"] for i in items)
        dias_dev = dev / (n_dev * h_ef)
        meses = dias_dev / 21
        pct = float(par["pm_pct"]) if "pm_pct" in par else pm_pct(meses, t)
        pm = equipo * pct
        total = equipo + pm
        out = {
            "horas_equipo_sin_pm": r1(equipo),
            "pm_pct": pct,
            "horas_pm": r1(pm),
            "horas_totales": r1(total),
            "dias_hombre": r1(total / h_ef),
            "dias_habiles_desarrollo": r1(dias_dev),
            "semanas_calendario": r1(dias_dev / 5),
        }
        if dias_iter:
            out["iteraciones"] = math.ceil(round(dias_dev / dias_iter, 6))
        out["rango"] = rango(total, fase, t)
        return out

    trad = totales("horas_equipo_tradicional", "_trad")
    ia = totales("horas_equipo_con_ia", "horas_dev_con_ia")

    por_rol = {}
    for rol in ["arquitecto", "desarrollo", "qa", "ux_ui"]:
        por_rol[rol] = r1(sum(i["roles_horas"][rol] for i in items))
    por_rol["project_manager"] = trad["horas_pm"]
    tot = sum(por_rol.values())
    por_rol_pct = {k: r1(v / tot * 100) for k, v in por_rol.items()}

    costo = None
    if par.get("tarifa_hora"):
        tar = par["tarifa_hora"]
        costo = {
            "moneda": par.get("moneda", "USD"),
            "tradicional_p80": round(trad["rango"]["comprometido_p80"] * tar),
            "con_ia_p80": round(ia["rango"]["comprometido_p80"] * tar),
        }

    if trad["rango"]["pesimista_p95"] / trad["rango"]["optimista_p5"] > 3:
        advertencias.append("Rango pesimista/optimista > 3x: alta incertidumbre, refinar antes de comprometer.")
    if trad["semanas_calendario"] > 26:
        advertencias.append("Duración > 6 meses: evaluar PM dedicado y entregas por fases con reestimación.")
    if fase == "concepto":
        advertencias.append("Fase 'concepto': la cifra puede desviarse 2-4x; presentar solo como ROM.")

    return {
        "proyecto": data.get("proyecto", ""),
        "parametros_efectivos": {
            "jornada_horas": jornada, "factor_productivo": fprod, "horas_efectivas_dia": r1(h_ef),
            "personas_desarrollo": n_dev, "dias_iteracion": dias_iter, "fase_definicion": fase,
            "pdr_ciclo_completo": t["pdr_ciclo_completo"],
        },
        "items": items,
        "tradicional": trad,
        "con_ia": ia,
        "ahorro_ia_pct_total": r1((1 - ia["horas_totales"] / trad["horas_totales"]) * 100),
        "distribucion_por_rol_horas": por_rol,
        "distribucion_por_rol_pct": por_rol_pct,
        "costo": costo,
        "advertencias": advertencias,
    }


def self_test():
    # 1) Reproduce el ejemplo resuelto de la guía top-down (206.8 h)
    d = {"parametros": {"pm_pct": 0.10, "fase_definicion": "requerimientos"},
         "items": [{"id": "EP-1", "modo": "epica", "talla": "M", "horas_dev": 120,
                    "arq_horas": 14, "ux_horas": 24}]}
    r = calcular(d)
    assert r["tradicional"]["horas_totales"] == 206.8, r["tradicional"]["horas_totales"]
    # 2) Ahorro SDD por tipo coincide con la guía SDD (fases por defecto)
    t = DEFAULTS
    assert round((1 - factor_sdd("crud", t)) * 100, 1) == 32.8
    assert round((1 - factor_sdd("logica_media", t)) * 100, 1) == 17.4
    # 3) SP sin calibración debe fallar
    try:
        calcular({"items": [{"id": "HU-1", "modo": "sp", "sp": 5}]})
        raise AssertionError("debió fallar")
    except ValueError:
        pass
    # 4) Capacidad: 8.4 h x 0.75 = 6.3 h efectivas
    r = calcular({"parametros": {"dias_iteracion": 10},
                  "items": [{"id": "HU-1", "modo": "horas", "horas_dev": 63}]})
    assert r["parametros_efectivos"]["horas_efectivas_dia"] == 6.3
    assert r["tradicional"]["iteraciones"] == 1
    print("self-test OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada", nargs="?")
    ap.add_argument("-o", "--salida")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        sys.exit(0)
    with open(a.entrada, encoding="utf-8") as f:
        res = calcular(json.load(f))
    txt = json.dumps(res, ensure_ascii=False, indent=2)
    if a.salida:
        with open(a.salida, "w", encoding="utf-8") as f:
            f.write(txt)
    print(txt)
