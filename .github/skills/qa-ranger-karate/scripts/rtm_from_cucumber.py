#!/usr/bin/env python3
"""
Genera una matriz de trazabilidad (RTM) desde reportes Cucumber JSON de Karate v1 o v2.
La matriz relaciona requisito, criterio, escenario y estado de ejecución.
Genera los reportes con outputCucumberJson(true).

Trazabilidad reconocida en cada escenario:
  - Nombre:  "[HU-245][CA-3] rechaza monto negativo"   (también [US-1], [REQ-9], [SEG], ...)
  - Tag:     @req=HU-245/CA-3   o   @req=HU-245

Uso:
  python rtm_from_cucumber.py target/karate-reports [--out rtm.md] [--csv rtm.csv]
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ID_IN_NAME = re.compile(r"\[([A-Za-z]+-?\d+)\](?:\[([A-Za-z]+-?\d+|[A-Z]{2,})\])?")
REQ_TAG = re.compile(r"^@req=([^/\s]+)(?:/(\S+))?$")


def load_features(root: Path):
    feats = []
    for f in sorted(root.rglob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            data = [data]
        if isinstance(data, list) and data and isinstance(data[0], dict) and "elements" in data[0]:
            feats += data
    return feats


def scenario_status(el):
    statuses = []
    for st in (el.get("before") or []) + (el.get("steps") or []) + (el.get("after") or []):
        statuses.append((st.get("result") or {}).get("status", "unknown"))
    if any(s == "failed" for s in statuses):
        return "FALLA"
    if statuses and all(s == "passed" for s in statuses):
        return "PASA"
    if any(s in ("skipped", "pending", "undefined") for s in statuses):
        return "OMITIDO"
    return "DESCONOCIDO"


def main():
    # Usa UTF-8 para conservar los acentos y símbolos del reporte en Windows.
    # La salida cp1252 puede fallar al imprimir caracteres como → o ✅.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reportes", help="carpeta con Cucumber JSON (p.ej. target/karate-reports)")
    ap.add_argument("--out", default=None, help="archivo markdown de salida (default: stdout)")
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()

    feats = load_features(Path(args.reportes))
    if not feats:
        sys.exit("No se encontró Cucumber JSON. Habilitar outputCucumberJson(true) en el runner "
                 "(v2: -f cucumber:json) y volver a ejecutar.")

    matrix = defaultdict(lambda: defaultdict(list))   # Agrupa los escenarios y sus estados por requisito y criterio.
    untraced = []
    for ft in feats:
        fname = ft.get("uri") or ft.get("name", "?")
        for el in ft.get("elements", []):
            if el.get("type") == "background":
                continue
            name = el.get("name", "")
            status = scenario_status(el)
            tags = [t.get("name", "") for t in el.get("tags", [])] + [t.get("name", "") for t in ft.get("tags", [])]
            links = []
            for t in tags:
                m = REQ_TAG.match(t)
                if m:
                    links.append((m.group(1), m.group(2) or "-"))
            for m in ID_IN_NAME.finditer(name):
                links.append((m.group(1), m.group(2) or "-"))
            if not links:
                untraced.append((fname, name, status))
            for req, crit in dict.fromkeys(links):
                matrix[req][crit].append((fname, name, status))

    def crit_status(items):
        st = {s for _, _, s in items}
        if "FALLA" in st:
            return "❌ FALLA"
        if st == {"PASA"}:
            return "✅ PASA"
        return "⚠️ PARCIAL"

    out = ["# Matriz de trazabilidad", ""]
    total = sum(len(c) for c in matrix.values())
    ok = sum(1 for c in matrix.values() for items in c.values() if crit_status(items) == "✅ PASA")
    out.append(f"Requisitos: {len(matrix)} · Criterios: {total} · Criterios en verde: {ok}/{total} · "
               f"Escenarios sin trazabilidad: {len(untraced)}")
    out += ["", "| Requisito | Criterio | Estado | Escenarios |", "|---|---|---|---|"]
    rows = []
    for req in sorted(matrix):
        for crit in sorted(matrix[req]):
            items = matrix[req][crit]
            esc = "<br>".join(f"{n} ({s})" for _, n, s in items)
            out.append(f"| {req} | {crit} | {crit_status(items)} | {esc} |")
            for f, n, s in items:
                rows.append([req, crit, f, n, s])
    if untraced:
        out += ["", "## Escenarios sin trazabilidad", "", "| Feature | Escenario | Estado |", "|---|---|---|"]
        for f, n, s in untraced:
            out.append(f"| {f} | {n} | {s} |")
    out += ["", "> La matriz solo refleja criterios que tienen al menos un escenario. Los criterios de la HU "
            "sin escenario asociado deben listarse aparte como **no verificados**."]

    text = "\n".join(out) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"RTM escrita en {args.out}")
    else:
        print(text)
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["requisito", "criterio", "feature", "escenario", "estado"])
            w.writerows(rows)


if __name__ == "__main__":
    main()
