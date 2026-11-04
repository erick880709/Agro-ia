# 03 — Arquitectura de suite

## 1. Estructura

```
proyecto/
├── requirements.txt            # versiones exactas
├── ejecutar.sh                 # lint -> dry run -> robot -> CTRF + RTM
├── variables/qa.py, stg.py     # datos no secretos por ambiente (Python: sin PyYAML)
├── resources/
│   ├── common.resource         # imports compartidos, evidencia, guardas
│   ├── db.resource | api.resource | web.resource
│   └── pages/<pantalla>.resource   # page objects (web)
├── libraries/QaEvidencia.py    # librerías Python propias
├── tests/<dominio>/<suite>.robot   (+ __init__.robot por carpeta)
├── tools/                      # lint, CTRF, RTM copiados de la skill
└── resources/qa/               # evidencia y reportes (ignorado; se publica como artefacto)
```

Release de base de datos (perfil `db-release`): `acceptance_test/test_cases/*.robot`, `acceptance_test/resources/connection_database.resource`, `acceptance_test/libraries/` — la ruta que esperan las tareas del stage (08).

## 2. Resources

- Solo keywords y variables; en Settings únicamente imports, `Documentation` y `Keyword Tags`.
- Uno por dominio o pantalla; `common.resource` con lo transversal. Importa con rutas relativas al archivo que importa.
- Una keyword de usuario expresa una intención de negocio ("La Cuenta Queda Bloqueada"), no un clic.
- Mismo nombre en dos resources ⇒ "Multiple keywords with name"; renombra o califica (`db.Conectar`).

## 3. `__init__.robot`

Settings de la carpeta: `Suite Setup`/`Teardown`, `Test Tags`, `Documentation`. Sus keywords **no** son visibles en las suites hijas, y un `Test Setup` definido allí se resuelve en cada hija (cada una importa el resource que lo define). Ejecutar un archivo hijo directamente omite el `__init__.robot`: usa `--suite`/`--include` desde la raíz.

## 4. Nombres, IDs y tags

- Test: `TC-01 [critical] [HU-123][CA-2] comportamiento observable`. Prefijos reconocidos por el contrato: `TC-`, `SEC-`, `FRAUD-`, `API-`, `A11Y-`, `UT-`, `PERF-` (BD usa `TC-` + tag `database`). Prioridad: `critical|high|medium|low`.
- Repite el ID como tag (`[Tags]    TC-01`): `--test "TC-01 [critical]*"` falla porque `[...]` es un comodín de clase de caracteres; `--include TC-01` funciona.
- No renumeres IDs con historial de ejecución.
- Tags de suite: `smoke`, `regresion`, nivel (`database`, `api`, `web`) y dominio. Reservados: solo los `robot:` documentados (`robot:skip`, `robot:exclude`, `robot:skip-on-failure`, `robot:continue-on-failure`, `robot:stop-on-failure`, `robot:private`, `robot:no-dry-run`).

## 5. Datos y ambientes

- `variables/<env>.py` con URL base, módulos de BD, timeouts y datos sintéticos de referencia; selección con `--variablefile variables/qa.py`.
- Secretos solo por entorno (`%{VAR}`), con `.env.qa` local ignorado por git y secretos del pipeline en CI.
- Datos por test: crea lo que el caso necesita y límpialo por ID; no dependas del orden ni de lo que dejó otro test.
