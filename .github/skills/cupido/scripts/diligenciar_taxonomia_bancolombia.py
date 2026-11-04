#!/usr/bin/env python3
"""
Diligencia la pestaña "Esfuerzo & Condiciones" del formato
"Taxonomía de Costos Bancolombia" a partir de la estimación de effort-estimator.

Uso:
    python3 diligenciar_taxonomia_bancolombia.py entrada.json plantilla.xlsx salida.xlsx
            [--escenario tradicional|con_ia]

- entrada.json es el MISMO archivo de entrada de calcular_estimacion.py, con una
  sección adicional "taxonomia_bancolombia" (ver references/guia-taxonomia-bancolombia.md).
- Solo modifica la hoja "Esfuerzo & Condiciones". El resto del libro queda intacto.

Por qué XML directo y no openpyxl: la hoja trae 12 listas desplegables (extensión x14)
y el logo como dibujo; openpyxl los elimina al guardar. Este script edita el XML del
paquete y conserva todo lo demás byte a byte.
"""
import argparse
import copy
import json
import math
import os
import re
import shutil
import sys
import tempfile
import zipfile
from collections import OrderedDict

from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calcular_estimacion as motor  # noqa: E402

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
N = "{%s}" % NS
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
HOJA = "Esfuerzo & Condiciones"

# Plantilla del bloque de fase (filas del formato original)
T_TITULO, T_SERVICIO, T_HDR1, T_HDR2, T_ROL, T_SUBTOTAL = 19, 20, 21, 22, 23, 27
PRIMERA_FILA_BLOQUES = 19
ESPACIO_ENTRE_BLOQUES = 2

ROLES_DEFECTO = {
    "project_manager": {"familia_trabajo": "T. Gerencia de Proyectos y Agilismo",
                        "familia_cargo": "Gerente de Proyecto", "cargo": "Project Manager", "seniority": "Senior"},
    "arquitecto": {"familia_trabajo": "T. Arquitectura de TI y Digital",
                   "familia_cargo": "Arquitectura de Aplicación", "cargo": "Senior Architect", "seniority": "Senior"},
    "desarrollo": {
        "senior": {"familia_trabajo": "2. Ingeniería de software", "familia_cargo": "Desarrollo Full-Stack Senior",
                   "cargo": "Senior Software Developer", "seniority": "Senior"},
        "semi_senior": {"familia_trabajo": "2. Ingeniería de software", "familia_cargo": "Desarrollo Full-Stack Intermedio",
                        "cargo": "Intermediate Software Developer", "seniority": "Intermediate"},
        "mixto": {"familia_trabajo": "2. Ingeniería de software", "familia_cargo": "Desarrollo Full-Stack Senior",
                  "cargo": "Senior Software Developer", "seniority": "Senior"},
        "junior": {"familia_trabajo": "2. Ingeniería de software", "familia_cargo": "Desarrollo Back-End Junior",
                   "cargo": "Junior Software Developer", "seniority": "Junior"},
    },
    "qa": {"familia_trabajo": "4. Ingeniería de QA", "familia_cargo": "Analista de Certificación Senior",
           "cargo": "Senior Certification Analyst", "seniority": "Senior"},
    "ux_ui": {"familia_trabajo": "1. Diseño de Producto Digital",
              "familia_cargo": "Diseñador Cusotmer Journey(CJ) y de Experiencia(UX)", "cargo": "Technical Lead",
              "seniority": "Senior"},
}
ORDEN_ROLES = ["project_manager", "arquitecto", "desarrollo", "qa", "ux_ui"]
FASES_PRIORIDAD = OrderedDict([("Alta", "Fase 1 - MVP"), ("Media", "Fase 2 - Release 2"),
                               ("Baja", "Fase 3 - Backlog futuro"), ("Sin priorizar", "Fase única")])


# ------------------------------------------------------------------ utilidades XML
def col_idx(col):
    n = 0
    for ch in col:
        n = n * 26 + ord(ch) - 64
    return n


def split_ref(ref):
    m = re.match(r"([A-Z]+)(\d+)$", ref)
    return m.group(1), int(m.group(2))


def set_str(cell, text):
    for ch in list(cell):
        cell.remove(ch)
    if text is None or text == "":
        cell.attrib.pop("t", None)
        return
    cell.set("t", "inlineStr")
    is_ = etree.SubElement(cell, N + "is")
    t = etree.SubElement(is_, N + "t")
    t.text = str(text)
    if str(text) != str(text).strip():
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def set_num(cell, value):
    for ch in list(cell):
        cell.remove(ch)
    cell.attrib.pop("t", None)
    if value is None:
        return
    v = etree.SubElement(cell, N + "v")
    v.text = repr(float(value)) if not float(value).is_integer() else str(int(value))


