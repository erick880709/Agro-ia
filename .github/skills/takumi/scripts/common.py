# -*- coding: utf-8 -*-
"""Utilidades compartidas por los exportadores de la skill `procesos` (Fase 2)."""
import copy
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from md_parser import strip_md_emphasis  # noqa: E402

BORRADOR_TEXT = "BORRADOR — pendiente de validación por el dueño del proceso"


def _strip_accents(text):
    table = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n",
    }
    return "".join(table.get(c, c) for c in text.lower())


def is_validado(front_matter):
    estado = _strip_accents(str(front_matter.get("estado", "")))
    return "validado por el dueno" in estado


def output_path_for(md_path, new_ext):
    base, _ = os.path.splitext(md_path)
    return base + new_ext


def extract_bold_field(text, label, collapse_whitespace=True):
    """Extrae el valor de un campo `**Label:** valor...` que puede envolver varias líneas de texto
    (el .md fuente hace word-wrap manual) hasta el próximo párrafo en blanco, el próximo campo en
    negrita (a inicio de línea, sin viñeta), o el final del texto.

    A propósito NO se detiene en una viñeta `- ` — si el campo completo es una lista (ej.
    "Definiciones" con varias sub-viñetas `- **Termino:** ...`), se captura completa como un solo
    bloque en vez de truncarla en la primera viñeta. `collapse_whitespace=False` conserva los saltos
    de línea (útil para pasar el bloque completo a `extract_bullets` después).
    """
    pattern = (
        r"\*\*" + re.escape(label) + r":?\*\*\s*(.+?)"
        r"(?=\n\s*\n|\n\*\*[^*\n]+\*\*|\Z)"
    )
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return ""
    value = m.group(1)
    if collapse_whitespace:
        return strip_md_emphasis(re.sub(r"\s+", " ", value).strip())
    return value.strip()


def extract_field_lines(text, label):
    """Extrae un campo `**Label:** ...` como lista de líneas de párrafo, sea prosa (1 línea) o una
    lista de viñetas (una línea por viñeta, con su `- ` conservado) — para pasar directo como
    `new_text_lines` a `replace_section_paragraphs` sin perder la viñeta ni concatenar párrafos con
    saltos de línea crudos (que python-docx no renderiza como líneas separadas)."""
    raw = extract_bold_field(text, label, collapse_whitespace=False)
    if not raw:
        return []
    bullets = extract_bullets(raw)
    if bullets:
        return [f"- {strip_md_emphasis(b)}" for b in bullets]
    return [strip_md_emphasis(re.sub(r"\s+", " ", raw).strip())]


def extract_bullets(text):
    """Extrae items de una lista `- texto...` uniendo líneas de continuación envueltas (sin viñeta
    propia) al item anterior."""
    bullets = []
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") or stripped == "-":
            if current is not None:
                bullets.append(" ".join(current).strip())
            current = [stripped[1:].strip()]
        elif current is not None:
            current.append(stripped)
    if current is not None:
        bullets.append(" ".join(current).strip())
    return [strip_md_emphasis(b) for b in bullets if b and b not in ("[ ]",)]


def extract_inline_field(text, label_regex):
    """Extrae un campo `**Label:** valor` de una línea que puede compartir varios campos separados
    por `·` (ej. `**Fecha:** X · **Hora:** Y`) — se detiene en el próximo `·`, salto de línea, o fin
    de texto. `label_regex` es un patrón (no un literal), para admitir variantes con/sin tilde."""
    m = re.search(rf"\*\*{label_regex}:?\*\*\s*(.+?)(?=\s*·|\n|\Z)", text)
    return strip_md_emphasis(m.group(1).strip().strip("[]").strip()) if m else ""


def extract_firmas(text):
    """Extrae (elaboro, reviso, aprobo) de la línea convencional
    `**Elaboró:** X · **Revisó:** Y · **Aprobó:** Z` (con o sin tilde, según la plantilla)."""
    return (
        extract_inline_field(text, "Elabor[oó]"),
        extract_inline_field(text, "Revis[oó]"),
        extract_inline_field(text, "Aprob[oó]"),
    )


