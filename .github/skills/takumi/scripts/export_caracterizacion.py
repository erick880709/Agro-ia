# -*- coding: utf-8 -*-
"""Genera el .xlsx oficial de caracterización de proceso a partir de un PROC-###.md.

Mapeo de celdas verificado a mano contra
`resources/procesos/templates/BUREAU_plantilla_[Formato caracterización de procesos].xlsx`
(hoja "Caracterización"). Si el cliente reemplaza esa plantilla, este mapeo debe re-verificarse
(ver SKILL.md, Gotchas).
"""
import os
import sys

import openpyxl

sys.path.insert(0, os.path.dirname(__file__))
from common import (  # noqa: E402
    BORRADOR_TEXT,
    extract_bold_field,
    extract_bullets,
    extract_firmas,
    insert_rows_and_shift_merges,
    is_validado,
    rows_from_table,
)
from md_parser import get_section, parse_md_file  # noqa: E402

TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "resources", "procesos", "templates",
    "BUREAU_plantilla_[Formato caracterización de procesos].xlsx",
)
TEMPLATE_PATH = os.path.normpath(TEMPLATE_PATH)


def _ensure_row_capacity(ws, first_data_row, last_preallocated_row, needed_count, merge_col_specs):
    """Si needed_count > filas preasignadas, inserta filas extra ANTES de last_preallocated_row+1,
    clonando el patrón de merges de la última fila (merge_col_specs: lista de (col_ini, col_fin)).

    Devuelve cuántas filas se insertaron (0 si no hizo falta) — quien llama debe sumar este valor a
    todas las referencias de fila que usen DESPUÉS de este punto, porque todo lo que estaba debajo
    de `last_preallocated_row` se corrió hacia abajo esa misma cantidad.
    """
    available = last_preallocated_row - first_data_row + 1
    if needed_count <= available:
        return 0
    extra = needed_count - available
    insert_at = last_preallocated_row + 1
    insert_rows_and_shift_merges(ws, insert_at, extra)
    for offset in range(extra):
        row = insert_at + offset
        for col_ini, col_fin in merge_col_specs:
            if col_fin > col_ini:
                ws.merge_cells(start_row=row, start_column=col_ini, end_row=row,
                                end_column=col_fin)
    return extra


