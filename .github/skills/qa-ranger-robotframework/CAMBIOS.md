# qa-ranger-robotframework — notas de integración

## Qué se agregó
- Especialista `qa-ranger-robotframework` con SKILL.md, 14 recursos, scripts (`scaffold.py`, `lint_robot.py`,
  `ctrf_from_robot.py`, `rtm_from_robot.py`), plantillas (`api`, `web-browser`, `web-selenium`, `db`, `db-release`),
  contrato, ejemplos, 5 evaluaciones y pruebas.
- Ranger: selección de capacidad, detección (`.robot`/`robotframework`), playbook de aceptación de BD,
  referencias y conteos (siete especialistas / ocho skills QA). Nota en `qa-ranger-selenium` para suites
  Robot con SeleniumLibrary.

## Verificación realizada (Robot Framework 7.5, Python 3.12)
- `python -m unittest discover -s qa-ranger-robotframework/tests -p "test_*.py"`: 8/8.
- Perfiles `api` y `db` (SQLite) y `db-release` (PostgreSQL 16 + psycopg2): ejecución real con CTRF y RTM.
- Guarda `%{USER}`: con el secreto sin inyectar, la suite se detiene con mensaje explícito.
- Reintento: `REINTENTOS=1` produce `retries` en el CTRF.
- `web-browser` y `web-selenium`: lint, Robocop y `robot --dryrun` limpios; **sin ejecución con navegador**
  (el entorno de construcción no tenía navegadores). Pendiente: correrlos contra una app real.
- `tests/contracts.test.mjs`: no ejecutado; requiere `.claude/contracts/output/` (no incluido en el zip).

## Pendiente fuera de este paquete
- Registrar `qa-ranger-robotframework` en `.claude/contracts/output/validators.json` (de ahí salen las
  capacidades que copian `evaluate.mjs` y `smoke-claude.mjs`) y, si `qa-policy.json` enumera capacidades,
  también allí. Sin ese registro `validate.mjs --expected-capability-id qa-ranger-robotframework` puede rechazarlo.
- Actualizar `.claude/doc/ranger/` si documenta la lista de especialistas.
- Confirmar con DevOps los nombres/versiones de las tareas del release (RobotFramework-DBLibrary 2.*,
  AutomationUse, Publish Report) y la versión de Robot/DatabaseLibrary del agente.
