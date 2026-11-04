#!/usr/bin/env python3
"""Vista previa aproximada (PNG) de diagramas .drawio y .excalidraw para el bucle
renderizar → mirar → corregir de guia-diseno-diagramas.md §9.

No reemplaza el render real de draw.io/Excalidraw: dibuja formas, contenedores, textos,
conectores (ortogonales con waypoints) y etiquetas con máscara, suficiente para ver
solapamientos, textos cortados, conectores que cruzan nodos y desequilibrios. Además
reporta colisiones entre etiquetas de conectores y entre etiquetas y nodos.

Uso:
    python render_preview.py <archivo.drawio|archivo.excalidraw> -o salida.png [--scale 1.5]
    python render_preview.py --self-test
Requiere Pillow (pip install pillow). Sale con 0 al generar la imagen; 2 si no puede leer.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    print("ERROR: se requiere Pillow (pip install pillow)")
    sys.exit(2)

FONT_CANDIDATES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                   "C:/Windows/Fonts/arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"]
MONO_CANDIDATES = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "C:/Windows/Fonts/consola.ttf"]


def font(size: float, mono: bool = False):
    for p in (MONO_CANDIDATES if mono else []) + FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, max(8, int(size)))
    try:
        return ImageFont.load_default(size=max(8, int(size)))
    except TypeError:
        return ImageFont.load_default()


@dataclass
class Shape:
    id: str
    kind: str  # rect, ellipse, diamond, container, icon, frame, text
    x: float
    y: float
    w: float
    h: float
    label: str = ""
    stroke: str = "#42526E"
    fill: str = "#FFFFFF"
    dashed: bool = False
    font_size: float = 13
    mono: bool = False
    align: str = "center"


@dataclass
class Edge:
    id: str
    points: list[tuple[float, float]]
    label: str = ""
    stroke: str = "#42526E"
    dashed: bool = False
    arrow: bool = True


@dataclass
class Scene:
    shapes: list[Shape] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)


def color(v: str | None, default: str) -> str:
    if not v or v in ("none", "transparent", "default"):
        return default
    return v if re.fullmatch(r"#[0-9a-fA-F]{3,8}", v) else default


def strip_html(v: str) -> str:
    v = re.sub(r"<br\s*/?>", "\n", v or "", flags=re.I)
    v = re.sub(r"</(div|p)>", "\n", v, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", v)).strip()


# ---------------------------------------------------------------- draw.io
def style_map(style: str) -> dict[str, str]:
    out = {}
    for part in (style or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
        elif part.strip():
            out[part.strip()] = "1"
    return out


def orth_route(s: Shape, t: Shape, waypoints: list[tuple[float, float]]) -> list[tuple[float, float]]:
    scx, scy, tcx, tcy = s.x + s.w / 2, s.y + s.h / 2, t.x + t.w / 2, t.y + t.h / 2
    pts = [(scx, scy)] + waypoints + [(tcx, tcy)]
    route = [pts[0]]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if abs(ax - bx) > 0.5 and abs(ay - by) > 0.5:
            if not waypoints and abs(scx - tcx) >= abs(scy - tcy):
                mx = (ax + bx) / 2
                route += [(mx, ay), (mx, by)]
            elif not waypoints:
                my = (ay + by) / 2
                route += [(ax, my), (bx, my)]
            else:
                route.append((bx, ay))
        route.append((bx, by))
    return clip_to_boxes(route, s, t)


def clip_to_boxes(route, s: Shape, t: Shape):
    def clip(p_in, p_out, b: Shape):
        (x1, y1), (x2, y2) = p_in, p_out
        for i in range(40):
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            inside = b.x <= mx <= b.x + b.w and b.y <= my <= b.y + b.h
            if inside:
                x1, y1 = mx, my
            else:
                x2, y2 = mx, my
        return (x2, y2)
    if len(route) >= 2:
        route[0] = clip(route[0], route[1], s)
        route[-1] = clip(route[-1], route[-2], t)
    return route


def parse_drawio(path: Path) -> Scene:
    root = ET.parse(path).getroot()
    cells = list(root.iter("mxCell"))
    if not cells:
        raise ValueError("no hay mxCell (¿XML comprimido? exporta sin compresión)")
    by = {c.get("id"): c for c in cells}
    has_children = {c.get("parent") for c in cells if c.get("vertex") == "1"}
    cache: dict[str, tuple[float, float]] = {}

    def geo(c):
        g = c.find("mxGeometry")
        if g is None:
            return 0.0, 0.0, 0.0, 0.0
        return tuple(float(g.get(k, 0) or 0) for k in ("x", "y", "width", "height"))

    def origin(cid):
        if cid is None or cid not in by:
            return 0.0, 0.0
        if cid in cache:
            return cache[cid]
        c = by[cid]
        if c.get("vertex") != "1":
            cache[cid] = (0.0, 0.0)
            return cache[cid]
        px, py = origin(c.get("parent"))
        x, y, _, _ = geo(c)
        cache[cid] = (px + x, py + y)
        return cache[cid]

    scene = Scene()
    shapes: dict[str, Shape] = {}
    for c in cells:
        if c.get("vertex") != "1":
            continue
        st = style_map(c.get("style", ""))
        px, py = origin(c.get("parent"))
        x, y, w, h = geo(c)
        label = strip_html(c.get("value") or "")
        if c.getparent() if hasattr(c, "getparent") else False:
            pass
        is_container = c.get("id") in has_children or st.get("container") == "1" or "group" in st or "swimlane" in st
        is_icon = "shape" in st and ("mxgraph." in st.get("shape", "") or st.get("shape") == "image") or "image" in st
        kind = "container" if is_container else "icon" if is_icon else \
            "ellipse" if "ellipse" in st else "diamond" if st.get("rhombus") == "1" or "rhombus" in st else \
            "text" if st.get("text") == "1" or "text" in st and w and not st.get("fillColor") else "rect"
        sh = Shape(c.get("id"), kind, px + x, py + y, w, h, label,
                   color(st.get("strokeColor"), "#6B778C" if kind == "container" else "#42526E"),
                   color(st.get("fillColor"), "#FFFFFF"), st.get("dashed") == "1",
                   float(st.get("fontSize", 12) or 12))
        shapes[sh.id] = sh
        scene.shapes.append(sh)
    for c in cells:
        if c.get("edge") != "1":
            continue
        s, t = shapes.get(c.get("source")), shapes.get(c.get("target"))
        st = style_map(c.get("style", ""))
        g = c.find("mxGeometry")
        wps = []
        if g is not None:
            arr = g.find("Array")
            if arr is not None:
                ox, oy = origin(c.get("parent"))
                wps = [(ox + float(p.get("x", 0)), oy + float(p.get("y", 0))) for p in arr.findall("mxPoint")]
        if not s or not t:
            continue
        label = strip_html(c.get("value") or "")
        for child in cells:
            if child.get("parent") == c.get("id") and child.get("vertex") == "1":
                label = label or strip_html(child.get("value") or "")
        scene.edges.append(Edge(c.get("id"), orth_route(s, t, wps), label,
                                color(st.get("strokeColor"), "#42526E"), st.get("dashed") == "1",
                                st.get("endArrow", "classic") != "none"))
    return scene


# ---------------------------------------------------------------- excalidraw
def parse_excalidraw(path: Path) -> Scene:
    doc = json.loads(path.read_text(encoding="utf-8"))
    els = [e for e in doc.get("elements", []) if not e.get("isDeleted")]
    by = {e["id"]: e for e in els if "id" in e}
    scene = Scene()
    labels = {}
    for e in els:
        if e.get("type") == "text" and e.get("containerId"):
            labels[e["containerId"]] = e
    shp: dict[str, Shape] = {}
    for e in els:
        t = e.get("type")
        if t in ("rectangle", "ellipse", "diamond", "frame"):
            lab = labels.get(e["id"])
            sh = Shape(e["id"], {"rectangle": "rect"}.get(t, t), e.get("x", 0), e.get("y", 0), e.get("width", 0), e.get("height", 0),
                       (lab or {}).get("text", e.get("name", "") if t == "frame" else ""),
                       color(e.get("strokeColor"), "#42526E"), color(e.get("backgroundColor"), "#FFFFFF") if t != "frame" else "#FFFFFF",
                       e.get("strokeStyle") in ("dashed", "dotted") or t == "frame",
                       float((lab or {}).get("fontSize", 16)), (lab or {}).get("fontFamily") == 3)
            shp[sh.id] = sh
            scene.shapes.append(sh)
    for e in els:
        if e.get("type") == "text" and not e.get("containerId"):
            scene.shapes.append(Shape(e["id"], "text", e.get("x", 0), e.get("y", 0), e.get("width", 0), e.get("height", 0),
                                      e.get("text", ""), color(e.get("strokeColor"), "#172B4D"), "#FFFFFF", False,
                                      float(e.get("fontSize", 16)), e.get("fontFamily") == 3, e.get("textAlign", "left")))
    for e in els:
        if e.get("type") in ("arrow", "line"):
            x0, y0 = e.get("x", 0), e.get("y", 0)
            pts = [(x0 + p[0], y0 + p[1]) for p in e.get("points", [])]
            if e.get("elbowed") and len(pts) >= 2:
                routed = [pts[0]]
                for (ax, ay), (bx, by_) in zip(pts, pts[1:]):
                    if abs(ax - bx) > 0.5 and abs(ay - by_) > 0.5:
                        routed.append((bx, ay))
                    routed.append((bx, by_))
                pts = routed
            lab = labels.get(e["id"])
            scene.edges.append(Edge(e["id"], pts, (lab or {}).get("text", ""), color(e.get("strokeColor"), "#42526E"),
                                    e.get("strokeStyle") in ("dashed", "dotted"),
                                    e.get("type") == "arrow" and e.get("endArrowhead", "arrow") is not None))
    return scene


# ---------------------------------------------------------------- render
def dashed_line(d: ImageDraw.ImageDraw, a, b, fill, width, dash=8, gap=5):
    (x1, y1), (x2, y2) = a, b
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if length == 0:
        return
    dx, dy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0.0
    while pos < length:
        e = min(pos + dash, length)
        d.line([(x1 + dx * pos, y1 + dy * pos), (x1 + dx * e, y1 + dy * e)], fill=fill, width=width)
        pos = e + gap


def wrap(text: str, f, max_w: float, d: ImageDraw.ImageDraw) -> list[str]:
    out = []
    for para in text.split("\n"):
        words, line = para.split(" "), ""
        for w in words:
            cand = (line + " " + w).strip()
            if d.textlength(cand, font=f) <= max_w or not line:
                line = cand
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


def render(scene: Scene, out: Path, scale: float = 1.5) -> dict:
    items = [(s.x, s.y, s.x + s.w, s.y + s.h) for s in scene.shapes] + \
            [(x, y, x, y) for e in scene.edges for x, y in e.points]
    if not items:
        raise ValueError("diagrama vacío")
    minx = min(i[0] for i in items) - 40
    miny = min(i[1] for i in items) - 40
    maxx = max(i[2] for i in items) + 40
    maxy = max(i[3] for i in items) + 40
    W, H = int((maxx - minx) * scale), int((maxy - miny) * scale)
    if W * H > 60_000_000:
        scale = (60_000_000 / ((maxx - minx) * (maxy - miny))) ** 0.5
        W, H = int((maxx - minx) * scale), int((maxy - miny) * scale)
    img = Image.new("RGB", (max(W, 10), max(H, 10)), "#FFFFFF")
    d = ImageDraw.Draw(img)
    T = lambda x, y: ((x - minx) * scale, (y - miny) * scale)  # noqa: E731

    def rect_of(s: Shape):
        (x1, y1), (x2, y2) = T(s.x, s.y), T(s.x + s.w, s.y + s.h)
        return [x1, y1, x2, y2]

    order = {"container": 0, "frame": 0, "rect": 2, "ellipse": 2, "diamond": 2, "icon": 2, "text": 3}
    containers = [s for s in scene.shapes if order.get(s.kind, 2) == 0]
    nodes = [s for s in scene.shapes if order.get(s.kind, 2) == 2]
    texts = [s for s in scene.shapes if s.kind == "text"]
    for s in sorted(containers, key=lambda s: -(s.w * s.h)):
        r = rect_of(s)
        if s.dashed:
            for a, b in (((r[0], r[1]), (r[2], r[1])), ((r[2], r[1]), (r[2], r[3])), ((r[2], r[3]), (r[0], r[3])), ((r[0], r[3]), (r[0], r[1]))):
                dashed_line(d, a, b, s.stroke, max(1, int(scale)))
        else:
            d.rectangle(r, outline=s.stroke, width=max(1, int(scale)))
        if s.label:
            d.text((r[0] + 6 * scale, r[1] + 4 * scale), s.label.split("\n")[0][:80], fill=s.stroke, font=font(12 * scale))

    label_boxes = []
    for e in scene.edges:
        pts = [T(*p) for p in e.points]
        for a, b in zip(pts, pts[1:]):
            if e.dashed:
                dashed_line(d, a, b, e.stroke, max(1, int(1.4 * scale)))
            else:
                d.line([a, b], fill=e.stroke, width=max(1, int(1.4 * scale)))
        if e.arrow and len(pts) >= 2:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            L = max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 1e-6)
            ux, uy = (x2 - x1) / L, (y2 - y1) / L
            s_ = 9 * scale
            d.polygon([(x2, y2), (x2 - ux * s_ - uy * s_ / 2, y2 - uy * s_ + ux * s_ / 2),
                       (x2 - ux * s_ + uy * s_ / 2, y2 - uy * s_ - ux * s_ / 2)], fill=e.stroke)

    for s in nodes:
        r = rect_of(s)
        if s.kind == "ellipse":
            d.ellipse(r, fill=s.fill, outline=s.stroke, width=max(1, int(1.5 * scale)))
        elif s.kind == "diamond":
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            d.polygon([(cx, r[1]), (r[2], cy), (cx, r[3]), (r[0], cy)], fill=s.fill, outline=s.stroke)
        elif s.kind == "icon":
            d.rounded_rectangle(r, radius=6 * scale, fill="#F4F5F7", outline=s.stroke, width=max(1, int(scale)))
            d.text(((r[0] + r[2]) / 2, (r[1] + r[3]) / 2), "◆", fill=s.stroke, font=font(18 * scale), anchor="mm")
        else:
            d.rounded_rectangle(r, radius=4 * scale, fill=s.fill, outline=s.stroke, width=max(1, int(1.5 * scale)))
            if s.dashed:
                d.rounded_rectangle(r, radius=4 * scale, outline="#FFFFFF", width=1)
        if s.label:
            f = font(s.font_size * scale, s.mono)
            if s.kind == "icon":
                lines = wrap(s.label, f, max(140 * scale, r[2] - r[0]), d)
                y = r[3] + 3 * scale
                for ln in lines:
                    d.text(((r[0] + r[2]) / 2, y), ln, fill="#172B4D", font=f, anchor="ma")
                    y += s.font_size * scale * 1.2
            else:
                lines = wrap(s.label, f, (r[2] - r[0]) - 8 * scale, d)
                total = len(lines) * s.font_size * scale * 1.2
                y = (r[1] + r[3]) / 2 - total / 2
                for ln in lines:
                    d.text(((r[0] + r[2]) / 2, y), ln, fill="#172B4D", font=f, anchor="ma")
                    y += s.font_size * scale * 1.2

    for e in scene.edges:
        if not e.label or len(e.points) < 2:
            continue
        pts = [T(*p) for p in e.points]
        segs = sorted(zip(pts, pts[1:]), key=lambda ab: -abs(ab[0][0] - ab[1][0]) - abs(ab[0][1] - ab[1][1]))
        (ax, ay), (bx, by) = segs[0]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        f = font(11 * scale)
        lines = e.label.split("\n")
        tw = max(d.textlength(l, font=f) for l in lines)
        th = len(lines) * 13 * scale
        box = [mx - tw / 2 - 4, my - th / 2 - 2, mx + tw / 2 + 4, my + th / 2 + 2]
        d.rectangle(box, fill="#FFFFFF")
        yy = box[1] + 2
        for ln in lines:
            d.text((mx, yy), ln, fill="#42526E", font=f, anchor="ma")
            yy += 13 * scale
        label_boxes.append((e.id, box))

    for s in texts:
        x, y = T(s.x, s.y)
        f = font(s.font_size * scale, s.mono)
        for ln in s.label.split("\n"):
            d.text((x, y), ln, fill=s.stroke, font=f)
            y += s.font_size * scale * 1.25

    issues = []
    for i, (ia, a) in enumerate(label_boxes):
        for ib, b in label_boxes[i + 1:]:
            if not (b[0] >= a[2] or b[2] <= a[0] or b[1] >= a[3] or b[3] <= a[1]):
                issues.append(f"etiquetas superpuestas: {ia} y {ib}")
        for s in nodes:
            r = rect_of(s)
            if not (r[0] >= a[2] or r[2] <= a[0] or r[1] >= a[3] or r[3] <= a[1]):
                issues.append(f"etiqueta de {ia} sobre el nodo {s.id}")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return {"output": str(out), "size": [img.width, img.height], "shapes": len(scene.shapes),
            "edges": len(scene.edges), "issues": issues}


def load_scene(path: Path) -> Scene:
    if path.suffix.lower() == ".excalidraw" or path.name.endswith(".excalidraw.json"):
        return parse_excalidraw(path)
    return parse_drawio(path)


def self_test() -> int:
    drawio = """<mxfile><diagram name="p"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="z" value="VPC" style="rounded=0;dashed=1;container=1;" vertex="1" parent="1"><mxGeometry x="10" y="10" width="500" height="200" as="geometry"/></mxCell>
