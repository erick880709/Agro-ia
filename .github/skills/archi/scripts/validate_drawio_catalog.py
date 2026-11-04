#!/usr/bin/env python3
"""Valida el catálogo curado de iconos y los .drawio generados por archi.

No requiere dependencias externas. La validación deliberadamente no decide la
arquitectura: comprueba trazabilidad visual, consistencia de proveedor y uso de
bibliotecas soportadas después de que el diseño haya sido definido.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = SKILL_ROOT / "assets" / "iconos" / "catalogo_iconos_curado.json"
DEFAULT_ALIASES = SKILL_ROOT / "assets" / "iconos" / "aliases_iconos.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SHA = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDER = re.compile(r"\[CT-[^\]]+\]", re.IGNORECASE)


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text.strip())


def read_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"No se pudo leer JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"La raíz de {path} debe ser un objeto JSON")
        return {}
    return value


def validate_catalog(
    catalog_path: Path, aliases_path: Path
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    catalog = read_json(catalog_path, errors)
    aliases_document = read_json(aliases_path, errors)
    if not catalog or not aliases_document:
        return {}, errors, warnings

    if catalog.get("schemaVersion") != "1.0":
        errors.append("catalogo: schemaVersion debe ser 1.0")
    if not SEMVER.fullmatch(str(catalog.get("catalogVersion", ""))):
        errors.append("catalogo: catalogVersion debe usar SemVer (x.y.z)")
    try:
        date.fromisoformat(str(catalog.get("generatedAt", "")))
    except ValueError:
        errors.append("catalogo: generatedAt debe ser una fecha ISO YYYY-MM-DD")

    source = catalog.get("source")
    if not isinstance(source, dict):
        errors.append("catalogo: falta source")
        source = {}
    if source.get("repository") != "https://github.com/jgraph/drawio":
        errors.append("catalogo: source.repository debe apuntar al repositorio oficial de draw.io")
    if not SHA.fullmatch(str(source.get("ref", ""))):
        errors.append("catalogo: source.ref debe fijar un commit SHA de 40 caracteres")
    if not SEMVER.fullmatch(str(source.get("drawioVersion", ""))):
        errors.append("catalogo: source.drawioVersion debe usar SemVer")
    if not source.get("sourceFiles") or not source.get("terms"):
        errors.append("catalogo: source debe declarar sourceFiles y terms")

    providers = catalog.get("providers")
    if not isinstance(providers, dict):
        errors.append("catalogo: providers debe ser un objeto")
        return {}, errors, warnings

    expected = {
        "azure": ("azure2", "image"),
        "aws": ("aws4", "stencil"),
        "gcp": ("gcp3", "stencil"),
    }
    index: dict[str, dict[str, Any]] = {}
    normalized_icon_aliases: dict[str, str] = {}

    for provider, (library, mechanism) in expected.items():
        definition = providers.get(provider)
        if not isinstance(definition, dict):
            errors.append(f"catalogo: falta el proveedor {provider}")
            continue
        if definition.get("library") != library:
            errors.append(f"catalogo: {provider}.library debe ser {library}")
        if definition.get("mechanism") != mechanism:
            errors.append(f"catalogo: {provider}.mechanism debe ser {mechanism}")
        icons = definition.get("icons")
        if not isinstance(icons, list) or not icons:
            errors.append(f"catalogo: {provider}.icons debe ser una lista no vacía")
            continue

        for position, icon in enumerate(icons, start=1):
            context = f"catalogo: {provider}.icons[{position}]"
            if not isinstance(icon, dict):
                errors.append(f"{context} debe ser un objeto")
                continue
            icon_id = icon.get("id")
            if not isinstance(icon_id, str) or not icon_id.startswith(f"{provider}."):
                errors.append(f"{context}.id debe iniciar con {provider}.")
                continue
            if icon_id in index:
                errors.append(f"catalogo: id duplicado {icon_id}")
                continue
            index[icon_id] = icon

            for field in ("displayName", "category", "style", "status"):
                if not icon.get(field):
                    errors.append(f"{context}: falta {field}")
            if icon.get("mechanism") != mechanism:
                errors.append(f"{context}: mechanism debe ser {mechanism}")
            if icon.get("status") not in {"active", "deprecated"}:
                errors.append(f"{context}: status debe ser active o deprecated")
            if icon.get("status") == "deprecated" and not icon.get("replacement"):
                errors.append(f"{context}: un icono deprecated requiere replacement")

            style = str(icon.get("style", ""))
            if provider == "azure":
                source_path = str(icon.get("sourcePath", ""))
                expected_image = f"img/lib/azure2/{source_path}"
                if not source_path or expected_image not in style:
                    errors.append(f"{context}: style/sourcePath no apuntan a {expected_image}")
                if "mxgraph.azure." in style or "img/lib/mscae/" in style:
                    errors.append(f"{context}: usa una biblioteca Azure legada")
            else:
                shape = str(icon.get("shape", ""))
                if not shape.startswith(f"mxgraph.{library}."):
                    errors.append(f"{context}: shape debe pertenecer a mxgraph.{library}")
                if f"shape={shape}" not in style:
                    errors.append(f"{context}: style no coincide con shape")
                res_icon = icon.get("resIcon")
                if res_icon and f"resIcon={res_icon}" not in style:
                    errors.append(f"{context}: style no coincide con resIcon")
                if "mxgraph.gcp2." in style:
                    errors.append(f"{context}: usa la biblioteca GCP2 legada")

            icon_aliases = icon.get("aliases", [])
            if not isinstance(icon_aliases, list) or not icon_aliases:
                errors.append(f"{context}: aliases debe ser una lista no vacía")
            else:
                for alias in icon_aliases:
                    normalized = normalize(str(alias))
                    previous = normalized_icon_aliases.get(normalized)
                    if previous and previous != icon_id:
                        warnings.append(
                            f"catalogo: alias ambiguo '{alias}' en {previous} y {icon_id}"
                        )
                    normalized_icon_aliases[normalized] = icon_id

        fallback = definition.get("fallback")
        if fallback not in index:
            errors.append(f"catalogo: fallback inválido para {provider}: {fallback}")

    if aliases_document.get("schemaVersion") != catalog.get("schemaVersion"):
        errors.append("aliases: schemaVersion no coincide con el catálogo")
    if aliases_document.get("catalogVersion") != catalog.get("catalogVersion"):
        errors.append("aliases: catalogVersion no coincide con el catálogo")
    aliases = aliases_document.get("aliases")
    if not isinstance(aliases, dict):
        errors.append("aliases: aliases debe ser un objeto")
    else:
        normalized_file_aliases: dict[str, str] = {}
        for alias, icon_id in aliases.items():
            normalized = normalize(str(alias))
            if alias != normalized:
                errors.append(f"aliases: la clave '{alias}' no está normalizada como '{normalized}'")
            if icon_id not in index:
                errors.append(f"aliases: '{alias}' apunta a un id inexistente: {icon_id}")
            previous = normalized_file_aliases.get(normalized)
            if previous and previous != icon_id:
                errors.append(f"aliases: clave ambigua '{alias}'")
            normalized_file_aliases[normalized] = str(icon_id)

    return index, errors, warnings


def style_map(style: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in style.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def validate_drawio(
    path: Path,
    catalog: dict[str, dict[str, Any]],
    provider: str | None,
    strict: bool,
    reference: bool,
    allow_multiple_pages: bool,
) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as exc:
        return [f"drawio: no se pudo leer {path}: {exc}"], warnings, 0

    root = tree.getroot()
    diagrams = [node for node in root if node.tag.rsplit("}", 1)[-1] == "diagram"]
    if not diagrams:
        errors.append("drawio: no contiene elementos <diagram>")
    elif len(diagrams) != 1 and not allow_multiple_pages:
        errors.append(f"drawio: debe contener una sola página; se encontraron {len(diagrams)}")

    cells = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "mxCell"]
    if not cells and diagrams and any((node.text or "").strip() for node in diagrams):
        errors.append("drawio: el XML está comprimido; guárdelo sin compresión para poder auditarlo")

    icon_count = 0
    used_providers: set[str] = set()
    for cell in cells:
        if cell.get("vertex") != "1":
            continue
        cell_id = cell.get("id", "(sin id)")
        style = cell.get("style", "")
        attributes = style_map(style)
        image = attributes.get("image", "")
        shape = attributes.get("shape", "")
        res_icon = attributes.get("resIcon", "")
        icon_id = cell.get("archiIconId")
        exception = cell.get("archiIconException")

        if "img/lib/mscae/" in style or "mxgraph.azure." in style:
            errors.append(f"drawio:{cell_id}: biblioteca Azure legada; use azure2")
        if "mxgraph.gcp2." in style:
            errors.append(f"drawio:{cell_id}: biblioteca GCP2 legada; use gcp3")

        detected: set[str] = set()
        if "img/lib/azure2/" in image:
            detected.add("azure")
        if "mxgraph.aws4." in style:
            detected.add("aws")
        if "mxgraph.gcp3." in style:
            detected.add("gcp")
        if image.startswith("data:image"):
            message = f"drawio:{cell_id}: imagen embebida fuera del catálogo"
            if strict and not exception:
                errors.append(message + "; declare archiIconException o use el catálogo")
            else:
                warnings.append(message)

        is_icon = bool(detected or image or shape.startswith("mxgraph."))
        if not is_icon:
            continue
        icon_count += 1
        used_providers.update(detected)

        if len(detected) > 1:
            errors.append(f"drawio:{cell_id}: mezcla bibliotecas de proveedor en una celda")
        if provider and detected and provider not in detected:
            errors.append(
                f"drawio:{cell_id}: icono {sorted(detected)} incompatible con proveedor {provider}"
            )

        if not icon_id:
            message = f"drawio:{cell_id}: falta archiIconId"
            if strict and not exception:
                errors.append(message)
            else:
                warnings.append(message)
            continue
        icon = catalog.get(icon_id)
        if icon is None:
            errors.append(f"drawio:{cell_id}: archiIconId inexistente: {icon_id}")
            continue
        icon_provider = icon_id.split(".", 1)[0]
        if provider and icon_provider != provider:
            errors.append(
                f"drawio:{cell_id}: {icon_id} no pertenece al proveedor esperado {provider}"
            )
        if detected and icon_provider not in detected:
            errors.append(
                f"drawio:{cell_id}: la biblioteca visual no coincide con {icon_id}"
            )
        if icon.get("status") == "deprecated":
            errors.append(
                f"drawio:{cell_id}: {icon_id} está deprecated; use {icon.get('replacement')}"
            )

        mechanism = icon.get("mechanism")
        if mechanism == "image":
            expected_image = f"img/lib/azure2/{icon.get('sourcePath', '')}"
            if image != expected_image:
                errors.append(
                    f"drawio:{cell_id}: image no coincide con {icon_id}; esperado {expected_image}"
                )
        elif mechanism == "stencil":
            if shape != icon.get("shape"):
                errors.append(
                    f"drawio:{cell_id}: shape no coincide con {icon_id}; esperado {icon.get('shape')}"
                )
            expected_res_icon = icon.get("resIcon")
            if expected_res_icon and res_icon != expected_res_icon:
                errors.append(
                    f"drawio:{cell_id}: resIcon no coincide con {icon_id}; esperado {expected_res_icon}"
                )

    if icon_count == 0:
        errors.append("drawio: no se encontraron iconos de infraestructura auditables")
    if len(used_providers) > 1:
        errors.append(f"drawio: mezcla proveedores en un mismo archivo: {sorted(used_providers)}")

    if not reference:
        for cell in cells:
            value = cell.get("value", "")
            if PLACEHOLDER.search(value):
                errors.append(
                    f"drawio:{cell.get('id', '(sin id)')}: conserva un placeholder [CT-*]"
                )

    return errors, warnings, icon_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida el catálogo curado y, opcionalmente, un archivo draw.io."
    )
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--aliases", type=Path, default=DEFAULT_ALIASES)
    parser.add_argument("--drawio", type=Path)
    parser.add_argument("--provider", choices=("azure", "aws", "gcp"))
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exige archiIconId y excepción explícita para imágenes fuera del catálogo.",
    )
    parser.add_argument(
        "--reference",
        action="store_true",
        help="Permite placeholders [CT-*] únicamente al validar la referencia neutra.",
    )
    parser.add_argument("--allow-multiple-pages", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index, errors, warnings = validate_catalog(args.catalog, args.aliases)
    icon_count = len(index)
    if args.drawio and index:
        drawio_errors, drawio_warnings, used_icons = validate_drawio(
            args.drawio,
            index,
            args.provider,
            args.strict,
            args.reference,
            args.allow_multiple_pages,
        )
        errors.extend(drawio_errors)
        warnings.extend(drawio_warnings)
    else:
        used_icons = 0

    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAIL: {len(errors)} error(es), {len(warnings)} advertencia(s)")
        return 1
    if args.drawio:
        print(
            f"OK: catálogo ({icon_count} iconos) y draw.io ({used_icons} iconos trazables) válidos"
        )
    else:
        print(f"OK: catálogo válido ({icon_count} iconos; {len(warnings)} advertencia(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
