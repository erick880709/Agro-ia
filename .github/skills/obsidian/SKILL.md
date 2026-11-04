---
name: obsidian
metadata:
  display-name: "Obsidian"
  capability: "Obsidian y grafo visual del proyecto"
  capability-summary: "Obsidian: notas con wikilinks, JSON Canvas y MCP; exporta .memoria/ como grafo visual."
description: >
  Puente del kit hacia Obsidian: leer y escribir notas con Obsidian Flavored Markdown (wikilinks,
  embeds, callouts, properties), crear y editar JSON Canvas (.canvas) y, sobre todo, exportar la
  memoria del proyecto (.memoria/) como un vault navegable y un grafo visual (Canvas + Graph view).
  Siempre guía o configura el MCP de Obsidian antes de operar, y se apoya en las skills `memoria`
  (grafo de conocimiento) y `graphify` (grafo visual) sin duplicarlas. Usar cuando se pida trabajar
  con un vault de Obsidian, crear mapas visuales del proyecto, conectar la memoria del kit con
  Obsidian o configurar el MCP de Obsidian para el agente.
---

# Obsidian — puente al vault y grafo visual del proyecto

## Agente top-level

Esta skill no tiene agente propio: la invoca el agente general o cualquier skill del kit que
necesite leer/escribir en un vault de Obsidian o materializar la memoria como grafo visual. Su
contrato es este `SKILL.md`; los detalles de sintaxis y de MCP están en [references/](references/).

## Regla principal: SIEMPRE guía o configura el MCP

Antes de operar sobre un vault, sigue este orden **obligatorio**:

1. **Detecta** si ya hay un MCP de Obsidian configurado (`claude mcp list`, o un bloque `obsidian`
   en `.mcp.json` del proyecto). No des por hecho que funciona: pídele al usuario abrir Obsidian
   con el plugin Local REST API activo si el MCP lo requiere.
2. **Si falta**, propone al usuario configurarlo y aplica la guía
   [mcp-configuracion.md](references/mcp-configuracion.md). Solo necesitas pedirle la API key del
   plugin Local REST API (host y puerto tienen valores por defecto). Nunca inventes credenciales.
3. **Si el usuario no quiere MCP**, usa la ruta sin MCP (Obsidian CLI) documentada en la misma
   guía y deja claro qué operaciones no estarán disponibles.

No leas ni escribas archivos del vault con herramientas genéricas sin haber pasado por este paso:
el MCP (o el CLI) es la vía canónica para operar sobre un vault abierto en Obsidian.

## Cuándo usar esta skill

- El usuario pide exportar la memoria del proyecto a Obsidian o verla como grafo visual.
- El usuario pide crear/editar notas con sintaxis de Obsidian (wikilinks, callouts, properties, embeds).
- El usuario pide un mapa visual, mind map o flujo en un `.canvas`.
- El usuario pide conectar el kit con su vault de Obsidian (configurar MCP o CLI).
- Otra skill del kit (memoria, archi, storming, takumi) necesita materializar un grafo o notas en Obsidian.

## Flujo de trabajo

### 1. Exportar la memoria como vault + grafo visual

`memoria` mantiene el grafo de conocimiento en `.memoria/graph.json`. Esta skill lo convierte en un
vault navegable y en un Canvas:

```bash
node .claude/skills/obsidian/scripts/obsidian.mjs export [--root <proyecto>] [--out <carpeta-vault>]
```

- Sin `--out`, escribe en `<root>/obsidian/`.
- Genera `Inicio.md` (Mapa de Contenido), una nota `.md` por nodo con wikilinks, y `Memoria.canvas`
  con los nodos coloreados por tipo y las aristas del grafo.
- Detalles de la correspondencia `.memoria/` ↔ Obsidian: [integracion-memoria.md](references/integracion-memoria.md).

Luego guía al usuario: abrir esa carpeta como vault en Obsidian (`Abrir carpeta como vault`) y
activar la vista de grafo. Si la skill `graphify` está disponible, puedes usarla para enriquecer o
comparar el grafo; el Canvas que genera `export` es el artefacto determinista de referencia.

### 2. Crear o editar notas con Obsidian Flavored Markdown

Usa la sintaxis de [obsidian-markdown.md](references/obsidian-markdown.md). Reglas de oro:

- `[[wikilink]]` para notas internas del vault; `[texto](url)` solo para enlaces externos.
- Frontmatter (properties) al inicio con `title`, `tags`, `aliases`, `status` según corresponda.
- Callouts `> [!tipo]` para resaltar; embeds `![[...]]` para incrustar notas/imágenes/PDF.
- Verifica que la nota renderice en la vista de lectura antes de darla por terminada.

### 3. Crear o editar un JSON Canvas

Sigue [json-canvas.md](references/json-canvas.md) para `.canvas` (nodos, aristas, grupos, colores).
Valida siempre antes de entregar:

```bash
node .claude/skills/obsidian/scripts/obsidian.mjs validate-canvas <archivo.canvas>
```

## Referencias

| Archivo | Contenido |
|---|---|
| [references/mcp-configuracion.md](references/mcp-configuracion.md) | Configuración del MCP (uvx/npm) y ruta sin MCP (Obsidian CLI) |
| [references/obsidian-markdown.md](references/obsidian-markdown.md) | Sintaxis Obsidian Flavored Markdown (wikilinks, embeds, callouts, properties, tags) |
| [references/json-canvas.md](references/json-canvas.md) | Especificación JSON Canvas 1.0 y reglas de validación |
| [references/integracion-memoria.md](references/integracion-memoria.md) | Correspondencia `.memoria/graph.json` ↔ vault + Canvas |

## Fronteras con otras skills

- **`memoria`** es la dueña del grafo de conocimiento; esta skill solo lo lee y lo proyecta a
  Obsidian. No inventes nodos de memoria aquí.
- **`graphify`** (si está disponible) enriquece o visualiza grafos; el Canvas de esta skill es la
  salida determinista que no depende de proveedores de IA.
- **`docx`/`pdf`/`pptx`/`xlsx`** siguen siendo las rutas para documentos de oficina; Obsidian es
  para notas y grafo, no para reemplazarlas.

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "obsidian", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill obsidian --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
