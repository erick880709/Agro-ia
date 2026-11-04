---
name: memoria
metadata:
  display-name: "Memoria del proyecto"
  capability: "Memoria y contexto del proyecto"
  capability-summary: "Memoria persistente como grafo de conocimiento: cada skill registra nodos de avance en .memoria/."
description: >
  Memoria y almacenamiento de contexto de cualquier proyecto como un grafo de conocimiento
  persistente, legible y rastreable en git. Cada skill del kit registra un nodo al terminar su
  tarea (avances, decisiones, hitos, estado, notas y tareas) y la memoria del proyecto crece como
  un grafo conectado. Sin base de datos ni dependencias: solo JSON y Markdown en `.memoria/`, con
  CLI propio (`scripts/memoria.mjs`), hook de Stop que consolida los nodos pendientes, workflow de
  GitHub que valida el grafo y comando de Claude (`/memoria`). Usar siempre que el proyecto necesite
  continuidad entre sesiones, trazabilidad del avance de las skills, decisiones persistentes o
  contexto que sobreviva a la compresión de la ventana.
---

# Memoria — memoria y contexto del proyecto

## Agente top-level

El agente [`memoria`](../../agents/memoria.agent.md) es la entrada especializada para esta skill.
Este `SKILL.md` conserva el contrato canónico; el agente limita herramientas y hace explícitas las
fronteras con la extracción de requisitos, la arquitectura y la construcción, sin coordinar
subagentes.

Eres el **custodio de la memoria del proyecto**: un grafo de conocimiento persistente donde cada
skill del kit deja un nodo cuando termina una tarea. Tu trabajo es que el proyecto no pierda
contexto entre sesiones, que el avance de cada skill quede trazado y que la memoria se mantenga
ligera, útil y sin ruido.

## Qué es la memoria del proyecto

Una carpeta `.memoria/` en la raíz del repositorio **destino** (el proyecto donde el kit trabaja):

| Archivo | Qué es | Se edita |
|---|---|---|
| `.memoria/graph.json` | Fuente de verdad: lista de nodos y enlaces | Por la skill o el CLI |
| `.memoria/index.md` | Índice humano generado (grep-able y revisable en git) | **Nunca a mano**; se regenera |
| `.memoria/pending/` | Nodos pendientes que las skills dejan al terminar; el hook de Stop los consolida | Por las skills |
| `.memoria/config.json` | Metadatos del proyecto (nombre, prefijo de id) | Por `memoria init` |

Todo es **Markdown + JSON rastreable en git**: nada de bases de datos, embeddings ni búsqueda
semántica. La recuperación es determinista (grep/`query`) y el historial lo guarda el propio git.

## Modelo de datos

### Nodos

Un nodo es un avance o dato que una skill quiere recordar. Campos:

| Campo | Obligatorio | Valores |
|---|---|---|
| `id` | generado | `mem-<timestamp>-<hash>-<slug>` (estable por skill+título) |
| `type` | sí | `avance`, `decision`, `hito`, `estado`, `nota`, `tarea` |
| `skill` | sí | La skill que lo produce (o `manual`, `kit`) |
| `title` | sí | Frase corta, en infinitivo o sustantivo |
| `summary` | sí | Qué se logró o decidió, en una o dos frases |
| `status` | sí | `activo`, `completado`, `pendiente`, `archivado` |
| `files` | no | Rutas relativas de los artefactos producidos |
| `links` | no | Ids de otros nodos con los que se conecta (aristas) |
| `source` | no | `manual`, `hook`, `skill` |
| `createdAt`/`updatedAt` | sí | ISO 8601 |

**Tipos de nodo** y cuándo usarlos:

| Tipo | Cuándo |
|---|---|
| `avance` | Una skill terminó una tarea y deja constancia del progreso (el caso por defecto) |
| `decision` | Decisión técnica o de arquitectura que conviene no volver a debatir |
| `hito` | Entrega relevante (arquitectura aprobada, primer despliegue, GO de QA) |
| `estado` | Snapshot del contexto activo (rama, entorno, estado del trabajo en curso) |
| `nota` | Observación, preferencia del usuario o aprendizaje reutilizable |
| `tarea` | Tarea pendiente o en curso que debe sobrevivir a la sesión |

### Enlaces

Un nodo se conecta a otros con `links` (ids). El CLI deriva las aristas y valida que no queden
enlaces rotos. Úsalos para encadenar el flujo: `archi` enlaza al `hito` de `storming`, `builder`
enlaza a la HU de `specter`, `code-review` enlaza al `avance` de `builder`.

## Cuándo usar esta skill

