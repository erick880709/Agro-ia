# -*- coding: utf-8 -*-
"""Genera el .docx oficial de política a partir de un DOC-###.md (tipo_documento: Politica).

Mapeo verificado a mano contra `resources/procesos/templates/BUREAU_plantilla_[Formato politica].docx`.

**Discrepancia conocida** (ver plan de la Fase 2 / SKILL.md Gotchas): a diferencia de todos los demás
formatos del proyecto, esta plantilla NO trae tablas de "CONTROL DE CAMBIOS"/"APROBACIÓN" en el cuerpo.
Se agregan aquí clonando la estructura de esas tablas desde la plantilla de "Documento de apoyo" (que sí
las trae) — no es una decisión de la skill, es hacer que el documento quede completo; si el cliente
prefiere que la política no lleve esas tablas, avisarlo (queda registrado como warning de salida).
"""
import copy
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

TEMPLATES_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "resources", "procesos", "templates",
))
TEMPLATE_PATH = os.path.join(TEMPLATES_DIR, "BUREAU_plantilla_[Formato politica].docx")
DONOR_TEMPLATE_PATH = os.path.join(TEMPLATES_DIR, "BUREAU_plantilla_[Documento de apoyo].docx")


def _append_cambios_y_aprobacion_tables(doc, warnings):
    """La plantilla de política no trae estas tablas — se clonan desde la de documento de apoyo."""
    existing = find_table_by_header(doc, ["VERSIÓN", "FECHA", "DESCRIPCIÓN DE LA ACTUALIZACIÓN"])
    if existing is not None:
        return
    warnings.append(
        "La plantilla oficial de política no trae tablas de Control de cambios/Aprobación en el "
        "cuerpo — se agregaron clonándolas de la plantilla de Documento de apoyo. Confirmar con el "
        "cliente si esto es lo esperado."
    )
    donor = docx.Document(DONOR_TEMPLATE_PATH)
    cambios_el = find_table_by_header(donor, ["VERSIÓN", "FECHA", "DESCRIPCIÓN DE LA ACTUALIZACIÓN"])._tbl
    aprobacion_el = find_table_by_header(donor, ["ELABORÓ", "REVISÓ", "APROBÓ"])._tbl
    import copy

    heading1 = doc.add_paragraph("CONTROL DE CAMBIOS")
    heading1._p.addnext(copy.deepcopy(cambios_el))
    heading2 = doc.add_paragraph("APROBACIÓN DEL DOCUMENTO")
    heading2._p.addnext(copy.deepcopy(aprobacion_el))


def export_politica(md_path, output_path=None):
    parsed = parse_md_file(md_path)
    fm = parsed["front_matter"]
    warnings = []

    doc = docx.Document(TEMPLATE_PATH)

    for label, key, default in (("Código", "codigo", "[PENDIENTE]"), ("Versión", "version", ""), ("Fecha", "fecha", "")):
        cell = resolve_header_table_cell(doc, label)
        if cell is not None:
            set_cell_text(cell, str(fm.get(key) or default))

    objeto = get_section(parsed, "Objeto") or {}
    alcance = get_section(parsed, "Alcance") or {}
    politica = get_section(parsed, "Politica", "Política") or {}

    ok = True
    ok &= replace_section_paragraphs(
        doc, r"^OBJETO:?\s*$", r"^ALCANCE:?\s*$",
        section_text_to_lines(objeto.get("texto", "")) or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^ALCANCE:?\s*$", r"^POL[IÍ]TICA\s*$",
        section_text_to_lines(alcance.get("texto", "")) or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^POL[IÍ]TICA\s*$", r"(?!)",
        section_text_to_lines(politica.get("texto", "")) or ["[PENDIENTE]"],
    )
    if not ok:
        warnings.append("No se encontraron todos los encabezados esperados (OBJETO/ALCANCE/POLÍTICA) — revisar plantilla.")

    _append_cambios_y_aprobacion_tables(doc, warnings)

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
    result = export_politica(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("OK ->", result["output"])
    for w in result["warnings"]:
        print("WARN:", w)