def section_text_to_lines(text):
    """Convierte el texto libre de una sección completa (## N. Titulo) en una lista de líneas de
    párrafo listas para `replace_section_paragraphs`: cada bloque separado por línea en blanco se
    colapsa a una sola línea de prosa, salvo que sea una lista `- item`, que se conserva viñeta por
    viñeta. Usado para DOC-###/ACTA-### donde cada sección ya es texto libre aislado (a diferencia de
    PROC-### donde varios campos comparten una sola sección "Descripción del proceso")."""
    lines = []
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if not block:
            continue
        bullets = extract_bullets(block)
        if bullets:
            lines.extend(f"- {b}" for b in bullets)
        else:
            lines.append(strip_md_emphasis(re.sub(r"\s+", " ", block)).strip())
    return lines


def rows_from_table(tabla, skip_header=True):
    """tabla: lista de filas (primera fila = encabezados) según md_parser."""
    if not tabla:
        return []
    return tabla[1:] if skip_header else tabla


def append_cloned_row(table):
    """Clona la ÚLTIMA fila de una tabla python-docx y la agrega al final (mismas celdas/estilos).

    Clonar siempre desde la última fila (no desde un índice fijo) es lo que garantiza que filas
    clonadas sucesivas queden en orden — clonar repetidamente desde la misma fila fija las insertaría
    en orden inverso, porque cada `addnext` se ejecuta justo después de esa fila fija.
    """
    last_tr = table.rows[-1]._tr
    new_tr = copy.deepcopy(last_tr)
    last_tr.addnext(new_tr)
    return table.rows[-1]


def fill_table_data_rows(table, rows, cell_setter, first_data_row=1):
    """Llena filas de datos de una tabla python-docx, reutilizando las filas pre-asignadas por la
    plantilla ANTES de clonar filas nuevas.

    Bug que esto evita: si la plantilla trae 2 filas de datos pre-asignadas (ej. una con ejemplo, otra
    en blanco) y solo se sobreescribe la primera usando siempre `append_cloned_row` para las
    siguientes, la fila en blanco original queda como fila fantasma en medio de los datos reales —
    ocurrió tanto en la tabla de agenda del acta como en "Control de cambios" de procedimiento/manual
    técnico/documento de apoyo/política antes de centralizar esta función.

    `cell_setter(row, data)` recibe la fila python-docx y el dato (ej. una lista de valores) y decide
    cómo escribirlo — esta función solo decide QUÉ fila usar, no cómo llenarla.
    """
    original_row_count = len(table.rows)
    for i, data in enumerate(rows):
        idx = first_data_row + i
        target_row = table.rows[idx] if idx < original_row_count else append_cloned_row(table)
        cell_setter(target_row, data)


def find_table_by_header(doc, header_texts):
    """Encuentra la primera tabla cuya fila de encabezado (fila 0) empiece con `header_texts`."""
    for table in doc.tables:
        if not table.rows:
            continue
        first_row = [c.text.strip() for c in table.rows[0].cells]
        if first_row[: len(header_texts)] == header_texts:
            return table
    return None


def set_cell_text(cell, text):
    """Reemplaza el texto de una celda docx conservando el primer run/estilo si existe."""
    text = text or ""
    if cell.paragraphs and cell.paragraphs[0].runs:
        cell.paragraphs[0].runs[0].text = text
        for extra_run in cell.paragraphs[0].runs[1:]:
            extra_run.text = ""
        for p in cell.paragraphs[1:]:
            for r in p.runs:
                r.text = ""
    elif cell.paragraphs:
        cell.paragraphs[0].add_run(text)
    else:
        cell.add_paragraph(text)


def find_paragraph_index(doc, heading_text_regex, occurrence=0):
    """Devuelve el índice (en doc.paragraphs) del párrafo cuyo texto matchea el regex dado."""
    matches = []
    for i, p in enumerate(doc.paragraphs):
        if re.match(heading_text_regex, p.text.strip(), re.IGNORECASE):
            matches.append(i)
    if len(matches) > occurrence:
        return matches[occurrence]
    return None


