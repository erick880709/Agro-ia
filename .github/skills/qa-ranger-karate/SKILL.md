---
name: qa-ranger-karate
metadata:
  display-name: "Especialista en pruebas de API (Karate)"
  capability: "Pruebas con Karate"
  capability-summary: "Crea y ejecuta pruebas de servicios y aceptación con Karate, con resultados verificables."
description: 'Diseña, implementa, revisa, ejecuta y migra suites Karate de API y aceptación. Usa esta skill cuando el encargo o el proyecto seleccionan Karate; determina primero versión de Karate, Java y build tool. Los pedidos QA genéricos pasan por Ranger para elegir la herramienta.'
---

# QA Ranger — Karate

Skill para diseñar, escribir, revisar, ejecutar y migrar suites de pruebas con **Karate** (Karate Labs). Produce código ejecutable, no pseudocódigo: features, `karate-config.js`, runners, mocks, simulaciones y pipelines listos para correr.


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
Para navegador conserva video, trace y screenshot de cada caso, también en CI;
para API conserva resultados del runner. En UI Karate, consulta
[los límites y la integración de evidencia](references/13-evidencia-ui.md)
antes de comprometer una ejecución completa. Una reducción requiere instrucción
explícita, registrada en `evidencePolicy.override`.

Cuando el encargo indica carpeta de resultados, lee el
[esquema común](../../contracts/output/schemas/result.schema.json) y
[tu contrato](contracts/output-contract.json); emite tu propio
`qa-ranger-karate-<n>.json`, con `capabilityId: "qa-ranger-karate"`,
en el archivo que indique el host. Sin carpeta, entrega artefactos
y respuesta sin JSON, manteniendo las mismas reglas de evidencia y cierre.
Los documentos y evidencia van bajo `resources/qa/`; el código conserva la
estructura de la suite. La Línea Base permanece en la raíz del proyecto de pruebas.

