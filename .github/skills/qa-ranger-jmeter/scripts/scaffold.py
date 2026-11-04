#!/usr/bin/env python3
"""
Genera un proyecto de pruebas de rendimiento con JMeter listo para correr.

Uso:
  python scaffold.py --nombre pagos-rendimiento --salida ./out [--ci github,azure]

Incluye: plan.jmx parametrizado (verificado contra el catálogo de JMeter 5.6.3), env/*.properties,
datos sin secretos, sla.json, ejecutar.sh (lint → JMeter → dashboard → gate SLA/regresión),
pipelines, Línea Base y una copia de scripts/ (lint_jmx.py, analizar_jtl.py, catálogo) para CI.
"""
import argparse
import re
import shutil
import signal
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--salida", default=".")
    ap.add_argument("--ci", default="github,azure")
    a = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.nombre):
        sys.exit("--nombre debe ser kebab-case")
    root = Path(a.salida).resolve() / a.nombre
    if root.exists() and any(root.iterdir()):
        sys.exit(f"{root} ya existe y no está vacío")
    ci = {c.strip() for c in a.ci.split(",") if c.strip()}

    src = SKILL / "templates" / "project"
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(src).as_posix()
        if rel.startswith(".github/") and "github" not in ci or rel == "azure-pipelines.yml" and "azure" not in ci:
            continue
        dest = root / rel.replace("__NOMBRE__", a.nombre)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f.read_text(encoding="utf-8").replace("__NOMBRE__", a.nombre), encoding="utf-8")
        dest.chmod(f.stat().st_mode)
    (root / f"Linea_Base_{a.nombre}.md").write_text(
        (SKILL / "templates/common/Linea_Base_TEMPLATE.md").read_text(encoding="utf-8").replace("__NOMBRE__", a.nombre), encoding="utf-8")
    (root / ".gitignore").write_text("resultados/\njmeter.log\n*.log\n.env\n", encoding="utf-8")
    scripts = root / "scripts"
    (scripts / "data").mkdir(parents=True, exist_ok=True)
    for s in ("lint_jmx.py", "analizar_jtl.py"):
        shutil.copy2(SKILL / "scripts" / s, scripts / s)
    shutil.copy2(SKILL / "scripts/data/jmx_catalogo.json", scripts / "data" / "jmx_catalogo.json")

    print(f"Proyecto generado en {root}")
    for p in sorted(root.rglob("*")):
        if p.is_file():
            print("  " + p.relative_to(root).as_posix())
    print("\nSiguiente: adaptar los pasos de plan.jmx a tu sistema, completar env/*.properties (CAMBIAR) y sla.json,"
          "\nluego validar con 1 usuario: CLAVE_PRUEBAS=... ./ejecutar.sh local -Jusuarios=1 -Jduracion=60")


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
