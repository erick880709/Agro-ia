---
name: qa-ranger-unitarias
metadata:
  display-name: "Especialista en pruebas unitarias"
  capability: "Pruebas unitarias"
  capability-summary: "Crea y ejecuta pruebas unitarias y entrega un informe de cobertura del código."
description: 'Diseña, implementa, revisa, ejecuta y diagnostica pruebas unitarias con el runner del stack y mide su cobertura contra la meta QA del 95%. Usa esta skill cuando el encargo sea de nivel unitario: escribir o mejorar unitarias, medir o subir cobertura, o revisar una suite unitaria. Los pedidos QA genéricos pasan por Ranger para elegir nivel y herramienta.'
---

# QA Ranger — Unitarias

Skill para diseñar, escribir, revisar, ejecutar y diagnosticar pruebas **unitarias**
con el runner que ya usa el proyecto, y para medir su cobertura con evidencia real.
Produce código ejecutable, no pseudocódigo: pruebas, configuración de cobertura y
el comando exacto para correrlas.

## Dependencia compartida

Distribuye esta skill junto con `ranger`: allí viven las herramientas QA compartidas.
Esta skill mantiene su propio `contracts/output-contract.json`, sus recursos
específicos y sus escenarios en `evals/`. La política QA y la validación de resultados
viven en `.claude/contracts/output/`, que también se requiere para preparar
workspaces de evaluación.

## Contrato y política QA compartida

Antes de trabajar, lee las [reglas QA](../ranger/references/qa-output.md) y
la [política compartida](../../contracts/output/validators/qa/qa-policy.json).
Conserva objetivo, alcance, tarea, fuentes, IDs y política recibidos de Ranger.
En uso directo resuelve la política desde el encargo y los valores compartidos.
Para unitarias la evidencia obligatoria son los resultados del runner (`raw_results`).
Una reducción requiere instrucción explícita, registrada en `evidencePolicy.override`.

Cuando el encargo indica carpeta de resultados, lee el
[esquema común](../../contracts/output/schemas/result.schema.json) y
[tu contrato](contracts/output-contract.json); emite tu propio
`qa-ranger-unitarias-<n>.json`, con `capabilityId: "qa-ranger-unitarias"`,
en el archivo que indique el host. Sin carpeta, entrega artefactos
y respuesta sin JSON, manteniendo las mismas reglas de evidencia y cierre.
Los documentos, reportes del runner y de cobertura van bajo `resources/qa/`;
el código de pruebas conserva la estructura del proyecto.

