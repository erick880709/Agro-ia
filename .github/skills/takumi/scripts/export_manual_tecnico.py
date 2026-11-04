# -*- coding: utf-8 -*-
"""Genera el .docx oficial de manual técnico a partir de un DOC-###.md (tipo_documento: Manual tecnico).

Mapeo verificado a mano contra
`resources/procesos/templates/BUREAU_plantilla_[Formato manual técnico]_.docx`.
"""
import os
import sys

import docx

sys.path.insert(0, os.path.dirname(__file__))
from common import (  # noqa: E402
    BORRADOR_TEXT,
    extract_firmas,
    fill_table_data_rows,
    find_table_by_header,
    insert_paragraph_before,
    is_validado,
    replace_section_paragraphs,
    resolve_header_table_cell,
    rows_from_table,
    section_text_to_lines,
    set_cell_text,
)
from md_parser import get_section, parse_md_file  # noqa: E402

TEMPLATE_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "resources", "procesos", "templates",
    "BUREAU_plantilla_[Formato manual técnico]_.docx",
))


def _desarrollo_lines(desarrollo_section):
    lines = section_text_to_lines(desarrollo_section.get("texto", ""))
    for tabla in desarrollo_section.get("tablas", []):
        for row in rows_from_table(tabla):
            paso, descripcion, responsable = (row + [""] * 3)[:3]
            lines.append(f"- {paso}: {descripcion} (Responsable: {responsable})".strip())
    return lines


def export_manual_tecnico(md_path, output_path=None):
    parsed = parse_md_file(md_path)
    fm = parsed["front_matter"]
    warnings = []

    doc = docx.Document(TEMPLATE_PATH)

    for label in ("Código", "Versión", "Fecha"):
        cell = resolve_header_table_cell(doc, label)
        if cell is not None:
            key = {"Código": "codigo", "Versión": "version", "Fecha": "fecha"}[label]
            default = "[PENDIENTE]" if key == "codigo" else ""
            set_cell_text(cell, str(fm.get(key) or default))

    objeto = get_section(parsed, "Objeto") or {}
    alcance = get_section(parsed, "Alcance") or {}
    definiciones = get_section(parsed, "Definiciones") or {}
    condiciones = get_section(parsed, "Condiciones generales") or {}
    desarrollo = get_section(parsed, "Desarrollo") or {}

    ok = True
    ok &= replace_section_paragraphs(
        doc, r"^OBJETO\s*$", r"^ALCANCE\s*$",
        section_text_to_lines(objeto.get("texto", "")) or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^ALCANCE\s*$", r"^DEFINICIONES\s*$",
        section_text_to_lines(alcance.get("texto", "")) or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^DEFINICIONES\s*$", r"^CONDICIONES GENERALES\s*$",
        section_text_to_lines(definiciones.get("texto", "")) or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^CONDICIONES GENERALES\s*$", r"^DESARROLLO\s*$",
        section_text_to_lines(condiciones.get("texto", "")) or ["[PENDIENTE]"],
    )
    desarrollo_lines = _desarrollo_lines(desarrollo)
    diagrama = get_section(parsed, "Diagrama") or {}
    if diagrama.get("mermaid"):
        slug = os.path.splitext(os.path.basename(md_path))[0]
        desarrollo_lines = desarrollo_lines + [
            f"Ver diagrama BPMN en el archivo adjunto {slug}.bpmn, importable en Bizagi Modeler."
        ]
    ok &= replace_section_paragraphs(
        doc, r"^DESARROLLO\s*$", r"^CONTROL DE CAMBIOS\s*$",
        desarrollo_lines or ["[PENDIENTE]"],
    )
    if not ok:
        warnings.append("No se encontraron todos los encabezados esperados — revisar plantilla.")

    cambios = get_section(parsed, "Control de cambios") or {}
    cambios_rows = rows_from_table(cambios["tablas"][0]) if cambios.get("tablas") else []
    tabla_cambios = find_table_by_header(doc, ["VERSIÓN", "FECHA", "DESCRIPCIÓN DE LA ACTUALIZACIÓN"])
    if tabla_cambios is not None and cambios_rows:
        def _set_cambios_row(row, data):
            version, fecha, razon = (data + [""] * 3)[:3]
            set_cell_text(row.cells[0], version)
            set_cell_text(row.cells[1], fecha)
            set_cell_text(row.cells[2], razon)

        fill_table_data_rows(tabla_cambios, cambios_rows, _set_cambios_row)

    elaboro, reviso, aprobo = extract_firmas(cambios.get("texto", ""))
    tabla_aprobacion = find_table_by_header(doc, ["ELABORÓ", "REVISÓ", "APROBÓ"])
    if tabla_aprobacion is not None:
        row = tabla_aprobacion.rows[1]
        set_cell_text(row.cells[0], elaboro or "[PENDIENTE]")
        set_cell_text(row.cells[1], reviso or "[PENDIENTE]")
        set_cell_text(row.cells[2], aprobo or "[PENDIENTE]")

    if not is_validado(fm) and doc.paragraphs:
        insert_paragraph_before(doc.paragraphs[0], BORRADOR_TEXT, bold=True)

    out_path = output_path or (os.path.splitext(md_path)[0] + ".docx")
    doc.save(out_path)
    return {"output": out_path, "warnings": warnings}


if __name__ == "__main__":
    result = export_manual_tecnico(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("OK ->", result["output"])
    for w in result["warnings"]:
        print("WARN:", w)