def set_formula(cell, formula):
    for ch in list(cell):
        cell.remove(ch)
    cell.attrib.pop("t", None)
    f = etree.SubElement(cell, N + "f")
    f.text = formula


def get_cell(row_el, ref, style_from=None):
    for c in row_el.findall(N + "c"):
        if c.get("r") == ref:
            return c
    col = split_ref(ref)[0]
    new = etree.Element(N + "c", r=ref)
    if style_from is not None and style_from.get("s"):
        new.set("s", style_from.get("s"))
    # insertar en orden de columna
    cells = row_el.findall(N + "c")
    for i, c in enumerate(cells):
        if col_idx(split_ref(c.get("r"))[0]) > col_idx(col):
            c.addprevious(new)
            return new
    row_el.append(new)
    return new


def clone_row(template_row, new_r):
    r = copy.deepcopy(template_row)
    r.set("r", str(new_r))
    for c in r.findall(N + "c"):
        col, _ = split_ref(c.get("r"))
        c.set("r", f"{col}{new_r}")
        f = c.find(N + "f")
        if f is not None and f.get("t") == "shared":
            # nunca clonar fórmulas compartidas: se reescriben explícitas
            c.remove(f)
            v = c.find(N + "v")
            if v is not None:
                c.remove(v)
    return r


def strip_values(row_el, cols):
    for c in row_el.findall(N + "c"):
        if split_ref(c.get("r"))[0] in cols:
            for ch in list(c):
                c.remove(ch)
            c.attrib.pop("t", None)


# ------------------------------------------------------------------ lectura de listas
def leer_listas(xlsx_path):
    """Lee listas de parametrización (solo lectura, sin guardar) para validar valores."""
    from openpyxl import load_workbook
    import warnings
    warnings.filterwarnings("ignore")
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    tx = wb["Parametrización Taxonomia"]
    cols = {"cliente": "B", "arquitecto_responsable": "C", "modelo_negocio": "D", "modelo_adquisicion": "E",
            "linea_servicio": "F", "unidad_tiempo": "G", "seniority": "I", "base_operacion": "J",
            "nivel_ingles": "K", "disponibilidad": "L", "poliza": "N"}
    listas = {k: set() for k in cols}
    for row in tx.iter_rows(min_row=2, values_only=False):
        for k, col in cols.items():
            v = row[col_idx(col) - 1].value if len(row) >= col_idx(col) else None
            if v not in (None, ""):
                listas[k].add(str(v).strip())
    ro = wb["Parametrización Roles"]
    triples = set()
    for row in ro.iter_rows(min_row=3, values_only=True):
        if row[1]:
            triples.add((str(row[1]).strip(), str(row[2]).strip(), str(row[3]).strip()))
    listas["roles"] = triples
    return listas


