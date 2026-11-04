# -*- coding: utf-8 -*-
"""Parsea un PROC-###/DOC-###/ACTA-###.md de la skill `procesos` a un dict estructurado.

No depende de nada fuera de pyyaml (ya disponible en el entorno) + stdlib.
"""
import datetime
import re
import yaml


def _stringify_dates(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _stringify_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_stringify_dates(v) for v in obj]
    return obj


_SECTION_RE = re.compile(r"^##\s+(?:(\d+)\.\s+)?(.+?)\s*$")
_MERMAID_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


def _normalize_title(title):
    t = title.strip().lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9 ]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def strip_md_emphasis(text):
    """Quita marcadores de énfasis Markdown (**negrita**, _cursiva_, `código`) dejando el texto
    plano — las salidas .docx/.xlsx oficiales no interpretan Markdown, así que dejarlos tal cual se
    verían como asteriscos/backticks literales."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text


def _parse_markdown_table(lines):
    """lines: lista de líneas de texto que forman una tabla Markdown (incluye separador ---)."""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [strip_md_emphasis(c.strip()) for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue  # fila separadora
        rows.append(cells)
    return rows


def parse_front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    fm_text = m.group(1)
    rest = text[m.end():]
    try:
        fm = _stringify_dates(yaml.safe_load(fm_text) or {})
    except yaml.YAMLError:
        fm = {}
        for line in fm_text.splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, rest


def _analyze_block(raw_lines):
    """Separa un bloque de líneas en {texto, tablas, mermaid} — usado tanto para secciones `## N.`
    como para el preámbulo de un acta (el contenido antes de la primera `## `)."""
    raw = "\n".join(raw_lines)
    mermaid_blocks = _MERMAID_RE.findall(raw)
    tablas = []
    table_buf = []
    texto_lines = []
    in_table = False
    for line in raw.splitlines():
        if line.strip().startswith("|"):
            table_buf.append(line)
            in_table = True
        else:
            if in_table and table_buf:
                tablas.append(_parse_markdown_table(table_buf))
                table_buf = []
            in_table = False
            texto_lines.append(line)
    if table_buf:
        tablas.append(_parse_markdown_table(table_buf))
    return {
        # OJO: conserva los marcadores **negrita** a propósito — los helpers de common.py
        # (extract_bold_field/extract_bullets/etc.) buscan literalmente "**Campo:**" y ellos mismos
        # limpian los marcadores en el valor final ya extraído, justo antes de insertarlo en el
        # docx/xlsx. Si esta función ya los quitara, esos regex dejarían de encontrar nada.
        "texto": "\n".join(texto_lines).strip(),
        "tablas": [t for t in tablas if t],
        "mermaid": mermaid_blocks,
    }


def parse_sections(body):
    """Divide el cuerpo (después del front-matter) en secciones `## N. Titulo`.

    Devuelve dict: {titulo_normalizado: {"numero": int, "titulo": str, "texto": str,
                                          "texto_con_marcas": str, "tablas": [[[celda,...],...]],
                                          "mermaid": [str,...]}}
    `texto` ya tiene los marcadores `**negrita**` quitados (para insertar directo en docx/xlsx);
    `texto_con_marcas` los conserva (para los helpers de `common.py` que buscan `**Campo:**`).
    """
    lines = body.splitlines()
    sections = {}
    current = None
    buffer = []

    def flush():
        if current is None:
            return
        analyzed = _analyze_block(buffer)
        sections[current["key"]] = {
            "numero": current["numero"],
            "titulo": current["titulo"],
            **analyzed,
        }

    for line in lines:
        m = _SECTION_RE.match(line)
        if m:
            flush()
            numero, titulo = m.groups()
            current = {"numero": int(numero) if numero else None, "titulo": titulo, "key": _normalize_title(titulo)}
            buffer = []
        else:
            if current is not None:
                buffer.append(line)
    flush()
    return sections


def parse_preamble(body):
    """Contenido antes de la primera `## ` (usado por ACTA-###.md: número/fecha/hora/lugar/
    elaborado por/objetivo/asistentes viven antes de la primera sección numerada)."""
    first_h2 = re.search(r"^##\s+", body, re.MULTILINE)
    end = first_h2.start() if first_h2 else len(body)
    h1 = re.search(r"^#\s+.+\n", body, re.MULTILINE)
    start = h1.end() if h1 else 0
    return _analyze_block(body[start:end].splitlines())


def parse_md_file(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    front_matter, body = parse_front_matter(text)
    sections = parse_sections(body)
    title_match = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
    titulo_documento = title_match.group(1) if title_match else front_matter.get("id", "")
    return {
        "front_matter": front_matter,
        "titulo_documento": titulo_documento,
        "secciones": sections,
    }


def get_section(parsed, *titulo_candidatos):
    """Busca una sección por cualquiera de los títulos normalizados candidatos.

    Primero intenta match exacto; si no hay, cae a "empieza con" en cualquier dirección — los
    esqueletos de `templates/*.md` traen guías parentéticas largas en el título (ej. "Diagrama (si
    el desarrollo tiene flujo operativo; omitir si...)") que un autor real suele acortar a solo
    "Diagrama" — sin este fallback, un título recortado no encontraría la sección.
    """
    for t in titulo_candidatos:
        key = _normalize_title(t)
        if key in parsed["secciones"]:
            return parsed["secciones"][key]
    for t in titulo_candidatos:
        key = _normalize_title(t)
        for existing_key, section in parsed["secciones"].items():
            if existing_key.startswith(key) or key.startswith(existing_key):
                return section
    return None


if __name__ == "__main__":
    import sys
    import json

    result = parse_md_file(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
