#!/usr/bin/env python3
"""
Genera un proyecto Robot Framework listo para correr con el flujo QA Ranger.

Uso:
  python scaffold.py --nombre banca-api-tests --perfil api --salida ./out [--base-url http://localhost:8080]
  python scaffold.py --nombre banca-web --perfil web-browser --salida ./out [--base-url ...] [--ruta-login /login]
  python scaffold.py --nombre banca-web --perfil web-selenium --salida ./out
  python scaffold.py --nombre cartera-bd --perfil db --motor postgres --tabla cuentas --columna estado --clave numero
  python scaffold.py --nombre aw0000000-bd --perfil db-release --motor postgres --tabla ... (estándar release Azure)

Perfiles:
  api           RequestsLibrary                    (evidencia nivel api: raw_results)
  web-browser   Browser Library (Playwright)       (video + trace + screenshot por caso)
  web-selenium  SeleniumLibrary (WebDriver)        (screenshot + traza; video solo con Grid que grabe)
  db            DatabaseLibrary 2.x, variables DB_* (nivel api)
  db-release    Layout acceptance_test/ del stage "Acceptance Test" de un release Azure DevOps (agentes Linux,
                variables DB/HOST/PORT/USER/PASSWORD en mayúscula; sintaxis compatible RF 5+ y DatabaseLibrary 1.x/2.x)
Motores (db, db-release): postgres, oracle, sqlserver, mysql, db2, sqlite (sqlite solo en db).
"""
import argparse
import re
import shutil
import signal
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TPL = SKILL / "templates"
MOTORES = {
    "postgres": ("psycopg2", "5432", "psycopg2-binary==2.9.13", "%s"),
    "oracle": ("oracledb", "1521", "oracledb==26.1.0", ":1"),
    "sqlserver": ("pymssql", "1433", "pymssql==2.4.6", "%s"),
    "mysql": ("pymysql", "3306", "PyMySQL==1.2.3", "%s"),
    "db2": ("ibm_db_dbi", "50000", "ibm_db==3.3.0", "?"),
    "sqlite": ("sqlite3", "", "", "?"),
}
SECRETOS = {
    "api": ["QA_API_TOKEN"],
    "web-browser": ["E2E_USER", "E2E_PASSWORD", "QA_CLAVE_INVALIDA"],
    "web-selenium": ["E2E_USER", "E2E_PASSWORD", "QA_CLAVE_INVALIDA"],
    "db": ["DB_NAME", "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD"],
    "db-release": ["DB", "HOST", "PORT", "USER", "PASSWORD"],
}


