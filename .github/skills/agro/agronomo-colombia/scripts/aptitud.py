#!/usr/bin/env python3
"""Preseleccion de aptitud climatica/altitudinal por cultivo (cafe, platano, frijol, citricos).

Usa solo rangos con fuente de references/rangos.json. Si una variable no tiene dato
verificado, lo dice; nunca inventa un rango. No sustituye la zonificacion de UPRA.
"""
import argparse
import json
import sys
from pathlib import Path

RANGOS = Path(__file__).resolve().parent.parent / "references" / "rangos.json"
VARS = ["altitud", "temp", "precip", "ph"]
UNIDAD = {"altitud": "msnm", "temp": "C", "precip": "mm/anio", "ph": ""}


def clasificar(valor, spec):
    if spec is None:
        return "sin dato verificado"
    if "minimo" in spec:
        return "cumple minimo" if valor >= spec["minimo"] else "fuera del rango de referencia"
    lo, hi = spec["optimo"]
    if lo <= valor <= hi:
        return "optimo"
    tol = spec.get("tolerable")
    if tol and tol[0] <= valor <= tol[1]:
        return "tolerable"
    return "fuera del rango de referencia"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cultivo", required=True, choices=["cafe", "platano", "frijol", "citricos"])
    p.add_argument("--variedad", help="platano: harton|dominico|dominico-harton; "
                                      "frijol: cargamanto|arbustivo-clima-medio|arbustivo-clima-calido")
    p.add_argument("--altitud", type=float)
    p.add_argument("--temp", type=float, help="temperatura media anual (C)")
    p.add_argument("--precip", type=float, help="precipitacion anual (mm)")
    p.add_argument("--ph", type=float)
    p.add_argument("--ficha", help="JSON generado por geo.py; los argumentos explicitos prevalecen")
    a = p.parse_args()

    estimados = set()
    if a.ficha:
        f = json.loads(Path(a.ficha).read_text(encoding="utf-8"))
        alt = (f.get("altitud") or {}).get("valor_m")
        if a.altitud is None and alt is not None:
            a.altitud = alt
        t = (f.get("clima") or {}).get("temp_media_estimada_c")
        if a.temp is None and t is not None:
            a.temp, _ = t, estimados.add("temp")
        ph = (((f.get("suelo") or {}).get("datos") or {}).get("phh2o") or {}).get("media_0_30cm")
        if a.ph is None and ph is not None:
            a.ph, _ = ph, estimados.add("ph")

    datos = json.loads(RANGOS.read_text(encoding="utf-8"))[a.cultivo]
    fuente = datos.get("fuente", "")
    if "variedades" in datos:
        if not a.variedad or a.variedad not in datos["variedades"]:
            print(f"Indica --variedad. Opciones: {', '.join(datos['variedades'])}", file=sys.stderr)
            return 2
        v = datos["variedades"][a.variedad]
        variables, fuente = v["variables"], v.get("fuente", "")
    else:
        variables = datos["variables"]

    entradas = {"altitud": a.altitud, "temp": a.temp, "precip": a.precip, "ph": a.ph}
    print(f"Cultivo: {datos['nombre']}" + (f" | variedad: {a.variedad}" if a.variedad else ""))
    for var in VARS:
        val = entradas[var]
        if val is None:
            continue
        spec = variables.get(var)
        estado = clasificar(val, spec)
        marca = " (estimado)" if var in estimados else ""
        print(f"  {var:<8} {val:g} {UNIDAD[var]:<8} -> {estado}{marca}")
        if spec and spec.get("fuente"):
            print(f"           fuente: {spec['fuente']}")
    for al in datos.get("alertas", []):
        val = entradas.get(al["variable"])
        if val is not None and al["op"] == ">" and val > al["valor"]:
            print(f"  ALERTA: {al['texto']}")
    if fuente:
        print(f"Fuente: {fuente}")
    if datos.get("nota"):
        print(f"Nota: {datos['nota']}")
    print("Aviso: preseleccion orientativa; confirmar con UPRA y asistencia tecnica.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
