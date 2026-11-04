#!/usr/bin/env python3
"""Valida un diagrama .excalidraw contra las reglas de archi (guia-excalidraw.md).

Verifica: JSON y raíz, IDs únicos, texto contenido y vinculaciones bidireccionales,
flechas vinculadas en ambos extremos, conectores ortogonales (codo o tramos H/V),
roughness/opacity, colores de la paleta semántica, tipografías, solapamientos parciales de
formas, desborde aproximado de texto, leyenda, presupuesto y, con --owner, que cada ID de
archi (CT-xx, EXT-xx, DATA-xxx, TB-xx, API-xxx, SEC-xxx, THR-xxx, DA-xxx, QA-xx) exista en el
artefacto dueño. --inventory imprime nodos y relaciones (importación/comparación).

Uso:
    python validate_excalidraw.py <archivo.excalidraw> [--strict] [--owner dueño.md] [--sketch] [--inventory]
    python validate_excalidraw.py --self-test
Sale con 1 si hay errores (o advertencias con --strict); 2 si no se puede leer.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

SHAPES = {"rectangle", "ellipse", "diamond"}
CONNECTORS = {"arrow", "line"}
PALETTE = {c.lower() for c in (
    "#FFFFFF", "#42526E", "#FFF4E5", "#C25100", "#E9F2FF", "#0C66E4", "#6B778C", "#DCFFF1",
    "#1F845A", "#FFECEB", "#AE2E24", "#FFF7D6", "#946F00", "#1E293B", "#E2E8F0", "#172B4D",
    "#626F86", "transparent", "#000000", "#1e1e1e")}
HANDWRITTEN_FONTS = {1, 5}
ARCHI_ID = re.compile(r"\b(?:CT|EXT|TB|QA)-\d{2,3}\b|\b(?:DATA|API|SEC|THR|DA|TP)-\d{3}(?:-OP-\d{3})?\b")
MAX_SHAPES, MAX_CONNECTORS, MAX_FOCUS = 15, 20, 2
TOL = 2.0


def box(e: dict) -> tuple[float, float, float, float]:
    x, y = float(e.get("x", 0)), float(e.get("y", 0))
    w, h = float(e.get("width", 0)), float(e.get("height", 0))
    if w < 0:
        x, w = x + w, -w
    if h < 0:
        y, h = y + h, -h
    return x, y, w, h


def contains(a, b) -> bool:
    return a[0] - TOL <= b[0] and a[1] - TOL <= b[1] and b[0] + b[2] <= a[0] + a[2] + TOL and b[1] + b[3] <= a[1] + a[3] + TOL


def intersects(a, b) -> bool:
    return not (b[0] >= a[0] + a[2] - TOL or b[0] + b[2] <= a[0] + TOL or b[1] >= a[1] + a[3] - TOL or b[1] + b[3] <= a[1] + TOL)


def text_size(e: dict) -> tuple[float, float]:
    lines = str(e.get("text", "")).split("\n") or [""]
    fs = float(e.get("fontSize", 16))
    factor = 0.6 if e.get("fontFamily") == 3 else 0.53
    return max(len(l) for l in lines) * fs * factor, len(lines) * fs * float(e.get("lineHeight", 1.25))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inventory(doc: dict) -> dict:
    els = [e for e in doc.get("elements", []) if not e.get("isDeleted")]
    by = {e.get("id"): e for e in els}
    label = {}
    for e in els:
        if e.get("type") == "text" and e.get("containerId"):
            label[e["containerId"]] = e.get("text", "")
    nodes = []
    for e in els:
        if e.get("type") in SHAPES | {"frame"}:
            t = label.get(e["id"], e.get("name", ""))
            ids = sorted(set(ARCHI_ID.findall(t)) | ({(e.get("customData") or {}).get("archiId")} - {None}))
            nodes.append({"id": e["id"], "type": e["type"], "label": t, "archiIds": ids})
    edges = []
    for e in els:
        if e.get("type") == "arrow":
            s = (e.get("startBinding") or {}).get("elementId")
            t = (e.get("endBinding") or {}).get("elementId")
            edges.append({"id": e["id"], "from": s, "to": t, "label": label.get(e["id"], ""),
                          "dashed": e.get("strokeStyle") in ("dashed", "dotted")})
    return {"nodes": nodes, "edges": edges, "known": sorted(by)}


def validate(doc: dict, owner_text: str | None = None, sketch: bool = False) -> tuple[list[str], list[str], dict]:
    errs: list[str] = []
    warns: list[str] = []
    if doc.get("type") != "excalidraw":
        errs.append("la raíz debe tener type: 'excalidraw'")
    els_all = doc.get("elements")
    if not isinstance(els_all, list):
        return errs + ["elements debe ser una lista"], warns, {}
    els = [e for e in els_all if isinstance(e, dict) and not e.get("isDeleted")]
    ids = [e.get("id") for e in els]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        errs.append(f"id duplicado: {d}")
    by = {e.get("id"): e for e in els}

    def bound_ids(e: dict, kind: str) -> set:
        return {b.get("id") for b in (e.get("boundElements") or []) if isinstance(b, dict) and b.get("type") == kind}

    texts = [e for e in els if e.get("type") == "text"]
    shapes = [e for e in els if e.get("type") in SHAPES]
    arrows = [e for e in els if e.get("type") == "arrow"]
    frames = [e for e in els if e.get("type") == "frame"]

    for t in texts:
        cid = t.get("containerId")
        if not str(t.get("text", "")).strip():
            warns.append(f"{t['id']}: texto vacío")
        if cid:
            c = by.get(cid)
            if c is None:
                errs.append(f"{t['id']}: containerId '{cid}' no existe")
                continue
            if t["id"] not in bound_ids(c, "text"):
                errs.append(f"{t['id']}: el contenedor '{cid}' no lo lista en boundElements")
            if c.get("type") in SHAPES:
                tw, th = text_size(t)
                _, _, cw, ch = box(c)
                if tw > cw - 8 or th > ch - 8:
                    warns.append(f"{t['id']}: el texto probablemente desborda '{cid}' (~{tw:.0f}x{th:.0f} en {cw:.0f}x{ch:.0f})")
        if t.get("fontFamily") in HANDWRITTEN_FONTS and not sketch:
            warns.append(f"{t['id']}: tipografía manuscrita en entregable formal (usa 2 o 3)")

    for a in arrows:
        for end in ("startBinding", "endBinding"):
            b = a.get(end) or {}
            target = b.get("elementId")
            if not target:
                warns.append(f"{a['id']}: {end} sin vincular (flecha que termina en el vacío)")
                continue
            if target not in by:
                errs.append(f"{a['id']}: {end} apunta a '{target}' inexistente")
            elif a["id"] not in bound_ids(by[target], "arrow"):
                errs.append(f"{a['id']}: '{target}' no lista la flecha en boundElements")
        lab = next((t for t in texts if t.get("containerId") == a.get("id")), None)
        if lab:
            pts = a.get("points") or [[0, 0]]
            length = max(abs(pts[-1][0] - pts[0][0]), abs(pts[-1][1] - pts[0][1]))
            lw, _ = text_size(lab)
            if lw > length - 16:
                warns.append(f"{a['id']}: la etiqueta (~{lw:.0f}px) no cabe en el conector ({length:.0f}px): alarga el tramo o acorta la etiqueta")
        if not a.get("elbowed"):
            pts = a.get("points") or []
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                if abs(x1 - x2) > 1 and abs(y1 - y2) > 1:
                    errs.append(f"{a['id']}: tramo diagonal; usa \"elbowed\": true o tramos horizontales/verticales")
                    break

    for e in els:
        if e.get("type") in SHAPES | CONNECTORS | {"text"}:
            if e.get("roughness", 0) not in (0, None) and not sketch:
                warns.append(f"{e['id']}: roughness {e.get('roughness')} (usa 0 en entregables formales)")
            if e.get("opacity", 100) != 100:
                warns.append(f"{e['id']}: opacity {e.get('opacity')} (usa 100)")
            for k in ("strokeColor", "backgroundColor"):
                v = str(e.get(k, "transparent")).lower()
                if v and v not in PALETTE:
                    warns.append(f"{e['id']}: {k} {v} fuera de la paleta semántica")

    focus = [s for s in shapes if str(s.get("strokeColor", "")).lower() == "#c25100"]
    if len(focus) > MAX_FOCUS:
        errs.append(f"{len(focus)} elementos en foco (máximo {MAX_FOCUS})")

    boxes = [(s["id"], box(s)) for s in shapes if box(s)[2] >= 24 and box(s)[3] >= 24]
    for i, (ia, a) in enumerate(boxes):
        for ib, b in boxes[i + 1:]:
            if intersects(a, b) and not contains(a, b) and not contains(b, a):
                errs.append(f"solapamiento parcial entre '{ia}' y '{ib}'")
    for f in frames:
        fb = box(f)
        for s in shapes:
            if s.get("frameId") == f["id"] and not contains(fb, box(s)):
                errs.append(f"'{s['id']}' pertenece al frame '{f['id']}' pero se sale de él")

    protagonists = [s for s in shapes if bound_ids(s, "text")]
    if len(protagonists) > MAX_SHAPES:
        warns.append(f"{len(protagonists)} formas con texto (presupuesto {MAX_SHAPES}): divide en vista general + detalle")
    if len(arrows) > MAX_CONNECTORS:
        warns.append(f"{len(arrows)} conectores (presupuesto {MAX_CONNECTORS})")

    styled = any(s.get("strokeStyle") in ("dashed", "dotted") for s in shapes + arrows) or \
        len({str(s.get("strokeColor", "")).lower() for s in shapes}) > 1
    if styled and not any(re.search(r"leyenda", str(t.get("text", "")), re.I) for t in texts):
        warns.append("usa estilos/colores distintos pero no hay leyenda (texto 'Leyenda')")

    if owner_text is not None:
        ids_in_diagram = set()
        for t in texts:
            ids_in_diagram |= set(ARCHI_ID.findall(str(t.get("text", ""))))
        for e in els:
            aid = (e.get("customData") or {}).get("archiId")
            if aid:
                ids_in_diagram.add(aid)
        for i in sorted(ids_in_diagram):
            if i not in owner_text:
                errs.append(f"{i} aparece en el diagrama pero no en el artefacto dueño")

    contained = sum(1 for t in texts if t.get("containerId"))
    metrics = {"shapes": len(shapes), "arrows": len(arrows), "texts": len(texts), "frames": len(frames),
               "text_in_containers_ratio": round(contained / len(texts), 2) if texts else 0.0}
    return errs, warns, metrics


def self_test() -> int:
    good = {"type": "excalidraw", "version": 2, "source": "archi", "appState": {}, "files": {}, "elements": [
        {"type": "rectangle", "id": "a", "x": 0, "y": 0, "width": 200, "height": 80, "strokeColor": "#42526E",
         "backgroundColor": "#FFFFFF", "roughness": 0, "opacity": 100,
         "boundElements": [{"id": "ta", "type": "text"}, {"id": "ar", "type": "arrow"}]},
        {"type": "text", "id": "ta", "x": 10, "y": 20, "width": 180, "height": 20, "text": "CT-01 API",
         "fontSize": 16, "fontFamily": 2, "containerId": "a", "strokeColor": "#172B4D", "backgroundColor": "transparent"},
        {"type": "rectangle", "id": "b", "x": 400, "y": 0, "width": 200, "height": 80, "strokeColor": "#0C66E4",
         "backgroundColor": "#E9F2FF", "roughness": 0, "opacity": 100,
         "boundElements": [{"id": "tb", "type": "text"}, {"id": "ar", "type": "arrow"}]},
        {"type": "text", "id": "tb", "x": 410, "y": 20, "width": 180, "height": 20, "text": "DATA-001 Pagos",
         "fontSize": 16, "fontFamily": 2, "containerId": "b", "strokeColor": "#172B4D", "backgroundColor": "transparent"},
        {"type": "arrow", "id": "ar", "x": 206, "y": 40, "width": 188, "height": 0, "points": [[0, 0], [188, 0]],
         "startBinding": {"elementId": "a", "focus": 0, "gap": 6}, "endBinding": {"elementId": "b", "focus": 0, "gap": 6},
         "strokeColor": "#42526E", "backgroundColor": "transparent", "roughness": 0, "opacity": 100},
        {"type": "text", "id": "leg", "x": 0, "y": 200, "width": 300, "height": 20, "text": "Leyenda: azul = datos",
         "fontSize": 14, "fontFamily": 2, "strokeColor": "#626F86", "backgroundColor": "transparent"},
    ]}
    e, w, _ = validate(good, owner_text="CT-01 y DATA-001")
    assert not e and not w, (e, w)
    bad = json.loads(json.dumps(good))
    bad["elements"][4]["points"] = [[0, 0], [188, 40]]
    bad["elements"][2]["boundElements"] = [{"id": "tb", "type": "text"}]
    bad["elements"][2]["x"] = 150
    e, w, _ = validate(bad, owner_text="CT-01")
    joined = "\n".join(e)
    for needle in ("diagonal", "no lista la flecha", "solapamiento", "DATA-001"):
        assert needle in joined, (needle, e)
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.excalidraw"
        p.write_text(json.dumps(good), encoding="utf-8")
        assert inventory(load(p))["edges"][0]["to"] == "b"
    print("SELF-TEST OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", type=Path)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--owner", type=Path, help="artefacto dueño (.md) para cruzar IDs de archi")
    ap.add_argument("--sketch", action="store_true", help="boceto: permite roughness y tipografía manuscrita")
    ap.add_argument("--inventory", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.path:
        ap.error("falta el archivo .excalidraw")
    try:
        doc = load(a.path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: no se pudo leer {a.path}: {exc}")
        return 2
    if a.inventory:
        print(json.dumps(inventory(doc), ensure_ascii=False, indent=2))
        return 0
    owner = a.owner.read_text(encoding="utf-8") if a.owner else None
    errs, warns, metrics = validate(doc, owner, a.sketch)
    for w in warns:
        print(f"WARN: {w}")
    for e in errs:
        print(f"ERROR: {e}")
    print(f"Métricas: {metrics}")
    if errs or (a.strict and warns):
        print(f"FAIL: {len(errs)} error(es), {len(warns)} advertencia(s)")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