# ------------------------------------------------------------------ cálculo de filas
def armar_fases(entrada, resultado, escenario, cfg, advertencias):
    par = entrada.get("parametros", {})
    jornada = float(cfg.get("horas_por_dia", par.get("jornada_horas", 8.4)))
    h_ef = resultado["parametros_efectivos"]["horas_efectivas_dia"]
    n_dev = int(par.get("personas_desarrollo", 1))
    modo = cfg.get("modo_horas", "esfuerzo")  # esfuerzo | dedicacion
    usar_p80 = cfg.get("cifra", "mas_probable") == "p80"
    agrupar = cfg.get("agrupar_por", "prioridad")  # prioridad | unica

    perfil_por_item = {it["id"]: it.get("perfil", "mixto") for it in entrada["items"]}
    tot = resultado["tradicional"] if escenario == "tradicional" else resultado["con_ia"]
    factor_p80 = tot["rango"]["comprometido_p80"] / tot["rango"]["mas_probable"] if usar_p80 else 1.0
    factor_modo = (jornada / h_ef) if modo == "dedicacion" else 1.0

    fases = OrderedDict()
    for it in resultado["items"]:
        clave = it["prioridad"] if agrupar == "prioridad" else "Sin priorizar"
        clave = clave if clave in FASES_PRIORIDAD else "Sin priorizar"
        f = fases.setdefault(clave, {"roles": {}, "dev_horas": 0.0, "perfiles": {}})
        roles = dict(it["roles_horas"])
        if escenario == "con_ia":
            roles["desarrollo"] = it["horas_dev_con_ia"]
        for rol, h in roles.items():
            f["roles"][rol] = f["roles"].get(rol, 0.0) + h
        f["dev_horas"] += roles["desarrollo"]
        p = perfil_por_item.get(it["id"], "mixto")
        f["perfiles"][p] = f["perfiles"].get(p, 0.0) + roles["desarrollo"]

    # PM global -> prorrateado por horas de equipo de cada fase
    eq_total = sum(sum(f["roles"].values()) for f in fases.values())
    for f in fases.values():
        f["roles"]["project_manager"] = tot["horas_pm"] * sum(f["roles"].values()) / eq_total

    # Cuadrar exactamente con el total del motor (evita diferencias por redondeo por ítem)
    objetivo = tot["horas_totales"]
    actual = sum(sum(f["roles"].values()) for f in fases.values())
    for f in fases.values():
        for rol in f["roles"]:
            f["roles"][rol] *= objetivo / actual

    orden = [k for k in FASES_PRIORIDAD if k in fases]
    salida = []
    over = cfg.get("roles", {})
    comunes = {k: cfg.get(k, d) for k, d in
               [("base_operacion", "Colombia"), ("nivel_ingles", "Nativo"), ("disponibilidad", "Horario Oficina")]}
    for clave in orden:
        f = fases[clave]
        dias = max(1, math.ceil(round(f["dev_horas"] / (n_dev * h_ef), 6)))
        filas = []
        for rol in ORDEN_ROLES:
            h = f["roles"].get(rol, 0.0) * factor_p80 * factor_modo
            if h <= 0.05:
                continue
            if rol == "desarrollo":
                perfil = max(f["perfiles"], key=f["perfiles"].get)
                tax = dict(over.get("desarrollo", {}).get(perfil) or ROLES_DEFECTO["desarrollo"].get(perfil)
                           or ROLES_DEFECTO["desarrollo"]["mixto"])
                recursos = n_dev
            else:
                tax = dict(over.get(rol) or ROLES_DEFECTO[rol])
                recursos = 1
            recursos = max(recursos, math.ceil(round(h / (dias * jornada), 6)))
            asignacion = h / (dias * jornada * recursos)
            fila = {"rol": rol, "horas": h, "recursos": recursos, "dias": dias,
                    "asignacion": round(asignacion, 6), **comunes, **tax}
            filas.append(fila)
        salida.append({"clave": clave, "nombre": cfg.get("nombres_fase", {}).get(clave, FASES_PRIORIDAD[clave]),
                       "dias": dias, "filas": filas,
                       "horas": round(sum(x["horas"] for x in filas), 1)})
        for x in filas:
            x["horas"] = round(x["horas"], 1)
    return salida


