# Formato de nodo

Referencia del esquema de `.memoria/graph.json` y de los payloads que acepta `record` y el hook de
Stop. La fuente de verdad es el grafo; este documento aclara los campos y muestra ejemplos.

## Esquema del grafo

```json
{
  "schema": "memoria/v1",
  "updatedAt": "2026-11-02T15:00:00.000Z",
  "nodes": [],
  "edges": []
}
```

`edges` se deriva de `links`: cada nodo con `links: ["<id>"]` genera una arista
`{ "from": "<id-propio>", "to": "<id>", "type": "relacionado" }` hacia un nodo existente. Los
enlaces a ids inexistentes se descartan (no dejan aristas rotas).

## Nodo

```json
{
  "id": "mem-20261102-a1b2c3-builder-implementar-login",
  "type": "avance",
  "status": "completado",
  "skill": "builder",
  "title": "Implementar login",
  "summary": "Flujo de login con JWT y refresh token, con pruebas.",
  "files": ["src/auth.ts", "src/auth.test.ts"],
  "links": ["mem-20261101-abc123-specter-hu-01"],
  "source": "skill",
  "createdAt": "2026-11-02T15:00:00.000Z",
  "updatedAt": "2026-11-02T15:05:00.000Z"
}
```

## Campos

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `id` | string | auto | `mem-<yyyyMMddHHmmss>-<hash6>-<slug>`; estable por `skill`+`title` |
| `type` | string | sí | `avance` \| `decision` \| `hito` \| `estado` \| `nota` \| `tarea` |
| `skill` | string | sí | nombre de la skill (o `manual`, `kit`) |
| `title` | string | sí | corto; clave de desduplicación junto con `skill` |
| `summary` | string | sí | qué se logró/decidió; 1–2 frases |
| `status` | string | sí | `activo` \| `completado` \| `pendiente` \| `archivado` |
| `files` | string[] | no | rutas relativas al proyecto; si no existen se guardan tal cual |
| `links` | string[] | no | ids de nodos a conectar |
| `source` | string | no | `manual` \| `hook` \| `skill` (default `manual`) |
| `createdAt` | ISO | auto | se rellena si falta |
| `updatedAt` | ISO | auto | se actualiza en cada `record`/promoción |

## Reglas de validación (`validate`)

- `type` y `status` dentro de sus conjuntos.
- `skill`, `title` y `summary` no vacíos.
- `files` y `links`, si existen, arrays de strings.
- `id` único en el grafo.
- Ningún `links` apunta a un id inexistente (enlaces rotos).

Un payload que viola una regla se rechaza; en el hook de Stop pasa a cuarentena
(`.memoria/pending/invalid/`) y no bloquea la sesión.

## Ejemplos por tipo

```json
{ "type": "decision", "skill": "archi", "title": "Persistencia en PostgreSQL",
  "summary": "Se elige PostgreSQL sobre MongoDB por transacciones y reportes.", "links": ["mem-...-storming-modelo"] }

{ "type": "hito", "skill": "archi", "title": "Arquitectura aprobada",
  "summary": "Documento de arquitectura aprobado por el comité." }

{ "type": "estado", "skill": "kit", "title": "Rama y entorno activos",
  "summary": "Trabajo en feat/pagos contra entorno non-prod." }

{ "type": "nota", "skill": "manual", "title": "Preferencia del usuario",
  "summary": "El equipo usa pnpm, no npm." }

{ "type": "tarea", "skill": "code-review", "title": "Corregir hallazgos de revisión",
  "summary": "Quedan 3 hallazgos HIGH por corregir antes del merge.", "status": "pendiente" }
```
