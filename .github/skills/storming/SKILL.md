---
name: storming
metadata:
  display-name: "Modelador de dominio"
  capability: "Modelado de dominio"
  capability-summary: "Descubre y documenta eventos, reglas y límites del negocio para orientar el diseño del sistema."
description: 'Descubre, valida y documenta dominios mediante los formatos Big Picture, Process Modelling y Software Design de EventStorming, seleccionados o encadenados según el objetivo. Usar cuando el usuario pida hacer EventStorming, modelar un proceso end-to-end, identificar eventos, comandos, políticas, actores, agregados, lenguaje ubicuo, bounded contexts, hotspots o escenarios de aceptación; también antes de diseñar arquitectura o desglosar épicas complejas con múltiples actores, estados, reglas, excepciones o integraciones.'
---

# Event Storming

## Agente top-level

El agente [`storming`](../../agents/storming.agent.md) es la entrada especializada para esta skill.
Este `SKILL.md` conserva el contrato canónico; el agente no lo duplica, no invoca los handoffs y no
añade paralelismo interno.

Modelar el dominio antes de diseñar la solución o convertirla en backlog. Producir un modelo trazable y
versionable en `resources/functional/eventstorming/`, sin confundir análisis documental con validación
real de expertos de dominio.

## Límites de responsabilidad

- Descubrir hechos del negocio, decisiones, reglas, excepciones y límites del dominio.
- Mantener separados AS-IS y TO-BE.
- Entregar insumos a `archi` y `specter`.
- No seleccionar arquitectura, nube, framework ni patrón de persistencia.
- No generar historias, tareas técnicas, subtareas, Story Points ni issues de Jira. Delegar ese
  desglose a `specter` usando la trazabilidad del modelo.
- No marcar como aprobado o validado un modelo inferido únicamente desde documentos.

## Resolver modo, objetivo y formato

Determinar tres dimensiones antes de modelar.

### 1. Modo

| Modo | Cuándo aplicarlo | Estado máximo permitido |
|---|---|---|
| `taller` | Participan expertos de dominio y pueden confirmar/corregir el modelo | `validado-dominio` |
| `documental` | Solo hay documentos, código, transcripciones o descripciones | `borrador-documental` |
| `reconciliacion` | Ya existen archivos `ES-*.md` y deben continuarse o actualizarse | Conservar o degradar el estado según la evidencia |

### 2. Objetivo

- `AS-IS`: describir lo que ocurre hoy.
- `TO-BE`: diseñar cambios futuros sobre un AS-IS validado o explícitamente aceptado como base.
- `AS-IS+TO-BE`: completar y validar primero el AS-IS; modelar el TO-BE después, sin mezclar eventos.

### 3. Formato

| Formato | Elegir cuando | Resultado principal |
|---|---|---|
| `big-picture` | Explorar una línea de negocio amplia, alinear perspectivas o localizar áreas críticas | Narrativa global, pivotes, personas/sistemas y hotspots |
| `process-modelling` | Descubrir o diseñar un proceso end-to-end específico con sus variantes | Flujo de baja fidelidad probado con comandos, eventos, políticas y read models |
| `software-design` | Diseñar el comportamiento del software para un proceso crítico | Flujo conductual con agregados, límites, lenguaje y escenarios |
| `cadena` | Un formato necesita explícitamente el resultado de otro | Secuencia declarada, por ejemplo `big-picture → process-modelling` |

No ejecutar los tres formatos por defecto. Usarlos individualmente o encadenarlos solo cuando el
objetivo lo justifique. Leer `references/format-profiles.md` después de seleccionar el formato.

Si no puede inferirse modo, objetivo o formato, formular una sola pregunta breve. No pedir información
que ya esté en las fuentes.

## Resolver las fuentes

Aceptar como entrada texto del chat, rutas explícitas, IDs de requerimientos o el valor `todos`.

Buscar, según aplique:

1. `resources/functional/context/`
2. `resources/functional/requests/`
3. `resources/functional/reqs/`
4. `resources/architecture/definitions/`
5. `resources/design/models/`
6. `resources/summary/`
7. `resources/functional/eventstorming/`

Para `todos`, leer el corpus relevante completo. Registrar las fuentes usadas en `ES-001` y mantener
trazabilidad hacia IDs `CTX`, `RF`, `RNF`, `RT` y `RD`.

Si existen artefactos `ES-*.md`, entrar en modo `reconciliacion`: leerlos antes de proponer cambios,
preservar ediciones manuales, mantener IDs estables y agregar nuevos IDs desde el máximo existente.

## Ejecutar el workflow

Crear o actualizar un plan con etapas correspondientes únicamente al formato seleccionado. Mantener el
board/modelo conversacional como artefacto primario durante la exploración y hacer harvesting después
de cada gate o al cierre; no interrumpir el taller para producir documentación pulida.