# ------------------------------------------------------------------ escritura
def diligenciar(entrada_path, plantilla, salida, escenario="tradicional"):
    entrada = json.load(open(entrada_path, encoding="utf-8"))
    cfg = entrada.get("taxonomia_bancolombia", {})
    resultado = motor.calcular(entrada)
    advertencias = []
    listas = leer_listas(plantilla)
    fases = armar_fases(entrada, resultado, escenario, cfg, advertencias)

    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(plantilla) as z:
        z.extractall(tmp)
        nombres = z.namelist()

    # localizar hoja
    wb_xml = etree.parse(os.path.join(tmp, "xl/workbook.xml"))
    rels = etree.parse(os.path.join(tmp, "xl/_rels/workbook.xml.rels"))
    rid = None
    for sh in wb_xml.getroot().iter(N + "sheet"):
        if sh.get("name") == HOJA:
            rid = sh.get("{%s}id" % REL_NS)
    if rid is None:
        raise SystemExit(f"No se encontró la hoja '{HOJA}'")
    target = [r.get("Target") for r in rels.getroot() if r.get("Id") == rid][0]
    sheet_path = os.path.join(tmp, "xl", target.lstrip("/").replace("xl/", ""))
    tree = etree.parse(sheet_path)
    root = tree.getroot()
    sd = root.find(N + "sheetData")
    rows = {int(r.get("r")): r for r in sd.findall(N + "row")}

    # ---- Ficha técnica / parametrización / condiciones
    ficha = cfg.get("ficha_tecnica", {})
    par = entrada.get("parametros", {})

    def put(ref, val, lista=None, numero=False):
        if val is None:
            return
        if lista and str(val) not in listas.get(lista, set()):
            advertencias.append(f"{ref}: '{val}' no está en la lista '{lista}' del formato; verifíquelo.")
        col, r = split_ref(ref)
        cell = get_cell(rows[r], ref)
        (set_num if numero else set_str)(cell, val)

    put("C8", ficha.get("cliente", "Bancolombia"), "cliente")
    put("C9", ficha.get("arquitecto_responsable"), "arquitecto_responsable")
    put("C10", ficha.get("nombre_proyecto", entrada.get("proyecto")))
    put("C11", ficha.get("url_sharepoint"))
    put("C12", ficha.get("id_jira"))
    put("C13", ficha.get("modelo_negocio"), "modelo_negocio")
    put("C14", ficha.get("modelo_adquisicion"), "modelo_adquisicion")
    put("C15", ficha.get("linea_servicio"), "linea_servicio")
    put("E8", "Días", "unidad_tiempo")
    put("E9", float(cfg.get("horas_por_dia", par.get("jornada_horas", 8.4))), numero=True)
    put("E10", sum(f["dias"] for f in fases), numero=True)
    put("E12", ficha.get("version_preventa", 1), numero=True)
    if ficha.get("fecha_preventa"):
        from datetime import date
        d = date.fromisoformat(ficha["fecha_preventa"])
        serial = (d - date(1899, 12, 30)).days
        put("E13", serial, numero=True)
    put("G8", ficha.get("poliza", "Ninguna"), "poliza")

    # ---- plantillas de bloque
    tpl = {k: copy.deepcopy(rows[v]) for k, v in
           dict(titulo=T_TITULO, servicio=T_SERVICIO, hdr1=T_HDR1, hdr2=T_HDR2, rol=T_ROL, subtotal=T_SUBTOTAL).items()}
    for r_num in [r for r in rows if r >= PRIMERA_FILA_BLOQUES]:
        sd.remove(rows[r_num])

    # ---- construir bloques
    r = PRIMERA_FILA_BLOQUES
    merges, rangos_rol, subtotales = [], [], []
    esc_txt = "Estimación tradicional" if escenario == "tradicional" else "Estimación con aceleración IA (SDD)"
    for i, fase in enumerate(fases, 1):
        t = clone_row(tpl["titulo"], r)
        set_str(get_cell(t, f"B{r}"), f"ESCENARIO {i} - {fase['nombre']} - {fase['dias']} días")
        sd.append(t)
        s = clone_row(tpl["servicio"], r + 1)
        set_str(get_cell(s, f"B{r + 1}"), cfg.get("nombre_servicio", entrada.get("proyecto", "")) + f" · {esc_txt}")
        sd.append(s)
        h1, h2 = r + 2, r + 3
        sd.append(clone_row(tpl["hdr1"], h1))
        sd.append(clone_row(tpl["hdr2"], h2))
        merges += [f"F{h1}:H{h1}", f"J{h1}:L{h1}", f"M{h1}:N{h1}", f"O{h1}:O{h2}"]
        primera = r + 4
        for k, fila in enumerate(fase["filas"]):
            rr = primera + k
            row = clone_row(tpl["rol"], rr)
            strip_values(row, list("BCDEFGHIJKLMNOQR"))
            put_row = lambda col, v, num=False: (set_num if num else set_str)(get_cell(row, f"{col}{rr}"), v)
            put_row("B", fila["familia_trabajo"]); put_row("C", fila["familia_cargo"]); put_row("D", fila["cargo"])
            put_row("E", fila["seniority"]); put_row("F", fila["base_operacion"]); put_row("G", fila["nivel_ingles"])
            put_row("H", fila["disponibilidad"])
            put_row("J", fila["recursos"], True); put_row("K", fila["asignacion"], True); put_row("L", fila["dias"], True)
            set_formula(get_cell(row, f"M{rr}"), f"(L{rr}*$E$9)*J{rr}")
            set_formula(get_cell(row, f"O{rr}"), f"SUM(M{rr}:N{rr},I{rr})*K{rr}")
            set_formula(get_cell(row, f"Q{rr}"), f"L{rr}/10")
            set_formula(get_cell(row, f"R{rr}"), f"L{rr}/20")
            trip = (fila["familia_trabajo"], fila["familia_cargo"], fila["cargo"])
            if trip not in listas["roles"]:
                advertencias.append(f"Fila {rr}: combinación de rol {trip} no existe en 'Parametrización Roles'.")
            for campo, lista in [("seniority", "seniority"), ("base_operacion", "base_operacion"),
                                 ("nivel_ingles", "nivel_ingles"), ("disponibilidad", "disponibilidad")]:
                if fila[campo] not in listas[lista]:
                    advertencias.append(f"Fila {rr}: '{fila[campo]}' no está en la lista '{lista}'.")
            sd.append(row)
        ultima = primera + len(fase["filas"]) - 1
        rangos_rol.append((primera, ultima))
        st = clone_row(tpl["subtotal"], ultima + 1)
        set_formula(get_cell(st, f"O{ultima + 1}"), f"SUM(O{primera}:O{ultima})")
        sd.append(st)
        subtotales.append(ultima + 1)
        fase["fila_subtotal"] = ultima + 1
        r = ultima + 2 + ESPACIO_ENTRE_BLOQUES

    # ---- Esfuerzo total
    set_formula(get_cell(rows[11], "E11"), "+".join(f"O{x}" for x in subtotales))

    # ---- merges
    mc = root.find(N + "mergeCells")
    for m in list(mc):
        top = split_ref(m.get("ref").split(":")[0])[1]
        if top >= PRIMERA_FILA_BLOQUES:
            mc.remove(m)
    for ref in merges:
        etree.SubElement(mc, N + "mergeCell", ref=ref)
    mc.set("count", str(len(mc)))

    # ---- validaciones de lista (x14) sobre las columnas de rol
    def union(col):
        return " ".join(f"{col}{a}:{col}{b}" for a, b in rangos_rol)
    for sq in root.iter("{http://schemas.microsoft.com/office/excel/2006/main}sqref"):
        m = re.match(r"([A-Z])\d+:[A-Z]\d+", sq.text or "")
        if m and m.group(1) in "BCDEF" and split_ref(sq.text.split(":")[0])[1] >= PRIMERA_FILA_BLOQUES:
            sq.text = union(m.group(1))

    # ---- dimensión
    dim = root.find(N + "dimension")
    dim.set("ref", f"B2:R{subtotales[-1]}")

    tree.write(sheet_path, xml_declaration=True, encoding="UTF-8", standalone=True)

    # ---- forzar recálculo al abrir y eliminar calcChain (Excel lo reconstruye)
    wbp = os.path.join(tmp, "xl/workbook.xml")
    w = open(wbp, encoding="utf-8").read()
    w = re.sub(r"<calcPr([^>]*)/>", lambda m: "<calcPr" + re.sub(r'\s*fullCalcOnLoad="[^"]*"', "", m.group(1))
               + ' fullCalcOnLoad="1"/>', w, count=1)
    open(wbp, "w", encoding="utf-8").write(w)
    cc = os.path.join(tmp, "xl/calcChain.xml")
    if os.path.exists(cc):
        os.remove(cc)
        rp = os.path.join(tmp, "xl/_rels/workbook.xml.rels")
        t_ = open(rp, encoding="utf-8").read()
        t_ = re.sub(r"<Relationship [^>]*calcChain[^>]*/>", "", t_)
        open(rp, "w", encoding="utf-8").write(t_)
        ctp = os.path.join(tmp, "[Content_Types].xml")
        t_ = open(ctp, encoding="utf-8").read()
        t_ = re.sub(r'<Override [^>]*calcChain[^>]*/>', "", t_)
        open(ctp, "w", encoding="utf-8").write(t_)

    if os.path.exists(salida):
        os.remove(salida)
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        for name in nombres:
            p = os.path.join(tmp, name)
            if os.path.exists(p):
                z.write(p, name)
    shutil.rmtree(tmp)

    total = round(sum(f["horas"] for f in fases), 1)
    tot = resultado["tradicional"] if escenario == "tradicional" else resultado["con_ia"]
    resumen = {
        "archivo": salida, "escenario": escenario,
        "cifra": cfg.get("cifra", "mas_probable"), "modo_horas": cfg.get("modo_horas", "esfuerzo"),
        "esfuerzo_total_formato_h": total,
        "esfuerzo_motor_mas_probable_h": tot["horas_totales"],
        "esfuerzo_motor_p80_h": tot["rango"]["comprometido_p80"],
        "margen_p80_para_costos_y_riesgos_h": round(tot["rango"]["comprometido_p80"] - tot["horas_totales"], 1),
        "fases": [{"nombre": f["nombre"], "dias": f["dias"], "horas": f["horas"], "fila_subtotal": f["fila_subtotal"],
                   "roles": [{k: x[k] for k in ("cargo", "seniority", "recursos", "asignacion", "dias", "horas")}
                             for x in f["filas"]]} for f in fases],
        "advertencias": advertencias,
    }
    return resumen


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("plantilla")
    ap.add_argument("salida")
    ap.add_argument("--escenario", default="tradicional", choices=["tradicional", "con_ia"])
    a = ap.parse_args()
    print(json.dumps(diligenciar(a.entrada, a.plantilla, a.salida, a.escenario), ensure_ascii=False, indent=2))
