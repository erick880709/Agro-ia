#!/usr/bin/env python3
"""
Analiza resultados de JMeter (.jtl en CSV): estadísticas por etiqueta, veredicto contra un SLA,
comparación con una ejecución base (regresión) y salida para CI.

Uso:
  python analizar_jtl.py resultados.jtl [--sla sla.json] [--base base.jtl]
                         [--excluir-inicio SEG] [--solo-transacciones]
                         [--md resumen.md] [--junit junit-sla.xml] [--json]

- Percentiles por el método de rango más cercano (nearest-rank), el mismo criterio que las
  columnas "90% Line" del Aggregate Report de JMeter.
- Transacciones: filas de Transaction Controllers (responseMessage "Number of samples in transaction")
  o, si no se detectan, etiquetas que empiezan por dos dígitos y guion bajo (convención 01_Login).
- Código de salida: 1 si algún criterio del SLA o de regresión falla; 2 si el archivo no es válido.

sla.json:
{
  "global": {"error_pct_max": 1.0},
  "transacciones": {"01_Login": {"p95_ms": 800, "p99_ms": 1500, "error_pct_max": 0.5, "throughput_min": 1.0}},
  "regresion": {"p95_tolerancia_pct": 10, "p95_min_diferencia_ms": 50}
}
"""
import argparse
import csv
import json
import math
import re
import signal
import sys
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

COLUMNAS_DEFECTO = ["timeStamp", "elapsed", "label", "responseCode", "responseMessage", "threadName", "dataType",
                    "success", "failureMessage", "bytes", "sentBytes", "grpThreads", "allThreads", "URL",
                    "Latency", "IdleTime", "Connect"]
MARCA_TX = "Number of samples in transaction"


def leer(path: Path):
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        primera = fh.readline()
        fh.seek(0)
        if primera.lstrip().startswith("<"):
            sys.exit(f"{path}: formato XML no soportado; usar jmeter.save.saveservice.output_format=csv")
        tiene_encabezado = "timeStamp" in primera and "elapsed" in primera
        lector = csv.DictReader(fh) if tiene_encabezado else csv.DictReader(fh, fieldnames=COLUMNAS_DEFECTO)
        filas = []
        for r in lector:
            if r.get("timeStamp") in (None, "", "timeStamp"):
                continue
            try:
                filas.append({
                    "ts": int(float(r["timeStamp"])), "elapsed": int(float(r["elapsed"])), "label": r["label"],
                    "code": r.get("responseCode", ""), "msg": r.get("responseMessage", "") or "",
                    "ok": str(r.get("success", "")).strip().lower() == "true",
                    "fail": r.get("failureMessage", "") or "", "hilos": int(float(r.get("allThreads") or 0)),
                })
            except (KeyError, ValueError) as e:
                sys.exit(f"{path}: fila inválida ({e}). ¿Es un JTL CSV de JMeter?")
    if not filas:
        print(f"{path}: sin muestras", file=sys.stderr)
        sys.exit(2)
    return filas


def percentil(ordenados, p):
    if not ordenados:
        return 0
    k = max(1, math.ceil(p / 100 * len(ordenados)))
    return ordenados[k - 1]


def estadisticas(filas, excluir_inicio=0, solo_tx=False):
    t0 = min(f["ts"] for f in filas)
    filas = [f for f in filas if f["ts"] >= t0 + excluir_inicio * 1000]
    tx_labels = {f["label"] for f in filas if f["msg"].startswith(MARCA_TX)}
    if not tx_labels:
        tx_labels = {f["label"] for f in filas if re.match(r"^\d{2}_", f["label"])}
    if solo_tx and tx_labels:
        filas = [f for f in filas if f["label"] in tx_labels]
    por = defaultdict(list)
    for f in filas:
        por[f["label"]].append(f)
    inicio = min(f["ts"] for f in filas)
    fin = max(f["ts"] + f["elapsed"] for f in filas)
    dur = max((fin - inicio) / 1000, 0.001)

    def calc(lista):
        t = sorted(x["elapsed"] for x in lista)
        err = sum(1 for x in lista if not x["ok"])
        return {"muestras": len(lista), "errores": err, "error_pct": round(100 * err / len(lista), 3),
                "avg_ms": round(sum(t) / len(t), 1), "p50_ms": percentil(t, 50), "p90_ms": percentil(t, 90),
                "p95_ms": percentil(t, 95), "p99_ms": percentil(t, 99), "max_ms": t[-1],
                "throughput": round(len(lista) / dur, 3)}

    stats = {lab: calc(l) for lab, l in sorted(por.items())}
    stats_glob = calc(filas)
    errores = defaultdict(int)
    for f in filas:
        if not f["ok"]:
            errores[(f["label"], f["code"], (f["fail"] or f["msg"])[:90])] += 1
    hilos_prom = sum(f["hilos"] for f in filas) / len(filas)
    return {"stats": stats, "global": stats_glob, "duracion_s": round(dur, 1), "transacciones": sorted(tx_labels),
            "errores": sorted(errores.items(), key=lambda kv: -kv[1]), "hilos_promedio": round(hilos_prom, 1),
            "excluido_inicio_s": excluir_inicio}


