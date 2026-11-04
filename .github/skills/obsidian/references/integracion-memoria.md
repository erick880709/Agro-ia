# Integración `.memoria/` ↔ Obsidian

Cómo proyecta la skill el grafo de conocimiento de `memoria` (`.memoria/graph.json`) a un vault de
Obsidian y a un JSON Canvas. El comando determinista es:

```bash
node .claude/skills/obsidian/scripts/obsidian.mjs export [--root <proyecto>] [--out <carpeta-vault>]
```

## Fuente de verdad

`memoria` almacena el grafo con el esquema `memoria/v1`:

```json
{
  "schema": "memoria/v1",
  "updatedAt": "2026-11-02T15:00:00.000Z",
  "nodes": [],
  "edges": []
}
```

Cada nodo tiene `id`, `type` (`avance`|`decision`|`hito`|`estado`|`nota`|`tarea`), `skill`, `title`,
`summary`, `status`, `files`, `links`, `createdAt`, `updatedAt`. Las `edges` se derivan de `links`
(`{from, to, type: "relacionado"}`). Detalle: `.claude/skills/memoria/references/formato-nodo.md`.

## Qué genera `export`

| Salida | Ruta | Contenido |
|---|---|---|
| Mapa de Contenido | `<out>/Inicio.md` | Índice por tipo con `[[wikilinks]]` a cada nota |
| Notas | `<out>/notas/<id>.md` | Una nota por nodo: frontmatter + resumen + archivos + relacionadas |
| Canvas | `<out>/Memoria.canvas` | Nodos `file` (uno por nota) coloreados por tipo + aristas del grafo |

### Nota por nodo

- Frontmatter: `title`, `tags` (`[memoria, <type>, <skill>, <status>]`), `type`, `skill`, `status`, `created`.
- Cuerpo: callout de cabecera con tipo/estado, resumen, lista de archivos y enlaces `[[...]]` a
  los nodos relacionados (ids de `links`).
- El nombre de archivo es `notas/<id>.md`: `id` es único y estable, lo que hace los enlaces
  inmunes a renombrados.

### Canvas

- Cada nodo es de tipo `file` apuntando a `notas/<id>.md`; el lienzo muestra una vista previa de la nota.
- Color por tipo: `avance`→`"5"`, `decision`→`"6"`, `hito`→`"2"`, `estado`→`"3"`, `nota`→`"1"`,
  `tarea`→`"4"` (y `"1"` por defecto).
- Aristas desde `graph.edges` (o derivadas de `links` si `edges` falta), con `toEnd: "arrow"` y
  `label` igual al tipo de relación.
- Layout en cuadrícula determinista (4 columnas), para que el grafo sea estable entre ejecuciones.

## Flujo en Obsidian

1. `export` escribe en `<out>` (por defecto `<root>/obsidian/`).
2. El usuario abre esa carpeta como vault (`Abrir carpeta como vault`).
3. Abre `Memoria.canvas` o la vista de grafo para ver las conexiones.
4. La skill deja el nodo de avance correspondiente en `.memoria/`.

## Relación con `graphify`

La skill `graphify` (si está disponible en el entorno) puede enriquecer el grafo o proponer
conexiones semánticas. El `export` de esta skill es la proyección **determinista** (sin proveedor de
IA) de `.memoria/` a Obsidian: úsalo como referencia y deja que `graphify` aporte solo lo adicional.
No exijas `graphify` para que el flujo funcione.
