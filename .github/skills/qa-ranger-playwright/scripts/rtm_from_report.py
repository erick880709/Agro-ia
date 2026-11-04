#!/usr/bin/env python3
"""
Genera una matriz de trazabilidad (RTM) desde el reporte JSON de Playwright.
La matriz relaciona requisito, criterio, prueba y estado de ejecución.

Identifica requisitos en cada prueba mediante título, anotación o etiqueta:
  - Título:     test('[HU-245][CA-1] transfiere con saldo suficiente', ...)
  - Anotación:  { annotation: { type: 'req', description: 'HU-245/CA-1' } }
  - Tag:        { tag: '@req:HU-245/CA-1' }   (también @req=HU-245)

Uso:
  npx playwright test --reporter=json > results/results.json   (o reporter json con outputFile en la config)
  python rtm_from_report.py results/results.json [--out rtm.md] [--csv rtm.csv]
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ID_IN_TITLE = re.compile(r"\[([A-Za-z]+-?\d+)\](?:\[([A-Za-z]+-?\d+|[A-Z]{2,})\])?")
REQ_VALUE = re.compile(r"^([^/\s]+)(?:/(\S+))?$")
STATUS = {"expected": "PASA", "unexpected": "FALLA", "flaky": "FLAKY", "skipped": "OMITIDO"}


def walk(suite, file_hint, acc):
    file = suite.get("file") or file_hint
    for spec in suite.get("specs", []):
        for t in spec.get("tests", []):
            acc.append({
                "file": spec.get("file") or file,
                "title": spec.get("title", ""),
                "tags": spec.get("tags", []) or [],
                "annotations": t.get("annotations", []) or [],
                "project": t.get("projectName", ""),
                "status": STATUS.get(t.get("status", ""), t.get("status", "?").upper()),
            })
    for child in suite.get("suites", []):
        walk(child, file, acc)


def links_of(test):
    links = []
    for a in test["annotations"]:
        if a.get("type") in ("req", "requisito", "requirement") and a.get("description"):
            m = REQ_VALUE.match(a["description"].strip())
            if m:
                links.append((m.group(1), m.group(2) or "-"))
    for tag in test["tags"]:
        t = tag.lstrip("@")
        m = re.match(r"^req[:=](.+)$", t)
        if m:
            mm = REQ_VALUE.match(m.group(1))
            if mm:
                links.append((mm.group(1), mm.group(2) or "-"))
    for m in ID_IN_TITLE.finditer(test["title"]):
        links.append((m.group(1), m.group(2) or "-"))
    return list(dict.fromkeys(links))


def overall(statuses):
    s = set(statuses)
    if "FALLA" in s:
        return "❌ FALLA"
    if "FLAKY" in s:
        return "⚠️ FLAKY"
    if s == {"PASA"}:
        return "✅ PASA"
    return "⚠️ PARCIAL"


def main():
    # Usa UTF-8 para conservar los acentos y símbolos del reporte en Windows.
    # La salida cp1252 puede fallar al imprimir caracteres como → o ✅.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reporte", help="archivo JSON del reporter json de Playwright")
    ap.add_argument("--out")
    ap.add_argument("--csv")
    args = ap.parse_args()

    try:
        data = json.loads(Path(args.reporte).read_text(encoding="utf-8"))
    except Exception as e:
        sys.exit(f"No se pudo leer el reporte JSON: {e}. Generarlo con --reporter=json o reporter ['json', {{ outputFile }}].")
    if "suites" not in data:
        sys.exit("El archivo no parece un reporte JSON de Playwright (falta 'suites').")

    tests = []
    for s in data["suites"]:
        walk(s, s.get("file", "?"), tests)
    # Excluye los proyectos de preparación y limpieza (setup/teardown) del conteo de casos.
    tests = [t for t in tests if not re.search(r"\.(setup|teardown)\.[jt]s$", t["file"] or "")
             and t["project"] not in ("setup", "teardown")]

    matrix = defaultdict(lambda: defaultdict(list))
    sin_traza = []
    for t in tests:
        ls = links_of(t)
        if not ls:
            sin_traza.append(t)
        for req, crit in ls:
            matrix[req][crit].append(t)

    total = sum(len(c) for c in matrix.values())
    verdes = sum(1 for c in matrix.values() for ts in c.values() if overall([t["status"] for t in ts]) == "✅ PASA")
    stats = data.get("stats", {})
    md = ["# Matriz de trazabilidad — Playwright", ""]
    if stats:
        md.append(f"Ejecución: {stats.get('expected', 0)} pasan · {stats.get('unexpected', 0)} fallan · "
                  f"{stats.get('flaky', 0)} flaky · {stats.get('skipped', 0)} omitidos")
    md.append(f"Requisitos: {len(matrix)} · Criterios: {total} · En verde: {verdes}/{total} · Tests sin trazabilidad: {len(sin_traza)}")
    md += ["", "| Requisito | Criterio | Estado | Tests (proyecto: estado) |", "|---|---|---|---|"]
    rows = []
    for req in sorted(matrix):
        for crit in sorted(matrix[req]):
            ts = matrix[req][crit]
            det = "<br>".join(f"{t['title']} ({t['project']}: {t['status']})" for t in ts)
            md.append(f"| {req} | {crit} | {overall([t['status'] for t in ts])} | {det} |")
            rows += [[req, crit, t["file"], t["title"], t["project"], t["status"]] for t in ts]
    if sin_traza:
        md += ["", "## Tests sin trazabilidad", "", "| Archivo | Test | Proyecto | Estado |", "|---|---|---|---|"]
        md += [f"| {t['file']} | {t['title']} | {t['project']} | {t['status']} |" for t in sin_traza]
    md += ["", "> Solo aparecen criterios con al menos un test. Los criterios de la HU sin test deben reportarse aparte como **no verificados**. "
           "Un test FLAKY no cuenta como evidencia de cumplimiento."]

    text = "\n".join(md) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"RTM escrita en {args.out}")
    else:
        print(text)
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["requisito", "criterio", "archivo", "test", "proyecto", "estado"])
            w.writerows(rows)


if __name__ == "__main__":
    main()
