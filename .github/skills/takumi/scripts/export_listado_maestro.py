# -*- coding: utf-8 -*-
"""Regenera el .xlsx oficial de un listado maestro de documentos a partir de su espejo en
`resources/procesos/00-listado-maestro-documentos-internos.md` / `-externos.md`.

El `.md` es la fuente de verdad una vez que la skill lo mantiene (ver `SKILL.md`, Paso 7b) — este
script solo reescribe la copia `.xlsx` oficial a partir de él; nunca al revés, y nunca toca el
archivo de `templates/`.
"""
import os
import re
import sys

import openpyxl

sys.path.insert(0, os.path.dirname(__file__))
from md_parser import strip_md_emphasis  # noqa: E402

TEMPLATES_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "resources", "procesos", "templates",
))
RESOURCES_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "resources", "procesos",
))


def _extract_md_table(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = [l for l in text.splitlines() if l.strip().startswith("|")]
    rows = []
    for line in lines:
        cells = [strip_md_emphasis(c.strip()) for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else []  # sin encabezado


def sync_listado_interno(output_path=None):
    md_path = os.path.join(RESOURCES_DIR, "00-listado-maestro-documentos-internos.md")
    template_path = os.path.join(TEMPLATES_DIR, "Listado maestro de documentos internos.xlsx")
    rows = _extract_md_table(md_path)

    wb = openpyxl.load_workbook(template_path)
    ws = wb["Listado activos"]
    # Encabezado real en fila 5 (verificado a mano); los datos empiezan en la fila 6.
    for r in range(6, ws.max_row + 1):
        for c in range(1, 13):
            ws.cell(row=r, column=c, value=None)
    for i, row in enumerate(rows):
        cells = (row + [""] * 12)[:12]
        for c, val in enumerate(cells):
            ws.cell(row=6 + i, column=c + 1, value=val)

    out_path = output_path or os.path.join(RESOURCES_DIR, "00-listado-maestro-documentos-internos.xlsx")
    wb.save(out_path)
    return {"output": out_path, "filas": len(rows)}


def sync_listado_externo(output_path=None):
    md_path = os.path.join(RESOURCES_DIR, "00-listado-maestro-documentos-externos.md")
    template_path = os.path.join(
        TEMPLATES_DIR, "BUREAU_FR_PM_MC_03_formato listado maestro de documentos externos.xlsx"
    )
    rows = [r for r in _extract_md_table(md_path) if any(c for c in r)]

    wb = openpyxl.load_workbook(template_path)
    ws = wb.active
    # Encabezado real en fila 5 (verificado a mano); los datos empiezan en la fila 6.
    for r in range(6, ws.max_row + 1):
        for c in range(1, 9):
            ws.cell(row=r, column=c, value=None)
    for i, row in enumerate(rows):
        cells = (row + [""] * 8)[:8]
        for c, val in enumerate(cells):
            ws.cell(row=6 + i, column=c + 1, value=val)

    out_path = output_path or os.path.join(RESOURCES_DIR, "00-listado-maestro-documentos-externos.xlsx")
    wb.save(out_path)
    return {"output": out_path, "filas": len(rows)}


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "internos"
    result = sync_listado_interno() if target == "internos" else sync_listado_externo()
    print("OK ->", result["output"], f"({result['filas']} filas)")
