# Evaluación de las skills QA

Evaluar una skill consiste en dar un encargo a un agente que la aplica y revisar
lo que entrega. Cada skill guarda escenarios en `evals/evals.json`: solicitudes,
archivos de entrada y resultados esperados. Los tests Node de la herramienta
comprueban su código con respuestas ficticias. No equivalen a esas evaluaciones.

La herramienta compartida, también llamada *harness*, tiene dos operaciones:
`prepare` crea una carpeta de trabajo independiente (*workspace*) con las ocho
skills, contratos y fuentes. `check` comprueba la entrega cuando el agente termina.
El script no inicia al agente: el encargo debe realizarse en otra sesión.
El host lee `resultsRoot` del contrato de la capacidad y crea
`<resultsRoot>/<runId>/` dentro del proyecto. Los reportes humanos conservan
su carpeta `reports/`; no se mezclan con los JSON contractuales.
El recibo `receipt.json` conserva los hashes de fuentes y artefactos; `evaluatedAt`
usa una fecha ISO 8601 en UTC. `check` invalida el recibo anterior antes de revisar
otra entrega para que un fallo no deje un éxito antiguo vigente.

El *oráculo* es el conjunto de expectativas usado para comprobar la entrega. Se
guarda fuera de la carpeta del agente, junto con el manifiesto del host —la lista
de trabajos esperados— y los hashes de las fuentes. Un hash identifica el contenido
de un archivo y permite detectar cambios. Separar estos archivos evita entregarlos
como parte del encargo, pero no impide técnicamente que el agente acceda a ellos.
Consulta las [definiciones del contrato común](../../../contracts/output/README.md#términos-para-leer-esta-documentación).

```powershell
node .claude/skills/ranger/scripts/evaluate.mjs prepare qa-ranger-plan-pruebas 1 <eval-root>/plan-01
# Abre otra sesión en <eval-root>/plan-01/workspace. Aplica la skill siguiendo encargo.md.
node .claude/skills/ranger/scripts/evaluate.mjs check <eval-root>/plan-01
```

`check` exige resultados reales y comprueba correlación del host, estado,
entregables solicitados, IDs declarados y conservación de las fuentes. Un resultado
sin los artefactos solicitados o con documentos fuera del encargo falla. La evaluación de razonamiento
requiere además contrastar resultados esperados, exclusiones y recomendaciones con
las fuentes: esa revisión no se deduce de un contrato válido.

Para Playwright 1, ejecutar el servidor demo local y conservar el JSON del runner,
traces y demás evidencia. Para Playwright 3, generar primero el trace con
`qa-ranger-playwright/evals/prepare_trace.py`. No sustituirlo por una conclusión del
oráculo. Para Karate 1, la ausencia de un servicio y datos válidos debe conservarse
como pendiente. El OpenAPI no acredita ejecución.

La plantilla Playwright se verifica con instalación, tipos, lint y ejecución real.
Los ejemplos de código defectuoso se verifican con sus linters. Los tests de la herramienta usan
salidas sintéticas para probar el evaluador, sin atribuirlas al desempeño de un modelo.
Registra por separado qué casos ejecutó un agente real y cuáles permanecen pendientes.
Los recibos y artefactos de cada evaluación se guardan fuera del repositorio.


## Propiedad de escenarios y herramientas

`ranger/scripts/evaluate.mjs` prepara workspaces y comprueba resultados ya
producidos. No inicia agentes. Las pruebas de esa herramienta están en
[tests/evaluations.test.mjs](../tests/evaluations.test.mjs).
`ranger/scripts/smoke-claude.mjs` es una prueba opcional con un agente real: prepara
workspaces aislados, lanza Claude Code y comprueba sus resultados con el host.
No abre navegadores ni genera carga. Se ejecuta a mano.
Cada skill es dueña de su `evals/evals.json` y entradas específicas. Los archivos de entrada
Cypress pertenecen a `ranger/evals/files/`. Los requisitos reutilizados por varias
skills también viven allí, referenciados sin duplicarlos. El workspace copia los
scripts y referencias compartidos de Ranger y el contrato común, pero excluye
los catálogos, oráculos y tests internos de cada skill. Conserva las suites bajo
`templates/**/tests/`: son código que genera la skill, no expectativas del evaluador.

Para Unitarias 1, conserva JUnit y LCOV del runner Node con las pruebas
excluidas de cobertura. Los conteos dependen de la versión de Node; el diagnóstico
debe usar el reporte observado. Unitarias 2 requiere pruebas nuevas y cobertura
verificada; Unitarias 3 conserva el bloqueo sin servicio ni runner. Unitarias 4
revisa la suite defectuosa sin reescribir las fuentes. Los cuatro escenarios
protegen sus archivos de entrada.

Para Robot Framework 1, crear la base SQLite desde `qa-ranger-robotframework/evals/files/cartera.sql`
y ejecutar la suite real: el caso de huérfanos (CA-3) debe fallar por el movimiento que referencia
la cuenta 9999; es un defecto del dato que el reporte conserva, no un test a corregir.
Robot Framework 3 se resuelve leyendo el log del release: no requiere ambiente.
Las pruebas Python de sus scripts (`tests/test_scripts.py`) no acreditan una evaluación con agente.
