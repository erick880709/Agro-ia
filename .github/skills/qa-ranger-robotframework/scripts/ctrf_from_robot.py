#!/usr/bin/env python3
"""
Convierte uno o varios output.xml de Robot Framework en un reporte CTRF
(https://ctrf.io) para el contrato QA de Ranger.

Uso:
  python ctrf_from_robot.py --output results/<runId>/output.xml --out resources/qa/reports/<runId>/ctrf.json \
      [--evidencia resources/qa/test-results/<runId>] [--proyecto chromium] [--project-root .]
  # Reintentos: pasa los output.xml en orden (original, rerun 1, rerun 2...)
  python ctrf_from_robot.py --output out/output.xml --output out/rerun1.xml --out ...

- No requiere Robot Framework: lee el XML (formato RF 6 y RF 7).
- Identidad del caso: prefijo del nombre (TC-, SEC-, FRAUD-, API-, A11Y-, UT-, PERF-) o un tag con ese
  formato. Prioridad: [critical|high|medium|low] en el nombre o como tag. Si alguno viene solo de los
  tags, el nombre CTRF se compone como "ID [prioridad] nombre" para que el lector común lo identifique.
  Un caso sin ID o prioridad conserva su nombre y se reporta en stderr: el validador lo contará como
  error de la corrida (no se inventa identidad).
- Adjuntos: solo archivos que EXISTEN en <evidencia>/<CASE-ID>/attempt-<n>/ (o <evidencia>/<CASE-ID>/).
  Se clasifican por extensión: video (.webm/.mp4), screenshot (.png/.jpg), trace (.zip/.har); el resto, log.
  El último intento usa nombres simples; los previos, "attempt-<n>/<tipo>".
- --proyecto fija "browser" (solo para pruebas de navegador). En API/BD no se declara proyecto.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

CASO = re.compile(r"^(TC|SEC|FRAUD|API|A11Y|UT|PERF)-\d+$")
CASO_NOMBRE = re.compile(r"^((TC|SEC|FRAUD|API|A11Y|UT|PERF)-\d+)\b")
PRIO = ("critical", "high", "medium", "low")
PRIO_NOMBRE = re.compile(r"\[(critical|high|medium|low)\]", re.I)
ESTADO = {"PASS": "passed", "FAIL": "failed", "SKIP": "skipped", "NOT RUN": "other", "NOT_RUN": "other"}
KINDS = [
    (re.compile(r"\.(webm|mp4|mkv|avi|mov)$", re.I), "video", lambda e: f"video/{'quicktime' if e == 'mov' else e}"),
    (re.compile(r"\.(png|jpe?g|gif|webp)$", re.I), "screenshot", lambda e: f"image/{'jpeg' if e == 'jpg' else e}"),
    (re.compile(r"\.(zip|har)$", re.I), "trace", lambda e: "application/json" if e == "har" else "application/zip"),
]


def ms_rf6(ts):
    return int(datetime.strptime(ts, "%Y%m%d %H:%M:%S.%f").timestamp() * 1000)


def tiempos(status):
    """(inicio_ms, duracion_ms) para RF 7 (start/elapsed) y RF 6 (starttime/endtime)."""
    if status.get("start"):
        ini = int(datetime.fromisoformat(status.get("start")).timestamp() * 1000)
        return ini, int(float(status.get("elapsed", "0")) * 1000)
    st, en = status.get("starttime"), status.get("endtime")
    if st and en and st != "N/A" and en != "N/A":
        a, b = ms_rf6(st), ms_rf6(en)
        return a, b - a
    return 0, 0


def leer(output: Path):
    root = ET.parse(output).getroot()
    if root.tag != "robot":
        sys.exit(f"{output} no es un output.xml de Robot Framework")
    tests = []

    def walk(suite, ruta):
        ruta = ruta + [suite.get("name", "")]
        for t in suite.findall("test"):
            st = t.find("status")
            ini, dur = tiempos(st)
            tests.append({
                "nombre": t.get("name", ""), "rfid": t.get("id", ""), "suite": ruta,
                "tags": [x.text or "" for x in t.findall("tags/tag")] + [x.text or "" for x in t.findall("tag")],
                "estado": ESTADO.get(st.get("status", ""), "other"), "inicio": ini, "duracion": dur,
                "mensaje": (st.text or "").strip(),
            })
        for s in suite.findall("suite"):
            walk(s, ruta)

    for s in root.findall("suite"):
        walk(s, [])
    return root.get("generator", "Robot"), tests


def identidad(t):
    nombre = t["nombre"]
    m = CASO_NOMBRE.match(nombre)
    cid = m.group(1) if m else next((x.upper() for x in t["tags"] if CASO.match(x.upper())), None)
    pm = PRIO_NOMBRE.search(nombre)
    prio = pm.group(1).lower() if pm else next((x.lower() for x in t["tags"] if x.lower() in PRIO), None)
    if cid and prio and not (m and pm):
        base = nombre
        if m:
            base = nombre[len(m.group(1)):].strip()
        base = PRIO_NOMBRE.sub("", base).strip()
        nombre = f"{cid} [{prio}] {base}".strip()
    return cid, prio, nombre


def adjuntos(evidencia: Path, cid, intento, ultimo, root: Path):
    if not evidencia or not cid:
        return []
    carpeta = evidencia / cid / f"attempt-{intento}"
    if not carpeta.is_dir():
        carpeta = evidencia / cid if intento == 0 and (evidencia / cid).is_dir() else None
    if carpeta is None:
        return []
    out = []
    for f in sorted(p for p in carpeta.iterdir() if p.is_file()):
        ext = f.suffix[1:].lower()
        kind, ctype = next(((k, c(ext)) for rx, k, c in KINDS if rx.search(f.name)), ("log", "text/plain"))
        try:
            ruta = f.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            sys.exit(f"La evidencia {f} está fuera del proyecto {root}")
        out.append({"name": kind if ultimo else f"attempt-{intento}/{kind}", "contentType": ctype, "path": ruta})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", action="append", required=True, help="output.xml (repetible, en orden de intento)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--evidencia")
    ap.add_argument("--proyecto")
    ap.add_argument("--project-root", default=".")
    a = ap.parse_args()
    root = Path(a.project_root)
    evid = Path(a.evidencia) if a.evidencia else None
    if evid and not evid.is_absolute():
        evid = root / evid

    intentos, generador = [], "Robot"
    for o in a.output:
        generador, tests = leer(Path(o))
        intentos.append(tests)

    # El último intento decide el estado; los previos cuentan como reintentos.
    final, historial = {}, {}
    for n, tests in enumerate(intentos):
        for t in tests:
            cid, prio, nombre = identidad(t)
            clave = (cid or ".".join(t["suite"] + [t["nombre"]]), a.proyecto or "")
            historial.setdefault(clave, []).append((n, t))
            final[clave] = (cid, prio, nombre, t, n)

    salida, sin_id = [], []
    for clave, (cid, prio, nombre, t, n) in final.items():
        previos = [x for x in historial[clave] if x[0] != n]
        item = {"name": nombre, "status": t["estado"], "duration": t["duracion"], "suite": t["suite"]}
        if a.proyecto:
            item["browser"] = a.proyecto
        if t["tags"]:
            item["tags"] = t["tags"]
        if t["estado"] == "failed" and t["mensaje"]:
            item["message"] = t["mensaje"][:2000]
        if previos:
            item["retries"] = len(previos)
            item["flaky"] = t["estado"] == "passed" and any(p[1]["estado"] == "failed" for p in previos)
        att = []
        for pn, _ in previos:
            att += adjuntos(evid, cid, pn, False, root)
        att += adjuntos(evid, cid, n, True, root)
        if att:
            item["attachments"] = att
        if not (cid and prio):
            sin_id.append(t["nombre"])
        salida.append(item)

    todos = [t for ts in intentos for t in ts]
    inicio = min((t["inicio"] for t in todos if t["inicio"]), default=0)
    fin = max((t["inicio"] + t["duracion"] for t in todos if t["inicio"]), default=0)
    resumen = {k: sum(1 for x in salida if x["status"] == k) for k in ("passed", "failed", "pending", "skipped", "other")}
    ctrf = {
        "reportFormat": "CTRF", "specVersion": "0.1.0",
        "generatedBy": "qa-ranger-robotframework/ctrf_from_robot.py",
        "results": {
            "tool": {"name": "robotframework", "version": re.sub(r"^\D*", "", generador).split(" ")[0] or None},
            "summary": {"tests": len(salida), **resumen, "start": inicio, "stop": fin},
            "tests": salida,
        },
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ctrf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CTRF escrito en {out}: {len(salida)} casos ({resumen['passed']} pasan, {resumen['failed']} fallan)")
    if sin_id:
        print("AVISO: casos sin ID o prioridad verificable (el validador los cuenta como error): " + "; ".join(sin_id), file=sys.stderr)


if __name__ == "__main__":
    main()
