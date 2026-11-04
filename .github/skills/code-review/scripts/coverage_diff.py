#!/usr/bin/env python3
"""Cobertura de las líneas nuevas de un diff ("new code coverage").

Cruza un diff unificado con uno o varios reportes de cobertura ya generados por
el proyecto y calcula, para las líneas añadidas en código fuente, cuántas son
ejecutables, cuántas están cubiertas y cuáles no (archivo:línea). Es la misma
idea que la condición `new_coverage` del quality gate de SonarQube, calculada
localmente: sirve cuando no hay Sonar o cuando su último análisis no
corresponde a la revisión revisada.

Formatos: LCOV (`--lcov`), JaCoCo XML (`--jacoco`), Cobertura XML
(`--cobertura`, también coverage.py/Istanbul cobertura) y perfil de Go
(`--go-cover`). Todos repetibles.

Uso:
    git diff main...HEAD | python coverage_diff.py --jacoco build/reports/jacoco/test/jacocoTestReport.xml
    python coverage_diff.py --diff-file cambio.diff --lcov coverage/lcov.info --threshold 80 --json

Reglas:
- Solo líneas añadidas (`+`) de archivos fuente; los tests se excluyen.
- Una línea añadida que el reporte no lista no es ejecutable (comentario,
  firma, llave) y no cuenta.
- Un archivo fuente del diff que no aparece en ningún reporte va a
  `sinDatos`: no se cuenta como cubierto ni como 0 %; es una señal a revisar
  (archivo no instrumentado o sin tests que lo carguen).

No ejecuta tests ni genera reportes: usa los que el proyecto produjo para la
revisión actual. Solo biblioteca estándar.
Código de salida: 0 normal; 1 si se indicó --threshold y no se cumple; 2 entrada inválida.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath

TEST_RE = re.compile(r"(^|/)(src/test/|test/|tests/|__tests__/|spec/)|(Test|Tests|IT|Spec)\.(java|kt|groovy|cs)$|"
                     r"(_test\.go|\.test\.\w+|\.spec\.\w+|_test\.py|test_[^/]*\.py)$", re.I)
SOURCE_EXT = (".java", ".kt", ".groovy", ".scala", ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".go",
              ".rs", ".cs", ".rb", ".php", ".swift", ".dart", ".c", ".cpp", ".cc", ".h")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def added_lines(diff: str) -> dict[str, set[int]]:
    files: dict[str, set[int]] = {}
    current, line = None, 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[4:].strip().split("\t")[0]
            current = None if path == "/dev/null" else re.sub(r"^b/", "", path)
            if current is not None:
                files.setdefault(current, set())
            continue
        if raw.startswith("--- ") or raw.startswith("diff --git"):
            continue
        m = HUNK.match(raw)
        if m:
            line = int(m.group(1))
            continue
        if current is None or not line:
            continue
        if raw.startswith("+"):
            files[current].add(line)
            line += 1
        elif raw.startswith("-"):
            continue
        elif raw.startswith("\\"):
            continue
        else:
            line += 1
    return files


# Cada parser devuelve {ruta_reporte: {línea: (cubierta: bool, ramas_total, ramas_cubiertas)}}
def parse_lcov(text: str) -> dict:
    out, current = {}, None
    branches: dict = {}
    for raw in text.splitlines():
        if raw.startswith("SF:"):
            current = raw[3:].strip()
            out.setdefault(current, {})
            branches = {}
        elif raw.startswith("DA:") and current:
            parts = raw[3:].split(",")
            ln, hits = int(parts[0]), int(float(parts[1]))
            prev = out[current].get(ln, (False, 0, 0))
            out[current][ln] = (prev[0] or hits > 0, prev[1], prev[2])
        elif raw.startswith("BRDA:") and current:
            ln, _, _, taken = raw[5:].split(",")
            tot, cov = branches.get(int(ln), (0, 0))
            branches[int(ln)] = (tot + 1, cov + (1 if taken not in ("-", "0") else 0))
        elif raw.startswith("end_of_record") and current:
            for ln, (tot, cov) in branches.items():
                c, _, _ = out[current].get(ln, (cov > 0, 0, 0))
                out[current][ln] = (c, tot, cov)
            current = None
    return out


def parse_jacoco(text: str) -> dict:
    root = ET.fromstring(text)
    out = {}
    for pkg in root.iter("package"):
        pname = pkg.get("name", "")
        for sf in pkg.findall("sourcefile"):
            key = f"{pname}/{sf.get('name')}" if pname else sf.get("name")
            lines = out.setdefault(key, {})
            for ln in sf.findall("line"):
                nr = int(ln.get("nr"))
                ci, mb, cb = int(ln.get("ci", 0)), int(ln.get("mb", 0)), int(ln.get("cb", 0))
                lines[nr] = (ci > 0, mb + cb, cb)
    return out


def parse_cobertura(text: str) -> dict:
    root = ET.fromstring(text)
    sources = [s.text.strip() for s in root.iter("source") if s.text and s.text.strip()]
    out = {}
    for cls in root.iter("class"):
        fn = cls.get("filename")
        if not fn:
            continue
        lines = out.setdefault(fn, {})
        for ln in cls.iter("line"):
            nr, hits = int(ln.get("number")), int(float(ln.get("hits", 0)))
            tot = cov = 0
            m = re.search(r"\((\d+)/(\d+)\)", ln.get("condition-coverage", ""))
            if ln.get("branch") == "true" and m:
                cov, tot = int(m.group(1)), int(m.group(2))
            prev = lines.get(nr, (False, 0, 0))
            lines[nr] = (prev[0] or hits > 0, max(prev[1], tot), max(prev[2], cov))
        for s in sources:
            out.setdefault(f"{s.rstrip('/')}/{fn}", lines)
    return out


def parse_go(text: str) -> dict:
    out = {}
    for raw in text.splitlines():
        if raw.startswith("mode:") or not raw.strip():
            continue
        m = re.match(r"^(.+):(\d+)\.\d+,(\d+)\.\d+ \d+ (\d+)$", raw.strip())
        if not m:
            raise ValueError(f"Línea de perfil Go inválida: {raw[:80]}")
        fn, a, b, count = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        lines = out.setdefault(fn, {})
        for nr in range(a, b + 1):
            prev = lines.get(nr, (False, 0, 0))
            lines[nr] = (prev[0] or count > 0, 0, 0)
    return out


def match(path: str, reports: dict) -> str | None:
    """Busca la entrada del reporte que corresponde a la ruta del diff (sufijo más largo)."""
    p = PurePosixPath(path).as_posix()
    best, best_len = None, 0
    for key in reports:
        k = PurePosixPath(key.replace("\\", "/")).as_posix().lstrip("./")
        if p == k or p.endswith("/" + k) or k.endswith("/" + p):
            n = min(len(k), len(p))
            if n > best_len:
                best, best_len = key, n
    return best


def compute(diff: str, reports: dict, threshold: float | None, include_tests: bool = False) -> dict:
    files = added_lines(diff)
    result = {"archivos": [], "sinDatos": [], "lineasEjecutables": 0, "lineasCubiertas": 0,
              "ramas": 0, "ramasCubiertas": 0, "cobertura": None, "umbral": threshold, "cumple": None}
    for path, added in sorted(files.items()):
        if not path.endswith(SOURCE_EXT) or (TEST_RE.search(path) and not include_tests) or not added:
            continue
        key = match(path, reports)
        if key is None:
            result["sinDatos"].append(path)
            continue
        data = reports[key]
        execu = sorted(l for l in added if l in data)
        if not execu:
            continue
        cubiertas = [l for l in execu if data[l][0]]
        sin = [l for l in execu if not data[l][0]]
        parciales = [l for l in execu if data[l][1] and data[l][2] < data[l][1]]
        ramas = sum(data[l][1] for l in execu)
        ramas_cov = sum(data[l][2] for l in execu)
        result["archivos"].append({
            "archivo": path, "ejecutables": len(execu), "cubiertas": len(cubiertas),
            "cobertura": round(100 * len(cubiertas) / len(execu), 1),
            "sinCubrir": sin, "ramasParciales": parciales})
        result["lineasEjecutables"] += len(execu)
        result["lineasCubiertas"] += len(cubiertas)
        result["ramas"] += ramas
        result["ramasCubiertas"] += ramas_cov
    if result["lineasEjecutables"]:
        # Igual que Sonar: (líneas cubiertas + ramas cubiertas) / (líneas + ramas)
        num = result["lineasCubiertas"] + result["ramasCubiertas"]
        den = result["lineasEjecutables"] + result["ramas"]
        result["cobertura"] = round(100 * num / den, 1)
        result["coberturaLineas"] = round(100 * result["lineasCubiertas"] / result["lineasEjecutables"], 1)
    if threshold is not None and result["cobertura"] is not None:
        result["cumple"] = result["cobertura"] >= threshold
    result["archivos"].sort(key=lambda f: f["cobertura"])
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--diff-file")
    ap.add_argument("--lcov", action="append", default=[])
    ap.add_argument("--jacoco", action="append", default=[])
    ap.add_argument("--cobertura", action="append", default=[])
    ap.add_argument("--go-cover", action="append", default=[])
    ap.add_argument("--threshold", type=float)
    ap.add_argument("--include-tests", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        diff = open(a.diff_file, encoding="utf-8").read() if a.diff_file else sys.stdin.read()
        reports: dict = {}
        for paths, parser in ((a.lcov, parse_lcov), (a.jacoco, parse_jacoco), (a.cobertura, parse_cobertura), (a.go_cover, parse_go)):
            for p in paths:
                for k, v in parser(open(p, encoding="utf-8").read()).items():
                    merged = reports.setdefault(k, {})
                    for ln, val in v.items():
                        prev = merged.get(ln, (False, 0, 0))
                        merged[ln] = (prev[0] or val[0], max(prev[1], val[1]), max(prev[2], val[2]))
    except (OSError, ValueError, ET.ParseError) as e:
        print(f"Entrada inválida: {e}", file=sys.stderr)
        return 2
    if not reports:
        print("Indica al menos un reporte de cobertura (--lcov, --jacoco, --cobertura o --go-cover).", file=sys.stderr)
        return 2
    if not diff.strip():
        print("El diff está vacío.", file=sys.stderr)
        return 2
    r = compute(diff, reports, a.threshold, a.include_tests)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        cob = "sin líneas ejecutables nuevas" if r["cobertura"] is None else f"{r['cobertura']} %"
        print(f"Cobertura de código nuevo: {cob} ({r['lineasCubiertas']}/{r['lineasEjecutables']} líneas, "
              f"{r['ramasCubiertas']}/{r['ramas']} ramas)" + (f" · umbral {r['umbral']} %: {'cumple' if r['cumple'] else 'NO cumple'}"
                                                             if r["cumple"] is not None else ""))
        for f in r["archivos"]:
            extra = f" · sin cubrir: {', '.join(map(str, f['sinCubrir'][:20]))}" if f["sinCubrir"] else ""
            print(f"  {f['cobertura']:>5} %  {f['archivo']}{extra}")
        for f in r["sinDatos"]:
            print(f"  sin datos  {f}  (no aparece en ningún reporte)")
    return 1 if r["cumple"] is False else 0


if __name__ == "__main__":
    sys.exit(main())
