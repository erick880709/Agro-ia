---
name: qa-ranger-jmeter
metadata:
  display-name: "Especialista en rendimiento"
  capability: "Pruebas de rendimiento"
  capability-summary: "Diseña y ejecuta pruebas de carga con JMeter y entrega un análisis de rendimiento."
description: Experto en pruebas de rendimiento con Apache JMeter (5.6.x) y JMeter DSL (Java) — diseño de carga (modelo de trabajo, Ley de Little, SLA), planes .jmx correctos, correlación y datos (CSV, extractores, Groovy/JSR223), Open Model Thread Group, ejecución CLI y distribuida, análisis de resultados (JTL, percentiles, dashboard HTML, Grafana) y quality gates en CI/CD (GitHub Actions, Azure DevOps, Jenkins). Usa esta skill SIEMPRE que el usuario mencione JMeter, .jmx, .jtl, jmeter -n, Thread Group, JMeter DSL, Taurus/bzt, BlazeMeter, o pida pruebas de carga, estrés, picos, resistencia o capacidad, aunque no nombre la herramienta (p. ej. "cuántos usuarios aguanta este servicio", "prueba de carga para la API de pagos", "analiza estos resultados de rendimiento", "mete performance en el pipeline", "por qué JMeter se queda sin memoria"). También aplica a revisar planes .jmx existentes y a interpretar resultados.
---

# QA Ranger — JMeter

Skill para diseñar, construir, ejecutar, analizar y automatizar pruebas de rendimiento con **Apache JMeter** y **JMeter DSL**. Produce planes ejecutables, comandos exactos y conclusiones respaldadas por datos.

## Tablero de trabajo (uso directo)

