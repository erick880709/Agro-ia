#!/usr/bin/env python3
"""Valida la calidad visual de un .drawio de despliegue (complementa validate_drawio_catalog.py).

validate_drawio_catalog.py verifica QUÉ icono se usa; este script verifica CÓMO está dibujado:
conectores ortogonales, etiquetas, extremos válidos, conectores que atraviesan nodos ajenos,
solapamientos, nodos fuera de su contenedor, tamaños de icono, grilla, leyenda y presupuesto.

Uso:
    python validate_drawio_layout.py --drawio 17.2-Despliegue_Azure_X.drawio [--strict] [--reference]
    python validate_drawio_layout.py --self-test

Sale con código 1 si hay errores (o advertencias con --strict).
"""
from __future__ import annotations

import argparse
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

ICON_MIN, ICON_MAX = 64, 78
MAX_RESOURCE_ICONS = 15
MAX_EDGES = 18
MAX_LABEL_CHARS = 40
GRID = 10
MARGIN = 4  # tolerancia en px para cruces y solapamientos


@dataclass
class Box:
    id: str
    x: float
    y: float
    w: float
    h: float
    is_container: bool
    is_icon: bool
    label: str

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def contains_box(self, o: "Box") -> bool:
        return (o.x >= self.x - MARGIN and o.y >= self.y - MARGIN
                and o.x + o.w <= self.x + self.w + MARGIN and o.y + o.h <= self.y + self.h + MARGIN)

    def intersects(self, o: "Box") -> bool:
        return not (o.x >= self.x + self.w - MARGIN or o.x + o.w <= self.x + MARGIN
                    or o.y >= self.y + self.h - MARGIN or o.y + o.h <= self.y + MARGIN)


