#!/usr/bin/env python3
"""Valida coherencia estructural y trazabilidad entre artefactos de archi.

La herramienta no evalúa la calidad de una decisión arquitectónica. Automatiza
integridad documental, cobertura de IDs y el contrato de auditoría definido para
25-Revision-Tecnica-Arquitectura.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote


ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "OBJ": re.compile(r"\bOBJ-\d{2,3}\b"),
    "RESTRICCION": re.compile(r"\b(?:RT|RN|RR)-D\d{2,3}\b"),
    "SUP": re.compile(r"\bSUP-D\d{2,3}\b"),
    "QA": re.compile(r"\bQA-\d{2,3}\b"),
    "FAS": re.compile(r"\bFAS-\d{3}\b"),
    "ARQ": re.compile(r"\bARQ-\d{3}\b"),
    "CT": re.compile(r"\bCT-\d{2,3}\b"),
    "API_OP": re.compile(r"\bAPI-\d{3}-OP-\d{3}\b"),
    "API_ERR": re.compile(r"\bAPI-\d{3}-ERR-\d{3}\b"),
    "API": re.compile(r"\bAPI-\d{3}\b"),
    "DATA": re.compile(r"\bDATA-\d{3}\b"),
    "THR": re.compile(r"\bTHR-\d{3}\b"),
    "SEC": re.compile(r"\bSEC-\d{3}\b"),
    "DA": re.compile(r"\bDA-\d{3}\b"),
    "TP": re.compile(r"\bTP-\d{3}\b"),
    "CC": re.compile(r"\bCC-\d{3}\b"),
    "CON": re.compile(r"\bCON-\d{3}\b"),
}

OWNER_PREFIXES: dict[str, tuple[str, ...]] = {
    "OBJ": ("02-",),
    "RESTRICCION": ("03-",),
    "SUP": ("04-",),
    "QA": ("05-",),
    "FAS": ("06-",),
    "ARQ": ("10.1-",),
    "CT": ("14-vistas-c4",),
    "API": ("14.00-",),
    "API_OP": ("14.00-",),
    "API_ERR": ("14.00-",),
    "DATA": ("16-modelo-de-datos",),
    "THR": ("19.1-",),
    "SEC": ("19.1-",),
    "DA": ("20-",),
    "TP": ("18-",),
    "CC": ("19-dimensiones",),
    "CON": ("25-revision-tecnica-arquitectura",),
}

COMMITMENT_TYPES = {"OBJ", "RESTRICCION", "SUP", "QA", "FAS", "SEC"}
DESIGN_TYPES = {"ARQ", "CT", "API", "DATA", "TP"}
EVIDENCE_STATES = {
    "definido",
    "disenado",
    "verificado en diseno",
    "demostrado",
    "implementado",
    "validado operacionalmente",
    "desviado con aprobacion",
    "no aplica",
}
DESIGN_STATES = {"justificado", "desviacion aprobada", "no cumple"}
CLOSURE_STATES = {"cumple", "cumple con observaciones", "no cumple", "no aplica"}
DOMAIN_READY_STATES = {"listo", "listo con riesgos"}
DOMAIN_EVENT_STORMING_VALUES = {"obligatorio", "evidencia equivalente", "no aplica"}
DOMAIN_MODEL_STATES = {
    "validado-dominio",
    "validacion-parcial",
    "evidencia-equivalente",
    "no-aplica",
}
BLOCKING_SEVERITIES = {"critica", "alta"}
OPEN_STATES = {"abierta", "en correccion"}
REQUIRED_PREFIXES: dict[str, tuple[str, ...]] = {
    "A": (
        "01-", "02-", "03-", "04-", "05-", "06-", "07-", "08-", "09-",
        "10-", "10.1-", "12-", "14-", "15-", "18-", "19-", "20-", "21-",
        "22-", "25-",
    ),
    "B": (
        "02-", "03-", "04-", "05-", "06-", "10.1-", "14-", "15-", "18-",
        "19-", "20-", "21-", "22-", "25-",
    ),
    "C": (
        "01-", "02-", "03-", "04-", "05-", "06-", "07-", "08-", "09-",
        "10-", "10.1-", "12-", "14-", "15-", "18-", "19-", "20-", "21-",
        "22-", "23-", "24-", "25-",
    ),
}
PLACEHOLDER_PATTERNS = (
    # TODO/TBD are intentional uppercase authoring markers.  Matching them
    # case-insensitively turns the Spanish word "todo" into a false positive.
    re.compile(r"\bTODO\b"),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"Missing evidence", re.IGNORECASE),
    re.compile(r"<Proyecto>", re.IGNORECASE),
    re.compile(r"\[CT-[^\]]+\]", re.IGNORECASE),
)
ALTERNATIVE_HEADING_PATTERN = re.compile(
    r"^(#{2,4})\s+Alternativa\s+[A-Z0-9][A-Z0-9._-]*\s+[—–-]\s+\S[^\r\n]*$",
    re.IGNORECASE | re.MULTILINE,
)
MERMAID_BLOCK_PATTERN = re.compile(
    r"^```mermaid[ \t]*\r?\n.+?^```[ \t]*$",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
ARCHETYPE_DETAIL_HEADING_PATTERN = re.compile(
    r"^###\s+(ARQ-\d{3})\s+[—–-]\s+\S[^\r\n]*$", re.IGNORECASE | re.MULTILINE
)
FENCED_CODE_BLOCK_PATTERN = re.compile(
    r"^```[^\r\n]*\r?\n.+?^```[ \t]*$", re.MULTILINE | re.DOTALL
)
ARCHETYPE_REQUIRED_SECTIONS = (
    "Definición y propósito de los arquetipos",
    "Perfil detallado del proyecto",
    "Arquetipos identificados",
    "Análisis detallado por arquetipo",
    "Baseline tecnológico canónico",
    "Componentes compartidos e integraciones",
    "Convenciones transversales",
    "Datos, seguridad y operación",
    "Patrones, desviaciones, legado y evolución",
    "Prioridad de construcción",
    "Decisiones de framework y baseline",
    "Matriz de trazabilidad",
    "Criterios de cierre",
)
ARCHETYPE_DETAIL_SUBSECTIONS = (
    "Scopes y componentes objetivo",
    "Propósito y cuándo usarlo",
    "Características principales",
    "Estructura de carpetas propuesta",
    "Patrones y controles incorporados",
    "Contrato de desarrollo",
    "Configuración y secretos",
    "Diferencias y reutilización",
    "Criterios de aceptación del scaffold",
)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, int] = field(default_factory=dict)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


@dataclass(frozen=True)
class SqlPhysicalObject:
    name: str
    kind: str
    columns: tuple[str, ...]


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[`*_]", "", text)
    return re.sub(r"\s+", " ", text.strip())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def numbered_prefix(path: Path) -> float | None:
    match = re.match(r"^(\d{2})(?:\.(\d+))?[-.]", path.name)
    if not match:
        return None
    base = int(match.group(1))
    suffix = match.group(2)
    return float(f"{base}.{suffix}") if suffix else float(base)


def extract_ids(text: str) -> dict[str, set[str]]:
    return {kind: set(pattern.findall(text)) for kind, pattern in ID_PATTERNS.items()}


def find_section(text: str, title: str) -> str:
    lines = text.splitlines()
    wanted = normalize(title)
    start = None
    level = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(#{2,6})\s+(.+?)\s*$", line)
        if not match:
            continue
        if wanted in normalize(match.group(2)):
            start = index + 1
            level = len(match.group(1))
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        match = re.match(r"^(#{2,6})\s+", lines[index])
        if match and len(match.group(1)) <= level:
            end = index
            break
    return "\n".join(lines[start:end])


def parse_markdown_table(section: str) -> list[dict[str, str]]:
    table_lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 2:
        return []
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in table_lines]
    headers = [normalize(cell) for cell in rows[0]]
    result: list[dict[str, str]] = []
    for row in rows[1:]:
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in row):
            continue
        if len(row) != len(headers):
            continue
        result.append(dict(zip(headers, row)))
    return result


def parse_markdown_tables(section: str) -> list[list[dict[str, str]]]:
    """Devuelve cada tabla Markdown consecutiva como una unidad independiente."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in section.splitlines():
        if line.strip().startswith("|"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return [rows for block in blocks if (rows := parse_markdown_table("\n".join(block)))]


def first_value(row: dict[str, str], *names: str) -> str:
    for name in names:
        normalized = normalize(name)
        if normalized in row:
            return row[normalized]
    return ""


def normalize_sql_identifier(value: str) -> str:
    parts = [part.strip().strip('"') for part in re.split(r"\s*\.\s*", value)]
    return ".".join(part.casefold() for part in parts if part)


def strip_sql_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    return re.sub(r"--[^\r\n]*", " ", text)


def find_balanced_parenthesis(text: str, opening: int) -> int | None:
    depth = 0
    quote: str | None = None
    index = opening
    while index < len(text):
        char = text[index]
        if quote:
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    index += 2
                    continue
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def split_sql_top_level(value: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    index = 0
    while index < len(value):
        char = value[index]
        if quote:
            if char == quote:
                if index + 1 < len(value) and value[index + 1] == quote:
                    index += 2
                    continue
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
        index += 1
    tail = value[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def extract_sql_physical_objects(path: Path, report: Report) -> dict[str, SqlPhysicalObject]:
    try:
        sql = strip_sql_comments(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        report.error(f"{path.name}: no se pudo leer el esquema SQL: {exc}")
        return {}

    identifier = r'(?:"[^"]+"|[A-Za-z_][\w$]*)(?:\s*\.\s*(?:"[^"]+"|[A-Za-z_][\w$]*))?'
    table_pattern = re.compile(
        rf"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>{identifier})\s*\(",
        re.IGNORECASE,
    )
    view_pattern = re.compile(
        rf"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:MATERIALIZED\s+)?VIEW\s+"
        rf"(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>{identifier})\b",
        re.IGNORECASE,
    )
    objects: dict[str, SqlPhysicalObject] = {}
    constraint_starters = {
        "constraint", "primary", "foreign", "unique", "check", "exclude", "like"
    }
    for match in table_pattern.finditer(sql):
        name = normalize_sql_identifier(match.group("name"))
        closing = find_balanced_parenthesis(sql, match.end() - 1)
        if closing is None:
            report.error(f"{path.name}: CREATE TABLE {name} tiene paréntesis sin cerrar")
            continue
        columns: list[str] = []
        for definition in split_sql_top_level(sql[match.end():closing]):
            column_match = re.match(
                r'^\s*("[^"]+"|[A-Za-z_][\w$]*)(?=\s|$)', definition
            )
            if not column_match:
                continue
            column = column_match.group(1).strip('"').casefold()
            if column in constraint_starters:
                continue
            columns.append(column)
        if name in objects:
            report.error(f"{path.name}: objeto físico duplicado {name}")
        objects[name] = SqlPhysicalObject(name, "tabla", tuple(columns))

    for match in view_pattern.finditer(sql):
        name = normalize_sql_identifier(match.group("name"))
        kind = "vista materializada" if "materialized" in normalize(match.group(0)) else "vista"
        if name in objects:
            report.error(f"{path.name}: objeto físico duplicado {name}")
        objects[name] = SqlPhysicalObject(name, kind, ())
    return objects


def extract_physical_dictionary_entries(
    section: str, path: Path, report: Report
) -> dict[str, tuple[str, str]]:
    heading_pattern = re.compile(
        r'^###\s+`?((?:"[^"]+"|[A-Za-z_][\w$]*)(?:\.(?:"[^"]+"|[A-Za-z_][\w$]*))?)`?'
        r'\s*[—–-]\s*(Tabla|Colección|Vista(?:\s+materializada)?|Proyección)\s*$',
        re.IGNORECASE | re.MULTILINE,
    )
    matches = list(heading_pattern.finditer(section))
    entries: dict[str, tuple[str, str]] = {}
    for index, match in enumerate(matches):
        name = normalize_sql_identifier(match.group(1))
        kind = normalize(match.group(2))
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        if name in entries:
            report.error(f"{path.name}: diccionario físico duplica el objeto {name}")
        entries[name] = (kind, section[match.end():body_end])
    return entries


def validate_dictionary_entry(
    model_path: Path,
    physical: SqlPhysicalObject,
    documented_kind: str,
    body: str,
    report: Report,
) -> None:
    if physical.kind.startswith("vista") and not documented_kind.startswith("vista"):
        report.error(f"{model_path.name}: {physical.name} es vista en el esquema y no en el diccionario")
    if physical.kind == "tabla" and documented_kind not in {"tabla", "coleccion"}:
        report.error(f"{model_path.name}: {physical.name} es tabla en el esquema y no en el diccionario")

    normalized = normalize(body)
    required_metadata = {
        "DATA": ("**data:**",),
        "propósito": ("**proposito:**",),
        "owner": ("**owner:**",),
        "rol del dato": ("**rol del dato:**",),
        "clasificación": ("**clasificacion:**",),
        "retención/borrado": ("**retencion/borrado:**", "**retencion y borrado:**"),
        "seguridad/RLS": ("**seguridad/rls:**", "**seguridad:**"),
        "índices/particiones": ("**indices/particiones:**", "**indices:**"),
        "consumidores/operaciones": ("**consumidores/operaciones:**", "**consumidores:**"),
    }
    for label, alternatives in required_metadata.items():
        if not any(normalize(token) in normalized for token in alternatives):
            report.error(f"{model_path.name}: {physical.name} no documenta {label}")
    if not ID_PATTERNS["DATA"].search(body):
        report.error(f"{model_path.name}: {physical.name} no enlaza un DATA-xxx")
    if physical.kind.startswith("vista") and not any(
        normalize(token) in normalized
        for token in ("**Fuentes/frescura:**", "**Fuentes y frescura:**")
    ):
        report.error(f"{model_path.name}: {physical.name} no documenta fuentes/frescura")

    tables = parse_markdown_tables(body)
    column_rows: list[dict[str, str]] = []
    for table in tables:
        headers = set(table[0])
        if any(header in headers for header in ("columna", "campo", "campo/ruta")):
            column_rows = table
            break
    if not column_rows:
        report.error(f"{model_path.name}: {physical.name} no contiene diccionario de columnas/campos")
        return
    headers = set(column_rows[0])
    required_header_groups = {
        "columna/campo": ("columna", "campo", "campo/ruta"),
        "tipo": ("tipo",),
        "nulabilidad": ("nulo", "nulabilidad"),
        "default": ("default", "valor por defecto"),
        "clave/referencia": ("clave/referencia", "clave", "referencia"),
        "restricciones": ("restricciones", "restriccion"),
        "clasificación/PII": ("clasificacion/pii", "clasificacion", "pii"),
        "descripción": ("descripcion",),
    }
    for label, alternatives in required_header_groups.items():
        if not any(header in alternatives for header in headers):
            report.error(f"{model_path.name}: {physical.name} diccionario sin columna de {label}")

    documented_columns: set[str] = set()
    for row_index, row in enumerate(column_rows, start=1):
        column = normalize_sql_identifier(first_value(row, "Columna", "Campo", "Campo/ruta"))
        if column:
            if column in documented_columns:
                report.error(
                    f"{model_path.name}: {physical.name}.{column} está documentada más de una vez"
                )
            documented_columns.add(column)
        for label, alternatives in required_header_groups.items():
            if any(header in alternatives for header in headers) and not first_value(
                row, *alternatives
            ).strip():
                report.error(
                    f"{model_path.name}: {physical.name} fila {row_index} deja vacío {label}"
                )
    if physical.kind == "tabla":
        physical_columns = set(physical.columns)
        for column in sorted(physical_columns - documented_columns):
            report.error(f"{model_path.name}: {physical.name}.{column} no está documentada")
        for column in sorted(documented_columns - physical_columns):
            report.error(f"{model_path.name}: {physical.name}.{column} está documentada pero no existe en el esquema")


def validate_physical_dictionary(
    model_path: Path,
    model_text: str,
    physical_assets: list[Path],
    report: Report,
) -> None:
    dictionary = find_section(model_text, "Diccionario físico de datos")
    if not dictionary:
        report.error(f"{model_path.name}: falta 'Diccionario físico de datos'")
        return
    entries = extract_physical_dictionary_entries(dictionary, model_path, report)
    sql_objects: dict[str, SqlPhysicalObject] = {}
    for asset in physical_assets:
        if asset.suffix.casefold() != ".sql":
            continue
        for name, obj in extract_sql_physical_objects(asset, report).items():
            if name in sql_objects:
                report.error(f"{model_path.name}: objeto físico {name} aparece en múltiples assets")
            sql_objects[name] = obj
    if not sql_objects:
        if not entries:
            report.error(f"{model_path.name}: el diccionario físico no contiene objetos documentados")
        return
    for name in sorted(sql_objects.keys() - entries.keys()):
        report.error(f"{model_path.name}: objeto físico {name} no está documentado")
    for name in sorted(entries.keys() - sql_objects.keys()):
        report.error(f"{model_path.name}: objeto {name} está documentado pero no existe en el esquema SQL")
    for name in sorted(sql_objects.keys() & entries.keys()):
        documented_kind, body = entries[name]
        validate_dictionary_entry(
            model_path, sql_objects[name], documented_kind, body, report
        )
    report.metrics["physical_objects"] = report.metrics.get("physical_objects", 0) + len(sql_objects)
    report.metrics["documented_physical_objects"] = (
        report.metrics.get("documented_physical_objects", 0)
        + len(sql_objects.keys() & entries.keys())
    )


def read_documents(directory: Path, report: Report) -> dict[Path, str]:
    documents: dict[Path, str] = {}
    if not directory.is_dir():
        report.error(f"No existe el directorio de arquitectura: {directory}")
        return documents
    for path in sorted(directory.glob("*.md")):
        try:
            documents[path] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            report.error(f"No se pudo leer {path.name}: {exc}")
    if not documents:
        report.error(f"No se encontraron Markdown directamente en {directory}")
    return documents


def validate_links(documents: dict[Path, str], report: Report) -> None:
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for path, text in documents.items():
        for raw_target in link_pattern.findall(text):
            target = raw_target.strip().strip("<>").split("#", 1)[0].strip()
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            if any(token in target for token in ("<", ">", "[", "]", "*")):
                report.warning(f"{path.name}: enlace con placeholder: {raw_target}")
                continue
            resolved = (path.parent / unquote(target)).resolve()
            if not resolved.exists():
                report.error(f"{path.name}: enlace local no resuelve: {raw_target}")


def validate_required_files(
    documents: dict[Path, str], scenario: str, report: Report
) -> None:
    names = [path.name.casefold() for path in documents]
    for prefix in REQUIRED_PREFIXES[scenario]:
        if not any(name.startswith(prefix) for name in names):
            report.error(f"Escenario {scenario}: falta artefacto obligatorio con prefijo {prefix}")


def validate_domain_readiness(
    documents: dict[Path, str], scenario: str, report: Report
) -> None:
    """Valida el contrato DR-01 registrado en la línea base de Casos A/C."""
    if scenario == "B":
        return

    candidates = [
        (path, text)
        for path, text in documents.items()
        if path.name.casefold().startswith("01-linea-base")
    ]
    if len(candidates) != 1:
        if len(candidates) > 1:
            report.error(f"DR-01: se esperaba una única línea base 01; hay {len(candidates)}")
        return

    path, text = candidates[0]
    section = find_section(text, "Preparación del dominio")
    if not section:
        report.error(f"{path.name}: falta la sección obligatoria 'Preparación del dominio' (DR-01)")
        return

    rows = parse_markdown_table(section)
    fields = {
        normalize(first_value(row, "Campo")): first_value(row, "Valor").strip()
        for row in rows
        if first_value(row, "Campo")
    }
    required = (
        "Escenario",
        "Complejidad del dominio",
        "Event Storming",
        "Estado del modelo",
        "Estado DR-01",
        "Evidencia",
        "Hotspots arquitectónicos bloqueantes",
        "Handoff pendiente",
        "Justificación",
    )
    missing = [field for field in required if not fields.get(normalize(field), "").strip()]
    if missing:
        report.error(f"{path.name}: DR-01 carece de campos obligatorios: {', '.join(missing)}")
        return

    declared_scenario = normalize(fields[normalize("Escenario")])
    if declared_scenario != scenario.casefold():
        report.error(
            f"{path.name}: DR-01 declara escenario '{fields[normalize('Escenario')]}' "
            f"pero el validador ejecuta escenario {scenario}"
        )

    readiness = normalize(fields[normalize("Estado DR-01")])
    if readiness not in DOMAIN_READY_STATES:
        report.error(
            f"{path.name}: DR-01 no habilita arquitectura; estado '{fields[normalize('Estado DR-01')]}'"
        )

    event_storming = normalize(fields[normalize("Event Storming")])
    if event_storming not in DOMAIN_EVENT_STORMING_VALUES:
        report.error(
            f"{path.name}: valor inválido de Event Storming en DR-01: "
            f"'{fields[normalize('Event Storming')]}'"
        )

    model_state = normalize(fields[normalize("Estado del modelo")])
    if model_state not in DOMAIN_MODEL_STATES:
        report.error(
            f"{path.name}: estado de modelo inválido en DR-01: "
            f"'{fields[normalize('Estado del modelo')]}'"
        )
    if event_storming == "obligatorio":
        if model_state not in {"validado-dominio", "validacion-parcial"}:
            report.error(
                f"{path.name}: Event Storming obligatorio exige modelo validado-dominio o "
                "validacion-parcial sin bloqueantes"
            )
        evidence = fields[normalize("Evidencia")]
        if not re.search(r"(?:resources[/\\]functional[/\\]eventstorming|\bES-\d{3}\b)", evidence, re.I):
            report.error(f"{path.name}: DR-01 no enlaza evidencia verificable de Event Storming")
    elif event_storming == "evidencia equivalente" and model_state != "evidencia-equivalente":
        report.error(f"{path.name}: evidencia equivalente exige estado de modelo evidencia-equivalente")
    elif event_storming == "no aplica" and model_state != "no-aplica":
        report.error(f"{path.name}: Event Storming no aplicable exige estado de modelo no-aplica")

    complexity = normalize(fields[normalize("Complejidad del dominio")])
    if not any(complexity.startswith(value) for value in ("complejo", "simple", "tecnico")):
        report.error(
            f"{path.name}: complejidad de dominio inválida en DR-01: "
            f"'{fields[normalize('Complejidad del dominio')]}'"
        )
    elif complexity.startswith("complejo") and event_storming != "obligatorio":
        report.error(f"{path.name}: un dominio complejo exige Event Storming obligatorio")
    elif complexity.startswith("simple") and event_storming == "no aplica":
        report.error(f"{path.name}: un dominio simple exige evidencia equivalente o Event Storming")
    elif complexity.startswith("tecnico") and event_storming != "no aplica":
        report.error(f"{path.name}: un alcance técnico debe justificar Event Storming como no aplicable")

    if model_state == "validacion-parcial" and readiness != "listo con riesgos":
        report.error(f"{path.name}: validacion-parcial exige estado DR-01 'Listo con riesgos'")

    empty_markers = {"ninguno", "ninguna", "0", "no aplica", "no-aplica"}
    hotspots = normalize(fields[normalize("Hotspots arquitectónicos bloqueantes")])
    if hotspots not in empty_markers:
        report.error(f"{path.name}: DR-01 conserva hotspots arquitectónicos bloqueantes: {hotspots}")
    handoff = normalize(fields[normalize("Handoff pendiente")])
    if handoff not in empty_markers:
        report.error(f"{path.name}: DR-01 conserva handoff pendiente: {handoff}")
    risks = normalize(fields.get(normalize("Riesgos no bloqueantes"), ""))
    if readiness == "listo" and risks not in empty_markers:
        if risks:
            report.error(f"{path.name}: DR-01 está Listo pero conserva riesgos no bloqueantes: {risks}")
    if readiness == "listo con riesgos" and (not risks or risks in empty_markers):
        report.error(f"{path.name}: DR-01 está Listo con riesgos pero no identifica ningún riesgo")

    report.metrics["domain_readiness"] = 1 if readiness in DOMAIN_READY_STATES else 0


def validate_alternative_diagrams(
    documents: dict[Path, str], scenario: str, report: Report
) -> None:
    if scenario == "B":
        return
    candidates = [
        (path, text)
        for path, text in documents.items()
        if path.name.casefold().startswith("09-alternativas-de-solucion")
    ]
    if len(candidates) != 1:
        report.error(
            "Se esperaba un único 09-Alternativas-de-Solucion.md "
            f"para validar Mermaid por alternativa; hay {len(candidates)}"
        )
        return

    path, text = candidates[0]
    headings = list(ALTERNATIVE_HEADING_PATTERN.finditer(text))
    if len(headings) < 2:
        report.error(
            f"{path.name}: debe declarar al menos dos secciones con el formato "
            "'### Alternativa <ID> — <Nombre>'"
        )
        return

    diagrams = 0
    for heading in headings:
        level = len(heading.group(1))
        section_end = len(text)
        following_heading = re.compile(
            rf"^#{{2,{level}}}\s+.+$", re.MULTILINE
        ).search(text, heading.end())
        if following_heading:
            section_end = following_heading.start()
        section = text[heading.end():section_end]
        if not MERMAID_BLOCK_PATTERN.search(section):
            title = heading.group(0).lstrip("#").strip()
            report.error(
                f"{path.name}: '{title}' no contiene un bloque Mermaid propio"
            )
            continue
        diagrams += 1

    report.metrics["solution_alternatives"] = len(headings)
    report.metrics["alternative_mermaid_diagrams"] = diagrams


def validate_archetype_analysis(
    documents: dict[Path, str], report: Report
) -> None:
    candidates = [
        (path, text)
        for path, text in documents.items()
        if path.name.casefold().startswith("10.1-arquetipo-de-solucion")
    ]
    if len(candidates) != 1:
        report.error(
            "Se esperaba un único 10.1-Arquetipo-de-Solucion_<Proyecto>.md "
            f"para validar el análisis de arquetipos; hay {len(candidates)}"
        )
        return

    path, text = candidates[0]
    for title in ARCHETYPE_REQUIRED_SECTIONS:
        if not find_section(text, title):
            report.error(f"{path.name}: falta la sección canónica '{title}'")

    inventory = find_section(text, "Arquetipos identificados")
    inventory_ids = extract_ids(inventory)["ARQ"] - {"ARQ-001"}
    if not inventory_ids:
        report.error(
            f"{path.name}: 'Arquetipos identificados' no contiene ningún ARQ-xxx implementable"
        )

    detail = find_section(text, "Análisis detallado por arquetipo")
    detail_headings = list(ARCHETYPE_DETAIL_HEADING_PATTERN.finditer(detail))
    detail_ids = {match.group(1).upper() for match in detail_headings}
    for archetype_id in sorted(inventory_ids - detail_ids):
        report.error(
            f"{path.name}: {archetype_id} está inventariado pero no tiene ficha detallada"
        )
    for archetype_id in sorted(detail_ids - inventory_ids):
        report.error(
            f"{path.name}: {archetype_id} tiene ficha detallada pero no está inventariado"
        )

    detailed_structures = 0
    for heading in detail_headings:
        next_heading = re.compile(r"^###\s+.+$", re.MULTILINE).search(
            detail, heading.end()
        )
        section_end = next_heading.start() if next_heading else len(detail)
        archetype_section = detail[heading.end():section_end]
        archetype_id = heading.group(1).upper()
        for subsection in ARCHETYPE_DETAIL_SUBSECTIONS:
            if not find_section(archetype_section, subsection):
                report.error(
                    f"{path.name}: {archetype_id} carece de la subsección '{subsection}'"
                )
        structure = find_section(archetype_section, "Estructura de carpetas propuesta")
        has_tree = bool(FENCED_CODE_BLOCK_PATTERN.search(structure))
        has_na_reason = bool(
            re.search(r"\bN/?A\b\s*[—–-]\s*\S", structure, re.IGNORECASE)
        )
        if not has_tree and not has_na_reason:
            report.error(
                f"{path.name}: {archetype_id} no contiene árbol de carpetas "
                "ni 'N/A — <motivo>'"
            )
        else:
            detailed_structures += 1

    report.metrics["implementable_archetypes"] = len(inventory_ids)
    report.metrics["detailed_archetype_structures"] = detailed_structures


def slugify_heading(text: str) -> str:
    """Aproxima el anchor que GitHub/VS Code generan para un encabezado.

    Conserva tildes y demás letras Unicode (los slugger reales no las quitan):
    solo minúsculas, quita puntuación ASCII y colapsa espacios en guiones.
    """
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text).strip("-")


def validate_table_of_contents(
    documents: dict[Path, str], report: Report, strict: bool
) -> None:
    for path, text in documents.items():
        prefix = numbered_prefix(path)
        if prefix is None or prefix == 0:
            continue
        toc_match = re.search(
            r"^##\s+Tabla de Contenido\s*$", text, re.MULTILINE | re.IGNORECASE
        )
        if not toc_match:
            report.error(f"{path.name}: falta la sección '## Tabla de Contenido'")
            continue
        next_heading = re.search(r"^##\s+\S", text[toc_match.end():], re.MULTILINE)
        toc_body = (
            text[toc_match.end(): toc_match.end() + next_heading.start()]
            if next_heading
            else text[toc_match.end():]
        )
        toc_anchors = set(re.findall(r"\(#([^)]+)\)", toc_body))
        other_headings = [
            heading
            for heading in re.findall(r"^##\s+(.+?)\s*$", text, re.MULTILINE)
            if normalize(heading).lower() != "tabla de contenido"
        ]
        missing = [h for h in other_headings if slugify_heading(h) not in toc_anchors]
        if missing:
            message = (
                f"{path.name}: la Tabla de Contenido no enlaza {len(missing)} "
                f"encabezado(s) '##' (ej. {missing[0]!r})"
            )
            if strict:
                report.error(message)
            else:
                report.warning(message)


def validate_closure_and_placeholders(
    documents: dict[Path, str], report: Report, strict: bool
) -> None:
    for path, text in documents.items():
        if numbered_prefix(path) is None:
            continue
        if not re.search(r"^##\s+Criterios de cierre\s*$", text, re.MULTILINE | re.IGNORECASE):
            report.error(f"{path.name}: falta la sección '## Criterios de cierre'")
        state_match = re.search(
            r"\*\*Estado:\*\*\s*([^\r\n]+)", text, re.IGNORECASE
        )
        if not state_match:
            report.error(f"{path.name}: falta el estado de cierre")
        else:
            state = normalize(state_match.group(1).strip("[] "))
            if state not in CLOSURE_STATES:
                report.error(f"{path.name}: estado de cierre inválido: {state_match.group(1)}")
            elif state == "no cumple":
                report.error(f"{path.name}: permanece en No cumple")

        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(text):
                message = f"{path.name}: conserva placeholder o evidencia faltante ({pattern.pattern})"
                if strict:
                    report.error(message)
                else:
                    report.warning(message)


def validate_id_ownership(documents: dict[Path, str], report: Report) -> dict[str, set[str]]:
    all_ids: dict[str, set[str]] = {kind: set() for kind in ID_PATTERNS}
    occurrences: dict[tuple[str, str], set[str]] = {}
    for path, text in documents.items():
        ids = extract_ids(text)
        for kind, values in ids.items():
            all_ids[kind].update(values)
            for value in values:
                occurrences.setdefault((kind, value), set()).add(path.name)

    for kind, values in all_ids.items():
        prefixes = OWNER_PREFIXES[kind]
        owner_files = [
            path
            for path in documents
            if any(path.name.casefold().startswith(prefix) for prefix in prefixes)
        ]
        for value in sorted(values):
            definitions = [path.name for path in owner_files if value in documents[path]]
            if not definitions:
                refs = ", ".join(sorted(occurrences[(kind, value)]))
                report.error(f"{value}: no está definido en su artefacto dueño; aparece en {refs}")
            elif len(definitions) > 1:
                report.error(f"{value}: aparece en múltiples artefactos dueño: {definitions}")
    return all_ids


def validate_api_operation_readiness(
    documents: dict[Path, str], report: Report
) -> None:
    catalogs = [
        (path, text)
        for path, text in documents.items()
        if path.name.casefold().startswith("14.00-")
    ]
    if not catalogs:
        return
    if len(catalogs) != 1:
        report.error(f"Se esperaba un único catálogo 14.00; hay {len(catalogs)}")
        return
    path, text = catalogs[0]
    section = find_section(text, "Catálogo inicial de operaciones")
    if not section:
        report.error(f"{path.name}: falta 'Catálogo inicial de operaciones'")
        return

    checked = 0
    for table in parse_markdown_tables(section):
        for row in table:
            operation = first_value(row, "OP ID", "Operación", "Operacion")
            match = ID_PATTERNS["API_OP"].search(operation)
            if not match:
                continue
            checked += 1
            driver = first_value(row, "FAS/QA", "Driver", "OBJ/FAS/QA")
            state = normalize(first_value(row, "Estado"))
            if (
                (ID_PATTERNS["FAS"].search(driver) or ID_PATTERNS["QA"].search(driver))
                and state.startswith("propuesta")
            ):
                report.error(
                    f"{path.name}: {match.group(0)} soporta {driver} y permanece en Propuesta"
                )
    report.metrics["catalogued_api_operations"] = checked


def validate_data_model_maturity(
    documents: dict[Path, str],
    all_ids: dict[str, set[str]],
    report: Report,
) -> None:
    details = [
        (path, text)
        for path, text in documents.items()
        if re.match(r"^16\.\d+-modelo-de-datos_", path.name, re.IGNORECASE)
    ]
    data_ids = all_ids.get("DATA", set())
    if not details:
        if data_ids:
            report.error("Existen DATA-xxx pero ningún modelo detallado 16.xx")
        return
    if not data_ids:
        report.error("Existen modelos 16.xx pero 16-Modelo-de-Datos.md no cataloga DATA-xxx")

    covered_ids: set[str] = set()
    physical_extensions = {
        ".sql", ".dbml", ".prisma", ".xml", ".json", ".yaml", ".yml",
        ".py", ".ts", ".js", ".cs", ".java", ".kt", ".hcl",
    }
    for path, text in details:
        targets = re.findall(r"\[[^\]]*\]\(([^)]+)\)", text)
        physical_targets: list[str] = []
        physical_assets: list[Path] = []
        for target in targets:
            clean_target = unquote(target.split("#", 1)[0].strip().strip("<>"))
            if not clean_target or re.match(
                r"^[a-z][a-z0-9+.-]*:", clean_target, re.IGNORECASE
            ):
                continue
            asset = (path.parent / clean_target).resolve()
            if (
                re.match(r"^16\.\d+\.\d+-", asset.name, re.IGNORECASE)
                and asset.suffix.casefold() in physical_extensions
                and asset.is_file()
            ):
                physical_targets.append(clean_target)
                physical_assets.append(asset)

        maturity = find_section(text, "Nivel de madurez del modelo")
        if not maturity:
            report.error(f"{path.name}: falta 'Nivel de madurez del modelo'")
        else:
            normalized = normalize(maturity)
            objective = re.search(
                r"\*\*Objetivo de entrega:\*\*\s*([^\r\n]+)",
                maturity,
                re.IGNORECASE,
            )
            if not objective:
                report.error(f"{path.name}: no declara '**Objetivo de entrega:**'")
            for level in ("conceptual", "logico", "fisico"):
                if level not in normalized:
                    report.error(f"{path.name}: la madurez no evalúa el nivel {level}")

            if objective and normalize(objective.group(1)).startswith("listo para implementacion"):
                if not physical_targets:
                    report.error(
                        f"{path.name}: objetivo Listo para implementación sin esquema físico procesable 16.xx.y"
                    )
                if not find_section(text, "Esquema físico y validación"):
                    report.error(
                        f"{path.name}: objetivo Listo para implementación sin sección de esquema físico y validación"
                    )

        if physical_assets:
            validate_physical_dictionary(path, text, physical_assets, report)

        coverage = find_section(text, "Matriz de cobertura de persistencia")
        if not coverage:
            report.error(f"{path.name}: falta 'Matriz de cobertura de persistencia'")
            continue
        tables = parse_markdown_tables(coverage)
        rows = tables[0] if tables else []
        if not rows:
            report.error(f"{path.name}: la matriz de cobertura de persistencia está vacía")
            continue
        headers = set(rows[0])
        required_header_groups = {
            "driver": ("driver", "fas/qa/sec"),
            "interfaz/origen": ("api/op", "evento", "origen"),
            "esquema": ("esquema", "schema"),
            "dato": ("data",),
            "entidad lógica": ("entidad", "estructura logica"),
            "estructura física/store": ("tabla", "coleccion", "store", "objeto"),
            "operación": ("operacion", "consulta dominante"),
            "clasificación": ("clasificacion",),
            "retención": ("retencion", "borrado"),
        }
        for label, tokens in required_header_groups.items():
            if not any(any(token in header for token in tokens) for header in headers):
                report.error(f"{path.name}: matriz de persistencia sin columna de {label}")
        for row in rows:
            covered_ids.update(ID_PATTERNS["DATA"].findall(" | ".join(row.values())))

    for data_id in sorted(data_ids - covered_ids):
        report.error(f"{data_id}: no aparece en ninguna matriz de cobertura de persistencia 16.xx")
    report.metrics["data_models"] = len(details)
    report.metrics["covered_data_ids"] = len(covered_ids)


def validate_snapshot(
    directory: Path, documents: dict[Path, str], audit_text: str, report: Report
) -> None:
    section = find_section(audit_text, "Snapshot de artefactos auditados")
    if not section:
        report.error("25: falta 'Snapshot de artefactos auditados'")
        return
    rows = parse_markdown_table(section)
    if not rows:
        report.error("25: el snapshot no contiene una tabla válida")
        return
    row_text = "\n".join(" | ".join(row.values()) for row in rows).casefold()
    candidates = [
        path
        for path in sorted(directory.iterdir())
        if path.is_file()
        and numbered_prefix(path) is not None
        and numbered_prefix(path) < 25
        and not path.name.casefold().startswith("00-")
    ]
    for path in candidates:
        if path.name.casefold() not in row_text:
            report.error(f"25 snapshot: falta {path.name}")
            continue
        matching_rows = [row for row in rows if path.name.casefold() in " | ".join(row.values()).casefold()]
        hashes = set(re.findall(r"\b[0-9a-fA-F]{64}\b", " ".join(" | ".join(row.values()) for row in matching_rows)))
        if not hashes:
            report.error(f"25 snapshot: {path.name} no registra SHA-256")
        elif sha256(path).casefold() not in {value.casefold() for value in hashes}:
            report.error(f"25 snapshot: SHA-256 no coincide para {path.name}")
    report.metrics["snapshot_files"] = len(candidates)


def ids_in_rows(rows: Iterable[dict[str, str]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        for value in row.values():
            for pattern in ID_PATTERNS.values():
                result.update(pattern.findall(value))
    return result


def validate_commitments(
    audit_text: str,
    all_ids: dict[str, set[str]],
    scenario: str,
    report: Report,
) -> None:
    section = find_section(audit_text, "Matriz de compromisos arquitectónicos")
    if not section:
        report.error("25: falta la matriz de compromisos arquitectónicos")
        return
    rows = parse_markdown_table(section)
    if not rows:
        report.error("25: la matriz de compromisos no contiene una tabla válida")
        return
    covered = ids_in_rows(rows)
    required = set().union(*(all_ids[kind] for kind in COMMITMENT_TYPES))
    missing = sorted(required - covered)
    for value in missing:
        report.error(f"25 compromisos: falta {value}")

    for index, row in enumerate(rows, start=1):
        row_ids = extract_ids(" | ".join(row.values()))
        commitment_ids = set().union(*(row_ids[kind] for kind in COMMITMENT_TYPES))
        if len(commitment_ids) > 1:
            report.error(
                f"25 compromisos fila {index}: use una fila por ID fuente; contiene {sorted(commitment_ids)}"
            )
        state_raw = first_value(row, "Estado")
        state = normalize(state_raw)
        if state not in EVIDENCE_STATES:
            report.error(f"25 compromisos fila {index}: estado inválido '{state_raw}'")
            continue
        if scenario in {"A", "C"} and state == "definido":
            report.error(f"25 compromisos fila {index}: 'Definido' no demuestra respuesta de diseño")
        if scenario == "B" and state in {
            "definido",
            "disenado",
            "verificado en diseno",
            "demostrado",
        }:
            report.error(
                f"25 compromisos fila {index}: Caso B requiere evidencia Implementada o superior"
            )
        response = first_value(row, "Respuesta de diseño", "Respuesta de diseno")
        evidence = first_value(row, "Evidencia/validación", "Evidencia/validacion", "Evidencia")
        if state not in {"no aplica", "desviado con aprobacion"} and (not response or not evidence):
            report.error(f"25 compromisos fila {index}: faltan respuesta de diseño o evidencia")
    report.metrics["commitments_required"] = len(required)
    report.metrics["commitments_covered"] = len(required & covered)


def validate_design_traceability(
    audit_text: str, all_ids: dict[str, set[str]], report: Report
) -> None:
    section = find_section(audit_text, "Trazabilidad bidireccional de elementos de diseño")
    if not section:
        report.error("25: falta la trazabilidad bidireccional de elementos de diseño")
        return
    rows = parse_markdown_table(section)
    if not rows:
        report.error("25: la trazabilidad bidireccional no contiene una tabla válida")
        return
    covered = ids_in_rows(rows)
    required = set().union(*(all_ids[kind] for kind in DESIGN_TYPES))
    for value in sorted(required - covered):
        report.error(f"25 trazabilidad inversa: falta justificar {value}")
    for index, row in enumerate(rows, start=1):
        row_ids = extract_ids(" | ".join(row.values()))
        design_ids = set().union(*(row_ids[kind] for kind in DESIGN_TYPES))
        if len(design_ids) != 1:
            report.error(
                f"25 diseño fila {index}: debe contener exactamente un ARQ/CT/API/TP material; contiene {sorted(design_ids)}"
            )
        state_raw = first_value(row, "Estado")
        state = normalize(state_raw)
        if state not in DESIGN_STATES:
            report.error(f"25 diseño fila {index}: estado inválido '{state_raw}'")
        elif state == "no cumple":
            report.error(f"25 diseño fila {index}: elemento de diseño no justificado")
        driver = first_value(
            row,
            "Driver/restricción/decisión",
            "Driver/restriccion/decision",
            "Driver/decisión",
        )
        owner = first_value(row, "Artefacto dueño", "Artefacto dueno")
        if state == "justificado" and (not driver or not owner):
            report.error(f"25 diseño fila {index}: faltan driver o artefacto dueño")
    report.metrics["design_elements_required"] = len(required)
    report.metrics["design_elements_covered"] = len(required & covered)


def validate_contradictions(audit_text: str, report: Report) -> None:
    section = find_section(audit_text, "Registro de contradicciones y elementos huérfanos")
    if not section:
        report.error("25: falta el registro de contradicciones y elementos huérfanos")
        return
    rows = parse_markdown_table(section)
    if not rows:
        report.error("25: el registro de contradicciones no contiene una tabla válida")
        return
    open_blocking = 0
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        row_id = first_value(row, "ID")
        con_match = ID_PATTERNS["CON"].search(row_id)
        if not con_match:
            report.error(f"25 contradicciones fila {index}: falta ID CON-xxx")
        elif con_match.group(0) in seen_ids:
            report.error(f"25 contradicciones: ID duplicado {con_match.group(0)}")
        else:
            seen_ids.add(con_match.group(0))
        state_raw = first_value(row, "Estado")
        severity_raw = first_value(row, "Severidad")
        state = normalize(state_raw)
        severity = normalize(severity_raw)
        if state in OPEN_STATES and severity in BLOCKING_SEVERITIES:
            open_blocking += 1
            report.error(
                f"25 contradicciones fila {index}: {severity_raw} permanece {state_raw}"
            )
        elif state in OPEN_STATES:
            report.warning(f"25 contradicciones fila {index}: permanece {state_raw}")
        if state == "aceptada":
            disposition = first_value(row, "Disposición", "Disposicion")
            if not ID_PATTERNS["DA"].search(disposition):
                report.error(
                    f"25 contradicciones fila {index}: aceptación sin DA-xxx en disposición"
                )
    report.metrics["blocking_contradictions_open"] = open_blocking


def validate_indicators_and_verdict(audit_text: str, report: Report) -> None:
    indicators = find_section(audit_text, "Indicadores de cobertura")
    if not indicators or not parse_markdown_table(indicators):
        report.error("25: faltan indicadores de cobertura en tabla")

    verdict = find_section(audit_text, "Dictamen de auditoría")
    if not verdict:
        report.error("25: falta el dictamen de auditoría")
        return
    result_match = re.search(r"\*\*Resultado:\*\*\s*([^\r\n]+)", verdict, re.IGNORECASE)
    blockers_match = re.search(
        r"\*\*Bloqueantes abiertos:\*\*\s*(\d+)", verdict, re.IGNORECASE
    )
    if not result_match:
        report.error("25: el dictamen no declara Resultado")
        return
    result = normalize(result_match.group(1).strip("[] "))
    if result not in {"apto", "apto con observaciones", "no apto"}:
        report.error(f"25: resultado de auditoría inválido: {result_match.group(1)}")
    if not blockers_match:
        report.error("25: el dictamen no declara un número de bloqueantes abiertos")
    elif int(blockers_match.group(1)) > 0 and result != "no apto":
        report.error("25: el dictamen se declara apto con bloqueantes abiertos")


DBA_OPEN_DISPOSITIONS = {None, "", "pendiente", "diferida"}
DBA_NOTE_REQUIRED = {"rechazada-justificada", "riesgo-aceptado"}


def validate_expert_data_review(directory: Path, documents: dict[Path, str], report: Report) -> None:
    """Integra la revisión experta de datos de la skill `dba` (16.00 / 16.00.1).

    - Con `16.00.1-*.json`: ninguna observación bloqueante/mayor puede quedar pendiente o
      diferida; las rechazadas o con riesgo aceptado exigen nota; las incorporadas y los
      riesgos deben citarse en los artefactos dueños.
    - Con modelos `16.xx` y sin `16.00`: advierte salvo que `16` declare la revisión
      experta como no disponible.
    """
    models = [p for p in documents if re.match(r"^16\.\d+-modelo-de-datos_", p.name, re.IGNORECASE)
              and not p.name.startswith("16.00")]
    reviews = [p for p in documents if p.name.casefold().startswith("16.00-revision-experta-datos")]
    json_files = sorted(directory.rglob("16.00.1-*.json"))
    if models and not reviews:
        main_model = "\n".join(t for p, t in documents.items() if p.name.casefold().startswith("16-modelo-de-datos"))
        if "revision experta de datos" not in normalize(main_model):
            report.warning("Hay modelos 16.xx sin revisión experta de datos (16.00 de `dba`) ni declaración "
                           "'Revisión experta de datos: No disponible' en 16")
    owners_text = {p.name: t for p, t in documents.items()}
    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.error(f"{jf.name}: JSON ilegible ({exc})")
            continue
        for finding in data.get("findings", []) if isinstance(data, dict) else []:
            fid = finding.get("id", "?")
            sev = finding.get("severity")
            disp = finding.get("disposition")
            status = finding.get("status")
            if sev in ("bloqueante", "mayor") and status not in ("verificado", "retirado") and disp in DBA_OPEN_DISPOSITIONS:
                report.error(f"{jf.name}: {fid} ({sev}) sin disposición de archi (estado '{disp or 'pendiente'}')")
            if disp in DBA_NOTE_REQUIRED and not finding.get("disposition_note"):
                report.error(f"{jf.name}: {fid} con disposición '{disp}' requiere disposition_note")
            if disp == "riesgo-aceptado" and not any(
                name.casefold().startswith("21-") and fid in text for name, text in owners_text.items()
            ):
                report.warning(f"{jf.name}: {fid} con riesgo aceptado no aparece en 21-Riesgos-y-Deuda-Tecnica")
            if disp == "incorporada" and not any(
                re.match(r"^(16|17|20)[.-]", name) and not name.startswith("16.00") and fid in text
                for name, text in owners_text.items()
            ):
                report.warning(f"{jf.name}: {fid} marcada incorporada pero ningún artefacto dueño (16.xx/17/20) la cita")


def find_audit(documents: dict[Path, str], report: Report) -> tuple[Path | None, str]:
    candidates = [
        (path, text)
        for path, text in documents.items()
        if path.name.casefold().startswith("25-revision-tecnica-arquitectura")
    ]
    if len(candidates) != 1:
        report.error(f"Se esperaba un único 25-Revision-Tecnica-Arquitectura.md; hay {len(candidates)}")
        return None, ""
    return candidates[0]


def validate_directory(directory: Path, scenario: str, strict: bool) -> Report:
    from validate_pricing import validate_directory as validate_costs

    report = Report()
    documents = read_documents(directory, report)
    if not documents:
        return report
    validate_required_files(documents, scenario, report)
    validate_domain_readiness(documents, scenario, report)
    validate_alternative_diagrams(documents, scenario, report)
    validate_archetype_analysis(documents, report)
    validate_links(documents, report)
    validate_table_of_contents(documents, report, strict)
    validate_closure_and_placeholders(documents, report, strict)
    all_ids = validate_id_ownership(documents, report)
    validate_api_operation_readiness(documents, report)
    validate_data_model_maturity(documents, all_ids, report)
    validate_expert_data_review(directory, documents, report)
    report.errors.extend(validate_costs(directory))
    _, audit_text = find_audit(documents, report)
    if audit_text:
        validate_snapshot(directory, documents, audit_text, report)
        validate_commitments(audit_text, all_ids, scenario, report)
        validate_design_traceability(audit_text, all_ids, report)
        validate_contradictions(audit_text, report)
        validate_indicators_and_verdict(audit_text, report)
    report.metrics["markdown_files"] = len(documents)
    return report


def closure() -> str:
    return "\n## Criterios de cierre\n**Estado:** Cumple\n\n- [x] Evidencia disponible\n"


def with_generated_toc(markdown: str) -> str:
    """Inserta una '## Tabla de Contenido' que enlaza los '##' existentes.

    Usado solo por self_test() para mantener los fixtures sincronizados con la
    regla de Tabla de Contenido sin tener que escribirla a mano en cada uno.
    """
    title, _, rest = markdown.partition("\n")
    headings = re.findall(r"^##\s+(.+?)\s*$", rest, re.MULTILINE)
    if not headings:
        return markdown
    items = "\n".join(f"- [{h}](#{slugify_heading(h)})" for h in headings)
    return f"{title}\n\n## Tabla de Contenido\n{items}\n{rest}"


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="archi-coherence-") as temp_name:
        root = Path(temp_name)
        sources = {
            "01-Linea-Base_Test.md": """# Línea base

## Preparación del dominio
| Campo | Valor |
|---|---|
| Escenario | A |
| Complejidad del dominio | Complejo |
| Event Storming | Obligatorio |
| Estado del modelo | validado-dominio |
| Estado DR-01 | Listo |
| Evidencia | resources/functional/eventstorming/ES-002.md |
| Hotspots arquitectónicos bloqueantes | Ninguno |
| Handoff pendiente | Ninguno |
| Riesgos no bloqueantes | Ninguno |
| Justificación | Proceso transversal validado con expertos de dominio |
""" + closure(),
            "02-Contexto-y-Alcance.md": "# Contexto\nOBJ-01 objetivo" + closure(),
            "03-Restricciones.md": "# Restricciones\nRT-D01 restricción" + closure(),
            "04-Supuestos.md": "# Supuestos\nSUP-D01 supuesto" + closure(),
            "05-Atributos-de-Calidad.md": "# Calidad\nQA-01 escenario OBJ-01" + closure(),
            "06-Funcionalidades-Significativas.md": "# FAS\nFAS-001 funcionalidad" + closure(),
            "07-Resultado-QAW.md": "# QAW" + closure(),
            "08-Well-Architected.md": "# Well-Architected" + closure(),
            "09-Alternativas-de-Solucion.md": """# Alternativas

### Alternativa A — Consolidada

#### Diagrama lógico
```mermaid
flowchart LR
    U[Usuario] --> A[Aplicación]
```

### Alternativa B — Distribuida

#### Diagrama lógico
```mermaid
flowchart LR
    U[Usuario] --> G[Gateway] --> S[Servicio]
```
""" + closure(),
            "10-Seleccion-de-Arquitectura.md": "# Selección" + closure(),
            "10.1-Arquetipo-de-Solucion_Test.md": """# Arquetipo

## Definición y propósito de los arquetipos
Los scaffolds estandarizan la construcción.

## Perfil detallado del proyecto
ARQ-001 representa la composición principal seleccionada.

## Arquetipos identificados
| `ARQ-xxx` | Nombre | Scopes | Estado |
|---|---|---|---|
| ARQ-002 | test-archetype-api | FAS-001 | Seleccionado |

## Análisis detallado por arquetipo

### ARQ-002 — test-archetype-api

#### Scopes y componentes objetivo
FAS-001.

#### Propósito y cuándo usarlo
API transaccional estándar.

#### Características principales
Runtime y framework confirmados.

#### Estructura de carpetas propuesta
```text
test-archetype-api/
├── src/
└── test/
```

#### Patrones y controles incorporados
Controles trazables.

#### Contrato de desarrollo
Build y pruebas definidos.

#### Configuración y secretos
Solo archivo de ejemplo sin credenciales.

#### Diferencias y reutilización
No existe baseline previo, según línea base.

#### Criterios de aceptación del scaffold
Generación y build limpio.

## Baseline tecnológico canónico
Baseline seleccionado.

## Componentes compartidos e integraciones
Sin componentes compartidos en esta prueba.

## Convenciones transversales
Nombres y pruebas estandarizados.

## Datos, seguridad y operación
Criterios enlazados.

## Patrones, desviaciones, legado y evolución

### Relación con arquetipos existentes
No existe baseline previo.

## Prioridad de construcción
ARQ-002 es la base inicial.

## Decisiones de framework y baseline
Decisiones enlazadas.

## Matriz de trazabilidad
FAS-001 → ARQ-002.
""" + closure(),
            "12-Registro-de-Incertidumbres.md": "# Incertidumbres" + closure(),
            "14-Vistas-C4.md": "# C4\nCT-01 API" + closure(),
            "14.00-Gobierno-y-Catalogo-Inicial-de-APIs_Test.md": """# API
API-001 catálogo

## Catálogo inicial de operaciones
| OP ID | FAS/QA | Propósito | Estado |
|---|---|---|---|
| API-001-OP-001 | FAS-001 | Operación de prueba | Definida |
""" + closure(),
            "15-Secuencias.md": "# Secuencias" + closure(),
            "16-Modelo-de-Datos.md": "# Datos\nDATA-001 dato canónico de CT-01" + closure(),
            "16.01-Modelo-de-Datos_CT-01_API.md": """# Modelo de datos CT-01

## Nivel de madurez del modelo
**Objetivo de entrega:** Arquitectónico

| Nivel | Estado | Evidencia | Vacío/condición para avanzar | Owner |
|---|---|---|---|---|
| Conceptual | Completo | ER | — | Arquitectura |
| Lógico | Completo | Entidades | — | Arquitectura |
| Físico | No requerido todavía | — | Antes de implementar | Datos |

## Matriz de cobertura de persistencia
| Driver FAS/QA/SEC/otro | API/OP/evento/job/origen | Esquema de intercambio | DATA-xxx | Entidad/estructura lógica | Tabla/colección/objeto/store | Operación y consulta dominante | Clasificación | Retención/borrado |
|---|---|---|---|---|---|---|---|---|
| FAS-001 | API-001-OP-001 | RequestSchema | DATA-001 | EntidadPrueba | PostgreSQL | Crear/consultar | Interno | 30 días |
""" + closure(),
            "18-Tacticas-y-Patrones.md": "# Patrones\nTP-001 táctica QA-01" + closure(),
            "19-Dimensiones-Arquitectonicas.md": "# Dimensiones" + closure(),
            "19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_Test.md": "# Seguridad\nSEC-001 requisito" + closure(),
            "20-Decisiones-Arquitectonicas.md": "# Decisiones" + closure(),
            "21-Riesgos-y-Deuda-Tecnica.md": "# Riesgos" + closure(),
            "22-Glosario.md": "# Glosario" + closure(),
        }
        for name, content in sources.items():
            (root / name).write_text(with_generated_toc(content), encoding="utf-8")
        snapshot = "\n".join(
            f"| {name} | Sí | {sha256(root / name)} | Cumple | — |" for name in sources
        )
        audit = f"""# Revisión técnica

### Snapshot de artefactos auditados
| Artefacto | Aplicable | Versión/SHA-256 | Estado de cierre | Observaciones |
|---|---|---|---|---|
{snapshot}

### Matriz de compromisos arquitectónicos
| ID fuente/compromiso | Tipo | Promesa o criterio verificable | Respuesta de diseño | Evidencia/validación | Estado | Desviación/DA | Responsable |
|---|---|---|---|---|---|---|---|
| OBJ-01 | Objetivo | Criterio | CT-01 | Diseño | Verificado en diseño | — | Arquitectura |
| RT-D01 | Restricción | Criterio | CT-01 | Diseño | Verificado en diseño | — | Arquitectura |
| SUP-D01 | Supuesto | Criterio | CT-01 | Diseño | Verificado en diseño | — | Arquitectura |
| QA-01 | Calidad | Criterio | CT-01, TP-001 | Diseño | Verificado en diseño | — | Arquitectura |
| FAS-001 | Funcionalidad | Criterio | CT-01 | Diseño | Verificado en diseño | — | Arquitectura |
| SEC-001 | Seguridad | Criterio | CT-01 | Diseño | Verificado en diseño | — | Arquitectura |

### Trazabilidad bidireccional de elementos de diseño
| Elemento de diseño | Tipo | Driver/restricción/decisión | Artefacto dueño | Evidencia | Estado |
|---|---|---|---|---|---|
| ARQ-001 | Arquetipo | OBJ-01 | 10.1 | Baseline | Justificado |
| ARQ-002 | Arquetipo implementable | FAS-001 | 10.1 | Scaffold | Justificado |
| CT-01 | Contenedor | FAS-001 | 14 | C4 | Justificado |
| API-001 | API | FAS-001 | 14.00 | Contrato | Justificado |
| DATA-001 | Dato | FAS-001 | 16 | Modelo lógico | Justificado |
| TP-001 | Táctica | QA-01 | 18 | Ficha | Justificado |

### Registro de contradicciones y elementos huérfanos
| ID | Descripción | Artefactos afectados | Severidad | Disposición | Responsable | Estado | Evidencia de cierre |
|---|---|---|---|---|---|---|---|
| CON-001 | Sin contradicciones | — | Baja | Cerrada | Arquitectura | Cerrada | Revisión |

### Indicadores de cobertura
| Indicador | Numerador | Denominador | Resultado | Umbral | Estado |
|---|---:|---:|---:|---:|---|
| Compromisos | 6 | 6 | 100% | 100% | Cumple |

### Dictamen de auditoría
**Resultado:** Apto
**Bloqueantes abiertos:** 0
**Fundamento:** Matrices completas
{closure()}
"""
        (root / "25-Revision-Tecnica-Arquitectura.md").write_text(
            with_generated_toc(audit), encoding="utf-8"
        )
        report = validate_directory(root, "A", True)
        if report.errors:
            for error in report.errors:
                print(f"SELF-TEST ERROR: {error}")
            return 1

        baseline_path = root / "01-Linea-Base_Test.md"
        valid_baseline = baseline_path.read_text(encoding="utf-8")
        baseline_path.write_text(
            with_generated_toc("# Línea base sin preparación de dominio" + closure()),
            encoding="utf-8",
        )
        missing_domain_report = validate_directory(root, "A", True)
        if not any("DR-01" in error for error in missing_domain_report.errors):
            print("SELF-TEST ERROR: DR-01 no rechazó una línea base sin preparación del dominio")
            return 1
        baseline_path.write_text(valid_baseline, encoding="utf-8")

        as_is_domain_report = Report()
        validate_domain_readiness({}, "B", as_is_domain_report)
        if as_is_domain_report.errors:
            print("SELF-TEST ERROR: DR-01 bloqueó incorrectamente un escenario B AS-IS")
            return 1

        scenario_c_text = valid_baseline.replace("| A |", "| C |", 1)
        scenario_c_report = Report()
        validate_domain_readiness({baseline_path: scenario_c_text}, "C", scenario_c_report)
        if scenario_c_report.errors:
            print("SELF-TEST ERROR: DR-01 rechazó incorrectamente un escenario C válido")
            return 1

        bypass_text = scenario_c_text.replace(
            "| Event Storming | Obligatorio |",
            "| Event Storming | Evidencia equivalente |",
        ).replace(
            "| Estado del modelo | validado-dominio |",
            "| Estado del modelo | evidencia-equivalente |",
        )
        bypass_report = Report()
        validate_domain_readiness({baseline_path: bypass_text}, "C", bypass_report)
        if not any("dominio complejo" in error for error in bypass_report.errors):
            print("SELF-TEST ERROR: DR-01 permitió omitir Event Storming en un dominio complejo")
            return 1

        physical_asset = root / "16.01.1-Schema_DATA-001.sql"
        physical_asset.write_text(
            """CREATE TABLE app.entity_test (
    id uuid PRIMARY KEY,
    value text NOT NULL DEFAULT 'test'
);
CREATE VIEW reporting.v_entity_test AS
SELECT id, value FROM app.entity_test;
""",
            encoding="utf-8",
        )
        dictionary_model_path = root / "16.01-Modelo-de-Datos_CT-01_API.md"
        physical_dictionary = """# Modelo físico

## Diccionario físico de datos

### `app.entity_test` — Tabla

- **DATA:** DATA-001
- **Propósito:** Entidad de prueba.
- **Owner:** CT-01 / Equipo API
- **Rol del dato:** Fuente de verdad
- **Clasificación:** Interno
- **Retención/borrado:** 30 días
- **Seguridad/RLS:** Mínimo privilegio
- **Índices/particiones:** PK id; sin partición
- **Consumidores/operaciones:** API-001-OP-001

| Columna | Tipo | Nulo | Default | Clave/referencia | Restricciones | Clasificación/PII | Descripción |
|---|---|---|---|---|---|---|---|
| id | uuid | No | N/A — asignado por aplicación | PK | UUID válido | Interno | Identificador |
| value | text | No | test | N/A — sin referencia | No vacío | Interno | Valor de prueba |

### `reporting.v_entity_test` — Vista

- **DATA:** DATA-001
- **Propósito:** Proyección de prueba.
- **Owner:** CT-01 / Equipo API
- **Rol del dato:** Proyección derivada
- **Clasificación:** Interno
- **Retención/borrado:** Heredada de app.entity_test
- **Seguridad/RLS:** Solo lectura
- **Índices/particiones:** N/A — vista no materializada
- **Consumidores/operaciones:** Reporting
- **Fuentes/frescura:** app.entity_test; tiempo real

| Columna | Tipo | Nulo | Default | Clave/referencia | Restricciones | Clasificación/PII | Descripción |
|---|---|---|---|---|---|---|---|
| id | uuid | No | N/A — derivada | Referencia lógica | — | Interno | Identificador |
| value | text | No | N/A — derivada | N/A — sin referencia | — | Interno | Valor |
"""
        dictionary_report = Report()
        validate_physical_dictionary(
            dictionary_model_path, physical_dictionary, [physical_asset], dictionary_report
        )
        if dictionary_report.errors:
            for error in dictionary_report.errors:
                print(f"SELF-TEST ERROR: diccionario físico válido rechazado: {error}")
            return 1
        missing_column_report = Report()
        validate_physical_dictionary(
            dictionary_model_path,
            physical_dictionary.replace(
                "| value | text | No | test | N/A — sin referencia | No vacío | Interno | Valor de prueba |\n",
                "",
            ),
            [physical_asset],
            missing_column_report,
        )
        if not any(
            "app.entity_test.value no está documentada" in error
            for error in missing_column_report.errors
        ):
            print("SELF-TEST ERROR: no detectó una columna física sin documentar")
            return 1
        missing_view_report = Report()
        validate_physical_dictionary(
            dictionary_model_path,
            physical_dictionary.split("### `reporting.v_entity_test`")[0],
            [physical_asset],
            missing_view_report,
        )
        if not any(
            "reporting.v_entity_test no está documentado" in error
            for error in missing_view_report.errors
        ):
            print("SELF-TEST ERROR: no detectó una vista física sin documentar")
            return 1

        alternatives_path = root / "09-Alternativas-de-Solucion.md"
        valid_alternatives = alternatives_path.read_text(encoding="utf-8")
        alternatives_path.write_text(
            valid_alternatives.replace(
                "```mermaid\nflowchart LR\n    U[Usuario] --> G[Gateway] --> S[Servicio]\n```",
                "La topología distribuida queda pendiente de diagrama.",
            ),
            encoding="utf-8",
        )
        invalid_diagram_report = validate_directory(root, "A", True)
        if not any(
            "Alternativa B" in error and "bloque Mermaid propio" in error
            for error in invalid_diagram_report.errors
        ):
            print("SELF-TEST ERROR: la prueba negativa no detectó una alternativa sin Mermaid")
            return 1
        alternatives_path.write_text(valid_alternatives, encoding="utf-8")
        archetype_path = root / "10.1-Arquetipo-de-Solucion_Test.md"
        valid_archetype = archetype_path.read_text(encoding="utf-8")
        archetype_path.write_text(
            valid_archetype.replace(
                "```text\ntest-archetype-api/\n├── src/\n└── test/\n```",
                "Estructura pendiente sin justificación.",
            ),
            encoding="utf-8",
        )
        invalid_archetype_report = validate_directory(root, "A", True)
        if not any(
            "ARQ-002" in error and "no contiene árbol de carpetas" in error
            for error in invalid_archetype_report.errors
        ):
            print("SELF-TEST ERROR: la prueba negativa no detectó un arquetipo sin estructura")
            return 1
        archetype_path.write_text(valid_archetype, encoding="utf-8")

        api_path = root / "14.00-Gobierno-y-Catalogo-Inicial-de-APIs_Test.md"
        valid_api = api_path.read_text(encoding="utf-8")
        api_path.write_text(
            valid_api.replace(
                "| API-001-OP-001 | FAS-001 | Operación de prueba | Definida |",
                "| API-001-OP-001 | FAS-001 | Operación de prueba | Propuesta |",
            ),
            encoding="utf-8",
        )
        invalid_api_report = validate_directory(root, "A", True)
        if not any(
            "API-001-OP-001" in error and "permanece en Propuesta" in error
            for error in invalid_api_report.errors
        ):
            print("SELF-TEST ERROR: no detectó una operación priorizada en Propuesta")
            return 1
        api_path.write_text(valid_api, encoding="utf-8")

        data_path = root / "16.01-Modelo-de-Datos_CT-01_API.md"
        valid_data = data_path.read_text(encoding="utf-8")
        data_path.write_text(
            valid_data.replace(
                "| FAS-001 | API-001-OP-001 | RequestSchema | DATA-001 | EntidadPrueba | PostgreSQL | Crear/consultar | Interno | 30 días |\n",
                "",
            ),
            encoding="utf-8",
        )
        invalid_coverage_report = validate_directory(root, "A", True)
        if not any(
            "matriz de cobertura de persistencia está vacía" in error
            for error in invalid_coverage_report.errors
        ):
            print("SELF-TEST ERROR: no detectó una matriz de persistencia vacía")
            return 1

        data_path.write_text(
            valid_data.replace(
                "**Objetivo de entrega:** Arquitectónico",
                "**Objetivo de entrega:** Listo para implementación",
            ),
            encoding="utf-8",
        )
        invalid_physical_report = validate_directory(root, "A", True)
        if not any(
            "sin esquema físico procesable" in error
            for error in invalid_physical_report.errors
        ):
            print("SELF-TEST ERROR: no detectó un modelo listo sin esquema físico")
            return 1
        data_path.write_text(valid_data, encoding="utf-8")

        invalid_audit = audit.replace(
            "| QA-01 | Calidad | Criterio | CT-01, TP-001 | Diseño | Verificado en diseño | — | Arquitectura |\n",
            "",
        )
        (root / "25-Revision-Tecnica-Arquitectura.md").write_text(
            with_generated_toc(invalid_audit), encoding="utf-8"
        )
        invalid_report = validate_directory(root, "A", True)
        if not any("falta QA-01" in error for error in invalid_report.errors):
            print("SELF-TEST ERROR: la prueba negativa no detectó QA-01 sin cobertura")
            return 1
    print(
        "SELF-TEST OK: auditoría válida, DR-01 A/C, exención B, rechazo de bypass y alternativa sin Mermaid, "
        "arquetipo sin estructura, operación priorizada en Propuesta, cobertura de "
        "persistencia vacía, modelo físico faltante, tabla/vista/columna física sin "
        "documentar y compromiso faltante"
    )
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida coherencia y contrato de auditoría de artefactos archi."
    )
    parser.add_argument("architecture_dir", nargs="?", type=Path)
    parser.add_argument("--scenario", choices=("A", "B", "C"), default="A")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    if args.architecture_dir is None:
        print("ERROR: architecture_dir es obligatorio salvo con --self-test")
        return 2
    report = validate_directory(args.architecture_dir.resolve(), args.scenario, args.strict)
    for warning in report.warnings:
        print(f"WARN: {warning}")
    for error in report.errors:
        print(f"ERROR: {error}")
    payload = {
        "directory": str(args.architecture_dir.resolve()),
        "scenario": args.scenario,
        "strict": args.strict,
        "errors": report.errors,
        "warnings": report.warnings,
        "metrics": report.metrics,
        "valid": not report.errors and (not args.strict or not report.warnings),
    }
    if args.json_output:
        args.json_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if report.errors or (args.strict and report.warnings):
        print(f"FAIL: {len(report.errors)} error(es), {len(report.warnings)} advertencia(s)")
        return 1
    print(
        f"OK: {report.metrics.get('markdown_files', 0)} documentos; "
        f"{report.metrics.get('commitments_covered', 0)}/"
        f"{report.metrics.get('commitments_required', 0)} compromisos; "
        f"{report.metrics.get('design_elements_covered', 0)}/"
        f"{report.metrics.get('design_elements_required', 0)} elementos justificados"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