Distingue `data.task`: diseño, implementación, revisión, diagnóstico, ejecución
o reporte, según las [reglas de cierre](../ranger/references/qa-output.md#tareas-y-cierre).
Diseñar casos no acredita ejecución. Una implementación sin ejecución verificada
o sin evidencia obligatoria queda `partial` o `failed`. Una revisión terminada
puede encontrar defectos y un reporte puede recomendar `NO-GO`.
Omite `metrics`, valida el archivo con `validate.mjs` y contrasta sus referencias
con los archivos y los resultados originales. Consulta los ejemplos en `contracts/examples/`.

## Tablero de trabajo (uso directo)

Si esta skill se invoca directamente (no a través de Ranger), aplica antes de empezar la
[pregunta del tablero](../ranger/references/tablero_de_trabajo_mcp.md#2-la-pregunta-inicial):
una sola vez, opcional y no bloqueante (si el usuario no tiene tablero, empieza el trabajo). Con
tablero conectado, lee las HU/planes del alcance y, al terminar, comenta y actualiza el estado según
la [guía de cierre](../ranger/references/tablero_de_trabajo_mcp.md#5-actualizar-el-tablero-al-terminar).
Cuando la coordina Ranger, no escribas en el tablero: Ranger hace la actualización consolidada.

## Paso 0 — Determinar la versión de Karate (obligatorio)

Karate tiene **dos líneas incompatibles a nivel de dependencias** y equivocarse aquí rompe todo lo demás. Antes de escribir una sola línea, identifica cuál aplica:

| Señal | Línea |
|---|---|
| `karate-junit6`, `io.karatelabs.core.Runner`, `SuiteResult`, Java 21+, `karate-pom.json`, `karate-boot.js`, `@lock=` | **v2** (2.x, rama `main` actual) |
| `karate-junit5`, `com.intuit.karate.Runner`, `Results`, Java 11/17, `@parallel=false` | **v1** (1.5.x, rama `v1`) |
| Proyecto nuevo, Java 21 disponible | **v2** por defecto |
| Proyecto nuevo, Java 17 (frecuente en banca), scaffold Bancolombia (`gradle gat`), `karate-robot` (desktop) | **v1.5.2** |

Si no hay señales y el usuario no lo dice, pregunta **una sola cosa**: versión de Java del proyecto (y si es Maven o Gradle). Para detalle de dependencias, setup y la matriz de decisión completa lee `references/01-version-y-setup.md`. Si el usuario viene de v1 y quiere pasar a v2, lee `references/11-migracion-v1-v2.md`.

Registra la versión elegida en la Línea Base (ver más abajo) para no volver a preguntar.

## Flujo de trabajo

Identifica el tipo de tarea y lee **solo** los recursos que necesita. No cargues todos.

| Tarea | Recursos a leer |
|---|---|
| Crear proyecto/suite desde cero | 01, 10, luego `scripts/scaffold.py` (usa `templates/`) |
| Escribir pruebas de API (REST, auth, datos) | 02, 03, 04 |
| Generar pruebas desde un OpenAPI/Swagger o una HU | 04, 10 (sección "De especificación a casos") |
| Validar respuestas / esquemas JSON | 03 |
| Mocks, virtualización, contract testing | 05 |
| UI web / pruebas híbridas API+UI | 06 |
| Performance / carga reutilizando features | 07 |
| Kafka, gRPC, WebSocket, BD, SSH, AWS | 08 |
| Runners, paralelismo, tags, reportes, pipelines | 09 |
| Matriz de trazabilidad / evidencia para auditoría | 09 §7 + `scripts/rtm_from_cucumber.py` |
| Revisar/mejorar features existentes | 10 + ejecutar `scripts/lint_features.py` |
| Migrar v1 → v2 | 11 |
| Error al ejecutar, comportamiento extraño | 12 |

### Al escribir pruebas

1. **Entiende el contrato antes que el código.** Endpoint, método, payloads de ejemplo, códigos de estado esperados, reglas de negocio, autenticación. Si falta algo crítico (p. ej. cómo se obtiene el token), pregúntalo; si es menor, asume y declara la suposición en un comentario de la feature.
2. **Diseña los casos** con técnicas reales de prueba (partición de equivalencia, valores límite, negativos, idempotencia, autorización) — ver `references/10-arquitectura-de-suite.md`. Cubre siempre: camino feliz, validaciones de entrada (400/422), autenticación/autorización (401/403), recurso inexistente (404) y al menos un caso de regla de negocio.
3. **Escribe idiomático Karate**, no Java disfrazado:
   - Configuración y URLs en `karate-config.js` por ambiente; nunca URLs ni secretos hardcodeados en features.
   - Token una sola vez por suite con `karate.callSingle()`, no un login por escenario.
   - Aserciones con `match` sobre el objeto completo (`match response == { ... }` con marcadores difusos) en lugar de diez `match response.campo == ...` sueltos.
   - Esquemas reutilizables en archivos `.json` leídos con `read()`.
   - Features auxiliares marcadas `@ignore` e invocadas con `call read(...)`.
   - Datos dinámicos con `Scenario Outline` + `Examples` (tabla, CSV, JSON o `@setup`), no copiar escenarios.
4. **Asegura independencia:** cada escenario crea sus propios datos o los obtiene de un setup idempotente; nada depende del orden de ejecución. Si hay recurso compartido que obliga a serializar, usa `@lock=<nombre>` (v2) o `@parallel=false` (v1).
5. **Valida lo que entregas**: corre `python scripts/lint_features.py <ruta>` sobre las features generadas y corrige los hallazgos antes de entregar. Si hay entorno con Java/Maven disponible y el sistema bajo prueba es accesible, ejecuta las pruebas.

### Al revisar features existentes

Corre el linter (cubre lo mecánico), luego revisa manualmente lo que el linter no ve —dependencias entre escenarios (A8), esquemas duplicados (A9), cobertura negativa faltante— contra la lista de anti-patrones de `references/10-arquitectura-de-suite.md`. Entrega hallazgos priorizados (Bloqueante / Mayor / Menor) con la corrección concreta para cada uno, no solo la descripción del problema.

## Formato de entrega

- Árbol de archivos propuesto primero (cuando son 3+ archivos), luego cada archivo completo.
- Comentarios en las features en español; nombres de `Feature`/`Scenario` en el idioma que use el equipo (por defecto español, con IDs de HU/criterio si existen: `Scenario: [HU-123][CA-2] rechaza monto negativo`).
- Instrucción exacta para ejecutar (`mvn test -Dkarate.env=dev -Dkarate.options="--tags @smoke"` o equivalente Gradle/CLI).
- Si se generan varios archivos, empaquetar en `.zip` con la estructura del proyecto.
- Señala explícitamente cualquier capacidad **comercial** usada (Kafka, gRPC, WebSocket nativos, Karate Agent, Xplorer): requieren licencia de Karate Labs. Ofrece la alternativa open source (Java interop) cuando exista.

## Línea Base del proyecto

Para proyectos que se trabajan en varias sesiones, mantén un archivo `Linea_Base_<Proyecto>.md` en la raíz del proyecto de pruebas (plantilla en `templates/common/Linea_Base_TEMPLATE.md`). Léelo al inicio si existe; créalo o actualízalo al cerrar un hito. Contiene: versión de Karate y Java, build tool, ambientes y sus URLs base (sin secretos), mecanismo de autenticación, convenciones de tags, estructura de carpetas, servicios cubiertos y pendientes, y decisiones tomadas. Es la memoria del proyecto: evita re-preguntar y mantiene consistencia entre sesiones.

## Reglas de exactitud

Karate v2 evoluciona rápido (release candidates frecuentes) y su API Java cambió respecto a v1. Por eso:

- No inventes métodos, keywords ni opciones. Si no estás seguro de que algo exista en la versión objetivo, dilo y propón verificarlo contra el repo (`github.com/karatelabs/karate`, carpeta `docs/` en `main` para v2, rama `v1` para v1).
- No mezcles APIs: `com.intuit.karate.*` es v1 (en v2 solo como shim deprecado); `io.karatelabs.*` nativo es v2.
- Los números de versión en las plantillas son los verificados al construir la skill (v2: 2.1.3 estable; v1: 1.5.2). Recomienda revisar Maven Central por la última versión antes de fijarla en un proyecto real.

## Recursos

- `references/01-version-y-setup.md` — matriz v1/v2, dependencias Maven/Gradle, CLI standalone, `karate-pom.json`, estructura.
- `references/02-sintaxis-dsl.md` — keywords, JSON vs JS, expresiones embebidas, `call`/`callonce`/`callSingle`, data-driven, hooks.
- `references/03-match-y-esquemas.md` — operadores de `match`, marcadores difusos, validación de esquemas, XML.
- `references/04-api-patterns.md` — auth (basic/bearer/OAuth2), headers, retry, multipart, GraphQL, SOAP, manejo de errores, patrones CRUD.
- `references/05-mocks-y-contratos.md` — mock server, mocks con estado, proxy, contract testing consumidor/proveedor.
- `references/06-ui-driver.md` — driver, localizadores, esperas, híbridas API+UI, contenedores, intercept.
- `references/07-performance-gatling.md` — karate-gatling, simulaciones, variables de sesión, eventos custom.
- `references/08-protocolos-y-extensiones.md` — Kafka, gRPC, WebSocket, BD, Java interop, `karate-boot.js`, ofertas enterprise.
- `references/09-ci-cd-y-reportes.md` — runners, paralelismo, tags, reportes, logging y enmascaramiento, Azure DevOps / GitHub Actions / Jenkins.
- `references/10-arquitectura-de-suite.md` — estructura de carpetas, convenciones, diseño de casos, anti-patrones, checklist de revisión.
- `references/11-migracion-v1-v2.md` — checklist y equivalencias.
- `references/12-troubleshooting.md` — errores frecuentes y su causa.
- `references/13-evidencia-ui.md` — límites del driver y preparación de video/trace.
- `templates/` — esqueletos de proyecto (Maven v2, Maven v1, Gradle v1) y archivos comunes.
- `scripts/scaffold.py` — genera un proyecto base listo para correr (Maven v2, Maven v1, Gradle v1).
  `python scripts/scaffold.py --nombre pagos-api-tests --linea v2 --build maven --dominios pagos,clientes --salida <dir>`
- `scripts/lint_features.py` — detecta anti-patrones (A1–A20 del recurso 10) en `.feature`; `--json` para salida estructurada; código de salida 1 si hay bloqueantes (usable como gate en CI).
- `scripts/rtm_from_cucumber.py` — matriz de trazabilidad HU → criterio → escenarios → estado desde el Cucumber JSON del reporte.

## Evaluación

Los casos están en [evals/evals.json](evals/evals.json). El
[harness QA](../ranger/references/evaluations.md) separa el encargo y los
fixtures de los oráculos, y distingue comprobación automática de evaluación con agente.

## Reporte de máquina para el contrato

Conserva el reporte nativo de la ejecución y usa el reporter CTRF del runner o
convierte ese archivo a CTRF con una herramienta compatible. Declara el CTRF como
`test_results` con su `path` local. En `data` declara `task`, `expected` (los casos
acordados o `null` si se desconocen), `exitCriteria` y `evidencePolicy`.
No uses `data.execution` ni `data.verification`, ni construyas conteos a mano.
Los nombres deben conservar el ID de caso y la prioridad para trazar el alcance.
La conversión no sustituye la ejecución ni acredita evidencia que no existe.
Para adjuntos externos puedes copiar y adaptar `../ranger/scripts/attach-evidence.mjs`:
organiza primero los archivos reales en `resources/qa/test-results/<runId>/<CASE-ID>/`.
Este enlace no modifica los runners ni captura evidencia adicional.

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "qa-ranger-karate", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill qa-ranger-karate --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
