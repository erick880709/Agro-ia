# -*- coding: utf-8 -*-
"""Genera el .docx oficial de procedimiento-instructivo a partir de un PROC-###.md.

Mapeo verificado a mano contra
`resources/procesos/templates/BUREAU_plantilla_[Formato procedimiento-instructivo]_.docx`.
Si el cliente reemplaza esa plantilla, este mapeo debe re-verificarse (ver SKILL.md, Gotchas).
"""
import os
import sys

import docx

sys.path.insert(0, os.path.dirname(__file__))
from common import (  # noqa: E402
    BORRADOR_TEXT,
    extract_bullets,
    extract_field_lines,
    extract_firmas,
    fill_table_data_rows,
    find_table_by_header,
    insert_paragraph_before,
    is_validado,
    replace_section_paragraphs,
    resolve_header_table_cell,
    rows_from_table,
    set_cell_text,
)
from md_parser import get_section, parse_md_file  # noqa: E402

TEMPLATE_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "resources", "procesos", "templates",
    "BUREAU_plantilla_[Formato procedimiento-instructivo]_.docx",
))


def export_procedimiento(md_path, output_path=None):
    parsed = parse_md_file(md_path)
    fm = parsed["front_matter"]
    warnings = []

    doc = docx.Document(TEMPLATE_PATH)

    codigo_cell = resolve_header_table_cell(doc, "Código")
    if codigo_cell is not None:
        set_cell_text(codigo_cell, str(fm.get("codigo") or "[PENDIENTE]"))
    version_cell = resolve_header_table_cell(doc, "Versión")
    if version_cell is not None:
        set_cell_text(version_cell, str(fm.get("version", "")))
    fecha_cell = resolve_header_table_cell(doc, "Fecha")
    if fecha_cell is not None:
        set_cell_text(fecha_cell, str(fm.get("fecha", "")))

    desc = get_section(parsed, "Descripcion del proceso", "Descripción del proceso") or {}
    desc_texto = desc.get("texto", "")
    objeto = extract_field_lines(desc_texto, "Objeto")
    alcance = extract_field_lines(desc_texto, "Alcance")
    definiciones = extract_field_lines(desc_texto, "Definiciones")
    condiciones = extract_field_lines(desc_texto, "Condiciones generales")
    responsable = [fm.get("responsable", "")] if fm.get("responsable") else extract_field_lines(
        desc_texto, "Responsable\\(s\\)"
    )

    docs_section = get_section(parsed, "Documentos asociados") or {}
    docs_texto = docs_section.get("texto", "")
    internos_block, _, externos_block = docs_texto.partition("**Otros documentos aplicables")
    documentos = extract_bullets(internos_block) + extract_bullets(externos_block)

    ok = True
    ok &= replace_section_paragraphs(
        doc, r"^OBJETO DEL PROCESO\s*$", r"^ALCANCE\s*$",
        objeto or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^ALCANCE\s*$", r"^DEFINICIONES\s*$",
        alcance or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^DEFINICIONES\s*$", r"^CONDICIONES GENERALES\s*$",
        definiciones or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^CONDICIONES GENERALES\s*$", r"^RESPONSABLE\(S\)\s*$",
        condiciones or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^RESPONSABLE\(S\)\s*$", r"^DOCUMENTOS RELACIONADOS\s*$",
        responsable or ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(
        doc, r"^DOCUMENTOS RELACIONADOS\s*$", r"^DESARROLLO\s*$",
        [f"- {d}" for d in documentos] if documentos else ["[PENDIENTE]"],
    )
    ok &= replace_section_paragraphs(doc, r"^DESARROLLO\s*$", r"(?!)", [])
    if not ok:
        warnings.append("No se encontraron todos los encabezados esperados (OBJETO/ALCANCE/…) — revisar plantilla.")

    desarrollo = get_section(parsed, "Desarrollo actividades PHVA", "Desarrollo — actividades (PHVA)") or {}
    desarrollo_tabla = desarrollo["tablas"][0] if desarrollo.get("tablas") else []
    actividades = rows_from_table(desarrollo_tabla)
    # La tabla trae ID (AC-###) como primera columna desde que se agregó la seccion 9 (actores/RACI);
    # documentos mas viejos sin esa columna solo tienen 5 (Etapa/Nombre/Como/Responsable/Registro).
    tiene_id = bool(desarrollo_tabla) and desarrollo_tabla[0][:1] == ["ID"]
    tabla_actividades = find_table_by_header(doc, ["NOMBRE ACTIVIDAD", "CÓMO", "RESPONSABLE", "REGISTRO"])
    if tabla_actividades is not None and actividades:
        def _set_actividad_row(row, data):
            if tiene_id:
                id_, etapa, nombre, como, resp, registro = (data + [""] * 6)[:6]
                nombre_completo = f"[{id_}][{etapa}] {nombre}".strip()
            else:
                etapa, nombre, como, resp, registro = (data + [""] * 5)[:5]
                nombre_completo = f"[{etapa}] {nombre}".strip()
            set_cell_text(row.cells[0], nombre_completo)
            set_cell_text(row.cells[1], como)
            set_cell_text(row.cells[2], resp)
            set_cell_text(row.cells[3], registro)

        fill_table_data_rows(tabla_actividades, actividades, _set_actividad_row)
    elif not actividades:
        warnings.append("PROC sin tabla de actividades (sección 6) — tabla de desarrollo quedó con la fila de ejemplo.")

    slug = os.path.splitext(os.path.basename(md_path))[0]
    replace_section_paragraphs(
        doc, r"^Flujograma:.*$", r"^CONTROL DE CAMBIOS\s*$",
        [f"Ver diagrama BPMN en el archivo adjunto {slug}.bpmn, importable en Bizagi Modeler."],
    )

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
    result = export_procedimiento(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("OK ->", result["output"])
    for w in result["warnings"]:
        print("WARN:", w)