Distingue `data.task`: diseño, implementación, revisión, diagnóstico, ejecución
o reporte, según las [reglas de cierre](../ranger/references/qa-output.md#tareas-y-cierre).
Diseñar casos no acredita ejecución ni cobertura. Una implementación sin ejecución
verificada o sin evidencia obligatoria queda `partial` o `failed`. Una revisión
terminada puede encontrar defectos y un diagnóstico puede terminar con cobertura
insuficiente o desconocida.
Omite `metrics`, valida el archivo con `validate.mjs` y contrasta sus referencias
con los archivos y los resultados originales. Consulta los ejemplos en `contracts/examples/`.

## Tablero de trabajo (uso directo)

Si esta skill se invoca directamente (no a través de Ranger), aplica antes de empezar la
[pregunta del tablero](../ranger/references/tablero_de_trabajo_mcp.md#2-la-pregunta-inicial):
una sola vez, opcional y no bloqueante (si el usuario no tiene tablero, empieza el trabajo). Con
tablero conectado, lee las HU/planes del alcance y, al terminar, comenta y actualiza el estado según
la [guía de cierre](../ranger/references/tablero_de_trabajo_mcp.md#5-actualizar-el-tablero-al-terminar).
Cuando la coordina Ranger, no escribas en el tablero: Ranger hace la actualización consolidada.

## Paso 0 — Identificar el runner y la cobertura (obligatorio)

Las unitarias **mantienen el runner del stack**. Antes de escribir una línea,
identifica cuál usa el proyecto y cómo mide cobertura:

| Señal | Runner | Cobertura |
|---|---|---|
| `vitest` en `package.json`, `vitest.config.*` | Vitest | `@vitest/coverage-v8` o `-istanbul` |
| `jest` en `package.json`, `jest.config.*` | Jest | `--coverage` (Istanbul) |
| `node:test` en las pruebas, sin otro runner | Node.js test runner | `--experimental-test-coverage` |
| `pytest.ini`, `[tool.pytest]`, `conftest.py` | pytest | `pytest-cov` / coverage.py con `--branch` |
| `junit-jupiter` en `pom.xml`/`build.gradle` | JUnit 5 | JaCoCo |
| `*.Tests.csproj` con xunit/nunit/mstest | xUnit/NUnit/MSTest | coverlet (Cobertura) |

Si hay varios runners, resuelve cuál corresponde al alcance solicitado. En un proyecto
sin runner, propone el nativo del stack y confirma antes de instalarlo. No migres
de runner ni impongas uno por palabras genéricas del encargo.
Para comandos, formatos de reporte y métricas soportadas lee
[runners y cobertura](references/01-runners-y-cobertura.md).

Si existe `resources/qa/project-context.md` (Paso 0.4 de Ranger), léelo y actualiza
solo la parte del runner y la cobertura que hayas verificado.

## Flujo de trabajo

Identifica el tipo de tarea y lee **solo** los recursos que necesita.

| Tarea | Recursos a leer |
|---|---|
| Diseñar casos unitarios desde requisitos o HU | 02 |
| Escribir o completar pruebas unitarias | 01, 02 |
| Medir cobertura o diagnosticar huecos | 01, luego `scripts/unit_report.py coverage` |
| Subir cobertura hasta la meta | 01, 02, 03 |
| Revisar una suite unitaria existente | 03 |
| Registrar la verificación de una corrida | 01, luego `scripts/unit_report.py junit` |

### Al escribir pruebas

1. **Entiende el comportamiento antes que el código.** Reglas, entradas válidas e
   inválidas, errores esperados y límites. Si falta una regla de negocio, pregúntala;
   no la deduzcas de la implementación.
2. **Diseña los casos** con partición de equivalencia, valores límite y caminos de
   error ([diseño de casos](references/02-diseno-de-casos.md)). Cubre siempre el camino
   feliz, cada rechazo y cada límite que cambia el resultado.
3. **Identifica cada caso** con su ID y prioridad en el nombre de la prueba,
   `UT-01 [high] [RF-02] <comportamiento>`, y añade HU/CA/RF solo cuando existan en la fuente.
4. **Aísla la unidad:** sin red, base de datos ni reloj real. Usa dobles de prueba
   solo para dependencias externas a la unidad; nunca simules la unidad que afirmas verificar.
5. **No toques el código bajo prueba** para subir la cobertura, salvo que el encargo
   lo pida. Si una rama es inalcanzable o un defecto impide probarla, regístralo.
6. **Ejecuta y mide**: corre el runner con cobertura y reporter CTRF, o convierte
   su JUnit XML a CTRF. Conserva ambos reportes en `resources/qa/unit/<runId>/`.
   Declara el CTRF como `test_results` y la cobertura nativa como `coverage_report`.
   Usa `coverage: {scope: "<unidad>"}` y `targetOverride: null`; el validador calcula
   los conteos. Declara `expected` con los casos acordados, o `null` si se desconoce,
   y `evidencePolicy` de nivel `unit`. No transcribas ejecución ni verificación.
   Excluye los archivos de prueba de la medición. Itera sobre los huecos hasta la
   meta o hasta documentar por qué no se alcanza.

### Al medir la cobertura

- La meta es 95% en **cada** métrica que el runner soporta (`unitCoverage` de la
  política). Solo cambia por solicitud explícita, en `targetOverride: {value, reason}`.
- El validador identifica las métricas en el reporte nativo; el resto queda `null`.
  Un denominador cero o una métrica faltante no acredita la meta.
- `coverageTargetRequired: true` cuando alcanzar la meta forma parte del encargo.
- La cobertura unitaria no incluye integración ni E2E. Si el proyecto mezcla niveles
  en un solo reporte, sepáralos o declara la medición como no unitaria.
- No encontrar pruebas no es 0%: la cobertura es desconocida (`coverage: null`).

### Al revisar pruebas existentes

Ejecuta la suite si el entorno lo permite y revisa contra el
[checklist de revisión](references/03-revision-y-antipatrones.md). Entrega hallazgos
priorizados (Bloqueante / Mayor / Menor) con la corrección concreta de cada uno.
Una revisión no implementa los cambios salvo que el encargo lo pida.

## Formato de entrega

- Árbol de archivos primero (cuando son 3+ archivos), luego cada archivo completo.
- Nombres de prueba y comentarios en español salvo convención del equipo.
- Comando exacto para ejecutar las pruebas con cobertura.
- Tabla final por métrica: cubierto/total, porcentaje y si alcanza la meta.

## Reglas de exactitud

- No inventes opciones de runners ni de herramientas de cobertura. Si no estás seguro
  de que una opción exista en la versión del proyecto, verifícala con `--help` o su documentación.
- Conserva los archivos nativos del runner; no transcribas conteos desde la consola.
- Una suite vacía, solo omitida o que solo compila no acredita verificación.

## Recursos

- `references/01-runners-y-cobertura.md` — comandos por runner, formatos de reporte, métricas soportadas y exclusiones.
- `references/02-diseno-de-casos.md` — técnicas de diseño, dobles de prueba, determinismo y trazabilidad.
- `references/03-revision-y-antipatrones.md` — checklist de revisión y antipatrones con su corrección.
- [references/04-patrones-javascript.md](references/04-patrones-javascript.md) — factories, Jest/RTL, MSW, asincronía y snapshots.
- [references/05-buenas-practicas-javascript.md](references/05-buenas-practicas-javascript.md) — testeabilidad, aislamiento, mantenimiento y depuración.
- [references/06-ejemplos-y-organizacion.md](references/06-ejemplos-y-organizacion.md) — ejemplos React y organización/configuración de cobertura.
- [references/07-accesibilidad-componentes.md](references/07-accesibilidad-componentes.md) — jest-axe y RTL para componentes aislados.
- `scripts/unit_report.py` — utilidad Python de análisis para uso independiente; sus bloques antiguos no son datos del contrato vigente.
- `../../contracts/output/validators/qa/coverage.mjs` — lee cobertura nativa para el contrato en Node.

## Evaluación

Los casos están en [evals/evals.json](evals/evals.json). El
[harness QA](../ranger/references/evaluations.md) separa el encargo y los
fixtures de los oráculos, y distingue comprobación automática de evaluación con agente.

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "qa-ranger-unitarias", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill qa-ranger-unitarias --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
