# Operaciones del CLI

Referencia completa de `scripts/memoria.mjs`. Todas las invocaciones aceptan `--root <dir>` para
actuar sobre un proyecto distinto del directorio de trabajo; si se omite, se usa el directorio
actual. `--help` muestra la ayuda.

```bash
node .claude/skills/memoria/scripts/memoria.mjs <comando> [opciones]
```

## `init`

Prepara `.memoria/` en el proyecto: crea `graph.json` vacío, `index.md`, `pending/` y
`config.json`; enlaza el hook de Stop en `.claude/settings.json` (sin pisar hooks existentes) y
copia el workflow `.github/workflows/memoria.yml` si no existe. Es **idempotente**.

```bash
node .claude/skills/memoria/scripts/memoria.mjs init [--root <dir>]
```

## `record`

Crea o actualiza un nodo. Si existe un nodo con el mismo `skill` + `title` (o el mismo `--id`), lo
actualiza; con `--new` fuerza uno nuevo aunque coincida el título.

```bash
node .claude/skills/memoria/scripts/memoria.mjs record \
  --skill <skill> --type <tipo> --title "<título>" --summary "<resumen>" \
  [--status <estado>] [--file <ruta>]... [--link <id>]... [--id <id>] [--new] [--root <dir>]
```

También acepta el payload por stdin (JSON):

```bash
echo '{"skill":"archi","type":"hito","title":"Arquitectura aprobada","summary":"Aprobada"}' \
  | node .claude/skills/memoria/scripts/memoria.mjs record
```

## `query`

Lista nodos con filtros combinables. Sin `--json`, imprime una línea por nodo
(`id  type  status  skill  title`).

```bash
node .claude/skills/memoria/scripts/memoria.mjs query \
  [--type <tipo>] [--skill <skill>] [--status <estado>] [--text <palabra>] [--limit <n>] [--json]
```

## `report`

Regenera `.memoria/index.md` desde `graph.json` y muestra el conteo por tipo.

```bash
node .claude/skills/memoria/scripts/memoria.mjs report [--root <dir>]
```

## `merge`

Consolida nodos duplicados (mismo `skill` + `title`, conservando el más reciente y fusionando
`files`/`links`). Con `--archive-completed`, marca `archivado` los nodos `completado` con más de
`--days` días (30 por defecto).

```bash
node .claude/skills/memoria/scripts/memoria.mjs merge [--archive-completed] [--days <n>]
```

## `validate`

Valida el esquema y la integridad del grafo (tipos, estados, campos obligatorios, ids únicos,
enlaces no rotos). Sale con código distinto de 0 si hay errores.

```bash
node .claude/skills/memoria/scripts/memoria.mjs validate [--root <dir>]
```

## `promote` y `hook-stop`

Consolidan `.memoria/pending/*.json` en el grafo y regeneran `index.md`. `hook-stop` está pensado
para el hook de Stop: nunca bloquea la sesión y mueve los pendientes mal formados a
`pending/invalid/`. `promote` es la versión manual.

```bash
node .claude/skills/memoria/scripts/memoria.mjs promote    # manual
node .claude/skills/memoria/scripts/memoria.mjs hook-stop  # hook de Stop
```

## Comando de Claude (`/memoria`)

El comando `.claude/commands/memoria.md` expone las operaciones más frecuentes en lenguaje natural:
inicializar, registrar, consultar, reportar, consolidar y validar la memoria.
