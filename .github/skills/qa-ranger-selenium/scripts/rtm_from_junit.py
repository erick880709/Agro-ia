#!/usr/bin/env python3
"""
Matriz de trazabilidad requisito -> criterio -> tests -> estado desde reportes JUnit XML
(Maven Surefire / Gradle / TestNG / pytest --junitxml).

Reconoce en el nombre del test (o su clase):
  - "[HU-245][CA-1] ..."                (JUnit 5 @DisplayName con usePhrasedTestCaseMethodName, TestNG description)
  - "test_hu245_ca1_..."                (pytest; también tc_/req_ en minúsculas)
Uso:
  python rtm_from_junit.py target/surefire-reports [--out rtm.md] [--csv rtm.csv]
  python rtm_from_junit.py reports/junit.xml
"""
import argparse
import signal
import csv
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

BRACKETS = re.compile(r"\[([A-Za-z]+-?\d+)\](?:\[([A-Za-z]+-?\d+|[A-Z]{2,})\])?")
SNAKE = re.compile(r"(?:^|_)(hu|us|req|tc)(\d+)(?:_(ca|ac|seg)(\d*))?(?=_|$)", re.I)


def casos(path: Path):
    files = [path] if path.is_file() else sorted(path.rglob("*.xml"))
    for f in files:
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        for tc in root.iter("testcase"):
            estado = "PASA"
            if tc.find("failure") is not None or tc.find("error") is not None:
                estado = "FALLA"
            elif tc.find("skipped") is not None:
                estado = "OMITIDO"
            yield {"clase": tc.get("classname", ""), "nombre": tc.get("name", ""), "estado": estado, "archivo": f.name}


def enlaces(nombre: str):
    out = [(m.group(1).upper(), (m.group(2) or "-").upper()) for m in BRACKETS.finditer(nombre)]
    if not out:
        for m in SNAKE.finditer(nombre):
            req = f"{m.group(1).upper()}-{m.group(2)}"
            crit = f"{m.group(3).upper()}-{m.group(4)}" if m.group(3) and m.group(4) else (m.group(3) or "-").upper()
            out.append((req, crit))
    return list(dict.fromkeys(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reportes")
    ap.add_argument("--out")
    ap.add_argument("--csv")
    a = ap.parse_args()
    tests = list(casos(Path(a.reportes)))
    if not tests:
        sys.exit("No se encontraron <testcase> en los XML indicados.")
    matriz, sin = defaultdict(lambda: defaultdict(list)), []
    for t in tests:
        ls = enlaces(t["nombre"]) or enlaces(t["clase"])
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
    md = ["# Matriz de trazabilidad — Selenium", "",
          f"Tests: {len(tests)} ({pasa} pasan) · Requisitos: {len(matriz)} · Criterios: {total} · En verde: {verdes}/{total} · Sin trazabilidad: {len(sin)}",
          "", "| Requisito | Criterio | Estado | Tests |", "|---|---|---|---|"]
    filas = []
    for req in sorted(matriz):
        for crit in sorted(matriz[req]):
            ts = matriz[req][crit]
            md.append(f"| {req} | {crit} | {estado(ts)} | " + "<br>".join(f"{t['nombre']} ({t['estado']})" for t in ts) + " |")
            filas += [[req, crit, t["clase"], t["nombre"], t["estado"]] for t in ts]
    if sin:
        md += ["", "## Tests sin trazabilidad", "", "| Clase | Test | Estado |", "|---|---|---|"]
        md += [f"| {t['clase']} | {t['nombre']} | {t['estado']} |" for t in sin]
    md += ["", "> Si los nombres salen como métodos (`metodo()`) en vez del @DisplayName, falta `usePhrasedTestCaseMethodName` en Surefire (resources/08 §1)."]
    txt = "\n".join(md) + "\n"
    if a.out:
        Path(a.out).write_text(txt, encoding="utf-8"); print(f"RTM escrita en {a.out}")
    else:
        print(txt)
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["requisito", "criterio", "clase", "test", "estado"]); w.writerows(filas)


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # salida limpia con | head
    main()