def evaluar(res, sla, base):
    checks = []   # (nombre, ok, detalle)
    g = res["global"]
    gl = (sla or {}).get("global", {})
    if "error_pct_max" in gl:
        checks.append(("global · errores", g["error_pct"] <= gl["error_pct_max"], f"{g['error_pct']}% (máx {gl['error_pct_max']}%)"))
    for tx, crit in (sla or {}).get("transacciones", {}).items():
        s = res["stats"].get(tx)
        if s is None:
            checks.append((f"{tx} · presente", False, "la transacción no aparece en los resultados"))
            continue
        for clave, op, unidad in (("avg_ms", "<=", "ms"), ("p50_ms", "<=", "ms"), ("p90_ms", "<=", "ms"), ("p95_ms", "<=", "ms"),
                                  ("p99_ms", "<=", "ms"), ("error_pct_max", "<=", "%"), ("throughput_min", ">=", "/s")):
            if clave not in crit:
                continue
            real = s["error_pct"] if clave == "error_pct_max" else s["throughput"] if clave == "throughput_min" else s[clave]
            limite = crit[clave]
            ok = real <= limite if op == "<=" else real >= limite
            nom = clave.replace("_max", "").replace("_min", "")
            checks.append((f"{tx} · {nom}", ok, f"{real}{unidad} ({'máx' if op == '<=' else 'mín'} {limite}{unidad})"))
    if base is not None:
        reg = (sla or {}).get("regresion", {})
        tol = reg.get("p95_tolerancia_pct", 10)
        min_abs = reg.get("p95_min_diferencia_ms", 50)   # evita falsas alarmas por ruido en tiempos muy bajos
        for tx, s in res["stats"].items():
            b = base["stats"].get(tx)
            if not b or (res["transacciones"] and tx not in res["transacciones"]):
                continue
            dif = s["p95_ms"] - b["p95_ms"]
            cambio = round(100 * dif / b["p95_ms"], 1) if b["p95_ms"] else (0.0 if dif <= 0 else float("inf"))
            regresion = cambio > tol and dif > min_abs
            checks.append((f"{tx} · regresión p95", not regresion,
                           f"{b['p95_ms']} → {s['p95_ms']} ms ({cambio:+}%, {dif:+} ms; falla si > +{tol}% y > +{min_abs} ms)"))
    return checks


def markdown(res, checks, base):
    L = [f"# Resultados de rendimiento", "",
         f"Duración analizada: {res['duracion_s']} s · Muestras: {res['global']['muestras']} · Errores: {res['global']['error_pct']}% · "
         f"Throughput: {res['global']['throughput']}/s · Hilos activos promedio: {res['hilos_promedio']}"
         + (f" · Excluidos los primeros {res['excluido_inicio_s']} s" if res["excluido_inicio_s"] else ""), "",
         "| Etiqueta | Muestras | Error % | Prom | p50 | p90 | p95 | p99 | Máx | Throughput/s |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for lab, s in res["stats"].items():
        marca = " **(tx)**" if lab in res["transacciones"] else ""
        L.append(f"| {lab}{marca} | {s['muestras']} | {s['error_pct']} | {s['avg_ms']} | {s['p50_ms']} | {s['p90_ms']} | "
                 f"{s['p95_ms']} | {s['p99_ms']} | {s['max_ms']} | {s['throughput']} |")
    if checks:
        ok = all(c[1] for c in checks)
        L += ["", f"## Veredicto: {'✅ APROBADO' if ok else '❌ NO APROBADO'}", "", "| Criterio | Resultado | Detalle |", "|---|---|---|"]
        L += [f"| {n} | {'✅' if o else '❌'} | {d} |" for n, o, d in checks]
    if res["errores"]:
        L += ["", "## Errores principales", "", "| Etiqueta | Código | Mensaje | Cantidad |", "|---|---|---|---:|"]
        L += [f"| {lab} | {code} | {msg.replace('|', '/')} | {n} |" for (lab, code, msg), n in res["errores"][:10]]
    L += ["", "> Percentiles por rango más cercano. Verifica que el generador no fue el cuello de botella antes de concluir (resources/12)."]
    return "\n".join(L) + "\n"


def junit(checks):
    fallos = sum(1 for c in checks if not c[1])
    x = [f'<?xml version="1.0" encoding="UTF-8"?>', f'<testsuite name="SLA rendimiento" tests="{len(checks)}" failures="{fallos}">']
    for n, ok, d in checks:
        x.append(f'  <testcase classname="rendimiento" name={quoteattr(n)}>' + ("" if ok else f'<failure message={quoteattr(d)}/>') + "</testcase>")
    x.append("</testsuite>")
    return "\n".join(x) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jtl")
    ap.add_argument("--sla")
    ap.add_argument("--base")
    ap.add_argument("--excluir-inicio", type=int, default=0)
    ap.add_argument("--solo-transacciones", action="store_true")
    ap.add_argument("--md")
    ap.add_argument("--junit")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    sla = json.loads(Path(a.sla).read_text(encoding="utf-8")) if a.sla else None
    res = estadisticas(leer(Path(a.jtl)), a.excluir_inicio, a.solo_transacciones)
    base = estadisticas(leer(Path(a.base)), a.excluir_inicio, a.solo_transacciones) if a.base else None
    checks = evaluar(res, sla, base)
    md = markdown(res, checks, base)
    if a.md:
        Path(a.md).write_text(md, encoding="utf-8")
    if a.junit:
        Path(a.junit).write_text(junit(checks), encoding="utf-8")
    if a.json:
        print(json.dumps({**res, "errores": [{"label": k[0], "codigo": k[1], "mensaje": k[2], "n": n} for k, n in res["errores"]],
                          "criterios": [{"criterio": n, "ok": o, "detalle": d} for n, o, d in checks]}, ensure_ascii=False, indent=2))
    else:
        print(md)
    sys.exit(0 if all(c[1] for c in checks) else 1)


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