def insert_paragraph_after(paragraph, text, bold=False, italic=False):
    """Inserta un nuevo párrafo justo después de `paragraph` (python-docx no lo expone directo)."""
    new_p = copy.deepcopy(paragraph._p)
    for child in list(new_p):
        new_p.remove(child)
    paragraph._p.addnext(new_p)
    from docx.text.paragraph import Paragraph

    new_paragraph = Paragraph(new_p, paragraph._parent)
    run = new_paragraph.add_run(text)
    run.bold = bold
    run.italic = italic
    return new_paragraph


def insert_rows_and_shift_merges(ws, at_row, amount):
    """openpyxl's `ws.insert_rows()` shifts cell VALUES but does NOT shift merged-cell ranges
    (known limitation) — sin esto, cualquier tabla/encabezado fusionado debajo del punto de
    inserción queda desalineado del contenido real que sí se movió. Se unmergean los rangos
    afectados, se inserta, y se vuelven a fusionar en su posición corrida."""
    to_restore = []
    for rng in list(ws.merged_cells.ranges):
        if rng.min_row >= at_row:
            to_restore.append((rng.min_row + amount, rng.min_col, rng.max_row + amount, rng.max_col))
            ws.unmerge_cells(str(rng))
        elif rng.max_row >= at_row:
            # el rango cruza el punto de inserción: se extiende hacia abajo
            to_restore.append((rng.min_row, rng.min_col, rng.max_row + amount, rng.max_col))
            ws.unmerge_cells(str(rng))

    ws.insert_rows(at_row, amount=amount)

    for min_row, min_col, max_row, max_col in to_restore:
        ws.merge_cells(start_row=min_row, start_column=min_col, end_row=max_row, end_column=max_col)


def replace_section_paragraphs(doc, start_heading_regex, stop_regex, new_text_lines):
    """Encuentra el párrafo `start_heading_regex`, borra los párrafos normales que le siguen
    (la instrucción/ejemplo de la plantilla) hasta el primer párrafo que matchee `stop_regex` o hasta
    la primera tabla — sin tocar tablas — y los reemplaza por `new_text_lines`.

    Devuelve True si encontró el encabezado, False si no (para que quien llama pueda registrar un
    warning en vez de fallar silenciosamente)."""
    from docx.text.paragraph import Paragraph

    start_idx = find_paragraph_index(doc, start_heading_regex)
    if start_idx is None:
        return False
    start_p = doc.paragraphs[start_idx]

    to_remove = []
    current = start_p._element.getnext()
    while current is not None:
        tag = current.tag.split("}")[-1]
        if tag == "tbl":
            break
        if tag == "p":
            p_obj = Paragraph(current, start_p._parent)
            if re.match(stop_regex, p_obj.text.strip(), re.IGNORECASE):
                break
        to_remove.append(current)
        current = current.getnext()
    for el in to_remove:
        el.getparent().remove(el)

    anchor = start_p
    for text in new_text_lines:
        anchor = insert_paragraph_after(anchor, text)
    return True


def insert_paragraph_before(paragraph, text, bold=False, italic=False):
    """Inserta un nuevo párrafo justo antes de `paragraph`."""
    new_p = copy.deepcopy(paragraph._p)
    for child in list(new_p):
        new_p.remove(child)
    paragraph._p.addprevious(new_p)
    from docx.text.paragraph import Paragraph

    new_paragraph = Paragraph(new_p, paragraph._parent)
    run = new_paragraph.add_run(text)
    run.bold = bold
    run.italic = italic
    return new_paragraph


def resolve_header_table_cell(doc, label_text, value_col_offset=1):
    """Busca en las tablas del header la fila cuyo texto contiene `label_text` y devuelve la celda
    vecina (donde va el valor: Código/Versión/Fecha)."""
    for section in doc.sections:
        for table in section.header.tables:
            for row in table.rows:
                for idx, cell in enumerate(row.cells):
                    if label_text.lower() in cell.text.strip().lower():
                        target_idx = idx + value_col_offset
                        if target_idx < len(row.cells):
                            return row.cells[target_idx]
    return None
