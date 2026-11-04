#!/usr/bin/env python3
"""
Genera los archivos de un proyecto Playwright Test en TypeScript.
Antes de ejecutar las pruebas, instala las dependencias y configura el ambiente y las credenciales.

Uso:
  python scaffold.py --nombre banca-web-e2e --salida ./out \
      [--version 1.63.0] [--navegadores chromium,firefox,mobile] \
      [--base-url-local http://localhost:3000] [--default-env qa] \
      [--web-server "npm run start"] [--ci github,azure] \
      [--label-usuario Usuario] [--label-clave Contraseña] [--boton-ingresar Ingresar] \
      [--ruta-login /login] [--heading-inicio Inicio]

Después:
  cd <salida>/<nombre> && npm install && npx playwright install --with-deps chromium
  cp .env.example .env   # completar credenciales
  npx playwright test
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TPL = SKILL_DIR / "templates"

DEVICES = {
    "firefox": "Desktop Firefox",
    "webkit": "Desktop Safari",
    "edge": None,           # Ejecuta Microsoft Edge mediante el canal msedge.
    "mobile": "Pixel 7",
    "iphone": "iPhone 15",
}


def project_block(name: str) -> str:
    if name == "edge":
        use = "{ ...devices['Desktop Edge'], channel: 'msedge', storageState: STORAGE_STATE }"
    else:
        use = f"{{ ...devices['{DEVICES[name]}'], storageState: STORAGE_STATE }}"
    extra = "\n      grep: /@mobile/," if name in ("mobile", "iphone") else ""
    return (f"    {{\n      name: '{name}',\n      use: {use},\n"
            f"      dependencies: ['setup'],{extra}\n    }},\n")


def web_server_block(cmd: str | None, url: str) -> str:
    if not cmd:
        return ""
    return (f"  webServer: {{\n    command: {json.dumps(cmd)},\n    url: {json.dumps(url)},\n"
            f"    reuseExistingServer: !isCI,\n    timeout: 120_000,\n  }},\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--salida", default=".")
    ap.add_argument("--version", default="1.63.0", help="versión exacta de @playwright/test")
    ap.add_argument("--navegadores", default="chromium",
                    help="chromium siempre incluido; extras: " + ",".join(DEVICES))
    ap.add_argument("--base-url-local", default="http://localhost:3000")
    ap.add_argument("--default-env", default="qa", choices=["local", "dev", "qa", "stg"])
    ap.add_argument("--web-server", default=None, help="comando para levantar la app (omitir si ya está desplegada)")
    ap.add_argument("--ci", default="github,azure")
    ap.add_argument("--label-usuario", default="Usuario")
    ap.add_argument("--label-clave", default="Contraseña")
    ap.add_argument("--boton-ingresar", default="Ingresar")
    ap.add_argument("--ruta-login", default="/login")
    ap.add_argument("--heading-inicio", default="Inicio")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", args.nombre):
        sys.exit("--nombre debe ser kebab-case")
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        sys.exit("--version debe ser exacta (p. ej. 1.63.0): versiones flotantes rompen las baselines y el CI")
    navs = list(dict.fromkeys(n.strip() for n in args.navegadores.split(",") if n.strip() and n.strip() != "chromium"))
    for n in navs:
        if n not in DEVICES:
            sys.exit(f"navegador no soportado: {n}")
    cis = {c.strip() for c in args.ci.split(",") if c.strip()}

    if not cis <= {"github", "azure"}:
        sys.exit("--ci solo admite github,azure")
    engines = list(dict.fromkeys(["chromium", *[{"iphone": "webkit", "mobile": "chromium", "edge": "msedge"}.get(n, n) for n in navs]]))

    root = Path(args.salida).resolve() / args.nombre
    if root.exists() and any(root.iterdir()):
        sys.exit(f"{root} ya existe y no está vacío")

    ctx = {
        "NOMBRE": args.nombre,
        "BROWSER_INSTALL": " ".join(engines),
        "PLAYWRIGHT_VERSION": args.version,
        "EXTRA_PROJECTS": "".join(project_block(n) for n in navs),
        "WEB_SERVER": web_server_block(args.web_server, args.base_url_local),
        "BASE_URL_LOCAL": args.base_url_local,
        "BASE_URL_DEV": "https://dev.CAMBIAR.com",
        "BASE_URL_QA": "https://qa.CAMBIAR.com",
        "BASE_URL_STG": "https://stg.CAMBIAR.com",
        "DEFAULT_ENV": args.default_env,
        "LABEL_USUARIO": args.label_usuario,
        "LABEL_CLAVE": args.label_clave,
        "BOTON_INGRESAR": args.boton_ingresar,
        "RUTA_LOGIN": args.ruta_login,
        "HEADING_INICIO": args.heading_inicio,
        "PROYECTOS": ", ".join(["chromium", *navs]),
        "CI": " + ".join(sorted(cis)) or "-",
    }

    def render(text: str) -> str:
        for k in ("LABEL_USUARIO", "LABEL_CLAVE", "BOTON_INGRESAR", "RUTA_LOGIN", "HEADING_INICIO", "BASE_URL_LOCAL", "BASE_URL_DEV", "BASE_URL_QA", "BASE_URL_STG", "DEFAULT_ENV"):
            text = text.replace("\'{{" + k + "}}\'", json.dumps(ctx[k], ensure_ascii=False))
        for k, v in ctx.items():
            text = text.replace("{{" + k + "}}", v)
        return text

    src = TPL / "project"
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        if rel.as_posix() == ".github/workflows/e2e.yml" and "github" not in cis:
            continue
        if rel.as_posix() == "azure-pipelines.yml" and "azure" not in cis:
            continue
        dest = root / ("." + rel.name if rel.name == "gitignore" else rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(f.read_text(encoding="utf-8")), encoding="utf-8")

    (root / f"Linea_Base_{args.nombre}.md").write_text(
        render((TPL / "common/Linea_Base_TEMPLATE.md").read_text(encoding="utf-8")), encoding="utf-8")
    (root / "README.md").write_text(README.format(**{k.lower(): v for k, v in ctx.items()}), encoding="utf-8")
    (root / "playwright/.auth").mkdir(parents=True, exist_ok=True)

    print(f"Proyecto generado en {root}")
    for p in sorted(root.rglob("*")):
        if p.is_file():
            print("  " + p.relative_to(root).as_posix())
    pend = [p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and ("CAMBIAR" in p.read_text(encoding="utf-8") or "TODO(verificar-locator)" in p.read_text(encoding="utf-8"))]
    if pend:
        print("\nPendientes de completar (URLs CAMBIAR / locators por verificar): " + ", ".join(pend))


README = """# {nombre}