### Etapa 0 — Encuadrar la sesión

1. Confirmar propósito, resultado esperado, formato, AS-IS/TO-BE y participantes.
2. Para `process-modelling` o `software-design`, confirmar punto inicial y punto final.
3. Para `big-picture`, confirmar la línea de negocio sin reducirla prematuramente a un único proceso.
4. Declarar inclusiones, exclusiones y fuentes.
5. Identificar expertos de dominio, facilitador y responsable de resolver hotspots.
6. Crear o reconciliar el encuadre mínimo de `ES-001-Resumen-Ejecutivo-y-Alcance.md`.

**Gate A:** no continuar si el propósito o el formato no están claros. La ambigüedad del dominio no
bloquea el inicio: hacerla visible es parte del trabajo.

### Receta A — Big Picture

1. Descubrir eventos de dominio en pasado, expresados con lenguaje del negocio.
2. Ordenar la narrativa cronológicamente e identificar eventos pivote y swimlanes cuando ayuden.
3. Identificar personas y sistemas externos.
4. Recorrer la narrativa en voz alta con un narrador y corregirla en tiempo real.
5. Marcar fricciones e incertidumbres como hotspots; no rellenarlas con invenciones.

**Gate B:** confirmar la línea de tiempo principal, pivotes y eventos faltantes con las fuentes o los
expertos disponibles. Cerrar aquí si `big-picture` era el único formato.

### Receta B — Process Modelling

1. Construir primero un camino base hasta un estado estable.
2. Asociar a cada evento el comando que lo provoca y el actor que emite el comando.
3. Identificar consultas/read models necesarios para decidir o ejecutar comandos.
4. Modelar políticas en formato `cuando evento → si condición → entonces comando`.
5. Introducir rutas alternativas, excepciones, compensaciones y casos límite.
6. Confirmar que cada stakeholder queda razonablemente satisfecho con el resultado.
7. Resolver cada hotspot o registrar responsable, riesgo aceptado y siguiente decisión.

**Gate C:** cada camino termina en estado estable; la gramática se respeta; las excepciones tienen
resultado, compensación o hotspot; las necesidades de los stakeholders son visibles. Cerrar aquí si
`process-modelling` era el único formato.

### Receta C — Software Design

1. Partir de un proceso crítico ya comprendido, no de un catálogo de entidades.
2. Visualizar y mover límites durante la discusión.
3. Proponer agregados por comportamiento, invariantes y ciclo de vida; tratarlos como máquinas de
   estado, no como contenedores de datos.
4. Modelar read models como información necesaria para decisiones.
5. Consolidar lenguaje ubicuo y términos polisémicos.
6. Proponer bounded contexts por lenguaje, reglas, ownership y ritmo de cambio.
7. Derivar entidades internas solo cuando identidad/ciclo de vida aclaren el comportamiento.

**Gate D:** no tratar un bounded context como servicio desplegable. Entregar límites de dominio a
`archi`, que decidirá su materialización técnica. Cerrar aquí si `software-design` era el único formato.

### Etapa transversal — Consolidar hotspots

1. Centralizar todos los hotspots en `ES-013-Hotspots-Consolidados.md`.
2. Clasificar impacto, prioridad, responsable, evidencia necesaria y estado.
3. Señalar explícitamente si cada hotspot bloquea dominio, arquitectura, backlog o implementación.
4. Evitar duplicar la descripción completa del hotspot en otros archivos; referenciar su ID.

En modo documental o conversación asíncrona, usar máximo 5 preguntas por ronda y priorizar hotspots
bloqueantes. En taller, permitir preguntas emergentes y usar hotspots para proteger el foco. Si se
continúa con riesgo aceptado, documentar quién lo aceptó y qué etapa/formato queda condicionado.

### Extensión opcional — Modelar mejoras y TO-BE

Ejecutar solo cuando el usuario solicite mejora/automatización/TO-BE y exista una base AS-IS.

1. Vincular cada problema u hotspot con oportunidades, sin saltar directamente a tecnología.
2. Priorizar oportunidades por valor, riesgo, dependencia y esfuerzo relativo.
3. Modelar eventos y comandos TO-BE como nuevos, modificados o retirados.
4. Comparar AS-IS y TO-BE y proponer una transición por capacidades.
5. Persistir `ES-014-Analisis-de-Mejoras.md` y `ES-015-Definicion-TO-BE.md`.

Las fases de transición no son tareas de Jira. Entregarlas a `specter` para el desglose ejecutable.

### Extensión opcional — Extraer pruebas de aceptación

Ejecutar después de `process-modelling` o `software-design` cuando el flujo sea suficientemente robusto
y la precisión adicional aporte valor a refinamiento, backlog, implementación o QA.

