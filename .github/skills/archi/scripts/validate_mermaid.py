#!/usr/bin/env python3
"""Valida los bloques Mermaid de los artefactos de archi.

Dos niveles:
1. Reglas de calidad visual (siempre): dirección explícita y curva ortogonal en flowchart/graph,
   etiquetas en conectores, presupuesto de complejidad, rutas de error en secuencias críticas,
   tecnología en relaciones C4, layout C4 declarado.
2. Compilación real con el parser oficial de Mermaid (cuando está disponible). Instalación única:
       npm install --prefix <dir> mermaid@11.4.1 jsdom@25.0.1
   y luego pase --node-modules <dir>/node_modules o defina ARCHI_MERMAID_NODE_MODULES.

Uso:
    python validate_mermaid.py resources/architecture/*.md [--strict] [--require-compile]
    python validate_mermaid.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BLOCK = re.compile(r"^```mermaid[ \t]*\r?\n(.*?)^```[ \t]*$", re.S | re.M)
BUDGET = {"flowchart_nodes": 12, "flowchart_edges": 18, "participants": 7, "messages": 25,
          "c4_elements": 12, "er_entities": 10}
ORTHO_CURVES = {"step", "stepBefore", "stepAfter", "linear"}

NODE_JS = r"""
import { JSDOM } from 'jsdom';
const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window; globalThis.document = dom.window.document;
for (const k of ['Element','HTMLElement','Node','DocumentFragment','DOMParser','NodeFilter','SVGElement']) {
  if (dom.window[k] && !(k in globalThis)) globalThis[k] = dom.window[k];
}
const { default: mermaid } = await import('mermaid');
mermaid.initialize({ startOnLoad: false });
import fs from 'fs';
const blocks = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = [];
for (const b of blocks) {
  try { await mermaid.parse(b); out.push(null); }
  catch (e) { out.push(String(e.message || e).split('\n').slice(0, 3).join(' | ')); }
}
console.log(JSON.stringify(out));
"""


def kind_of(block: str) -> str:
    for line in block.splitlines():
        s = line.strip()
        if not s or s.startswith("%%") or s == "---":
            continue
        if ":" in s and not s.split(":")[0].strip().isidentifier():
            pass
        return s.split()[0]
    return ""


def strip_frontmatter(block: str) -> tuple[str, str]:
    if block.lstrip().startswith("---"):
        parts = block.lstrip().split("---", 2)
        if len(parts) == 3:
            return parts[1], parts[2]
    return "", block


def lint(block: str, context: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    front, body = strip_frontmatter(block)
    config_text = front + "\n" + "\n".join(l for l in block.splitlines() if l.strip().startswith("%%{"))
    k = kind_of(body)
    lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("%%")]

    if k in ("graph", "flowchart"):
        first = lines[0].split()
        if len(first) < 2 or first[1] not in ("TB", "TD", "LR", "RL", "BT"):
            errors.append(f"{context}: {k} sin dirección explícita (TB/LR)")
        m = re.search(r"curve['\"]?\s*:\s*['\"]?(\w+)", config_text)
        if not m:
            errors.append(f"{context}: {k} sin curva declarada; use frontmatter "
                          "config.flowchart.curve: step (ortogonal) en vez del basis curvo por defecto")
        elif m.group(1) not in ORTHO_CURVES:
            errors.append(f"{context}: curve '{m.group(1)}' produce curvas; use step")
        elif m.group(1) == "linear":
            warnings.append(f"{context}: curve linear dibuja diagonales; prefiera step (ángulos rectos)")
        edges = [l for l in lines[1:] if re.search(r"(-->|-\.->|==>|---|-\.-)", l)]
        unlabeled = [l for l in edges if not re.search(r"\|[^|]+\||--\s+[^->]+\s+-->|-\.\s+[^.]+\s+\.->", l)]
        if unlabeled:
            errors.append(f"{context}: {len(unlabeled)} conector(es) sin etiqueta, p. ej. «{unlabeled[0][:60]}»")
        nodes = set()
        for l in lines[1:]:
            if l.startswith(("subgraph", "end", "classDef", "class ", "style ", "linkStyle", "click")):
                continue
            nodes.update(re.findall(r"(?:^|[\s>|&-])([A-Za-z_][\w-]*)\s*(?=[\[\(\{>]|\s*$|\s*-|\s*&|\s*:::)", l))
        if len(nodes) > BUDGET["flowchart_nodes"]:
            warnings.append(f"{context}: ~{len(nodes)} nodos (> {BUDGET['flowchart_nodes']}); divida en vista general + detalle")
        if len(edges) > BUDGET["flowchart_edges"]:
            warnings.append(f"{context}: {len(edges)} conectores (> {BUDGET['flowchart_edges']})")

    elif k == "sequenceDiagram":
        parts = [l for l in lines if re.match(r"(participant|actor)\s", l)]
        msgs = [l for l in lines if re.search(r"-{1,2}>>|-{1,2}\)|-{1,2}x", l)]
        if len(parts) > BUDGET["participants"]:
            warnings.append(f"{context}: {len(parts)} participantes (> {BUDGET['participants']}); agrupe o divida")
        if len(msgs) > BUDGET["messages"]:
            warnings.append(f"{context}: {len(msgs)} mensajes (> {BUDGET['messages']}); divida el flujo")
        if not any(l.startswith("autonumber") for l in lines):
            warnings.append(f"{context}: agregue autonumber para poder referenciar pasos desde el texto")
        if not any(re.match(r"(alt|opt|break|critical)\b", l) for l in lines):
            warnings.append(f"{context}: sin alt/opt/break; los flujos críticos deben mostrar la ruta de error")

    elif k.startswith("C4"):
        elems = [l for l in lines if re.match(r"(Person|System|Container|Component)\w*\(", l)
                 and not re.match(r"\w*_Boundary\(", l)]
        rels = [l for l in lines if re.match(r"(Bi)?Rel\w*\(", l)]
        if len(elems) > BUDGET["c4_elements"]:
            warnings.append(f"{context}: {len(elems)} elementos C4 (> {BUDGET['c4_elements']}); agrupe por dominio")
        no_tech = [r for r in rels if len(re.findall(r'"[^"]*"', r)) < 2]
        if no_tech:
            warnings.append(f"{context}: {len(no_tech)} Rel sin tecnología/protocolo, p. ej. «{no_tech[0][:60]}»")
        if not any(l.startswith("UpdateLayoutConfig") for l in lines):
            warnings.append(f"{context}: declare UpdateLayoutConfig(...) para controlar la grilla C4 de Mermaid")

    elif k == "erDiagram":
        ents = set(re.findall(r"^([A-Z][A-Z0-9_]*)\s*\{", body, re.M))
        if len(ents) > BUDGET["er_entities"]:
            warnings.append(f"{context}: {len(ents)} entidades (> {BUDGET['er_entities']})")
    return errors, warnings


def find_node_modules(arg: str | None) -> Path | None:
    for cand in (arg, os.environ.get("ARCHI_MERMAID_NODE_MODULES")):
        if cand and Path(cand, "mermaid").is_dir() and Path(cand, "jsdom").is_dir():
            return Path(cand)
    return None


def compile_blocks(blocks: list[str], node_modules: Path) -> list[str | None]:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node no está instalado")
    with tempfile.TemporaryDirectory() as d:
        script = Path(d, "parse.mjs")
        script.write_text(NODE_JS, encoding="utf-8")
        link = Path(d, "node_modules")
        try:
            link.symlink_to(node_modules, target_is_directory=True)
        except OSError:
            shutil.copytree(node_modules, link)
        res = subprocess.run([node, str(script)], input=json.dumps(blocks), capture_output=True,
                             text=True, cwd=d, timeout=180)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip()[:300])
    return json.loads(res.stdout.strip().splitlines()[-1])


def run(files: list[Path], node_modules: Path | None, require_compile: bool) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    all_blocks: list[tuple[str, str]] = []
    for f in files:
        text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
        for n, b in enumerate(BLOCK.findall(text), 1):
            ctx = f"{f.name}#mermaid{n}"
            all_blocks.append((ctx, b))
            e, w = lint(b, ctx)
            errors += e
            warnings += w
    if all_blocks:
        if node_modules:
            try:
                results = compile_blocks([b for _, b in all_blocks], node_modules)
                for (ctx, _), r in zip(all_blocks, results):
                    if r:
                        errors.append(f"{ctx}: no compila: {r}")
            except Exception as exc:  # noqa: BLE001
                (errors if require_compile else warnings).append(f"compilación no ejecutada: {exc}")
        else:
            msg = ("compilación Mermaid no verificada (falta node_modules con mermaid+jsdom; "
                   "vea la cabecera del script)")
            (errors if require_compile else warnings).append(msg)
    return errors, warnings, len(all_blocks)


GOOD = """```mermaid
---
config:
  flowchart:
    curve: step
---
flowchart LR
    U[Usuario] -->|HTTPS| G[Gateway]
    G -->|REST/JSON| S[Servicio]
```
"""
BAD = """```mermaid
graph
    U[Usuario] --> G[Gateway]
```
"""


def self_test() -> int:
    with tempfile.TemporaryDirectory() as d:
        g, b = Path(d, "ok.md"), Path(d, "bad.md")
        g.write_text(GOOD, encoding="utf-8")
        b.write_text(BAD, encoding="utf-8")
        e1, _, _ = run([g], None, False)
        e2, _, _ = run([b], None, False)
    need = ["dirección explícita", "sin curva", "sin etiqueta"]
    miss = [n for n in need if not any(n in e for e in e2)]
    if e1 or miss:
        print("SELF-TEST ERROR", e1, miss)
        return 1
    print("SELF-TEST OK: bloque correcto sin errores; incorrecto detecta dirección, curva y etiquetas")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--node-modules")
    ap.add_argument("--strict", action="store_true", help="las advertencias también fallan")
    ap.add_argument("--require-compile", action="store_true", help="falla si no puede compilar")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.files:
        ap.error("indique archivos .md o --self-test")
    errors, warnings, n = run(a.files, find_node_modules(a.node_modules), a.require_compile)
    for w in warnings:
        print(f"ADVERTENCIA: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    failed = bool(errors) or (a.strict and bool(warnings))
    print(("FALLA" if failed else "OK") + f": {n} bloque(s), {len(errors)} error(es), {len(warnings)} advertencia(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
