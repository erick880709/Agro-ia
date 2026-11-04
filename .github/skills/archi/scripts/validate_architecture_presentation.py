#!/usr/bin/env python3
"""Valida estructura, gate, fuentes y operación offline de 25.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

DATA_RE = re.compile(r'<script\s+type="application/json"\s+id="presentation-data">(.*?)</script>', re.DOTALL)
ID_RE = re.compile(r'\bid="([^"]+)"')
REMOTE_RE = re.compile(r'(?:src|href)=["\']https?://', re.IGNORECASE)
REQUIRED_KEYS = {
    "schemaVersion", "project", "scenario", "review", "decisionRequest",
    "executiveSummary", "workPerformed", "drivers", "alternatives", "selection",
    "architecture", "security", "validation", "risks", "sources", "conflicts",
}
REQUIRED_MARKERS = (
    "executive", "architecture", "complete", "Trabajo realizado y gates",
    "Alternativas y trade-offs", "Arquitectura diseñada", "Datos y ownership",
    "Cloud, despliegue y operación", "Seguridad arquitectónica", "Validación y ATAM", "Riesgos, deuda y condiciones",
    "BORRADOR — NO APTO PARA APROBACIÓN",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_inside(root: Path, relative: str) -> Path | None:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def walk_source_refs(value, path="$", refs=None):
    refs = refs if refs is not None else []
    if isinstance(value, dict):
        if "source" in value and isinstance(value["source"], dict):
            refs.append((f"{path}.source", value["source"].get("id")))
        for key, nested in value.items():
            if key not in {"sources", "source"}:
                walk_source_refs(nested, f"{path}.{key}", refs)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            walk_source_refs(nested, f"{path}[{index}]", refs)
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--presentation", required=True, type=Path)
    parser.add_argument("--project-root", default=Path.cwd(), type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    presentation_path = (args.presentation if args.presentation.is_absolute() else root / args.presentation).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    try:
        html = presentation_path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        print(f"ERROR: no se pudo leer la presentación: {exc}", file=sys.stderr)
        return 2

    if "__PRESENTATION_DATA__" in html:
        errors.append("La plantilla conserva el token sin reemplazar")
    match = DATA_RE.search(html)
    if not match:
        errors.append("No existe el bloque application/json presentation-data")
        data = {}
    else:
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            errors.append(f"El manifiesto embebido no es JSON válido: {exc}")
            data = {}

    missing = sorted(REQUIRED_KEYS - set(data))
    if missing:
        errors.append("Campos obligatorios ausentes: " + ", ".join(missing))
    for marker in REQUIRED_MARKERS:
        if marker not in html:
            errors.append(f"La plantilla no contiene el marcador obligatorio: {marker}")
    ids = ID_RE.findall(html)
    duplicates = sorted({identifier for identifier in ids if ids.count(identifier) > 1})
    if duplicates:
        errors.append("IDs HTML duplicados: " + ", ".join(duplicates))
    if REMOTE_RE.search(html):
        errors.append("El HTML depende de recursos HTTP(S); debe funcionar sin conexión")

    sources = data.get("sources", []) if isinstance(data.get("sources"), list) else []
    source_map: dict[str, dict] = {}
    for index, source in enumerate(sources):
        source_id, relative = source.get("id"), source.get("path")
        if not source_id or source_id in source_map:
            errors.append(f"Fuente {index + 1} con id vacío o duplicado")
            continue
        source_map[source_id] = source
        if not relative:
            errors.append(f"Fuente {source_id} sin path")
            continue
        source_path = resolve_inside(root, relative)
        if source_path is None:
            errors.append(f"Fuente fuera de project-root: {relative}")
        elif not source_path.is_file():
            errors.append(f"Fuente inexistente: {relative}")
        elif source.get("sha256") != sha256(source_path):
            errors.append(f"Hash desactualizado o ausente: {relative}")

    for location, source_id in walk_source_refs(data):
        if not source_id:
            errors.append(f"Referencia de fuente vacía en {location}")
        elif source_id not in source_map:
            errors.append(f"Referencia a fuente desconocida {source_id} en {location}")

    diagram_paths: set[str] = set()
    for key in ("architecture", "data", "deployment", "security", "validation", "economics"):
        section = data.get(key, {})
        if isinstance(section, dict):
            diagram_paths.update(section.get("diagrams", []) or [])
    for collection in ("workPerformed", "drivers", "alternatives", "uncertainties", "pocs", "criticalFlows", "tactics", "decisions", "risks", "roadmap"):
        for item in data.get(collection, []) or []:
            if isinstance(item, dict) and item.get("diagram"):
                diagram_paths.add(item["diagram"])
    for relative in sorted(diagram_paths):
        diagram = resolve_inside(root, relative)
        if diagram is None or not diagram.is_file():
            errors.append(f"Asset de diagrama inexistente o fuera del proyecto: {relative}")
        elif diagram.suffix.lower() not in {".svg", ".png", ".jpg", ".jpeg", ".webp"}:
            errors.append(f"Formato de diagrama no renderizable directamente: {relative}")

    review = data.get("review", {})
    eligible = review.get("approvalEligible") is True
    blocking = review.get("blockingFindings", []) or []
    open_material = [c for c in data.get("conflicts", []) or [] if c.get("status") == "Abierto" and c.get("severity") in {"Bloqueante", "Alta"}]
    selection_status = (data.get("selection") or {}).get("status")
    selection_ok = selection_status in ({"Observado", "No aplica", "Cumple"} if data.get("scenario") == "B" else {"Seleccionada", "Seleccionado", "Cumple"})
    audit_ok = review.get("auditVerdict") in {None, "Apto", "Apto con observaciones"}
    coherence = review.get("coherenceValidator")
    coherence_ok = coherence is None or (
        isinstance(coherence, dict)
        and coherence.get("status") == "Correcto"
        and coherence.get("errors") == 0
    )
    calculated = (
        review.get("status") in {"Cumple", "Cumple con observaciones"}
        and not blocking
        and not open_material
        and selection_ok
        and audit_ok
        and coherence_ok
    )
    if eligible != calculated:
        errors.append(
            "approvalEligible contradice revisión, auditoría de coherencia, bloqueos, conflictos o selección"
        )
    if eligible:
        for key in ("workPerformed", "drivers", "alternatives", "risks"):
            if not data.get(key):
                errors.append(f"Una presentación apta no puede dejar vacío {key}")
        for key in ("architecture", "security", "validation"):
            section = data.get(key, {})
            if not section or "missing evidence" in str(section.get("summary", "")).lower():
                errors.append(f"Una presentación apta carece de evidencia material en {key}")
    elif "document.body.classList.toggle('draft', !review.approvalEligible)" not in html:
        errors.append("La presentación borrador no activa el watermark desde el gate")

    if not diagram_paths:
        warnings.append("No se declararon diagramas exportados; confirme que el escenario realmente no los requiere")
    if not data.get("economics"):
        warnings.append("No existe economics; el resumen debe explicar costo como Missing evidence o No aplica")
    if data.get("scenario") == "C" and not data.get("roadmap"):
        errors.append("Caso C requiere roadmap en la presentación")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"RESULTADO: NO CUMPLE ({len(errors)} errores, {len(warnings)} advertencias)", file=sys.stderr)
        return 2
    print(f"RESULTADO: CUMPLE ({len(warnings)} advertencias)")
    print(f"SHA-256 presentación: {sha256(presentation_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