1. Elegir escenarios principales y casos límite relevantes.
2. Formular una expectativa observable por escenario:

   ```text
   DADO / GIVEN [estado y contexto verificables]
   CUANDO / WHEN [comando, acción o evento disparador]
   ENTONCES / THEN [evento, estado o resultado observable]
   ```

3. Vincular cada escenario únicamente a IDs reales `CM`, `EV`, `PL`, `RN`, `AG`, `BC` y `HS`.
4. Incluir ejemplos concretos, nombres y cantidades cuando reduzcan ambigüedad.
5. Persistirlos opcionalmente en `ES-016-Escenarios-de-Aceptacion.md`.
6. Entregarlos a `epicureo`, `specter` y `ranger`; no convertirlos aquí en historias o tareas.

### Etapa final — Harvesting, validación y cierre

Aplicar únicamente el perfil de harvesting del formato seleccionado en
`references/artifact-contract.md`. Registrar uno de estos estados:

- `borrador-documental`
- `validacion-parcial`
- `validado-dominio`
- `bloqueado-por-hotspots`

Incluir en el cierre:

- Estado y modo.
- Fuentes y participantes.
- Conteo de eventos, comandos, políticas, agregados, contextos y hotspots.
- Hotspots bloqueantes pendientes.
- Artefactos creados o modificados.
- Recomendación de siguiente skill.

No exigir los 15/16 documentos como condición de éxito. Producir el mínimo que preserve aprendizaje,
decisiones, hotspots y trazabilidad; generar el perfil extendido solo si el usuario lo pide o un
consumidor posterior lo necesita.

No usar `validado-dominio` sin confirmación explícita de expertos de dominio identificables.

## Convenciones obligatorias

- Asignar durante el harvesting IDs estables: `EV`, `AC`, `SX`, `CM`, `QR`, `PL`, `RN`, `EN`, `AG`,
  `SD`, `BC`, `HS`, `OP`, `AT`. No frenar la exploración del taller para numerar elementos.
- Usar consecutivos con cero a la izquierda y no reutilizar IDs eliminados.
- Nombrar eventos en pasado: `PedidoRealizado`, no `RealizarPedido`.
- Nombrar comandos en imperativo/infinitivo: `RealizarPedido`.
- Diferenciar evento ocurrido, comando solicitado, consulta y política.
- Usar enlaces relativos entre documentos e IDs de fuente para trazabilidad.
- Mantener una única fuente de verdad por concepto y referenciarla desde los demás archivos.
- Usar Mermaid para líneas de tiempo y mapas cuando aporte claridad, pero mantener tablas como fuente
  versionable de detalle.

## Handoffs

### Hacia `archi`

Entregar al menos `ES-002`, `ES-004`, `ES-010`, `ES-012`, `ES-013` y `ES-015` cuando exista. Informar
hotspots que bloqueen decisiones arquitectónicas y evitar traducir automáticamente `BC = microservicio`.

### Hacia `specter`

Entregar oportunidades/capacidades priorizadas y exigir trazabilidad:

```text
HU/TT → AT → OP → BC → CM → EV → PL/RN
```

Permitir que `specter` genere historias y tareas; Event Storming solo aporta el modelo y las fases de
capacidad.

### Hacia `epicureo`

Devolver necesidades o hotspots que requieran aclaración formal, métricas de éxito, alcance o decisión
de stakeholders. Incorporar después la respuesta sin renumerar el modelo.

## Gotchas

- **No modelar soluciones durante Big Picture.** Primero descubrir hechos; diseñar mejoras después.
- **No mezclar AS-IS con TO-BE.** Etiquetar claramente eventos nuevos, modificados y retirados.
- **No presentar inferencias como decisiones del negocio.** Marcar fuente, supuesto y estado.
- **No crear un agregado por entidad.** Usar invariantes y consistencia como criterio.
- **No convertir bounded contexts en microservicios.** Esa decisión pertenece a arquitectura.
- **No esconder preguntas abiertas en notas dispersas.** Consolidarlas en `ES-013`.
- **No sobrescribir modelos existentes.** Reconciliar y conservar IDs y ediciones manuales.
- **No confundir EventStorming con sus documentos.** La conversación y el aprendizaje compartido son
  el resultado principal; los archivos son harvesting posterior.
- **No ejecutar todos los formatos por rutina.** Elegir la receta mínima que resuelva el objetivo.

## Referencias

- Leer `references/format-profiles.md` después de determinar formato y antes de planificar la sesión.
- Leer `references/artifact-contract.md` antes del harvesting o validación de archivos `ES-*`.
- Leer `references/facilitation-guide.md` al conducir un taller o una ronda de validación con expertos.

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "storming", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill storming --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
