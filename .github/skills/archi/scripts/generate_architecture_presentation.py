#!/usr/bin/env python3
"""Genera 25.1 HTML desde el manifiesto estructurado de arquitectura."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

TOKEN = "__PRESENTATION_DATA__"
REQUIRED = {
    "schemaVersion", "project", "scenario", "review", "decisionRequest",
    "executiveSummary", "workPerformed", "drivers", "alternatives",
    "selection", "architecture", "security", "validation", "risks", "sources", "conflicts",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"La fuente sale del project-root: {relative}") from exc
    return candidate


def validate_shape(data: dict) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED - set(data))
    if missing:
        errors.append("Campos obligatorios ausentes: " + ", ".join(missing))
    if data.get("schemaVersion") != "1.0":
        errors.append("schemaVersion debe ser 1.0")
    if data.get("scenario") not in {"A", "B", "C"}:
        errors.append("scenario debe ser A, B o C")
    project = data.get("project", {})
    for key in ("name", "version", "date", "authors"):
        if not project.get(key):
            errors.append(f"project.{key} es obligatorio")
    review = data.get("review", {})
    if review.get("status") not in {"Cumple", "Cumple con observaciones", "No cumple"}:
        errors.append("review.status no es válido")
    if "auditVerdict" in review and review.get("auditVerdict") not in {
        "Apto", "Apto con observaciones", "No apto"
    }:
        errors.append("review.auditVerdict no es válido")
    coherence = review.get("coherenceValidator")
    if coherence is not None:
        if not isinstance(coherence, dict):
            errors.append("review.coherenceValidator debe ser un objeto")
        elif coherence.get("status") not in {
            "Correcto", "Con advertencias", "Fallido", "No ejecutado"
        }:
            errors.append("review.coherenceValidator.status no es válido")
        else:
            if not coherence.get("command"):
                errors.append("review.coherenceValidator.command es obligatorio")
            for key in ("errors", "warnings"):
                if not isinstance(coherence.get(key), int) or coherence.get(key) < 0:
                    errors.append(f"review.coherenceValidator.{key} debe ser entero no negativo")
    if not isinstance(review.get("blockingFindings", []), list):
        errors.append("review.blockingFindings debe ser una lista")
    for key in ("workPerformed", "drivers", "alternatives", "risks", "sources", "conflicts"):
        if not isinstance(data.get(key), list):
            errors.append(f"{key} debe ser una lista")
    return errors


def unresolved_conflicts(data: dict) -> list[dict]:
    return [
        conflict for conflict in data.get("conflicts", [])
        if conflict.get("status") == "Abierto" and conflict.get("severity") in {"Bloqueante", "Alta"}
    ]


def selection_is_valid(data: dict) -> bool:
    if data.get("scenario") == "B":
        return data.get("selection", {}).get("status") in {"Observado", "No aplica", "Cumple"}
    return data.get("selection", {}).get("status") in {"Seleccionada", "Seleccionado", "Cumple"}


def calculated_eligibility(data: dict) -> bool:
    review = data.get("review", {})
    audit_ok = review.get("auditVerdict") in {None, "Apto", "Apto con observaciones"}
    coherence = review.get("coherenceValidator")
    coherence_ok = coherence is None or (
        isinstance(coherence, dict)
        and coherence.get("status") == "Correcto"
        and coherence.get("errors") == 0
    )
    return (
        review.get("status") in {"Cumple", "Cumple con observaciones"}
        and not review.get("blockingFindings", [])
        and not unresolved_conflicts(data)
        and selection_is_valid(data)
        and audit_ok
        and coherence_ok
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--project-root", default=Path.cwd(), type=Path)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = args.project_root.resolve()
    output_path = (args.output if args.output.is_absolute() else root / args.output).resolve()
    manifest_path = (args.manifest if args.manifest.is_absolute() else root / args.manifest).resolve()
    skill_root = Path(__file__).resolve().parents[1]
    template_path = args.template or skill_root / "assets" / "plantilla-presentacion-arquitectura.html"
    if not template_path.is_absolute():
        template_path = (root / template_path).resolve()

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: no se pudo leer el manifiesto: {exc}", file=sys.stderr)
        return 2

    errors = validate_shape(data)
    source_ids: set[str] = set()
    for index, source in enumerate(data.get("sources", []), start=1):
        source_id = source.get("id")
        relative = source.get("path")
        if not source_id or source_id in source_ids:
            errors.append(f"sources[{index}] tiene id vacío o duplicado")
            continue
        source_ids.add(source_id)
        if not relative:
            errors.append(f"sources[{index}] no tiene path")
            continue
        try:
            path = resolve_inside(root, relative)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.is_file():
            errors.append(f"Fuente inexistente: {relative}")
            continue
        source["sha256"] = sha256(path)
        source["href"] = Path(os.path.relpath(path, output_path.parent)).as_posix()

    diagram_paths: set[str] = set()
    for key in ("architecture", "data", "deployment", "security", "validation", "economics"):
        section = data.get(key, {})
        if isinstance(section, dict):
            diagram_paths.update(section.get("diagrams", []) or [])
    for collection in ("workPerformed", "drivers", "alternatives", "uncertainties", "pocs", "criticalFlows", "tactics", "decisions", "risks", "roadmap"):
        for item in data.get(collection, []) or []:
            if isinstance(item, dict) and item.get("diagram"):
                diagram_paths.add(item["diagram"])
    data["assetHrefs"] = {}
    for relative in diagram_paths:
        try:
            asset = resolve_inside(root, relative)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if asset.is_file():
            data["assetHrefs"][relative] = Path(os.path.relpath(asset, output_path.parent)).as_posix()

    eligible = calculated_eligibility(data)
    declared = data.get("review", {}).get("approvalEligible")
    if declared is True and not eligible:
        errors.append("approvalEligible=true contradice el estado real del gate")
    data.setdefault("review", {})["approvalEligible"] = eligible

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.strict and not eligible:
        print("ERROR: la presentación no es apta para aprobación; revise bloqueos, conflictos y selección", file=sys.stderr)
        return 3

    try:
        template = template_path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        print(f"ERROR: no se pudo leer la plantilla: {exc}", file=sys.stderr)
        return 2
    if template.count(TOKEN) != 1:
        print(f"ERROR: la plantilla debe contener exactamente un token {TOKEN}", file=sys.stderr)
        return 2

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output = template.replace(TOKEN, payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8", newline="\n")
    mode = "APTA PARA APROBACIÓN" if eligible else "BORRADOR — NO APTO PARA APROBACIÓN"
    print(f"OK: {output_path} ({mode})")
    print(f"SHA-256: {sha256(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
