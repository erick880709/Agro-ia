# 09 — Ejecución, paralelismo y reintentos

## 1. Comandos

```bash
python -m robot --outputdir resources/qa/test-results/$QA_RUN_ID --xunit xunit.xml \
    --variablefile variables/qa.py tests                     # suite completa
python -m robot --include smoke tests                         # por tag
python -m robot --include "database AND smoke" --exclude wip tests
python -m robot --include TC-03 tests                         # un caso (por su tag de ID)
python -m robot --suite aceptacion tests                      # una suite con sus __init__.robot
python -m robot --dryrun --output NONE --report NONE --log NONE tests
```

- Operadores de tags en mayúscula y entre comillas: `"smoke NOT lento"`; en minúscula forman parte del nombre del tag.
- `--test` acepta comodines: `*`, `?` y `[...]`; por eso se selecciona por tag de ID y no por el nombre con `[critical]`.
- Ejecuta desde la raíz para que apliquen los `__init__.robot`.
- Código de salida = número de tests fallidos (máx. 250); 251 ayuda, 252 datos inválidos, 253 interrumpido. `0` no significa que hubo tests: valida el alcance en el CTRF.

## 2. Orden de ejecución

Smoke y `critical` primero (`--include smoke`), regresión después. Un fallo de `Suite Setup` marca todos los tests de la suite como fallidos sin ejecutarlos: es un error global de la corrida, no N defectos.

## 3. Paralelismo con pabot

```bash
pabot --processes 4 --outputdir resources/qa/test-results/$QA_RUN_ID tests            # por suite
pabot --testlevelsplit --processes 4 ...                                            # por test
```

Requisitos: tests independientes, datos únicos por test, sin `scope=GLOBAL` compartido, contexto/navegador por test. Recursos compartidos (una cuenta, una fila) con `pabot`'s `--resourcefile`/`Acquire Lock` de PabotLib. No paralelices contra una BD compartida con casos que escriben sin coordinar datos.

## 4. Reintentos visibles

```bash
python -m robot --outputdir $OUT tests || \
QA_ATTEMPT=1 python -m robot --rerunfailed $OUT/output.xml --output rerun1.xml --outputdir $OUT tests
rebot --merge --outputdir $OUT --output merged.xml $OUT/output.xml $OUT/rerun1.xml   # reporte combinado
python tools/ctrf_from_robot.py --output $OUT/output.xml --output $OUT/rerun1.xml --out <ctrf>
```

El CTRF conserva `retries` y marca `flaky` si pasó al reintentar: un reintento no oculta inestabilidad. `--rerunfailed` falla si no hubo fallidos. `--skiponfailure flaky` convierte en *skip* los fallos de tests etiquetados: úsalo solo con ticket de causa raíz, porque un skip de un crítico impide `GO`.

## 5. Variables de la corrida

`QA_RUN_ID` (nuevo por ejecución), `QA_ROOT` (`resources/qa`), `QA_ATTEMPT` (0, 1…) los usa `QaEvidencia` para la carpeta `test-results/<runId>/<CASE-ID>/attempt-<n>/`. En CI usa el ID del build (`run-$(Build.BuildId)-$(System.JobAttempt)`).
