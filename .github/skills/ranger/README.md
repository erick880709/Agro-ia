# ranger

Skill de ingeniería de calidad (QA). Define la estrategia de pruebas, analiza
requisitos, elige la herramienta adecuada, coordina a las skills especialistas,
ejecuta pruebas y entrega resultados con evidencia y un veredicto GO / NO-GO.

> En una frase: Ranger decide **qué** probar y **con qué**; las skills
> `qa-ranger-*` hacen el trabajo especializado; todo termina en evidencia por caso
> y un veredicto calculado, no opinado.

Este README es la guía rápida de uso. La fuente operativa es [SKILL.md](SKILL.md)
y la documentación completa está en [.claude/doc/ranger/](../../doc/ranger/README.md)
(con su [guía de validación](../../doc/ranger/validacion.md)).

---

## Índice

1. [Cuándo usarla](#1-cuándo-usarla)
2. [La familia QA](#2-la-familia-qa)
3. [Cómo invocarla](#3-cómo-invocarla)
4. [Cómo elige la herramienta](#4-cómo-elige-la-herramienta)
5. [Flujo de trabajo](#5-flujo-de-trabajo)
6. [Playbooks especializados](#6-playbooks-especializados)
7. [Dónde quedan los entregables](#7-dónde-quedan-los-entregables)
8. [Evidencia y veredicto](#8-evidencia-y-veredicto)
9. [Credenciales y datos de prueba](#9-credenciales-y-datos-de-prueba)
10. [Reglas de oro](#10-reglas-de-oro)
11. [Scripts](#11-scripts)
12. [Validar y evaluar la familia QA](#12-validar-y-evaluar-la-familia-qa)
13. [Problemas frecuentes](#13-problemas-frecuentes)

---

## 1. Cuándo usarla

- Definir la estrategia de pruebas de un proyecto (pirámide, cobertura, gates de CI).
- Analizar una HU o spec antes de probarla: ambigüedades, conflictos, trazabilidad.
- Crear un plan de pruebas o un runbook, o ejecutar uno existente.
- Generar o mejorar pruebas unitarias, de integración, de API o E2E.
- Ejecutar pruebas y entregar evidencia (video, trace, screenshot) y un reporte.
- Estabilizar pruebas inestables (flaky).
- Probar seguridad funcional, escenarios de fraude, accesibilidad o carga.
- Elegir, comparar o migrar herramientas de automatización.

No la uses para implementar la funcionalidad que se va a probar (eso es `builder`)
ni para revisar un diff de código (eso es `code-review`).

---

### Tablero de trabajo (opcional)

Antes de empezar, Ranger pregunta una vez si tienes un tablero en **Jira** o **Azure DevOps**
(p. ej. `https://personalsoftsas.visualstudio.com/`) para conectarlo por MCP. Con tablero, lee las HU,
criterios y planes de prueba, y al terminar comenta lo realizado y cambia el estado del work item
según el veredicto (con tu confirmación, salvo que elijas `automático`). Si respondes que no, empieza
el trabajo con lo que le compartas. Las credenciales van en variables de entorno, nunca en archivos.
Guía: [tablero_de_trabajo_mcp.md](references/tablero_de_trabajo_mcp.md).

---

## 2. La familia QA

Ranger trabaja con siete especialistas. Si el pedido ya nombra la herramienta, puedes
invocar al especialista directamente; si es un pedido QA genérico, empieza por Ranger.

| Skill | Úsala para |
|---|---|
| `ranger` | Estrategia, selección de herramienta, coordinación, ejecución de runbooks, reporte, y las herramientas sin especialista (Cypress, WebdriverIO, Appium, k6, BDD) |
| [qa-ranger-plan-pruebas](../qa-ranger-plan-pruebas/SKILL.md) | Solo el plan de pruebas, solo el runbook, o ambos |
| [qa-ranger-playwright](../qa-ranger-playwright/SKILL.md) | Suites Playwright: E2E web, API, grabación, traces y evidencia |
| [qa-ranger-karate](../qa-ranger-karate/SKILL.md) | Suites Karate de API y aceptación (v1 y v2) |
| [qa-ranger-selenium](../qa-ranger-selenium/SKILL.md) | Suites Selenium WebDriver 4 en Java (JUnit 5/TestNG) o Python (pytest) |
| [qa-ranger-robotframework](../qa-ranger-robotframework/SKILL.md) | Suites Robot Framework: aceptación de base de datos (incluido el stage Acceptance Test del release en Azure DevOps), API, Browser y SeleniumLibrary |
| [qa-ranger-jmeter](../qa-ranger-jmeter/SKILL.md) | Pruebas de carga con JMeter: planes `.jmx`, correlación, análisis JTL y gates de SLA |
| [qa-ranger-unitarias](../qa-ranger-unitarias/SKILL.md) | Pruebas unitarias con el runner del stack y cobertura contra la meta del 95% |

Aplicar un especialista no crea otro agente: la misma sesión sigue sus
instrucciones. Cada skill aplicada entrega su propio resultado.

---

## 3. Cómo invocarla

```text
/ranger define la estrategia de pruebas para el módulo de pagos
/ranger prueba la HU-04 y genera evidencia
/ranger ejecuta el runbook resources/qa/runbooks/qa-runbook-login.md
/ranger crea el plan de pruebas de PROJ-123
/ranger por qué falla de forma intermitente el test de checkout
/ranger diseña pruebas anti-fraude para el flujo de transferencias
/ranger audita la accesibilidad del formulario de registro
```

Con un especialista directo:

```text
/qa-ranger-playwright automatiza el login con evidencia
/qa-ranger-karate genera las pruebas de aceptación desde este OpenAPI
/qa-ranger-robotframework crea las pruebas de aceptación de la BD para el release
/qa-ranger-jmeter prueba de carga de la API de pagos a 200 usuarios
/qa-ranger-unitarias sube la cobertura del servicio de facturación
```

También se activa sola al mencionar una HU (`HU-01`), una clave de Jira o frases
como *"prueba esto"*, *"genera el plan de pruebas"* o *"¿está listo para salir?"*.

---

## 4. Cómo elige la herramienta

1. **Respeta lo que pidas.** Si nombras una herramienta, usa esa. Pedir otra
   herramienta no autoriza a borrar la suite que ya existe.
2. **Conserva la vigente.** En un pedido genérico, detecta lo instalado
   (`playwright.config.*`, `cypress.config.*`, `wdio.conf.*`, `selenium-java`, `.robot`,
   `selenium` en Python, Appium, `.jmx`, k6) y lo mantiene. Si hay varias, pregunta.
3. **Propone una solo si no hay ninguna.** Playwright para E2E web; Karate para
   aceptación/API en proyectos Java; las unitarias usan el runner del stack.
4. **No migra en silencio.** Una migración se confirma y se hace por módulo,
   conservando los IDs de caso.

La decisión queda registrada en `resources/qa/project-context.md` para no volver a
detectarla en la siguiente conversación.

---

## 5. Flujo de trabajo

```
0 Reconocer el proyecto ─► 1 Estrategia ─► 2 Plan ─► 3 Implementar pruebas
                                                             │
           6 Mantener la suite ◄─ 5 Ejecutar y reportar ◄─ 4 Configurar evidencia
```

| Paso | Qué hace |
|---|---|
| 0 Reconocer | Lee `CLAUDE.md`, `package.json` y la configuración de pruebas; detecta herramienta y gestor de paquetes; instala solo lo que falta como devDependency (y te dice qué instaló); analiza los requisitos; guarda el contexto del proyecto |
| 1 Estrategia | Clasifica flujos críticos y riesgos, distribuye la pirámide (unitarias 50-60 %, integración 25-35 %, E2E 10-15 %) y define gates de CI |
| 2 Plan | Lo crea `qa-ranger-plan-pruebas` con casos, resultados esperados y criterios de salida |
| 3 Implementar | Pruebas con nombres de comportamiento, Arrange-Act-Assert, locators resilientes, Page Objects y el ID del caso en el título |
| 4 Evidencia | Configura video, trace y screenshot por caso y el archivo `.env.qa` |
| 5 Ejecutar | Smoke primero, después regresión por prioridad; genera el reporte desde el CTRF con el veredicto calculado |
| 6 Mantener | Aísla pruebas, elimina el no-determinismo y trata las flaky por causa raíz |

Si falta información para casos críticos (pasos, resultados esperados o datos),
Ranger se detiene y la pide; no inventa reglas de negocio.

---

## 6. Playbooks especializados

Cada tipo de prueba usa un prefijo de ID para que el reporte lo reconozca y lo
cuente en el veredicto:

| Playbook | Prefijo | Notas |
|---|---|---|
| Funcional / E2E | `TC-` | Caso general |
| Seguridad funcional (auth, autorización, IDOR, sesión, cabeceras) | `SEC-` | Solo en entornos de prueba; la autorización se prueba contra el endpoint, no ocultando botones |
| Adversarial / anti-fraude (doble envío, carreras, bypass de límites) | `FRAUD-` | Un `FRAUD-` crítico que logra el abuso fuerza `NO-GO` |
| API (contrato, negativos, idempotencia, paginación, versiones) | `API-` | Con trace como evidencia |
| Accesibilidad WCAG 2.1 AA | `A11Y-` | axe más checklist manual de teclado y lector de pantalla |
| Carga con k6 o JMeter | `PERF-` | Carga, umbrales p95/p99 y tasa de error acordados antes; nunca contra producción sin autorización |
| Unitarias | `UT-` | Runner del stack |

También incluye guías para BDD/Gherkin, Cypress, WebdriverIO, Appium (móvil nativo)
y migración entre herramientas.

---

## 7. Dónde quedan los entregables

Todo lo que produce Ranger en el proyecto queda bajo `resources/qa/`. Cada ejecución
usa un `runId` nuevo y nunca pisa las anteriores. Los specs automatizados no van
aquí: viven en el código del proyecto (`e2e/`, `tests/`).

```
resources/qa/
├── project-context.md              Stack, herramienta y convenciones detectadas
├── plans/test-plan-<feature>.md
├── runbooks/qa-runbook-<feature>.md
├── TC-01/<runId>/chromium/attempt-0/   video.webm, trace.zip, screenshot
├── test-results/<runId>/           Originales del runner (no se borran)
├── perf/<runId>/                   Resultados de k6
├── contracts/<runId>/              Resultados contractuales <capabilityId>-<n>.json
└── reports/<runId>/
    ├── ctrf.json                   Resultado de la corrida y adjuntos por caso
    ├── html/                       Reporte HTML del runner
    └── execution-report.md         Reporte con el veredicto calculado
```

---

## 8. Evidencia y veredicto

**Política de evidencia por defecto:**

| Tipo de prueba | Evidencia obligatoria por caso |
|---|---|
| Navegador (E2E) | Video, trace y screenshot, en cada caso y no solo en los fallidos |
| API y unitarias | Resultados del runner (y cobertura nativa en unitarias) |

Reducir la política (por ejemplo, `retain-on-failure` en CI) requiere pedirlo de
forma explícita.

**Veredicto.** Lo calcula el generador de reportes a partir del CTRF; Ranger lo
publica tal cual:

| Veredicto | Significa |
|---|---|
| `GO` | Listo |
| `GO with known risks` | Listo, con riesgos conocidos y documentados |
| `NO-GO` | Hay defectos bloqueantes (por ejemplo, falló un caso `[critical]`) |

```bash
node .claude/contracts/output/generate-execution-report.mjs \
  --ctrf resources/qa/reports/<runId>/ctrf.json \
  --expected <casos.json> --exit-criteria <criterios.json> \
  --out resources/qa/reports/<runId>/execution-report.md
```

Una suite vacía, un caso crítico omitido o evidencia faltante no acreditan un `GO`.
Un reporte terminado puede recomendar `NO-GO`: el estado de la entrega y el
veredicto de calidad son cosas distintas.

**Nombrar los casos.** El ID y la prioridad van en el título para que la evidencia
se asocie sola:

```ts
test('TC-01 [critical] [HU-123][CA-2] Login con credenciales válidas', async ({ page }) => { ... });
```

---

## 9. Credenciales y datos de prueba

- Las credenciales van en `.env.qa` (ignorado por Git), creado desde
  [templates/env.example](templates/env.example). Nunca en planes, runbooks o specs.
- Si falta un usuario de prueba, Ranger no te pide la contraseña: ejecuta
  `node scripts/ensure-test-user.mjs --role user` (o `--role admin`), que genera la
  cuenta y la guarda en `.env.qa`.
- Si un runbook trae una credencial literal, Ranger se detiene y lo señala antes de
  ejecutar.
- Seguridad, fraude y carga se ejecutan solo en entornos de prueba y con datos
  sintéticos.

---

## 10. Reglas de oro

Valen para cualquier herramienta. Si una prueba generada las incumple, es un error
que se corrige antes de entregar:

1. Locators por rol, label o texto antes que CSS o XPath; `data-testid` es el último recurso.
2. Nunca esperas fijas (`waitForTimeout`, `Thread.sleep`, `cy.wait(ms)`); usar aserciones que esperan una condición.
3. Cada prueba aislada: sin estado compartido ni dependencia del orden.
4. URL base centralizada; nada de URLs escritas en los specs.
5. Declarar el nivel y el sistema bajo prueba: en E2E no se simula lo que se dice verificar.

---

## 11. Scripts

| Script | Para qué |
|---|---|
| `scripts/ensure-qa-dependencies.mjs --tool <playwright\|cypress> [--with-unit] [--with-msw] [--with-a11y] [--with-api]` | Instala lo que falte como devDependency, incluidos los navegadores de Playwright |
| `scripts/ensure-test-user.mjs --role <user\|admin>` | Crea credenciales de prueba y las guarda en `.env.qa` |
| `scripts/attach-evidence.mjs` | Asocia adjuntos de otros runners a sus casos en el CTRF |
| `scripts/evaluate.mjs`, `scripts/smoke-claude.mjs` | Preparan y comprueban evaluaciones de las skills |

Los scripts se copian y adaptan al proyecto destino; no están pensados para
ejecutarse desde la carpeta de la skill. Selenium, Robot Framework, JMeter, Appium y k6 tienen su
propio setup, fuera de este instalador.

---

## 12. Validar y evaluar la familia QA

Los validadores del contrato y el generador de reportes necesitan Node 22 o
posterior. Desde la raíz del kit:

```powershell
npm ci
node --test
node .claude/skills/ranger/scripts/evaluate.mjs prepare qa-ranger-plan-pruebas 1 <directorio-nuevo>
#   el agente trabaja en <directorio-nuevo>/workspace siguiendo encargo.md
node .claude/skills/ranger/scripts/evaluate.mjs check <directorio-nuevo>
```

Cada skill de la familia tiene `contracts/output-contract.json` y `evals/evals.json`.
El contrato común vive en `.claude/contracts/output/`. Un contrato válido comprueba
estructura, reglas y archivos; no certifica que el plan sea correcto ni que la
prueba sea auténtica. Ver la [guía de validación](../../doc/ranger/validacion.md) y
el [harness QA](references/evaluations.md).

---

## 13. Problemas frecuentes

| Problema | Qué hacer |
|---|---|
| El veredicto da `NO-GO` y no está claro por qué | Falló un caso `[critical]`; revisa su video y trace en los adjuntos del CTRF |
| Un caso aparece "sin ID o prioridad verificable" | El título debe usar un prefijo reconocido (`TC-`, `SEC-`, `FRAUD-`, `API-`, `A11Y-`, `UT-`, `PERF-`) y una prioridad (`[critical]` o `@critical`) |
| `Executable doesn't exist` al correr Playwright | `node scripts/ensure-qa-dependencies.mjs --tool playwright` |
| Generó specs con la herramienta equivocada | Indica la herramienta vigente; Ranger debe detectarla en el Paso 0.1 |
| Pasa en local y falla en CI | Revisar paridad de entorno, zona horaria, reintentos y modo headless |
| axe no encuentra nada, pero el flujo no es accesible | axe cubre ~30-40 % de los problemas; falta el checklist manual |
| `k6: command not found` | k6 es un binario aparte; ver [performance_testing_guide.md](references/performance_testing_guide.md) |
| `project-context.md` quedó desactualizado | Ranger reverifica solo la parte que cambió y reescribe el archivo |

Más casos en la sección *Solución de problemas* de [SKILL.md](SKILL.md).