def conexion_db(motor):
    if motor == "sqlite":
        return ("    Verificar Variables De Entorno    DB_NAME\n"
                "    Connect To Database    ${DB_MODULE}    database=%{DB_NAME}    isolation_level=${None}")
    return ("    Verificar Variables De Entorno    DB_NAME    DB_HOST    DB_PORT    DB_USER    DB_PASSWORD\n"
            "    Connect To Database    ${DB_MODULE}\n"
            "    ...    db_name=%{DB_NAME}    db_user=%{DB_USER}    db_password=%{DB_PASSWORD}\n"
            "    ...    db_host=%{DB_HOST}    db_port=%{DB_PORT}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--perfil", required=True, choices=list(SECRETOS))
    ap.add_argument("--salida", default=".")
    ap.add_argument("--env", default="qa")
    ap.add_argument("--rf", default="7.5", help="versión exacta de robotframework para requirements.txt")
    ap.add_argument("--base-url", default="http://localhost:8080")
    ap.add_argument("--ci", choices=["github", "azure", "ambos", "ninguno"], default=None)
    ap.add_argument("--motor", choices=list(MOTORES), default="postgres")
    ap.add_argument("--tabla", default="cuentas")
    ap.add_argument("--columna", default="estado")
    ap.add_argument("--clave", default="numero")
    ap.add_argument("--clave-ejemplo", default="0001")
    ap.add_argument("--valor-ejemplo", default="ACTIVA")
    ap.add_argument("--ruta-salud", default="/health")
    ap.add_argument("--ruta-login", default="/login")
    ap.add_argument("--campo-usuario", default="usuario")
    ap.add_argument("--campo-clave", default="clave")
    ap.add_argument("--boton-ingresar", default="Ingresar")
    ap.add_argument("--heading-inicio", default="Inicio")
    a = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.nombre):
        sys.exit("--nombre debe ser kebab-case")
    if not re.fullmatch(r"\d+\.\d+(\.\d+)?", a.rf):
        sys.exit("--rf debe ser una versión exacta (p. ej. 7.5)")
    if not re.fullmatch(r"[a-z]+", a.env):
        sys.exit("--env debe ser un nombre simple en minúsculas (dev, qa, stg...)")
    for campo in ("tabla", "columna", "clave"):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", getattr(a, campo)):
            sys.exit(f"--{campo} debe ser un identificador SQL simple")
    if a.perfil == "db-release" and a.motor == "sqlite":
        sys.exit("db-release usa la conexión posicional del release; sqlite solo con --perfil db")
    ci = a.ci or ("ninguno" if a.perfil == "db-release" else "github")

    root = Path(a.salida).resolve() / a.nombre
    if root.exists() and any(root.iterdir()):
        sys.exit(f"{root} ya existe y no está vacío")

    modulo, puerto, driver, ph = MOTORES[a.motor]
    release = a.perfil == "db-release"
    web = a.perfil.startswith("web")
    tests = "acceptance_test/test_cases" if release else "tests"
    suites = "acceptance_test" if release else "tests resources"
    rf_major = "5" if release else a.rf.split(".")[0]
    secretos = SECRETOS[a.perfil]
    stack = {
        "api": "RequestsLibrary 0.9.7",
        "web-browser": "Browser Library 20.6.0 (Playwright, [bb])",
        "web-selenium": "SeleniumLibrary 6.9.0 (Selenium 4, Selenium Manager)",
        "db": f"DatabaseLibrary 2.5.0 + {modulo}",
        "db-release": f"DatabaseLibrary (versión del agente) + {modulo} — release Azure DevOps",
    }[a.perfil]
    extra_paso = ("      - name: Navegadores de Playwright\n        run: rfbrowser install chromium --with-deps\n"
                  if a.perfil == "web-browser" else "")
    extra_az = ("  - script: rfbrowser install chromium --with-deps\n    displayName: Navegadores de Playwright\n"
                if a.perfil == "web-browser" else "")
    ctx = {
        "__NOMBRE__": a.nombre, "__ENV__": a.env, "__RF__": a.rf, "__RF_MAJOR__": rf_major,
        "__BASE_URL__": a.base_url if not a.perfil.startswith("db") else f"{a.motor} (host por variable de entorno)",
        "__STACK__": stack, "__CI__": {"github": "GitHub Actions", "azure": "Azure Pipelines (YAML)",
                                       "ambos": "GitHub Actions y Azure Pipelines",
                                       "ninguno": "release clásico Azure DevOps (PIPELINE_RELEASE.md)" if release else "sin CI"}[ci],
        "__VARFILE__": "(solo variables de entorno)" if release else f"variables/{a.env}.py",
        "__ENV_VARS__": ", ".join(f"`{s}`" for s in secretos),
        "__VARFILE_ARGS__": "" if release else f"--variablefile variables/{a.env}.py",
        "__TESTS__": tests, "__SUITES__": suites,
        "__PROYECTO_ARG__": "--proyecto chromium" if web else "",
        "__DB_MODULE__": modulo, "__DB_PORT__": puerto, "__DRIVER_PKG__": driver, "__PH__": ph,
        "__TABLA__": a.tabla, "__COLUMNA__": a.columna, "__CLAVE__": a.clave,
        "__CLAVE_EJEMPLO__": a.clave_ejemplo, "__VALOR_EJEMPLO__": a.valor_ejemplo,
        "__CONNECT__": conexion_db(a.motor),
        "__RUTA_SALUD__": a.ruta_salud, "__RUTA_LOGIN__": a.ruta_login, "__CAMPO_USUARIO__": a.campo_usuario,
        "__CAMPO_CLAVE__": a.campo_clave, "__BOTON_INGRESAR__": a.boton_ingresar, "__HEADING_INICIO__": a.heading_inicio,
        "__GH_SECRETS__": "\n".join(f"      {s}: ${{{{ secrets.{s} }}}}" for s in secretos),
        "__AZ_SECRETS__": "\n".join(f"      {s}: $({s})" for s in secretos),
        "__GH_EXTRA_STEP__": extra_paso.rstrip("\n"), "__AZ_EXTRA_STEP__": extra_az.rstrip("\n"),
    }

    def render(t):
        for k, v in ctx.items():
            t = t.replace(k, v)
        return t

    def copiar(src: Path, dest_root: Path):
        for f in sorted(src.rglob("*")):
            if not f.is_file() or "__pycache__" in f.parts:
                continue
            rel = f.relative_to(src).as_posix().replace("__ENV__", a.env)
            dest = dest_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(render(f.read_text(encoding="utf-8")), encoding="utf-8")

    copiar(TPL / a.perfil, root)
    com = TPL / "common"
    lib_dest = root / ("acceptance_test/libraries" if release else "libraries")
    copiar(com / "libraries", lib_dest)
    (root / ".gitignore").write_text(render((com / "gitignore").read_text(encoding="utf-8")), encoding="utf-8")
    (root / f"Linea_Base_{a.nombre}.md").write_text(render((com / "Linea_Base_TEMPLATE.md").read_text(encoding="utf-8")), encoding="utf-8")
    eje = root / "ejecutar.sh"
    eje.write_text(render((com / "ejecutar.sh").read_text(encoding="utf-8")), encoding="utf-8")
    eje.chmod(0o755)
    if ci in ("github", "ambos"):
        copiar(com / ".github", root / ".github")
    if ci in ("azure", "ambos"):
        (root / "azure-pipelines.yml").write_text(render((com / "azure-pipelines.yml").read_text(encoding="utf-8")), encoding="utf-8")
    tools = root / "tools"
    tools.mkdir()
    for s in ("lint_robot.py", "ctrf_from_robot.py", "rtm_from_robot.py"):
        shutil.copy2(SKILL / "scripts" / s, tools / s)
    # requirements sin líneas vacías (sqlite no necesita driver)
    req = root / "requirements.txt"
    req.write_text("\n".join(l for l in req.read_text(encoding="utf-8").splitlines() if l.strip()) + "\n", encoding="utf-8")
    (root / "README.md").write_text(render(README), encoding="utf-8")

    restantes = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
                 and re.search(r"__[A-Z_]+__", p.read_text(encoding="utf-8", errors="ignore"))]
    if restantes:
        sys.exit("ERROR interno: placeholders sin reemplazar en " + ", ".join(restantes))

    print(f"Proyecto generado en {root}")
    for p in sorted(root.rglob("*")):
        if p.is_file():
            print("  " + p.relative_to(root).as_posix())
    if web:
        print("\nPendiente: verificar los localizadores marcados con TODO(verificar-locator) contra la app real.")
    if a.perfil.startswith("db"):
        print("\nPendiente: reemplazar tabla/columnas/reglas de ejemplo por las del modelo de datos y la HU.")


README = """# __NOMBRE__

Pruebas Robot Framework (__STACK__) generadas con qa-ranger-robotframework.

```bash
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
cp env.example .env.qa   # completar con valores de PRUEBA; .env.qa está en .gitignore
./ejecutar.sh __ENV__                   # lint -> dry run -> robot -> CTRF + RTM
./ejecutar.sh __ENV__ --include smoke   # por tag
REINTENTOS=1 ./ejecutar.sh __ENV__      # reintenta fallidos una vez y lo reporta como reintento
```
Resultados: `resources/qa/test-results/<runId>/` (output.xml, log.html, report.html, evidencia por caso)
· CTRF y RTM: `resources/qa/reports/<runId>/`.
Variables de entorno requeridas: __ENV_VARS__.
"""

if __name__ == "__main__":
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