def style_map(style: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (style or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
        elif part.strip():
            out[part.strip()] = "1"
    return out


def seg_hits_box(x1: float, y1: float, x2: float, y2: float, b: Box) -> bool:
    """Segmento horizontal o vertical contra el interior de una caja (con margen)."""
    bx1, by1 = b.x + MARGIN, b.y + MARGIN
    bx2, by2 = b.x + b.w - MARGIN, b.y + b.h - MARGIN
    if abs(y1 - y2) < 0.5:  # horizontal
        lo, hi = sorted((x1, x2))
        return by1 < y1 < by2 and lo < bx2 and hi > bx1
    if abs(x1 - x2) < 0.5:  # vertical
        lo, hi = sorted((y1, y2))
        return bx1 < x1 < bx2 and lo < by2 and hi > by1
    return False


def candidate_routes(s: Box, t: Box, waypoints: list[tuple[float, float]]) -> list[list[tuple[float, float]]]:
    """Aproxima la ruta ortogonal de draw.io. Con waypoints se usa la ruta declarada."""
    if waypoints:
        pts = [(s.cx, s.cy)] + waypoints + [(t.cx, t.cy)]
        route: list[tuple[float, float]] = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            if abs(ax - bx) > 0.5 and abs(ay - by) > 0.5:
                route.append((bx, ay))
            route.append((bx, by))
        return [route]
    if abs(s.cy - t.cy) < 0.5 or abs(s.cx - t.cx) < 0.5:
        return [[(s.cx, s.cy), (t.cx, t.cy)]]
    mx = (s.cx + t.cx) / 2
    my = (s.cy + t.cy) / 2
    return [
        [(s.cx, s.cy), (mx, s.cy), (mx, t.cy), (t.cx, t.cy)],  # Z horizontal
        [(s.cx, s.cy), (s.cx, my), (t.cx, my), (t.cx, t.cy)],  # Z vertical
        [(s.cx, s.cy), (t.cx, s.cy), (t.cx, t.cy)],            # L horizontal
        [(s.cx, s.cy), (s.cx, t.cy), (t.cx, t.cy)],            # L vertical
    ]


def route_hits(route: list[tuple[float, float]], boxes: list[Box]) -> list[str]:
    hits = []
    for b in boxes:
        for (x1, y1), (x2, y2) in zip(route, route[1:]):
            if seg_hits_box(x1, y1, x2, y2, b):
                hits.append(b.id)
                break
    return hits


def validate(path: Path, reference: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        return [f"no se pudo leer {path}: {exc}"], warnings

    cells = list(root.iter("mxCell"))
    if not cells:
        return ["no hay mxCell (¿XML comprimido?)"], warnings
    by_id = {c.get("id"): c for c in cells}
    parents_with_children = {c.get("parent") for c in cells if c.get("vertex") == "1"}

    abs_cache: dict[str, tuple[float, float]] = {}

    def origin(cid: str | None) -> tuple[float, float]:
        if cid is None or cid not in by_id:
            return (0.0, 0.0)
        if cid in abs_cache:
            return abs_cache[cid]
        c = by_id[cid]
        g = c.find("mxGeometry")
        px, py = origin(c.get("parent"))
        if c.get("vertex") == "1" and g is not None:
            res = (px + float(g.get("x", 0)), py + float(g.get("y", 0)))
        else:
            res = (px, py)
        abs_cache[cid] = res
        return res

    boxes: dict[str, Box] = {}
    for c in cells:
        if c.get("vertex") != "1":
            continue
        g = c.find("mxGeometry")
        if g is None or g.get("relative") == "1":
            continue  # etiquetas hijas de edges
        st = style_map(c.get("style", ""))
        x, y = origin(c.get("id"))
        is_container = (c.get("id") in parents_with_children or st.get("container") == "1"
                        or st.get("swimlane") == "1" or "group" in st.get("shape", ""))
        is_icon = not is_container and bool(c.get("archiIconId") or st.get("shape") == "image" or "resIcon" in st
                       or st.get("shape", "").startswith("mxgraph.gcp3"))
        boxes[c.get("id")] = Box(c.get("id"), x, y, float(g.get("width", 0)), float(g.get("height", 0)),
                                 is_container, is_icon, (c.get("value") or "").strip())

        # Grilla
        if not reference:
            for attr in ("x", "y"):
                v = float(g.get(attr, 0))
                if abs(v % GRID) > 0.01 and abs(v % GRID - GRID) > 0.01:
                    warnings.append(f"{c.get('id')}: {attr}={v:g} fuera de la grilla de {GRID}px")
                    break

    icons = [b for b in boxes.values() if b.is_icon]
    for b in icons:
        if not (ICON_MIN <= b.w <= ICON_MAX and ICON_MIN <= b.h <= ICON_MAX):
            errors.append(f"{b.id}: icono de {b.w:g}x{b.h:g}px; use {ICON_MIN}-{ICON_MAX}px")
        if not b.label:
            errors.append(f"{b.id}: icono sin etiqueta (componente real · servicio)")
    for c in cells:
        st = style_map(c.get("style", ""))
        if st.get("shape") == "mxgraph.aws4.resourceIcon" and st.get("strokeColor", "none") == "none":
            errors.append(f"{c.get('id')}: AWS resourceIcon con strokeColor=none: el glifo no se dibuja; use strokeColor=#ffffff")
    sizes = {(b.w, b.h) for b in icons}
    if len(sizes) > 1:
        warnings.append(f"tamaños de icono no uniformes: {sorted(sizes)}")
    if len(icons) > MAX_RESOURCE_ICONS:
        warnings.append(f"{len(icons)} recursos en una página (> {MAX_RESOURCE_ICONS}); divida en vista general + detalle")

    # Solapamientos entre iconos y desbordes de contenedor
    for i, a in enumerate(icons):
        for b in icons[i + 1:]:
            if a.intersects(b):
                errors.append(f"{a.id} y {b.id} se solapan")
    for b in boxes.values():
        parent = by_id[b.id].get("parent")
        if parent in boxes and not boxes[parent].contains_box(b):
            errors.append(f"{b.id} se sale de su contenedor {parent}")

    # Conectores
    edges = [c for c in cells if c.get("edge") == "1"]
    if len(edges) > MAX_EDGES:
        warnings.append(f"{len(edges)} conectores (> {MAX_EDGES}); divida el diagrama")
    edge_labels = {c.get("parent") for c in cells if c.get("vertex") == "1"
                   and (c.find("mxGeometry") is not None and c.find("mxGeometry").get("relative") == "1")
                   and (c.get("value") or "").strip()}
    exits: dict[tuple[str, str], int] = {}
    for e in edges:
        eid = e.get("id")
        st = style_map(e.get("style", ""))
        src, tgt = e.get("source"), e.get("target")
        if src not in boxes or tgt not in boxes:
            errors.append(f"{eid}: source/target inexistente o sin geometría ({src} → {tgt})")
            continue
        if st.get("edgeStyle") != "orthogonalEdgeStyle":
            errors.append(f"{eid}: falta edgeStyle=orthogonalEdgeStyle")
        if st.get("curved") != "0":
            errors.append(f"{eid}: declare curved=0 explícitamente")
        if st.get("rounded") not in ("0", "1", None):
            warnings.append(f"{eid}: rounded inválido")
        label = (e.get("value") or "").strip()
        if not label and eid not in edge_labels:
            errors.append(f"{eid}: conector sin etiqueta (protocolo + propósito)")
        if len(label) > MAX_LABEL_CHARS:
            warnings.append(f"{eid}: etiqueta de {len(label)} caracteres; resuma a ≤{MAX_LABEL_CHARS}")
        if "exitX" not in st:
            exits[(src, "auto")] = exits.get((src, "auto"), 0) + 1

        g = e.find("mxGeometry")
        wps: list[tuple[float, float]] = []
        if g is not None:
            arr = g.find("Array")
            if arr is not None:
                ox, oy = origin(e.get("parent"))
                wps = [(ox + float(p.get("x", 0)), oy + float(p.get("y", 0))) for p in arr.findall("mxPoint")]
        s, t = boxes[src], boxes[tgt]
        ancestors = set()
        for end in (src, tgt):
            p = by_id[end].get("parent")
            while p in by_id:
                ancestors.add(p)
                p = by_id[p].get("parent")
        obstacles = [b for b in boxes.values()
                     if b.id not in (src, tgt) and b.id not in ancestors and not b.is_container]
        routes = candidate_routes(s, t, wps)
        hit_sets = [route_hits(r, obstacles) for r in routes]
        if all(hit_sets):
            best = min(hit_sets, key=len)
            errors.append(f"{eid} ({src} → {tgt}) atraviesa {', '.join(best)}; reubique nodos o agregue waypoints")

    for (src, _), n in exits.items():
        if n >= 3:
            warnings.append(f"{src}: {n} conectores salen sin exitX/exitY fijos; reparta puntos de anclaje")

    if not any("leyenda" in (b.label or "").lower() or "legend" in (b.label or "").lower() for b in boxes.values()):
        warnings.append("no hay leyenda (existente/nuevo/compartido, síncrono/asíncrono)")
    return errors, warnings


SELF_TEST_OK = """<mxfile><diagram name="p"><mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="a" value="API · App Service" archiIconId="azure.app-service" style="shape=image;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="72" height="72" as="geometry"/></mxCell>
<mxCell id="b" value="BD · PostgreSQL" archiIconId="azure.postgresql" style="shape=image;" vertex="1" parent="1"><mxGeometry x="240" y="40" width="72" height="72" as="geometry"/></mxCell>
<mxCell id="l" value="Leyenda" style="text;" vertex="1" parent="1"><mxGeometry x="40" y="200" width="100" height="20" as="geometry"/></mxCell>
<mxCell id="e" value="SQL/TLS" style="edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;" edge="1" parent="1" source="a" target="b"><mxGeometry relative="1" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>"""

SELF_TEST_BAD = SELF_TEST_OK.replace(
    '<mxCell id="l"',
    '<mxCell id="c" value="Caché · Redis" archiIconId="azure.managed-redis" style="shape=image;" vertex="1" parent="1">'
    '<mxGeometry x="140" y="40" width="72" height="72" as="geometry"/></mxCell><mxCell id="l"'
).replace('value="SQL/TLS" style="edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;"', 'value="" style="rounded=0;"')


def self_test() -> int:
    with tempfile.TemporaryDirectory() as d:
        ok, bad = Path(d, "ok.drawio"), Path(d, "bad.drawio")
        ok.write_text(SELF_TEST_OK, encoding="utf-8")
        bad.write_text(SELF_TEST_BAD, encoding="utf-8")
        e1, _ = validate(ok, False)
        e2, _ = validate(bad, False)
    expected = ["orthogonalEdgeStyle", "curved=0", "sin etiqueta", "atraviesa"]
    missing = [x for x in expected if not any(x in e for e in e2)]
    if e1 or missing:
        print("SELF-TEST ERROR", e1, missing)
        return 1
    print("SELF-TEST OK: caso válido sin errores; caso inválido detecta estilo, curved, etiqueta y cruce")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drawio", type=Path)
    ap.add_argument("--strict", action="store_true", help="las advertencias también fallan")
    ap.add_argument("--reference", action="store_true", help="plantilla de referencia: omite grilla")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.drawio:
        ap.error("indique --drawio o --self-test")
    errors, warnings = validate(a.drawio, a.reference)
    for w in warnings:
        print(f"ADVERTENCIA: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    failed = bool(errors) or (a.strict and bool(warnings))
    print(("FALLA" if failed else "OK") + f": {len(errors)} error(es), {len(warnings)} advertencia(s) en {a.drawio.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
