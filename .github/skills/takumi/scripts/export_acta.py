# -*- coding: utf-8 -*-
"""Genera el .docx oficial de acta de reunión a partir de un ACTA-###.md.

Mapeo verificado a mano contra
`resources/procesos/templates/BUREAU_FR_PM_MC_01_[Formato acta].docx` (9 tablas fijas).
"""
import os
import sys

import docx

sys.path.insert(0, os.path.dirname(__file__))
from common import (  # noqa: E402
    BORRADOR_TEXT,
    extract_firmas,
    extract_inline_field,
    fill_table_data_rows,
    find_table_by_header,
    is_validado,
    rows_from_table,
    set_cell_text,
)
from md_parser import (  # noqa: E402
    get_section,
    parse_front_matter,
    parse_md_file,
    parse_preamble,
    strip_md_emphasis,
)

TEMPLATE_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "resources", "procesos", "templates",
    "BUREAU_FR_PM_MC_01_[Formato acta].docx",
))


def _fill_item_table(doc, title, rows, ncols):
    """Filas de datos empiezan en el índice 2 (0=título, 1=encabezado Ítem/Tema/…)."""
    table = find_table_by_header(doc, [title])
    if table is None or not rows:
        return

    def _set_row(row, data):
        cells = (data + [""] * ncols)[:ncols]
        for c, val in enumerate(cells):
            set_cell_text(row.cells[c], val)

    fill_table_data_rows(table, rows, _set_row, first_data_row=2)


def export_acta(md_path, output_path=None):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    fm, body = parse_front_matter(text)
    preambulo = parse_preamble(body)
    warnings = []

    doc = docx.Document(TEMPLATE_PATH)
    # El código/versión/fecha de este formato (FR-PM-MC-01) son fijos de la plantilla — no se
    # sobreescriben, a diferencia de los demás tipos de documento que sí traen código propio.

    numero_acta = fm.get("id", "[PENDIENTE]")
    fecha = fm.get("fecha", "")
    hora = extract_inline_field(preambulo["texto"], "Hora")
    lugar = extract_inline_field(preambulo["texto"], "Lugar")
    elaborado_por = extract_inline_field(preambulo["texto"], "Elaborado por") or extract_inline_field(
        preambulo["texto"], "Elaboro"
    )
    objetivo = extract_inline_field(preambulo["texto"], "Objetivo de la reunion") or extract_inline_field(
        preambulo["texto"], "Objetivo de la reunión"
    )
    asistentes_rows = rows_from_table(preambulo["tablas"][0]) if preambulo.get("tablas") else []
    asistentes_texto = "; ".join(
        f"{r[0]} ({r[1]})" if len(r) > 1 and r[1] else r[0] for r in asistentes_rows if r and r[0]
    )

    tabla0 = doc.tables[0]
    set_cell_text(tabla0.rows[0].cells[0], f"Número de acta: {numero_acta}")
    set_cell_text(tabla0.rows[1].cells[0], f"Fecha: {fecha}")
    set_cell_text(tabla0.rows[2].cells[1], hora or "[PENDIENTE]")
    set_cell_text(tabla0.rows[3].cells[1], lugar or "[PENDIENTE]")
    set_cell_text(tabla0.rows[4].cells[1], elaborado_por or "[PENDIENTE]")
    set_cell_text(tabla0.rows[5].cells[1], objetivo or "[PENDIENTE]")
    set_cell_text(tabla0.rows[6].cells[1], asistentes_texto or "[PENDIENTE]")

    parsed = parse_md_file(md_path)

    agenda_section = get_section(parsed, "Agenda") or {}
    _fill_item_table(
        doc, "Agenda (Orden del día)",
        rows_from_table(agenda_section["tablas"][0]) if agenda_section.get("tablas") else [],
        2,
    )

    compromisos_ant = get_section(parsed, "Compromisos del acta anterior") or {}
    _fill_item_table(
        doc, "Compromisos del acta anterior",
        rows_from_table(compromisos_ant["tablas"][0]) if compromisos_ant.get("tablas") else [],
        4,
    )

    desarrollo = get_section(parsed, "Desarrollo tematico", "Desarrollo temático") or {}
    tabla_desarrollo = find_table_by_header(doc, ["Desarrollo temático"])
    if tabla_desarrollo is not None:
        texto = strip_md_emphasis(desarrollo.get("texto", "")).strip()
        set_cell_text(tabla_desarrollo.rows[1].cells[0], texto or "[PENDIENTE]")

    documentos = get_section(parsed, "Documentos anexos") or {}
    _fill_item_table(
        doc, "Documentos anexos",
        rows_from_table(documentos["tablas"][0]) if documentos.get("tablas") else [],
        2,
    )

    acuerdos = get_section(parsed, "Acuerdos o compromisos") or {}
    _fill_item_table(
        doc, "Acuerdos o compromisos",
        rows_from_table(acuerdos["tablas"][0]) if acuerdos.get("tablas") else [],
        4,
    )

    proxima = get_section(parsed, "Proxima reunion", "Próxima reunión") or {}
    tabla_proxima = find_table_by_header(doc, ["Próxima reunión"])
    if tabla_proxima is not None:
        fecha_proxima = extract_inline_field(proxima.get("texto", ""), "Fecha")
        set_cell_text(tabla_proxima.rows[1].cells[1], fecha_proxima or "No se acordó")

    cambios = get_section(parsed, "Control de cambios") or {}
    cambios_rows = rows_from_table(cambios["tablas"][0]) if cambios.get("tablas") else []
    tabla_cambios = find_table_by_header(doc, ["VERSIÓN", "FECHA", "DESCRIPCIÓN DE LA ACTUALIZACIÓN"])
    if tabla_cambios is not None and cambios_rows:
        def _set_cambios_row(row, data):
            version, fecha_c, razon = (data + [""] * 3)[:3]
            set_cell_text(row.cells[0], version)
            set_cell_text(row.cells[1], fecha_c)
            set_cell_text(row.cells[2], razon)

        fill_table_data_rows(tabla_cambios, cambios_rows, _set_cambios_row)

    elaboro, reviso, aprobo = extract_firmas(cambios.get("texto", ""))
    tabla_aprobacion = find_table_by_header(doc, ["ELABORÓ", "REVISÓ", "APROBÓ"])
    if tabla_aprobacion is not None and (elaboro or reviso or aprobo):
        row = tabla_aprobacion.rows[1]
        set_cell_text(row.cells[0], elaboro or "[PENDIENTE]")
        set_cell_text(row.cells[1], reviso or "[PENDIENTE]")
        set_cell_text(row.cells[2], aprobo or "[PENDIENTE]")
    elif tabla_aprobacion is not None:
        warnings.append(
            "El acta no trae Elaboró/Revisó/Aprobó explícitos — se dejaron los firmantes por "
            "defecto de la plantilla; confirmar si aplican a esta reunión."
        )

    if not is_validado(fm):
        # El acta empieza directo con una tabla (sin párrafo previo) — a diferencia de los demás
        # tipos de documento, aquí no hay un `doc.paragraphs[0]` útil como ancla al inicio real del
        # cuerpo; se ancla directo antes de la primera tabla.
        watermark = doc.add_paragraph()
        run = watermark.add_run(BORRADOR_TEXT)
        run.bold = True
        doc.tables[0]._tbl.addprevious(watermark._p)

    out_path = output_path or (os.path.splitext(md_path)[0] + ".docx")
    doc.save(out_path)
    return {"output": out_path, "warnings": warnings}


if __name__ == "__main__":
    result = export_acta(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("OK ->", result["output"])
    for w in result["warnings"]:
        print("WARN:", w)
