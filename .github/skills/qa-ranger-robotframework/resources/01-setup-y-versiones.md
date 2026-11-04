# 01 — Setup y versiones

## 1. Versiones verificadas (PyPI, octubre de 2026)

| Paquete | Versión | Python | Notas |
|---|---|---|---|
| `robotframework` | 7.5 | ≥ 3.8 | `robot --version` sale con código 251: usa `python -c "import robot; print(robot.__version__)"` |
| `robotframework-databaselibrary` | 2.5.0 | ≥ 3.8 | Argumentos renombrados en 2.0 (`db_module`, `db_name`, …); keywords con motor de aserciones |
| `robotframework-requests` | 0.9.7 | — | Sin pasos post-instalación |
| `robotframework-browser` | 20.6.0 | ≥ 3.10 | `[bb]` (BrowserBatteries) evita Node.js |
| `robotframework-seleniumlibrary` | 6.9.0 | ≥ 3.10 | Selenium ≥ 4.6 resuelve drivers (Selenium Manager) |
| `RESTinstance` | 1.8.0 | ≥ 3.11 | `Library    REST` |
| `robotframework-robocop` | 9.1.2 | ≥ 3.10 | Lint y formato; `--target-version` con el major de RF |
| `robotcode` | 2.8.0 | ≥ 3.10 | CLI: discover, analyze, libdoc, results, debug |
| `robotframework-pabot` | 5.2.2 | ≥ 3.6 | Ejecución paralela |

Verifica la última antes de fijar versiones (`pip index versions <paquete>`). Fija versiones exactas en `requirements.txt` (o lockfile) y regístralas en la Línea Base.

## 2. Entorno

Usa la herramienta del proyecto: `uv.lock` → uv; `poetry.lock` → Poetry; `requirements*.txt` o `.venv` → venv + pip. Proyecto nuevo sin preferencia del equipo: venv + pip (lo que suelen tener los agentes corporativos).

```bash
python3.12 -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m robot --dryrun --outputdir results/dryrun tests   # todo resuelve antes de ejecutar
```

- Nunca `sudo pip`, `--break-system-packages` ni `pip install --user` para dependencias del proyecto; `pipx`/`uv tool` aíslan y `robot` no ve esas librerías.
- Ejecuta siempre con el intérprete del entorno (`python -m robot`, `uv run robot`, `poetry run robot`).
- Proxy corporativo: `pip install --proxy http://...` o `PIP_INDEX_URL` hacia el Artifactory interno; para TLS inspeccionado, `REQUESTS_CA_BUNDLE`/`PIP_CERT` con el bundle corporativo, nunca desactivar verificación.

## 3. Librerías web

| Librería | Instalación | Paso extra |
|---|---|---|
| Browser (recomendada para web nueva) | `pip install "robotframework-browser[bb]"` | `rfbrowser install chromium` (descarga navegadores; en CI `--with-deps`) |
| Browser con Node.js | `pip install robotframework-browser` | Node 22/24 LTS y `rfbrowser init chromium` |
| SeleniumLibrary | `pip install robotframework-seleniumlibrary` | Un navegador instalado o `remote_url` a Grid |

No mezcles `rfbrowser install` (solo `[bb]`) con `rfbrowser init` (ruta Node). Sin acceso a la CDN de Playwright, usa la imagen `ghcr.io/marketsquare/robotframework-browser/rfbrowser-stable` o un mirror interno.

## 4. Drivers de base de datos

| Motor | Módulo (`db_module`) | Paquete pip | Puerto | Placeholder de `parameters` |
|---|---|---|---|---|
| PostgreSQL | `psycopg2` | `psycopg2-binary` | 5432 | `%s` |
| Oracle | `oracledb` (thin por defecto; `oracle_driver_mode=thick` con Instant Client) | `oracledb` | 1521 | `:1`, `:2` |
| SQL Server | `pymssql` (o `pyodbc` con `odbc_driver=`) | `pymssql` | 1433 | `%s` (`?` con pyodbc) |
| MySQL | `pymysql` | `PyMySQL` | 3306 | `%s` |
| IBM DB2 | `ibm_db_dbi` (no `ibm_db`) | `ibm_db` | 50000 | `?` |
| SQLite | `sqlite3` (stdlib) | — | — | `?` |

Instala el driver: DatabaseLibrary no lo trae. Verifica con `python -c "import psycopg2"` en el mismo intérprete que corre `robot`.

## 5. Herramientas opcionales

`robocop check --target-version 7 tests resources` (lint), `robotcode analyze code` (análisis estático), `python -m robot.libdoc <Lib> list|show` (firmas). Si no están instaladas, decláralo como paso omitido; `scripts/lint_robot.py` no las requiere.
