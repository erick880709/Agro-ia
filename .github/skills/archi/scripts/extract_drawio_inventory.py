#!/usr/bin/env python3
"""Extrae un inventario determinista de un diagrama de despliegue `.drawio`.

Fuente del blueprint de IaC (`17.7.1-Inventario-Despliegue_<Proyecto>.json`, ver
`references/guia-diagrama-a-iac.md`). Lee XML sin compresión y produce: recursos con
`archiIconId`, jerarquía de límites que los contienen, conectores con etiqueta y conteos.

Uso:
    python extract_drawio_inventory.py --drawio 17.1-Despliegue_AWS_X.drawio [--output inv.json]
    python extract_drawio_inventory.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = SKILL_DIR / "assets" / "iconos" / "catalogo_iconos_curado.json"
BOUNDARY_HINTS = ("container=1", "shape=mxgraph.aws4.group", "swimlane")


def style_map(style: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for part in style.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            result[key.strip()] = value.strip()
        elif part.strip():
            result[part.strip()] = "1"
    return result


def load_catalog(path: Path) -> dict[str, dict[str, Any]]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    index: dict[str, dict[str, Any]] = {}
    for provider in catalog.get("providers", {}).values():
        for icon in provider.get("icons", []):
            index[icon["id"]] = icon
    return index


def cell_attrs(element: ET.Element) -> tuple[dict[str, str], ET.Element | None]:
    """Devuelve atributos combinados de <object>/<UserObject> + <mxCell> interno."""
    if element.tag in ("object", "UserObject"):
        inner = element.find("mxCell")
        attrs = dict(inner.attrib) if inner is not None else {}
        attrs.update({k: v for k, v in element.attrib.items()})
        if "label" in element.attrib and "value" not in attrs:
            attrs["value"] = element.attrib["label"]
        return attrs, inner
    return dict(element.attrib), element


def extract(drawio: Path, catalog_path: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    raw = drawio.read_bytes()
    root = ET.fromstring(raw)
    diagrams = root.findall("diagram") if root.tag == "mxfile" else []
    model = root if root.tag == "mxGraphModel" else root.find(".//mxGraphModel")
    if model is None:
        raise ValueError("No se encontró mxGraphModel; el XML podría estar comprimido")
    catalog = load_catalog(catalog_path)

    cells: dict[str, dict[str, str]] = {}
    for element in model.iter():
        if element.tag not in ("mxCell", "object", "UserObject"):
            continue
        if element.tag == "mxCell" and element.attrib.get("id") is None:
            continue
        attrs, _ = cell_attrs(element)
        cid = attrs.get("id")
        if cid and cid not in cells:
            cells[cid] = attrs

    parents_of_vertices = {a.get("parent") for a in cells.values() if a.get("vertex") == "1"}

    def is_boundary(attrs: dict[str, str]) -> bool:
        icon = catalog.get(attrs.get("archiIconId", ""), {})
        if icon.get("category") == "boundary":
            return True
        if attrs.get("vertex") != "1" or attrs.get("archiIconId"):
            return False
        style = attrs.get("style", "")
        # Un límite es un contenedor declarado o un vértice que agrupa otros vértices.
        return any(h in style for h in BOUNDARY_HINTS) or attrs.get("id") in parents_of_vertices

    def chain(cid: str) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        parent = cells.get(cid, {}).get("parent")
        while parent and parent in cells and parent not in seen:
            seen.add(parent)
            if is_boundary(cells[parent]):
                result.append(parent)
            parent = cells[parent].get("parent")
        return list(reversed(result))

    boundaries, resources, edges, missing = [], [], [], []
    for cid, attrs in cells.items():
        if attrs.get("vertex") == "1" and is_boundary(attrs):
            boundaries.append({
                "id": cid,
                "label": attrs.get("value", ""),
                "archiIconId": attrs.get("archiIconId"),
                "parents": chain(cid),
            })
    for cid, attrs in cells.items():
        if attrs.get("vertex") != "1" or is_boundary(attrs):
            continue
        icon_id = attrs.get("archiIconId")
        style = attrs.get("style", "")
        looks_like_icon = "mxgraph." in style or "img/lib/" in style
        if not icon_id:
            if looks_like_icon:
                missing.append(cid)
            continue
        icon = catalog.get(icon_id, {})
        resources.append({
            "id": cid,
            "label": attrs.get("value", ""),
            "archiIconId": icon_id,
            "service": icon.get("displayName", "desconocido"),
            "category": icon.get("category", "desconocida"),
            "boundaries": chain(cid),
        })
    resource_ids = {r["id"] for r in resources}
    for cid, attrs in cells.items():
        if attrs.get("edge") != "1":
            continue
        edges.append({
            "id": cid,
            "source": attrs.get("source"),
            "target": attrs.get("target"),
            "label": attrs.get("value", ""),
            "dashed": style_map(attrs.get("style", "")).get("dashed") == "1",
            "betweenResources": attrs.get("source") in resource_ids and attrs.get("target") in resource_ids,
        })

    providers = sorted({r["archiIconId"].split(".", 1)[0] for r in resources})
    counts = Counter(r["archiIconId"] for r in resources)
    findings = []
    if missing:
        findings.append(f"Celdas con icono sin archiIconId: {', '.join(sorted(missing))}")
    unlabeled = [e["id"] for e in edges if not e["label"].strip()]
    if unlabeled:
        findings.append(f"Conectores sin etiqueta (propósito/protocolo): {', '.join(unlabeled)}")
    orphans = sorted(resource_ids - {e["source"] for e in edges} - {e["target"] for e in edges})
    if orphans:
        findings.append(f"Recursos sin conectores: {', '.join(orphans)}")

    return {
        "schemaVersion": "1.0",
        "source": {"file": drawio.name, "sha256": hashlib.sha256(raw).hexdigest(), "pages": max(len(diagrams), 1)},
        "providers": providers,
        "totals": {"resources": len(resources), "boundaries": len(boundaries), "edges": len(edges)},
        "countsByIcon": dict(sorted(counts.items())),
        "boundaries": sorted(boundaries, key=lambda b: b["id"]),
        "resources": sorted(resources, key=lambda r: r["id"]),
        "edges": sorted(edges, key=lambda e: e["id"]),
        "findings": findings,
    }


SELF_TEST_XML = """<mxfile><diagram id="p1" name="AWS"><mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="cloud" value="AWS Cloud" archiIconId="aws.group-cloud" style="shape=mxgraph.aws4.group;container=1;" vertex="1" parent="1"><mxGeometry as="geometry"/></mxCell>
<mxCell id="vpc" value="VPC" archiIconId="aws.group-vpc" style="shape=mxgraph.aws4.group;container=1;" vertex="1" parent="cloud"><mxGeometry as="geometry"/></mxCell>
<mxCell id="az" value="us-east-1a" style="fillColor=none;strokeColor=#147EBA;dashed=1;container=1;" vertex="1" parent="vpc"><mxGeometry as="geometry"/></mxCell>
<mxCell id="alb" value="ALB" archiIconId="aws.application-load-balancer" style="shape=mxgraph.aws4.resourceIcon;" vertex="1" parent="az"><mxGeometry as="geometry"/></mxCell>
<object id="svc" label="API (CT-01)" archiIconId="aws.ecs"><mxCell style="shape=mxgraph.aws4.resourceIcon;" vertex="1" parent="az"><mxGeometry as="geometry"/></mxCell></object>
<mxCell id="db" value="Aurora" archiIconId="aws.aurora" style="shape=mxgraph.aws4.resourceIcon;" vertex="1" parent="az"><mxGeometry as="geometry"/></mxCell>
<mxCell id="e1" value="HTTPS" edge="1" source="alb" target="svc" parent="1" style="edgeStyle=orthogonalEdgeStyle;"><mxGeometry relative="1" as="geometry"/></mxCell>
<mxCell id="e2" value="" edge="1" source="svc" target="db" parent="1" style="dashed=1;"><mxGeometry relative="1" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>"""


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "t.drawio"
        path.write_text(SELF_TEST_XML, encoding="utf-8")
        inv = extract(path)
    assert inv["totals"] == {"resources": 3, "boundaries": 3, "edges": 2}, inv["totals"]
    svc = next(r for r in inv["resources"] if r["id"] == "svc")
    assert svc["boundaries"] == ["cloud", "vpc", "az"], svc
    assert svc["label"] == "API (CT-01)"
    assert inv["providers"] == ["aws"]
    assert any("sin etiqueta" in f for f in inv["findings"]), inv["findings"]
    assert inv["edges"][1]["dashed"] is True
    print("OK: autoprueba de extract_drawio_inventory")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--drawio", type=Path)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.drawio:
        parser.error("--drawio es obligatorio (o use --self-test)")
    try:
        inventory = extract(args.drawio, args.catalog)
    except (ET.ParseError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    text = json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"OK: {inventory['totals']['resources']} recursos, {inventory['totals']['boundaries']} límites, "
              f"{inventory['totals']['edges']} conectores → {args.output}")
    else:
        sys.stdout.write(text)
    for finding in inventory["findings"]:
        print(f"HALLAZGO: {finding}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
