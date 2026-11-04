#!/usr/bin/env python3
"""
Genera un proyecto de pruebas Selenium listo para correr.

Uso:
  python scaffold.py --nombre banca-ui-tests --stack java-junit5 --salida ./out \
      [--group co.empresa.qa] [--java 17] [--selenium 4.50.0] [--base-url http://localhost:3000] \
      [--env qa] [--hilos 4] [--campo-usuario usuario] [--campo-clave clave] \
      [--boton-ingresar Ingresar] [--ruta-login /login] [--heading-inicio Inicio]
  python scaffold.py --nombre banca-ui-py --stack python-pytest --salida ./out

Stacks: java-junit5 (Maven), python-pytest.
"""
import argparse
import signal
import re
import shutil
import sys
from pathlib import Path

TPL = Path(__file__).resolve().parent.parent / "templates"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--stack", choices=["java-junit5", "python-pytest"], default="java-junit5")
    ap.add_argument("--salida", default=".")
    ap.add_argument("--group", default="co.empresa.qa")
    ap.add_argument("--java", default="17", choices=["11", "17", "21"])
    ap.add_argument("--selenium", default="4.50.0")
    ap.add_argument("--base-url", default="http://localhost:3000")
    ap.add_argument("--env", default="qa")
    ap.add_argument("--hilos", default="4")
    ap.add_argument("--campo-usuario", default="usuario")
    ap.add_argument("--campo-clave", default="clave")
    ap.add_argument("--boton-ingresar", default="Ingresar")
    ap.add_argument("--ruta-login", default="/login")
    ap.add_argument("--heading-inicio", default="Inicio")
    a = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.nombre):
        sys.exit("--nombre debe ser kebab-case")
    if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*", a.group):
        sys.exit("--group debe ser un paquete Java válido (p. ej. co.empresa.qa)")
    if not re.fullmatch(r"\d+\.\d+\.\d+", a.selenium):
        sys.exit("--selenium debe ser una versión exacta (p. ej. 4.50.0)")
    if not re.fullmatch(r"[a-z]+", a.env):
        sys.exit("--env debe ser un nombre simple en minúsculas (dev, qa, stg...)")

    root = Path(a.salida).resolve() / a.nombre
    if root.exists() and any(root.iterdir()):
        sys.exit(f"{root} ya existe y no está vacío")

    ctx = {
        "__GROUP__": a.group, "__NOMBRE__": a.nombre, "__JAVA__": a.java, "__SELENIUM__": a.selenium,
        "__PKG__": a.group, "__ENV__": a.env, "__BASE_URL__": a.base_url, "__HILOS__": a.hilos,
        "__CAMPO_USUARIO__": a.campo_usuario, "__CAMPO_CLAVE__": a.campo_clave,
        "__BOTON_INGRESAR__": a.boton_ingresar, "__RUTA_LOGIN__": a.ruta_login,
        "__HEADING_INICIO__": a.heading_inicio,
        "__STACK__": f"Java {a.java} + JUnit 5 + AssertJ (Maven)" if a.stack == "java-junit5" else "Python + pytest",
    }

    def render(t):
        for k, v in ctx.items():
            t = t.replace(k, v)
        return t

    src = TPL / a.stack
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(src).as_posix()
        rel = rel.replace("__PKGPATH__", a.group.replace(".", "/")).replace("__ENV__", a.env)
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(f.read_text(encoding="utf-8")), encoding="utf-8")

    (root / ".gitignore").write_text((TPL / "common/gitignore").read_text(encoding="utf-8"), encoding="utf-8")
    (root / f"Linea_Base_{a.nombre}.md").write_text(
        render((TPL / "common/Linea_Base_TEMPLATE.md").read_text(encoding="utf-8")), encoding="utf-8")
    (root / "README.md").write_text(render(README_JAVA if a.stack == "java-junit5" else README_PY), encoding="utf-8")

    restantes = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
                 and re.search(r"__[A-Z_]+__", p.read_text(encoding="utf-8"))]
    if restantes:
        sys.exit("ERROR interno: placeholders sin reemplazar en " + ", ".join(restantes))

    print(f"Proyecto generado en {root}")
    for p in sorted(root.rglob("*")):
        if p.is_file():
            print("  " + p.relative_to(root).as_posix())
    print("\nPendiente: verificar los localizadores marcados con TODO(verificar-locator) contra la app real.")


README_JAVA = """# __NOMBRE__

Pruebas UI con Selenium __SELENIUM__, Java __JAVA__, JUnit 5 y AssertJ.

```bash
export E2E_USER=... E2E_PASSWORD=...
mvn test                                   # ambiente __ENV__ (src/test/resources/config/__ENV__.properties)
mvn test -Denv=qa -Dgroups=smoke           # por ambiente y tag
mvn test -Dheadless=false                  # ver el navegador
mvn test -DgridUrl=http://localhost:4444   # contra Selenium Grid / docker-selenium
```
Evidencia de fallos: `target/evidencia/` · Reportes: `target/surefire-reports/`
"""

README_PY = """# __NOMBRE__

Pruebas UI con Selenium __SELENIUM__ y pytest.

```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
export E2E_USER=... E2E_PASSWORD=...
pytest                                     # ambiente __ENV__ (__BASE_URL__)
pytest -m smoke -n 4                       # smoke en paralelo
pytest --base-url-app https://qa.ejemplo.com --headed
pytest --grid-url http://localhost:4444
```
Evidencia de fallos: `reports/evidencia/` · JUnit XML: `reports/junit.xml`
"""

if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # salida limpia con | head
    main()