Si esta skill se invoca directamente (no a través de Ranger), aplica antes de empezar la
[pregunta del tablero](../ranger/references/tablero_de_trabajo_mcp.md#2-la-pregunta-inicial):
una sola vez, opcional y no bloqueante (si el usuario no tiene tablero, empieza el trabajo). Con
tablero conectado, lee las HU/planes del alcance y, al terminar, comenta y actualiza el estado según
la [guía de cierre](../ranger/references/tablero_de_trabajo_mcp.md#5-actualizar-el-tablero-al-terminar).
Cuando la coordina Ranger, no escribas en el tablero: Ranger hace la actualización consolidada.

## Paso 0 — Contexto

Antes de construir nada, establece el **objetivo de la prueba**. Una prueba de carga sin objetivo produce números que nadie sabe interpretar.

| Pregunta | Por qué importa |
|---|---|
| ¿Qué se quiere saber? (¿aguanta la carga esperada?, ¿dónde se rompe?, ¿se degrada con el tiempo?, ¿empeoró tras un cambio?) | Define el tipo de prueba (`resources/02`) |
| ¿Carga objetivo? (usuarios concurrentes, transacciones/s, horario pico real) | Define el modelo de trabajo |
| ¿Criterios de aceptación? (p95 < X ms, errores < Y %, throughput ≥ Z) | Sin SLA no hay veredicto |
| ¿Ambiente? (¿réplica de producción?, ¿compartido?, ¿datos realistas?, ¿autorización para cargar?) | Validez de los resultados y seguridad |
| ¿Formato? `.jmx` (equipo QA, GUI) o **JMeter DSL** (Java en el repo, CI) | Modo de trabajo |

Si el usuario no tiene SLA ni carga objetivo, **no los inventes como si fueran requisitos**: propón valores de partida explícitamente marcados como supuestos y explica cómo obtener los reales (logs de producción, APM, negocio).

**Versión**: JMeter **5.6.3** es la versión estable vigente (requiere Java 8+, recomendado 17). La rama principal prepara la **6.0.0** (Java 17 obligatorio, elimina MongoDB, Groovy 5). Revisa `resources/01` antes de usar elementos nuevos.

## Principio central: un `.jmx` correcto se verifica, no se supone

Un `.jmx` es XML que JMeter carga **sin validar los nombres de propiedad**: una propiedad mal escrita se ignora en silencio y el elemento hace otra cosa (por ejemplo, una aserción vacía que nunca falla). Por eso:
1. Genera los `.jmx` a partir de las plantillas de `templates/` o con nombres de propiedad del catálogo verificado (`scripts/data/jmx_catalogo.json`, extraído del código fuente de JMeter 5.6.3).
2. Ejecuta **siempre** `python scripts/lint_jmx.py <plan.jmx>` antes de entregar: valida la estructura, las propiedades contra el catálogo y los antipatrones de rendimiento.
3. Conserva las erratas históricas de JMeter: la propiedad de la aserción de respuesta es **`Asserion.test_strings`** (sin la segunda "s" en Assertion). "Corregirla" rompe la aserción en silencio.
4. Antes de la prueba real, valida con **1 usuario y 1 iteración** (`-Jusuarios=1 -Jiteraciones=1`): 0 % de errores y las respuestas esperadas.

## Flujo por tarea

Lee **solo** los recursos que la tarea necesita.

| Tarea | Recursos |
|---|---|
| Definir qué prueba hacer y con qué carga | 02 |
| Crear plan .jmx desde cero | 03, 04, 05, luego `scripts/scaffold.py` |
| Correlación (tokens, IDs), datos de prueba, scripting | 04 |
| Aserciones y criterios de aceptación | 05 |
| Ejecutar (CLI, distribuido, Docker, Taurus) | 06 |
| Analizar resultados (.jtl, dashboard) | 07 + `scripts/analizar_jtl.py` |
| Integrar en CI/CD con quality gate | 08 |
| Pruebas de rendimiento como código Java (JMeter DSL) | 09 |
| Revisar un .jmx existente | 10 + `scripts/lint_jmx.py` |
| JDBC, Kafka, gRPC, WebSocket, SOAP, autenticación OAuth2 | 11 |
| JMeter se queda sin memoria, resultados raros, cuello de botella del generador | 12 |

### Al construir un plan

1. **Modelo de trabajo** (02): flujos de negocio, mezcla porcentual, tiempo de reflexión, ritmo objetivo. Calcula usuarios con la Ley de Little y muestra el cálculo.
2. **Parametriza todo con propiedades** `${__P(nombre,valor_defecto)}`: host, protocolo, puerto, usuarios, rampa, duración, ritmo. El mismo `.jmx` sirve para todos los ambientes y tipos de prueba.
3. **Estructura**: HTTP Request Defaults, Header/Cookie/Cache Manager, CSV Data Set, Transaction Controllers por paso de negocio, extractores para correlación, aserciones ligeras, timers de reflexión.
4. **Sin listeners de visualización** (View Results Tree, gráficas) en el plan de carga: los resultados van al `.jtl` vía CLI (`-l`).
5. **Groovy en JSR223** con caché de compilación (sin `${}` dentro del script); nunca BeanShell.
6. **Valida**: `lint_jmx.py`, luego 1 usuario/1 iteración, luego humo de pocos usuarios, y entonces la prueba real.

### Al analizar resultados

`python scripts/analizar_jtl.py resultados.jtl --sla sla.json [--base anterior.jtl]`: estadísticas por transacción (p50/p90/p95/p99, errores, throughput), veredicto contra el SLA y comparación con una ejecución base. Interpreta, no solo reportes números: relaciona la degradación con la carga (¿en qué punto empezó?), separa errores funcionales de saturación, y verifica que el **generador** no fue el cuello de botella (12).

## Formato de entrega

- Plan de prueba: objetivo, tipo, modelo de trabajo con cálculos, SLA, supuestos, riesgos.
- Archivos completos (`.jmx`, CSV de datos, `user.properties` por ambiente, scripts de ejecución, pipeline); empaqueta en `.zip` si son 3 o más.
- Comando exacto: `jmeter -n -t plan.jmx -q env/qa.properties -l resultados.jtl -e -o reporte/`.
- Resultados: tabla por transacción, veredicto por criterio (✅/❌), observaciones e hipótesis de causa, y siguiente paso.
- Declara qué se ejecutó y qué no: «validado con lint», «ejecutado 1 usuario», «prueba completa ejecutada», «sin acceso al ambiente».

## Línea Base del proyecto

Como en las demás skills QA Ranger: `Linea_Base_<Proyecto>.md` en la raíz (plantilla en `templates/common/`). Registra: versión de JMeter/Java/plugins, ambientes y hosts (sin secretos), modelo de trabajo y SLA acordados, **resultados de referencia por versión del sistema** (para detectar regresiones), capacidad del generador, decisiones y deuda.

## Seguridad y límites

- **Solo ambientes propios o con autorización explícita y por escrito.** Una prueba de carga contra un sistema sin autorización es indistinguible de un ataque de denegación de servicio. No ayudes a cargar sistemas de terceros, evadir rate limits o protecciones anti-DDoS/WAF.
- Coordina ventana, volumen y responsables con operación/infraestructura antes de cargar ambientes compartidos; define criterio de aborto.
- Nunca contra producción sin aprobación formal, plan de reversión y monitoreo activo.
- Credenciales por propiedades/variables de entorno, nunca dentro del `.jmx`. Los `.jtl` y reportes pueden contener datos de respuestas: trátalos como confidenciales.

## Reglas de exactitud

- No inventes elementos, propiedades ni opciones de línea de comandos. Verifica contra el catálogo, `jmeter --help`, o el código fuente (`apache/jmeter`, `xdocs/usermanual/component_reference.xml`).
- Distingue elementos del núcleo de los de **plugins** (Concurrency/Ultimate Thread Group, Throughput Shaping Timer, etc.): exigen el Plugins Manager y deben declararse en la Línea Base.
- Un percentil no es un promedio: reporta p90/p95/p99 y nunca concluyas solo con el promedio.

## Recursos

- `resources/01-setup-y-versiones.md` — instalación, Java, heap, propiedades, plugins, versiones 5.6.x y 6.0.
- `resources/02-diseno-de-pruebas.md` — tipos de prueba, modelo de trabajo, Ley de Little, think time, pacing, SLA.
- `resources/03-estructura-jmx.md` — elementos, alcance y orden de ejecución, thread groups (incl. Open Model), propiedades vs variables.
- `resources/04-correlacion-y-datos.md` — extractores, CSV Data Set, funciones, JSR223/Groovy.
- `resources/05-aserciones-y-sla.md` — aserciones ligeras, criterios de aceptación, gates.
- `resources/06-ejecucion.md` — CLI, distribuida, Docker, Taurus.
- `resources/07-resultados-y-reportes.md` — JTL, dashboard HTML, métricas, interpretación, Grafana.
- `resources/08-ci-cd.md` — GitHub Actions, Azure DevOps, Jenkins, gate y comparación con base.
- `resources/09-jmeter-dsl.md` — pruebas de rendimiento como código Java (Abstracta JMeter DSL).
- `resources/10-revision-y-antipatrones.md` — reglas J1–J25, checklist, formato de revisión.
- `resources/11-protocolos-y-autenticacion.md` — JDBC, Kafka, gRPC, WebSocket, SOAP, OAuth2.
- `resources/12-troubleshooting-y-tuning.md` — memoria, generador saturado, errores de red, lectura de anomalías.
- `scripts/scaffold.py` — proyecto parametrizado listo para correr: `plan.jmx`, ambientes, datos sin secretos, `sla.json`, `ejecutar.sh` (lint → JMeter → dashboard → gate SLA/regresión; si el lint falla, no se genera carga), pipelines y Línea Base.
- `scripts/lint_jmx.py` — valida estructura, propiedades (contra el catálogo) y antipatrones de un `.jmx`.
- `scripts/analizar_jtl.py` — estadísticas, veredicto SLA y comparación con base desde un `.jtl`; `--junit` para la pestaña de tests del CI; código de salida 1 si falla (gate).
- `scripts/data/jmx_catalogo.json` — propiedades válidas por elemento, extraídas del código fuente de JMeter 5.6.3.

## Contrato de resultados QA

Lee [las reglas comunes de resultado](../ranger/references/qa-output.md) y
[el contrato de esta capacidad](contracts/output-contract.json) antes de cerrar.
Si el host da el archivo o la carpeta de resultados, escribe allí tu resultado
(`<capabilityId>-<n>.json` si solo da la carpeta) con el capabilityId de esta skill.
No escribas identidad: el host la conoce por la ruta. No sustituyas el capabilityId por `ranger`.
Sin carpeta de resultados, entrega los artefactos sin escribir JSON contractual.

Guarda planes, reportes y evidencias locales bajo `resources/qa/`; `test_code`
conserva la estructura del proyecto. La carpeta contractual solo contiene los
resultados de las invocaciones; los archivos del runner van en otra subcarpeta.
Declara exactamente una ubicación por artefacto: `path`, `content` o `uri`.
Omite `metrics`: las deriva el validador común en Node.

Declara `data.task`: `design`, `implement`, `review`, `diagnose`, `execute` o
`report`. Diseño incluye requisitos, casos y exclusiones; no acredita ejecución.
Implementación requiere código, verificación satisfactoria y ejecución con
evidencia por caso para `completed`. Sin entorno entrega `partial` o `failed`,
con pendientes y responsable. Usa `input_required` cuando falten datos.
Una ejecución completa puede tener pruebas fallidas y recomendar `NO-GO`.
El reporte y el contrato usan el mismo motor de veredicto de Ranger.

La política de evidencia recibida del host prevalece. Reducir los tipos
predeterminados requiere una excepción explícita del encargo en `override.reason`.
Conserva el alcance previsto, errores globales, criterios de salida y evidencia
real de cada caso. No presentes compilar o pasar un linter como suite ejecutada.

Valida con `node .claude/contracts/output/validate.mjs <resultado.json>
--project-root <proyecto> --run-result --expected-capability-id qa-ranger-jmeter`.
Ejemplos ficticios: [ejecución](contracts/examples/qa-ranger-jmeter-ejecucion.json) y
[sin entorno](contracts/examples/qa-ranger-jmeter-sin-entorno.json).

Para carga sobre API usa el nivel existente `api` con `raw_results` por caso;
no inventes un nivel `performance`. Los casos representan escenarios/transacciones
acordados; conserva JTL y análisis SLA como artefactos. Expresa cada SLA acordado
en `exitCriteria`: el motor común deriva GO/NO-GO sin sustituir el análisis JTL.

La integración contractual conserva los scripts Python, las plantillas y el flujo
JMeter/JMeter DSL de esta skill. El validador común en Node comprueba el
resultado JSON; no sustituye el lint ni el análisis JTL en Python.

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
`{ "skill": "qa-ranger-jmeter", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill qa-ranger-jmeter --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