<mxCell id="a" value="CT-01 API" style="rounded=1;" vertex="1" parent="z"><mxGeometry x="20" y="60" width="140" height="60" as="geometry"/></mxCell>
<mxCell id="b" value="DATA-001" style="shape=cylinder3;" vertex="1" parent="z"><mxGeometry x="320" y="60" width="120" height="60" as="geometry"/></mxCell>
<mxCell id="e" value="SQL/TLS · lee" style="edgeStyle=orthogonalEdgeStyle;" edge="1" parent="1" source="a" target="b"><mxGeometry relative="1" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>"""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.drawio"
        p.write_text(drawio, encoding="utf-8")
        r = render(load_scene(p), Path(d) / "x.png")
        assert r["edges"] == 1 and r["shapes"] == 3 and Path(r["output"]).stat().st_size > 1000, r
        ex = {"type": "excalidraw", "elements": [
            {"type": "rectangle", "id": "a", "x": 0, "y": 0, "width": 160, "height": 60, "boundElements": [{"id": "t", "type": "text"}]},
            {"type": "text", "id": "t", "x": 0, "y": 20, "width": 160, "height": 20, "text": "CT-01", "containerId": "a"},
            {"type": "arrow", "id": "r", "x": 160, "y": 30, "points": [[0, 0], [100, 40]], "elbowed": True},
            {"type": "text", "id": "l", "x": 0, "y": 120, "width": 100, "height": 20, "text": "Leyenda"}]}
        q = Path(d) / "y.excalidraw"
        q.write_text(json.dumps(ex), encoding="utf-8")
        r2 = render(load_scene(q), Path(d) / "y.png")
        assert r2["edges"] == 1, r2
    print("SELF-TEST OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--scale", type=float, default=1.5)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.path:
        ap.error("falta el archivo")
    out = a.output or a.path.with_suffix(a.path.suffix + ".preview.png")
    try:
        result = render(load_scene(a.path), out, a.scale)
    except (OSError, ValueError, ET.ParseError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2
    for i in result["issues"]:
        print(f"REVISAR: {i}")
    print(f"Vista previa: {result['output']} ({result['size'][0]}x{result['size'][1]}), "
          f"{result['shapes']} formas, {result['edges']} conectores. Ábrela y aplica el bucle de revisión.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