Pruebas E2E con Playwright {playwright_version} (TypeScript).

## Preparar
```bash
npm install
npx playwright install --with-deps {browser_install}
cp .env.example .env        # completar E2E_USER / E2E_PASSWORD
```

## Ejecutar
```bash
npx playwright test                         # ambiente por defecto: {default_env}
TEST_ENV=dev npx playwright test --grep @smoke
npx playwright test tests/login.spec.ts --project=chromium
npx playwright test --ui                    # modo interactivo
npx playwright show-report resources/qa/reports/<runId>/html
npm run lint                                # ESLint + tipos
```

## Estructura
- `playwright.config.ts` — proyectos ({proyectos}), reporters, trazas
- Evidencia: `resources/qa/<CASE-ID>/<runId>/<proyecto>/attempt-<n>/`; reportes: `resources/qa/reports/<runId>/`.
- `reporters/evidence-ctrf.ts` organiza los adjuntos automáticamente y delega el CTRF al paquete instalado, sin manifest.
- Los originales se conservan en `resources/qa/test-results/<runId>/`. Comparte `resources/qa/` con su estructura.
- `QA_RUN_ID` conserva el ID del host; sin él se genera un ID único.
- Video, trace y screenshot de todos los casos, incluidos los exitosos y CI.
- `config/env.ts` — URLs por ambiente
- `fixtures/` — `test` extendido (page objects, datos, fixture de errores JS)
- `pages/` — page objects
- `tests/auth.setup.ts` — login una vez por ejecución → `playwright/.auth/user.json`
- `Linea_Base_{nombre}.md` — memoria del proyecto
"""

if __name__ == "__main__":
    main()
