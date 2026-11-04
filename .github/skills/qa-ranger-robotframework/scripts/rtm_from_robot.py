#!/usr/bin/env python3
"""
Matriz de trazabilidad requisito -> criterio -> casos -> estado desde output.xml de Robot Framework.

Reconoce requisitos y criterios en el nombre del test o en sus tags:
  - Nombre: "TC-01 [critical] [HU-245][CA-1] comportamiento"
  - Tags:   HU-245    CA-1      (también RF-01, REQ-7, US-3, AC-2)
Uso:
  python rtm_from_robot.py results/<runId>/output.xml [--out rtm.md] [--csv rtm.csv]
"""
import argparse
import csv
import re
import signal
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

REQ = re.compile(r"^(HU|US|RF|REQ|RQ)-?\d+$", re.I)
CRIT = re.compile(r"^(CA|AC)-?\d+$", re.I)
BRACKETS = re.compile(r"\[((?:HU|US|RF|REQ|RQ)-?\d+)\](?:\[((?:CA|AC)-?\d+)\])?", re.I)
ESTADO = {"PASS": "PASA", "FAIL": "FALLA", "SKIP": "OMITIDO", "NOT RUN": "NO EJECUTADO"}


def casos(path: Path):
    root = ET.parse(path).getroot()
    for t in root.iter("test"):
        st = t.find("status")
        tags = [x.text or "" for x in t.findall("tags/tag")] + [x.text or "" for x in t.findall("tag")]
        yield {"nombre": t.get("name", ""), "tags": tags, "estado": ESTADO.get(st.get("status"), "OTRO")}


def enlaces(t):
    out = [(m.group(1).upper(), (m.group(2) or "-").upper()) for m in BRACKETS.finditer(t["nombre"])]
    if not out:
        reqs = [x.upper() for x in t["tags"] if REQ.match(x)]
        crits = [x.upper() for x in t["tags"] if CRIT.match(x)] or ["-"]
        out = [(r, c) for r in reqs for c in crits]
    return list(dict.fromkeys(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output")
    ap.add_argument("--out")
    ap.add_argument("--csv")
    a = ap.parse_args()
    tests = list(casos(Path(a.output)))
    if not tests:
        sys.exit("El output.xml no contiene tests.")
    matriz, sin = defaultdict(lambda: defaultdict(list)), []
    for t in tests:
        ls = enlaces(t)
        if not ls:
            sin.append(t)
        for req, crit in ls:
            matriz[req][crit].append(t)

    def estado(ts):
        s = {t["estado"] for t in ts}
        return "❌ FALLA" if "FALLA" in s else "✅ PASA" if s == {"PASA"} else "⚠️ PARCIAL"

    total = sum(len(c) for c in matriz.values())
    verdes = sum(1 for c in matriz.values() for ts in c.values() if estado(ts) == "✅ PASA")
    pasa = sum(t["estado"] == "PASA" for t in tests)
    md = ["# Matriz de trazabilidad — Robot Framework", "",
          f"Tests: {len(tests)} ({pasa} pasan) · Requisitos: {len(matriz)} · Criterios: {total} · En verde: {verdes}/{total} · Sin trazabilidad: {len(sin)}",
          "", "| Requisito | Criterio | Estado | Tests |", "|---|---|---|---|"]
    filas = []
    for req in sorted(matriz):
        for crit in sorted(matriz[req]):
            ts = matriz[req][crit]
            md.append(f"| {req} | {crit} | {estado(ts)} | " + "<br>".join(f"{t['nombre']} ({t['estado']})" for t in ts) + " |")
            filas += [[req, crit, t["nombre"], t["estado"]] for t in ts]
    if sin:
        md += ["", "## Tests sin trazabilidad", "", "| Test | Estado |", "|---|---|"]
        md += [f"| {t['nombre']} | {t['estado']} |" for t in sin]
    txt = "\n".join(md) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(txt, encoding="utf-8")
        print(f"RTM escrita en {a.out}")
    else:
        print(txt)
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["requisito", "criterio", "test", "estado"])
            w.writerows(filas)


if __name__ == "__main__":
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