def export_caracterizacion(md_path, output_path=None):
    parsed = parse_md_file(md_path)
    fm = parsed["front_matter"]
    warnings = []

    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    ws = wb["Caracterización"]

    ws["H2"] = fm.get("codigo") or "[PENDIENTE]"
    ws["H3"] = fm.get("version", "")
    ws["H4"] = fm.get("fecha", "")

    ws["B7"] = fm.get("macroproceso", "")
    ws["B8"] = fm.get("proceso", "")
    ws["B9"] = fm.get("tipo_proceso", "")

    desc = get_section(parsed, "Descripcion del proceso", "Descripción del proceso") or {}
    objeto = extract_bold_field(desc.get("texto", ""), "Objeto")
    responsable = fm.get("responsable", "")
    ws["A12"] = f"OBJETO: {objeto}" if objeto else ws["A12"].value
    ws["A13"] = f"RESPONSABLE(S): {responsable}" if responsable else ws["A13"].value

    recursos = get_section(parsed, "Recursos") or {}
    recursos_map = {}
    if recursos.get("tablas"):
        for row in rows_from_table(recursos["tablas"][0]):
            if len(row) >= 2:
                recursos_map[row[0].strip().lower()] = row[1]
    ws["C16"] = recursos_map.get("tecnológicos", recursos_map.get("tecnologicos", ""))
    ws["C17"] = recursos_map.get("infraestructura", "")
    ws["C18"] = recursos_map.get("humano", "")
    ws["C19"] = recursos_map.get("servicios", "")
    procesos_apoyo = extract_bold_field(recursos.get("texto", ""), "Procesos de apoyo")
    ws["E15"] = f"PROCESOS DE APOYO\n{procesos_apoyo}" if procesos_apoyo else ws["E15"].value

    control = get_section(parsed, "Control y medicion del proceso", "Control y medición del proceso") or {}
    tablas_control = control.get("tablas", [])
    indicadores = rows_from_table(tablas_control[0]) if len(tablas_control) > 0 else []
    mecanismos = rows_from_table(tablas_control[1]) if len(tablas_control) > 1 else []
    n_needed = max(len(indicadores), len(mecanismos), 1)
    offset = _ensure_row_capacity(ws, 24, 26, n_needed, [(4, 7)])
    for i in range(n_needed):
        r = 24 + i
        if i < len(indicadores) and len(indicadores[i]) >= 3:
            ws.cell(row=r, column=1, value=indicadores[i][0])
            ws.cell(row=r, column=2, value=indicadores[i][1])
            ws.cell(row=r, column=3, value=indicadores[i][2])
        if i < len(mecanismos) and len(mecanismos[i]) >= 1:
            texto_mecanismo = " / ".join(c for c in mecanismos[i][:2] if c)
            ws.cell(row=r, column=4, value=texto_mecanismo)

    sipoc = get_section(parsed, "Flujo SIPOC") or {}
    sipoc_rows = rows_from_table(sipoc["tablas"][0]) if sipoc.get("tablas") else []
    sipoc_rows = [r for r in sipoc_rows if any(c.strip() for c in r)]
    # Fila 33 (en la plantilla original) es un divisor de ancho completo (A33:G33 fusionada) antes
    # de "DOCUMENTOS ASOCIADOS", no una fila de datos — las filas de datos reales pre-asignadas son
    # 29-32; se suma `offset` porque la sección de indicadores/mecanismos pudo haber insertado filas
    # arriba y corrido todo esto hacia abajo.
    sipoc_first = 29 + offset
    sipoc_last_prealloc = 32 + offset
    offset += _ensure_row_capacity(ws, sipoc_first, sipoc_last_prealloc, max(len(sipoc_rows), 1), [])
    for i, row in enumerate(sipoc_rows):
        r = sipoc_first + i
        for col in range(min(7, len(row))):
            ws.cell(row=r, column=col + 1, value=row[col])

    docs_section = get_section(parsed, "Documentos asociados") or {}
    docs_texto = docs_section.get("texto", "")
    internos_block, _, externos_block = docs_texto.partition("**Otros documentos aplicables")
    internos = extract_bullets(internos_block)
    externos = extract_bullets(externos_block)
    n_docs = max(len(internos), len(externos), 1)
    docs_first = 35 + offset
    docs_last_prealloc = 43 + offset
    offset += _ensure_row_capacity(ws, docs_first, docs_last_prealloc, n_docs, [(1, 3), (4, 7)])
    for i in range(n_docs):
        r = docs_first + i
        if i < len(internos):
            ws.cell(row=r, column=1, value=internos[i])
        if i < len(externos):
            ws.cell(row=r, column=4, value=externos[i])

    cambios = get_section(parsed, "Control de cambios") or {}
    cambios_rows = rows_from_table(cambios["tablas"][0]) if cambios.get("tablas") else []
    # La fila real de "CONTROL DE CAMBIOS" se desplaza si se insertaron filas arriba (indicadores/
    # mecanismos, SIPOC o documentos asociados crecieron más allá de lo pre-asignado) — se busca en
    # vez de asumir un offset fijo.
    control_header_row = None
    for r in range(46, ws.max_row + 1):
        if str(ws.cell(row=r, column=1).value or "").strip().upper() == "CONTROL DE CAMBIOS":
            control_header_row = r
            break
    data_start = (control_header_row or 46) + 2
    _ensure_row_capacity(ws, data_start, data_start + 1, max(len(cambios_rows), 1), [(3, 7)])
    for i, row in enumerate(cambios_rows):
        r = data_start + i
        if len(row) >= 3:
            ws.cell(row=r, column=1, value=row[0])
            ws.cell(row=r, column=2, value=row[1])
            ws.cell(row=r, column=3, value=row[2])

    firma_row = None
    for r in range(data_start, ws.max_row + 1):
        if str(ws.cell(row=r, column=1).value or "").strip().upper() == "ELABORÓ":
            firma_row = r + 1
            break
    elaboro, reviso, aprobo = extract_firmas(cambios.get("texto", ""))
    if firma_row:
        ws.cell(row=firma_row, column=1, value=elaboro or "[PENDIENTE]")
        ws.cell(row=firma_row, column=3, value=reviso or "[PENDIENTE]")
        ws.cell(row=firma_row, column=5, value=aprobo or "[PENDIENTE]")

    if not is_validado(fm):
        # Se inserta AL FINAL: insert_rows desplaza los VALORES ya escritos correctamente, y
        # insert_rows_and_shift_merges corre también los merges de todo lo que ya se llenó arriba.
        insert_rows_and_shift_merges(ws, 5, 1)
        ws.merge_cells(start_row=5, start_column=1, end_row=5, end_column=7)
        ws.cell(row=5, column=1, value=BORRADOR_TEXT)

    out_path = output_path or (os.path.splitext(md_path)[0] + ".xlsx")
    wb.save(out_path)
    return {"output": out_path, "warnings": warnings}


if __name__ == "__main__":
    result = export_caracterizacion(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("OK ->", result["output"])
    for w in result["warnings"]:
        print("WARN:", w)
