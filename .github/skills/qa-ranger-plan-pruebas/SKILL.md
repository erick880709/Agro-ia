---
name: qa-ranger-plan-pruebas
metadata:
  display-name: "Planificador de pruebas"
  capability: "Plan de pruebas"
  capability-summary: "Crea el plan de pruebas y la guía de ejecución a partir de requisitos."
description: 'Crea un plan de pruebas y su runbook a partir de requisitos, alcance y riesgos: casos, resultados esperados, criterios de salida y exclusiones justificadas. Ranger la usa para el plan dentro de un trabajo QA más amplio. Invócala directamente cuando el pedido sea solo el plan o el runbook.'
---

# Crear el Plan de Pruebas

Usa el contexto y la estrategia que la sesión coordinadora ya identificó. En uso
directo, lee las fuentes y el alcance del encargo.


Consulta los [términos QA](../ranger/references/qa-output.md#términos-qa) para interpretar runbook, runner, fixture, trace y otros términos de estas instrucciones.

## Dependencia compartida

Distribuye esta skill junto con `ranger`: allí viven las herramientas QA compartidas.
Esta skill mantiene su propio `contracts/output-contract.json`, sus recursos
específicos y sus escenarios en `evals/`. La política QA y la validación de resultados
viven en `.claude/contracts/output/`, que también se requiere para preparar
workspaces de evaluación.

## Tablero de trabajo (uso directo)

Si esta skill se invoca directamente (no a través de Ranger), aplica antes de empezar la
[pregunta del tablero](../ranger/references/tablero_de_trabajo_mcp.md#2-la-pregunta-inicial):
una sola vez, opcional y no bloqueante (si el usuario no tiene tablero, empieza el trabajo). Con
tablero conectado, lee las HU/planes del alcance y, al terminar, comenta y actualiza el estado según
la [guía de cierre](../ranger/references/tablero_de_trabajo_mcp.md#5-actualizar-el-tablero-al-terminar).
Cuando la coordina Ranger, no escribas en el tablero: Ranger hace la actualización consolidada.

## Antes de diseñar

El resultado JSON aplica solo cuando el encargo indica una carpeta de resultados.
Sin ella, omite el JSON y lo que esta skill dice sobre él. Entrega los documentos
solicitados, o las preguntas pendientes en la respuesta.

Con carpeta, lee el [esquema del resultado](../../contracts/output/schemas/result.schema.json),
las [reglas de salida QA](../ranger/references/qa-output.md) y
el [contrato del plan](contracts/output-contract.json). `contracts/output-contract.json` define
condiciones de aceptación. Los campos del resultado los define el esquema.

Comprueba si las fuentes permiten definir resultados esperados verificables.
Si faltan requisitos o criterios de aceptación, detén el diseño: entrega
`status: "input_required"`, `data: null` y `artifacts: []`. Registra las preguntas
y su responsable en `pending`, siguiendo el
[ejemplo sin requisitos](contracts/examples/qa-ranger-plan-pruebas-sin-requisitos.json).
En ese estado no cargues las plantillas ni crees un plan o runbook con supuestos.
Guarda únicamente el resultado JSON (o, sin carpeta, responde con las preguntas)
y termina. Las preguntas no necesitan un documento de análisis adicional.

Con requisitos disponibles, consulta la
[guía de análisis](../ranger/references/requirements_analysis_guide.md).
Una pregunta o un ejemplo de las guías no es un requisito del proyecto:
no asignes resultados esperados a reglas de negocio sin confirmar.

## Procedimiento

1. Identifica si se pidió plan, runbook o ambos.
   Produce únicamente los documentos solicitados.
   Registra esa selección en `data.deliverables` cuando haya JSON.
   Define qué features, páginas y flujos críticos quedan dentro y fuera del alcance.
2. Define tipos y prioridades de prueba (smoke, regresión, exploratoria).
3. Define escenarios con precondiciones, pasos, resultados esperados y etiquetas de riesgo.
   Incluye límites y combinaciones que cambien el comportamiento. La matriz
   del plan identifica cada caso y requisito con los mismos IDs que el runbook
   y el resultado JSON.
4. Define estrategia de datos (usuarios de prueba por rol, fixtures,
   entornos, estrategia de reseteo) — las credenciales siempre vía
   variables de entorno, nunca en texto plano.
5. Define criterios de entrada y salida (cobertura, tasa de aprobación, política de bloqueantes).
   Respeta las metas del encargo. No introduzcas umbrales alternativos sin acuerdo.
6. Define requisitos de evidencia (screenshots, trace, video, logs) — ver
   la [política QA compartida](../../contracts/output/validators/qa/qa-policy.json): evidencia
   completa por caso de navegador, resultados del runner para API y unitarias.
   Documenta las excepciones explícitas del encargo y pásalas a quien ejecute.
7. Si se pidió plan, prodúcelo como un archivo Markdown real en
   `resources/qa/plans/test-plan-<feature>.md` (creando la carpeta si no
   existe) usando `templates/test_plan_template.md`, no solo como un
   resumen en el chat.

Adapta las plantillas al nivel de pruebas solicitado. Para unitarias, usa datos
en memoria, assertions y reportes del runner. Navegador, cuentas y video solo
aplican si el encargo los requiere. Comprueba qué comandos y dependencias
existen, y distingue la preparación pendiente de una configuración disponible.
Identifica al autor con el nombre del agente que atiende el encargo.

Referencia: `../ranger/references/testing_strategies.md`, `templates/test_plan_template.md`

## Flujo de Plantilla

Usar `templates/test_plan_template.md` directamente — ya cubre objetivo,
matriz funcional, riesgos, estrategia de datos/entorno (variables de
entorno, nunca secretos literales), estrategia de ejecución, requisitos de
evidencia y criterios de entrada/salida.

Salidas según el encargo (todas dentro de `resources/qa/`, creando las carpetas que falten):
- `resources/qa/plans/test-plan-<feature>.md` — documento de plan de pruebas (Markdown, a partir de la plantilla).
- `resources/qa/runbooks/qa-runbook-<feature>.md` — checklist de escenarios para ejecución (runbook en Markdown, `../ranger/references/markdown_test_runbook.md`).
- Registro de defectos con severidad y reproducibilidad (dentro del mismo runbook o del reporte de ejecución).

## Contrato de Salida

Usa el [ejemplo de plan](contracts/examples/qa-ranger-plan-pruebas-completo.json) como
referencia de estructura, reemplazando sus datos por los del encargo.
`deliverables` declara `["test_plan"]`, `["test_runbook"]` o ambos.
`requirements` contiene IDs. Cada caso contiene únicamente
`id`, `requirements` y `expectedResult`. Los detalles de ejecución van en el runbook.

Antes de entregar, compara el JSON con los archivos que referencia: mismos
casos, resultados esperados y rutas existentes. Al corregir un documento,
comprueba el archivo completo para retirar contenido que ya no corresponde.
El resultado describe diseño de pruebas. No acredita ejecución ni cobertura de código.

El resultado lo entrega esta skill: `capabilityId: "qa-ranger-plan-pruebas"`, en el
archivo de resultados que indique el encargo, según las reglas de salida QA. Omite `metrics`: las calcula el validador. No presentes como verificado un
resultado que no haya pasado por él.

## Evaluación

[evals/evals.json](evals/evals.json) cubre alcance, requisitos faltantes y
trazabilidad. Usa el [harness QA](../ranger/references/evaluations.md) para
contrastar entregables reales con el encargo y sus fuentes.

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "qa-ranger-plan-pruebas", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill qa-ranger-plan-pruebas --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