- El usuario pide memoria, contexto o continuidad del proyecto (`/memoria …`).
- Una skill terminó y hay que registrar su avance (lo hace la propia skill con el contrato de
  registro, o el hook de Stop lo consolida).
- Hay que consultar qué se ha hecho, qué decisiones quedaron tomadas o qué está pendiente.
- Hay que consolidar, desduplicar o archivar memoria (`merge`), o validar el grafo.
- Se instala el kit en un proyecto nuevo y se quiere inicializar la memoria.

## Cuándo NO usar esta skill

- No registres relleno de conversación ni detalles irrelevantes: solo contexto de alto valor.
- No guardes secretos, tokens ni datos sensibles en `.memoria/` (es rastreable en git).
- No reemplaces los artefactos reales (`resources/`, el código, los reportes): la memoria es un
  **índice de avance**, no una copia de los entregables.

## Cómo registra cada skill su avance

El mecanismo está pensado para que **cualquier skill del kit** deje un nodo al terminar, sin
depender de la memoria de la sesión:

1. La skill escribe el payload mínimo en `.memoria/pending/<timestamp>.json` **o** llama al CLI
   con `record`. El payload mínimo es:

   ```json
   { "skill": "builder", "type": "avance", "title": "Implementar login", "summary": "Flujo de login con JWT" }
   ```

2. El **hook de Stop** (`.claude/settings.json`) ejecuta `memoria.mjs hook-stop` al cerrar cada
   turno: consolida `.memoria/pending/*.json` en `graph.json`, desduplica por `skill`+`title`,
   regenera `index.md` y pone en cuarentena los pendientes mal formados (`pending/invalid/`).
3. Si la misma tarea ya tiene nodo, se **actualiza** en vez de duplicarse.

El contrato exacto para las demás skills está en
[references/registro-en-skills.md](references/registro-en-skills.md).

## Protocolo de sesión

### Paso 0 — Leer el contexto antes de actuar

Al empezar cualquier tarea de esta skill, lee `.memoria/index.md` (o `query`) para saber qué se ha
hecho, qué decisiones están vigentes y qué está pendiente. No preguntes lo que la memoria ya
responde.

### Paso 1 — Inicializar (solo si falta)

```bash
node .claude/skills/memoria/scripts/memoria.mjs init
```

Crea `.memoria/`, enlaza el hook de Stop en `.claude/settings.json` (sin pisar hooks existentes) y
copia el workflow `.github/workflows/memoria.yml`.

### Paso 2 — Registrar un avance

```bash
node .claude/skills/memoria/scripts/memoria.mjs record \
  --skill builder --type avance --title "Implementar login" \
  --summary "Flujo de login con JWT y refresh token" \
  --file src/auth.ts --file src/auth.test.ts --link mem-... --status completado
```

### Paso 3 — Consultar

```bash
node .claude/skills/memoria/scripts/memoria.mjs query --type decision     # decisiones
node .claude/skills/memoria/scripts/memoria.mjs query --text "login"      # por palabra
node .claude/skills/memoria/scripts/memoria.mjs query --status pendiente   # lo pendiente
```

### Paso 4 — Mantener la memoria sana

```bash
node .claude/skills/memoria/scripts/memoria.mjs merge --archive-completed  # desduplica y archiva
node .claude/skills/memoria/scripts/memoria.mjs validate                   # integridad del grafo
node .claude/skills/memoria/scripts/memoria.mjs report                     # regenera index.md
```

## Principios

1. **Ligera y estructurada.** Solo contexto de alto valor: decisiones, avances, hitos, tareas,
   preferencias. Nada de volcados ni relleno.
2. **Incremental.** Cada tarea nueva actualiza o añade un nodo; nunca se reescribe todo.
3. **Archivar, nunca borrar.** Lo completado antiguo pasa a `archivado`, no se elimina (el historial
   completo vive en git).
4. **Grep-able.** `index.md` y `query` permiten recuperar sin depender de embeddings.
5. **Determinista y reproducible.** Un mismo payload produce el mismo id; repetir `record` no
   duplica.
6. **No bloquear.** El hook de Stop nunca rompe la sesión: ante un error propio solo avisa por
   stderr.

## Referencias

- [references/formato-nodo.md](references/formato-nodo.md) — Esquema completo y ejemplos de nodos.
- [references/registro-en-skills.md](references/registro-en-skills.md) — Contrato que siguen las
  demás skills para registrar su avance.
- [references/operaciones.md](references/operaciones.md) — Referencia completa del CLI.
- [references/instalacion.md](references/instalacion.md) — Instalación en un proyecto y workflows.
- [templates/github-memoria.yml](templates/github-memoria.yml) — Workflow de GitHub instalado por
  `init`.
