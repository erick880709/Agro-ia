# Stage "Acceptance Test" del release — __NOMBRE__

Configuración del release clásico en Azure DevOps (pool de agentes Linux de automatización) para ejecutar
`acceptance_test/test_cases` con Robot Framework. Basado en el estándar interno de pruebas de aceptación de
bases de datos; confirma los nombres de las tareas y sus versiones en tu organización antes de copiarlos.

## 1. Variables del pipeline (scope: Release o el stage)

| Nombre | Secreto | Cómo la lee Robot |
|---|---|---|
| `DB` | Sí | `%{DB}` |
| `HOST` | Sí | `%{HOST}` |
| `PORT` | No | `%{PORT}` (__DB_PORT__ por defecto para __DB_MODULE__) |
| `USER` | Sí | `%{USER}` |
| `PASSWORD` | Sí | `%{PASSWORD}` |

- En Linux los nombres son sensibles a mayúsculas y Azure DevOps expone las variables en MAYÚSCULA
  (`keyPath` → `%{KEYPATH}`, `ma_db_user` → `%{MA_DB_USER}`). Escribe siempre la forma en mayúscula en el `.resource`.
- `USER` y `HOST` también existen en el sistema del agente. Si el secreto no llega al proceso, `%{USER}`
  devuelve el usuario del agente y la conexión falla por autenticación, no por variable faltante. La keyword
  `Verificar Variables De Entorno` detiene la suite con un mensaje explícito en ese caso.
- Los valores nunca van en el repositorio, en los `.robot` ni en el log (`DatabaseLibrary` registra las filas
  consultadas: en ambientes con datos reales usa `log_query_results=False`).

## 2. Tareas del Agent job (en este orden)

1. **RobotFramework-DBLibrary** — versión `2.*`, que permite manejar las variables de conexión ocultas.
   - Test Cases Path: `$(System.DefaultWorkingDirectory)/_<ARTEFACTO>/acceptance_test/test_cases`
2. **AutomationUse** — Testing Framework: `Robot Framework`.
   - Path of main folder: `$(System.DefaultWorkingDirectory)/_<ARTEFACTO>/acceptance_test/test_cases`
   - Test Result folder path: `$(System.DefaultWorkingDirectory)/_<ARTEFACTO>/acceptance_test`
   - Repository name: el del repositorio (p. ej. `AW0000000_NOMBRE`)
   - AWS Credentials: la conexión de servicio que define tu equipo.
3. **Publish Report** (Publish HTML Report) — publica `report.html`/`log.html`.

`<ARTEFACTO>` es el alias del artefacto del build que contiene la carpeta `acceptance_test`.

## 3. Antes del primer release

- [ ] `python tools/lint_robot.py acceptance_test --rf 5` sin bloqueantes.
- [ ] Ejecución local con `./ejecutar.sh` y `.env.qa` contra un ambiente de pruebas.
- [ ] Revisar en el log de la tarea la versión de Robot Framework y de DatabaseLibrary del agente y
      registrarla en la Línea Base: decide si se puede usar `VAR`, `RETURN`, `Check Row Count`, etc.
- [ ] Confirmar que el usuario de BD del pipeline es de **solo lectura** o que las pruebas solo leen.

## 4. Errores frecuentes

| Síntoma en el log | Causa probable | Acción |
|---|---|---|
| `Variable '%{DB}' not found` | Nombre en minúscula o variable sin scope en el stage | Nombre en MAYÚSCULA y scope correcto |
| `password authentication failed for user "<usuario-del-agente>"` | `%{USER}` tomó el usuario del sistema | Verificar que la tarea 2.* inyecte el secreto |
| `No module named 'psycopg2'` (u otro driver) | El runtime del agente no trae el driver | Solicitar el driver o cambiar de tarea/versión |
| `No keyword with name 'Check Row Count'` | DatabaseLibrary 1.x en el agente | Usar `Query` + `Should Be Equal…` (como esta plantilla) |
| `[Return]` / `Run Keyword If` deprecated | Sintaxis heredada | `RETURN` / `IF` según la versión de RF del agente |
