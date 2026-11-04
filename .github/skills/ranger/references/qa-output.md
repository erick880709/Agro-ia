# Contrato de salida QA: datos y validación

Este documento explica cómo la sesión entrega resultados al aplicar una skill QA.
La sesión que coordina conserva un resultado por capacidad aplicada: cuando hace
trabajo propio siguiendo Ranger, lo identifica como la skill `ranger`.
El [contrato común](../../../contracts/output/README.md#términos-para-leer-esta-documentación)
define host, agente, invocación, artefacto y normalización antes de describir sus campos.

Las ocho skills QA tienen contrato propio y comparten la
[política QA](../../../contracts/output/validators/qa/qa-policy.json). Ninguna hereda el contrato de otra skill.
Todas utilizan el [resultado común 0.1.0](../../../contracts/output/README.md).
Antes de producir un resultado, lee su
[esquema](../../../contracts/output/schemas/result.schema.json): define los campos
y estados compartidos. Los archivos `contracts/output-contract.json` definen condiciones
de aceptación y el campo obligatorio `resultsRoot`. El host lee esa carpeta relativa
al proyecto y crea `<resultsRoot>/<runId>/`; las ocho skills QA declaran
`resources/qa/contracts`. Una skill sin `resultsRoot` no se consume como contrato.
El schema común define la estructura del objeto emitido; QA añade las reglas de dominio.
Valida el resultado con el validador común:

`node <ruta-kit>/.claude/contracts/output/validate.mjs <resultado.json> --project-root <proyecto-objetivo>`

## Términos QA

- **QA:** aseguramiento de calidad. En estas skills incluye diseño, revisión, ejecución y evaluación de pruebas.
- **UI:** interfaz con la que interactúa el usuario, como una pantalla web.
- **API:** interfaz que permite a un programa solicitar datos u operaciones a otro.
- **E2E:** prueba de un flujo completo y de la integración que se declara bajo prueba.
- **Suite:** conjunto de pruebas. El **runner** es el programa que las ejecuta.
- **Runbook:** documento con los pasos, datos y resultados esperados para ejecutar casos de prueba.
- **Locator:** expresión que identifica un elemento de la interfaz para interactuar con él o comprobarlo.
- **Aserción:** comprobación de un resultado esperado. Una aserción **web-first** reintenta hasta cumplirse o agotar su tiempo límite.
- **Trace:** registro de una ejecución que permite inspeccionar acciones, estados y peticiones al diagnosticar un fallo.
- **Fixture:** datos o recursos preparados para una prueba. En Playwright también designa el mecanismo que los crea y libera.
- **Worker:** proceso que ejecuta pruebas. Varios workers permiten ejecutar pruebas en paralelo.
- **Mock:** sustituto controlado de una dependencia. Sus resultados no demuestran el funcionamiento de la dependencia real.
- **Flaky:** prueba cuyo resultado cambia entre ejecuciones sin un cambio que lo justifique.
- **RTM:** matriz de trazabilidad que vincula requisitos, criterios de aceptación, casos y resultados.
- **HU y CA:** historia de usuario y criterio de aceptación. Sus IDs deben proceder de las fuentes del encargo.
- **Línea Base:** archivo que conserva versiones, configuración, decisiones y pendientes del proyecto de pruebas entre sesiones.
- **Scaffold:** conjunto inicial de archivos generado para preparar un proyecto. Requiere configurar dependencias, entorno y datos antes de ejecutar pruebas.
- **GO / NO-GO:** recomendación sobre la entrega evaluada. Completar una revisión o un reporte no implica obtener GO.

## Aplicación

1. Comprueba las precondiciones del contrato. Registra cada una en `checks` como
   `{id, passed, evidence}`, con evidencia concreta.
2. Produce el entregable solicitado y conserva las limitaciones en `pending`, cada
   una con su responsable. Una implementación sin ejecución satisfactoria queda
   `partial` o `failed`. Un diagnóstico o reporte puede completarse aunque describa
   resultados negativos. Usa `input_required` cuando falte información del usuario.
3. Usa en `capabilityId` la skill que produce este resultado (`ranger`,
   `qa-ranger-plan-pruebas`, `qa-ranger-playwright`, `qa-ranger-karate`,
   `qa-ranger-unitarias`, `qa-ranger-selenium`, `qa-ranger-robotframework` o `qa-ranger-jmeter`).
   No escribas identidad, tiempos ni costos: el host los conoce por la ruta del archivo.
4. Guarda el JSON en el archivo que indica el encargo, dentro de la carpeta de la
   corrida (p. ej. `resources/qa/contracts/<runId>/qa-ranger-playwright-1.json`).
   Si el encargo da la carpeta pero no el nombre, usa `<capabilityId>-<n>.json` y
   continúa desde el `n` más alto de esa skill en la carpeta, así dos usos de la
   misma skill no se pisan. Sin carpeta indicada no se escribe JSON.
   Escribe un objeto conforme al esquema, sin Markdown dentro del archivo.
   El host lee ese archivo. No extrae el resultado del texto del chat.
   Omite `metrics`. Al terminar el turno, el hook `Stop` del proyecto valida el
   archivo y te devuelve los errores si los hay; también puedes ejecutar
   `validate.mjs` antes. El host conserva el `result` normalizado.
5. Revisa las `semanticPostconditions`: validar estructura y aritmética no
   demuestra que la evidencia declarada sea verdadera o el análisis correcto.

Cada invocación conserva su resultado. Los planes miden diseño. Las ejecuciones miden casos ejecutados.
Las unitarias miden su cobertura propia. No mezcles esos porcentajes.

Para un archivo local, el artefacto tiene únicamente `id`, `kind` y `path`:
`{"id": "plan", "kind": "test_plan", "path": "resources/qa/plans/test-plan-feature.md"}`.
`content` es una alternativa para texto entregado sin archivo, no un resumen
que se añada junto a `path`. Usa exactamente una ubicación por artefacto.

## Datos de cada skill

`qa-ranger-plan-pruebas` exige `data: {requirements, cases, exclusions}`.
Añade `deliverables: ["test_plan"]`, `["test_runbook"]` o ambos según el encargo.
Si se omite por compatibilidad con resultados 0.1.0 anteriores, se exigen ambos.
El host corrobora la selección con `--expected-deliverables`.

En `ranger`, `qa-ranger-playwright`, `qa-ranger-karate`, `qa-ranger-unitarias`, `qa-ranger-selenium`, `qa-ranger-robotframework` y `qa-ranger-jmeter`, `data.task` es obligatorio:
`design`, `implement`, `review`, `diagnose`, `execute` o `report`.
El resto de campos depende de la tarea:

| Campo | Uso |
|---|---|
| `design` | `{requirements, cases, exclusions}`; mismos campos y reglas que el plan |
| `coverage` y `targetOverride` | Medición unitaria y ajuste explícito de la meta; se declaran juntos |
| `coverageTargetRequired` | Booleano: alcanzar la meta unitaria forma parte del encargo |
| `expected` | Lista acordada `{id, project, priority}`; obligatoria con CTRF para implementar, ejecutar o reportar; `null` si se desconoce |
| `exitCriteria` | Criterios `{id, status, evidence}` evaluados |
| `evidencePolicy` | Política de evidencia recibida del encargo |

Los campos pueden combinarse en una misma entrega de la skill `ranger`. Se omiten cuando
no aplican. Una entrega documental puede usar `data: {task: "diagnose"}`. Los documentos conservan
las otras mediciones y conclusiones. El validador rechaza campos desconocidos.

Para un diagnóstico sin ejecutar pruebas ni disponer de reportes previos,
usa `data: {task: "diagnose"}` y guarda stack, hallazgos, riesgos y acciones en el informe
Markdown. No encontrar tests no es una medición del 0%: la cobertura es desconocida.

`data: null` permite reportar una entrega incompleta cuando aún no hay datos.
Los artefactos tienen los tipos indicados en [qa-policy.json](../../../contracts/output/validators/qa/qa-policy.json). Los documentos y copias
de evidencia locales van en `resources/qa/`. `test_code` conserva la estructura
del proyecto. El validador comprueba que los archivos existan dentro del proyecto.

### Plan

`requirements` contiene IDs únicos. Cada caso declara
`{id, requirements: [IDs], expectedResult}` y cada exclusión `{requirement, reason}`.
Para terminar, cada requisito tiene caso o exclusión justificada y existen
los documentos solicitados en `deliverables`. Las exclusiones
permanecen en el denominador de cobertura.
Si `requirements_available` no tiene `passed: true`, `data` debe ser `null` y
`artifacts` debe estar vacío: las preguntas y los temas pendientes de definición
se registran en `pending`. No se entregan planes ni runbooks sin requisitos.
El resultado no genera métricas de requisitos hasta disponer de ellos.
Ejemplos: [plan](../../qa-ranger-plan-pruebas/contracts/examples/qa-ranger-plan-pruebas-completo.json) y
[solicitud de requisitos](../../qa-ranger-plan-pruebas/contracts/examples/qa-ranger-plan-pruebas-sin-requisitos.json).

### Unitarias

`coverage` es `null` sin medición. Si existe, declara `{scope, include?, exclude?}`
y un solo artefacto `coverage_report` con `path` al archivo nativo del runner.
El validador lee LCOV, Istanbul json-summary, Cobertura XML o JaCoCo XML y calcula
los conteos y porcentajes. No transcribas métricas en el JSON contractual.
`include` y `exclude` filtran archivos de LCOV e Istanbul; para XML delimita el
alcance al generar el reporte. El alcance debe ser exclusivamente unitario.
Las métricas faltantes y los denominadores cero no acreditan la meta.
La comparación usa la razón sin redondear.

La meta predeterminada es 95% en cada métrica soportada. Solo cambia por solicitud
explícita, registrada en `targetOverride: {value, reason}`. Normalmente es `null`.
`coverageTargetRequired: true` exige acreditar esa meta para completar el encargo.
Se omite o es `false` cuando alcanzar la meta no forma parte de la entrega.
Un diagnóstico puede terminar con cobertura insuficiente o desconocida.
[Ejemplo](../contracts/examples/ranger-unitarias.json).

### Verificación de pruebas implementadas

La verificación se deriva de los casos del CTRF declarado como `test_results`.
Al menos un test pasado y cero fallos acreditan verificación satisfactoria.
Una suite vacía o solo omitida no acredita éxito. No uses `data.verification`.
Una implementación (`task: "implement"`) necesita verificación satisfactoria.
En Ranger también se exige al entregar `test_code`. Los cambios ejecutables
solicitados forman parte de una tarea `implement`. Compilar o pasar un linter
no acredita pruebas ejecutadas.

### Ejecución y reporte

Todas las skills QA entregan su corrida como CTRF (<https://ctrf.io>).
Playwright usa `playwright-ctrf-json-reporter`; otros runners usan su reporter CTRF
o convierten el reporte nativo. Conserva también el original. Declara el CTRF
como artefacto `test_results` y no transcribas casos ni conteos:

```json
{"id": "ctrf", "kind": "test_results", "path": "resources/qa/reports/<runId>/ctrf.json", "mediaType": "application/json"}
```

El validador lee del CTRF cada caso, su proyecto de navegador (`browser` o el
primer elemento de `suite` cuando no hay `browser`), estado,
reintentos y adjuntos (video, trace y screenshot). Los adjuntos deben existir en
`resources/qa/`. El ID y la prioridad salen del título (`TC-01 [critical] …`), de las
anotaciones `case` y `priority` o de los tags. Un caso sin ID o prioridad verificable
cuenta como error de la corrida. Fuera del nivel de navegador, una jerarquía
de clases en `suite` no se interpreta como proyecto: se usa `browser` explícito
o el proyecto vacío. En `data` declaras solo lo que el reporte no sabe:
`{task, expected, exitCriteria, evidencePolicy}`. `expected` es la lista acordada en el
plan (`null` si se desconoce) y `exitCriteria`, los criterios de salida evaluados.
Las métricas de la corrida quedan con fuente `machine_report`.
[Ejemplo](../../qa-ranger-playwright/contracts/examples/qa-ranger-playwright-ejecucion.json).

No declares `data.execution` ni `data.verification`: el validador los rechaza.
El CTRF aporta casos, estados, reintentos y adjuntos. Para unitarias sin IDs del plan,
el nombre del test conserva su identidad y la prioridad predeterminada es `medium`.
Los prefijos adicionales `UT-` y `PERF-` identifican unitarias y rendimiento.
No reconstruyas un CTRF a mano desde una descripción del agente.

El validador deriva ejecución, aprobación, omitidos, bloqueos y reintentos.
Un crítico faltante/omitido, corrida vacía, error global o criterio incumplido
impide `GO`. Alcance desconocido o evidencia incompleta impide un `GO` limpio.
Un reporte terminado con `NO-GO` es válido: el exit code del validador no es un
gate de release. [Ejemplo](../contracts/examples/ranger-ejecucion.json).

Contrasta los conteos con el runner y el plan.
[`generate-execution-report.mjs`](../../../contracts/output/generate-execution-report.mjs)
genera el reporte Markdown. El reporte puede listar los casos; su veredicto es
el que deriva el generador, no uno redactado aparte. El contrato referencia el
CTRF y no duplica esa lista. `validate.mjs` valida el resultado JSON.
Ambos usan las mismas reglas de `qa.mjs` y `qa-policy.json`. El reporte puede
consumir directamente `--result <resultado.json>`. Para un CTRF suelto usa
`--ctrf <ctrf.json>` con `--expected <casos.json>`, `--exit-criteria <criterios.json>`
y `--evidence-policy <politica.json>` cuando apliquen. Sin alcance previsto o
criterios acreditados no se emite un GO limpio.

## Tareas y cierre

- `design`: casos diseñados con trazabilidad. Sin ejecución, verificación ni cobertura.
  Playwright, Karate, Selenium, Robot Framework y JMeter requieren `design` y un artefacto `test_cases` o `test_plan`.
- `implement`: código y verificación satisfactoria. Playwright, Karate, Selenium, Robot Framework y JMeter requieren
  además la corrida CTRF, con alcance
  completo y evidencia por caso. Sin entorno, conserva el código y entrega
  `partial` o `failed`, indicando el pendiente.
- `review` / `diagnose`: informe de hallazgos. Pueden completar aunque encuentren
  defectos. No inventes resultados de ejecución para cerrar la revisión.
- `execute`: resultados y reporte. `completed` exige alcance conocido no vacío,
  todos los casos previstos ejecutados, sin bloqueados/omitidos ni errores globales,
  y evidencia obligatoria completa. Casos fallidos pueden dar `NO-GO` con una
  ejecución completa: el estado expresa trabajo terminado, no aprobación del release.
- `report`: evaluación de resultados existentes. Puede completar con ejecución
  incompleta o evidencia faltante, conservando las brechas y la recomendación.
  Todas las capacidades requieren el CTRF (`test_results`) y un `report`.

## Política de evidencia y delegación

La política se resuelve antes de ejecutar, también sin carpeta de resultados.
El encargo explícito prevalece sobre los valores compartidos. Las plantillas
se adaptan a esa decisión y nunca reducen la retención por estar en CI.

Si una guía o ejemplo recomienda conservar menos evidencias, aplica la política
resuelta. Esa recomendación no autoriza una excepción al encargo. Antes de
ejecutar, comprueba que la configuración de la suite conserva las evidencias
exigidas también para los casos exitosos.

`data.evidencePolicy` contiene:

```json
{"level": "browser", "required": ["video", "trace", "screenshot"], "override": null}
```

Los valores predeterminados de [qa-policy.json](../../../contracts/output/validators/qa/qa-policy.json) exigen video,
trace y screenshot por caso de navegador, incluidos los exitosos. Para API y
unitarias exigen `raw_results`. No se exige video. `required` puede añadir
`log` u otros tipos admitidos. Si se reduce el conjunto predeterminado,
`override: {"reason": "instrucción explícita del encargo"}` es obligatorio.
No inventes la excepción. Para suites mixtas separa resultados por nivel de
prueba e invocación, conservando sus IDs y fuentes originales.

`cases[].evidence` referencia artefactos del tipo solicitado, no cualquier
informe. Los videos, traces y screenshots se entregan como `path` o `uri`,
nunca como texto inline. La métrica `qa.casesMissingEvidence` cuenta casos
con tipos faltantes. `qa.evidenceMissing.<n>` indica caso/proyecto y tipos que
faltan. Se deriva comparando lo solicitado con los artefactos capturados.
Validar referencias no demuestra que un archivo sea una captura auténtica.

El agente coordinador pasa a cada skill:
- Objetivo, alcance, tarea, fuentes e IDs de requisitos y casos.
- El archivo de resultado asignado por el host y la política de evidencia resuelta, si aplican.

Cada skill emite su `<capabilityId>-<n>.json` en la misma carpeta. Ranger no
reescribe el resultado de Playwright o Karate como propio. En uso directo,
la skill resuelve la política con el encargo y los valores compartidos.
El host puede corroborarla usando `--expected-evidence-policy <politica.json>`:
el archivo contiene el objeto `evidencePolicy` que pasó a la skill. Esto exige
la misma política cuando hay ejecución y evita aceptar una reducción unilateral.
`--expected-task execute` corrobora también la tarea encargada para impedir
que se cierre cambiándola por un reporte. Una entrega incompleta sin datos de
corrida puede validarse sin inventar ejecución. Conserva los pendientes.

Ejemplos ficticios:
[Playwright: diseño](../../qa-ranger-playwright/contracts/examples/qa-ranger-playwright-diseno.json),
[Playwright: ejecución](../../qa-ranger-playwright/contracts/examples/qa-ranger-playwright-ejecucion.json),
[Karate: revisión](../../qa-ranger-karate/contracts/examples/qa-ranger-karate-revision.json),
[Karate: implementación pendiente](../../qa-ranger-karate/contracts/examples/qa-ranger-karate-sin-ejecucion.json),
[Selenium: ejecución](../../qa-ranger-selenium/contracts/examples/qa-ranger-selenium-ejecucion.json),
[Selenium: sin entorno](../../qa-ranger-selenium/contracts/examples/qa-ranger-selenium-sin-entorno.json),
[Robot Framework: ejecución](../../qa-ranger-robotframework/contracts/examples/qa-ranger-robotframework-ejecucion.json),
[Robot Framework: sin entorno](../../qa-ranger-robotframework/contracts/examples/qa-ranger-robotframework-sin-entorno.json),
[JMeter: ejecución](../../qa-ranger-jmeter/contracts/examples/qa-ranger-jmeter-ejecucion.json),
[JMeter: sin entorno](../../qa-ranger-jmeter/contracts/examples/qa-ranger-jmeter-sin-entorno.json).

## Correlación del host

Para comprobar la entrega completa de una corrida, usa
`validate-run.mjs <carpeta-resultados> --manifest <encargo-host.json> --project-root <proyecto>`.
El manifiesto vive fuera de la carpeta contractual y contiene `invocations`,
una lista de objetos `{invocationId, capabilityId, task, resultFile}`. Puede añadir
`evidencePolicy`, `deliverables` y `expected` (lista de casos con ID, proyecto y prioridad).
Si fija `expected`, el resultado debe conservar exactamente ese alcance y sus prioridades.
`validateResult` recibe esa lista como `expectedScope`; la CLI usa `--expected-scope <casos.json>`. `resultFile` es el nombre de archivo que el host
asigna y le indica al agente; así la identidad no depende de que el modelo copie IDs.
El host registra una invocación antes de iniciarla, también cuando repite una skill.
La carpeta contractual contiene solo los JSON de salida. Guarda reportes del runner
en otra subcarpeta. El validador rechaza resultados ausentes o no asignados.
La integración de esta interfaz con PAP sigue pendiente.

## Identidad y evidencia de Playwright

Usa títulos `TC-01 [critical] [HU-123][CA-2] <comportamiento>`: `TC` identifica
el caso, HU/CA su trazabilidad y la prioridad su riesgo. También se admiten
anotaciones `case`, `priority` y `req` (el reporter las conserva con `annotations: true`).
No inventes IDs de requisitos. La plantilla de Playwright organiza los adjuntos en
`resources/qa/<CASE-ID>/<runId>/<proyecto>/attempt-<n>/`, conservando los originales
en `resources/qa/test-results/<runId>/`, y el CTRF en `resources/qa/reports/<runId>/ctrf.json`.
El CTRF trae los adjuntos del último intento y los previos con nombres
`attempt-<n>/<adjunto>`; `retries`
cuenta los intentos previos. La lista ejecutada no demuestra por sí sola que el
alcance esté completo: compárala con `expected`, la lista acordada en el plan.

## Integración con hosts

Un host Node puede importar el validador sin lanzar procesos. Las funciones son
asíncronas y devuelven el mismo JSON que la CLI; una entrega inválida lanza
`ContractError`. Los errores de lectura de archivos también se propagan.

```js
import { validateRun } from './.claude/contracts/output/validate-run.mjs';
import { readFile } from 'node:fs/promises';
import { resolveResultsFolder } from './.claude/contracts/output/results-root.mjs';

const runId = 'corrida-01';
const manifest = JSON.parse(await readFile('host-manifest.json', 'utf8'));
const capability = manifest.invocations[0].capabilityId;
const contract = JSON.parse(await readFile(`.claude/skills/${capability}/contracts/output-contract.json`, 'utf8'));
const folder = resolveResultsFolder(contract, runId, process.cwd());
const outcome = await validateRun(folder, manifest, process.cwd());
// outcome.results: [{invocationId, resultFile, result}], un resultado normalizado por invocación.
```

La ruta de importación se resuelve desde el archivo del host. También se exporta
`validateResult(json, {projectRoot, expectedCapabilityId, expectedTask,
expectedEvidencePolicy, expectedDeliverables, expectedScope})`
desde `validate.mjs`. `projectRoot` identifica el proyecto y sus artefactos.
