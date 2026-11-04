# 05 — Filtros (`--filter`) y ejecución por cambios de Git

Contenido: sintaxis completa del lenguaje de filtros, expresiones de Git, destroys de huérfanos, `.terragrunt-filters`, equivalencias con flags legados y recetas de CI.

Comandos que aceptan `--filter`: `find`, `list`, `run`, `hcl fmt` (solo rutas de archivos), `hcl validate`, `stack run`, `stack generate` (solo expresiones que apunten a `type=stack`), `dag graph`. **Ensaya siempre con `find`/`list` antes de `run`.**

## 1. Tipos de expresión

| Tipo | Sintaxis | Ejemplo |
|---|---|---|
| Nombre (basename) | `nombre`, glob, o `name=` | `app*`, `name=vpc` |
| Ruta | empieza por `./`, `/` o contiene glob de ruta | `./prod/**`, `./live/us-east-1/*` |
| Atributo | `type=unit\|stack`, `external=true`, `reading=<archivo>`, `source=<glob>` | `reading=shared.hcl`, `source=*//modules/rds*` |
| Negación | `!expr` | `!./test/**` |
| Intersección | `expr \| expr` (en el mismo `--filter`) | `./prod/** \| type=unit \| !name=legacy` |
| Unión | varios `--filter` | `--filter app1 --filter app2` |
| Grafo | `expr...` (dependencias), `...expr` (dependientes), `...expr...` (ambos), `^` excluye el objetivo, profundidad `1...vpc`, `service...2` | `...^vpc` |
| Frontera | `(dir)...expr` limita el descubrimiento | `(./live/staging)...[main...HEAD]` |
| Git | `[ref1...ref2]`, `[ref]` (= `[ref...HEAD]`) | `[origin/main...HEAD]`, `[HEAD~1...HEAD]`, `[v1.0.0...v2.0.0]` |
| Externos | `{./**}...` | incluye dependencias fuera del árbol |

## 2. Expresiones de Git: cómo funcionan

1. Terragrunt crea un **worktree temporal por referencia** y compara con `git diff`.
2. Units/stacks **agregados o modificados** → se ejecutan en el worktree "to" (HEAD) con `plan`/`apply`.
3. Units **eliminados** (o que un stack dejó de generar: `terragrunt.stack.hcl` borrado, expansión reducida, archivo leído por el stack modificado) → se ejecutan con `plan -destroy`/`apply -destroy` en el worktree "from".
4. Los destroys **solo** ocurren con `--filter-allow-destroy`. Sin él, los huérfanos se omiten.
5. Con `run`, solo se permiten `plan` y `apply` (sin `-destroy` manual): Terragrunt decide la dirección.
6. Las rutas combinadas con Git se resuelven **desde la raíz del worktree**, no desde el cwd: `[main...HEAD] | ./live/prod/**`.
7. **Requiere estado remoto**: con estado local los worktrees no ven el estado y se usarían mocks.
8. Cambios fuera del repo (env vars que alteran una expansión, values externos) no se detectan: destruir manualmente.
9. Los cambios en archivos leídos (`read_terragrunt_config`, `file`, `mark_as_read`, `mark_glob_as_read`) también seleccionan a los units que los leen — por eso modificar `account.hcl` o `root.hcl` dispara muchos units. Es correcto: cambian su configuración efectiva.

`--filter-affected` = `[<rama por defecto>...HEAD]` con detección automática de la rama default.

## 3. Recetas

```bash
# ¿Qué cambió en este PR?
terragrunt find --filter '[origin/main...HEAD]' --dag

# Plan solo de lo afectado (PR)
terragrunt run --all --non-interactive --filter '[origin/main...HEAD]' -- plan

# Apply post-merge de lo que entró con el último merge commit, incluyendo destroys
terragrunt run --all --non-interactive --filter '[HEAD^...HEAD]' --filter-allow-destroy -- apply

# Monorepo con catálogo: limita el descubrimiento a live con una frontera inline (VERIFICADO en v1.2.1)
terragrunt run --all --filter '(./live)...[origin/main...HEAD]' -- plan

# Solo prod, solo units
terragrunt run --all --filter './prod/** | type=unit' -- plan

# Todo lo que lee un archivo compartido
terragrunt find --filter 'reading=_envcommon/mysql.hcl'

# Un servicio y sus dependencias directas
terragrunt run --all --filter 'service...1' -- plan
```

Granularidad observada (v1.2.1): si en un `terragrunt.stack.hcl` solo cambian los `values` de un unit, se selecciona el stack y **solo ese unit** generado, no todos los del stack.

### Trampa verificada: catálogo dentro del mismo repo

Cuando el diff modifica un `terragrunt.stack.hcl`, Terragrunt **genera los stacks en ambos worktrees** y, en v1.2.1, también intenta generar los stacks del catálogo (`catalog/stacks/*`), que fallan con `There is no variable named "values"`. Ni `.terragrunt-filters` con `!./catalog/**` ni `--discovery-boundary` lo evitaron en las pruebas; **sí** lo evita la frontera inline:

```bash
terragrunt run --all --filter '(./live)...[origin/main...HEAD]' -- plan
```

Alternativas: catálogo en repo separado (recomendación Gruntwork) o ejecutar desde un checkout que no contenga el catálogo. Los deletes de stacks completos no disparan este problema (no hay regeneración en ambos lados).

En CI asegúrate de tener historial suficiente: `actions/checkout` con `fetch-depth: 0` (o al menos la base del PR) y la rama base disponible como `origin/main`.

## 4. `.terragrunt-filters`

Archivo en la raíz del repo, una expresión por línea, se aplica a todos los comandos (y dentro de cada worktree Git). Desactivar con `--no-filters-file`; ruta alternativa con `--filters-file`.

```text
# .terragrunt-filters
!./catalog/**
!./examples/**
!./sandbox/**
```

Imprescindible en monorepos con catálogo: los units de catálogo leen `values` y fallan si se ejecutan solos.

## 5. Equivalencias con flags legados

| Legado | Filtro |
|---|---|
| `--queue-include-dir=./x` | `--filter './x'` |
| `--queue-exclude-dir=./x` | `--filter '!./x'` |
| `--queue-include-external` | `--filter '{./**}...'` |
| `--queue-include-units-reading=f` / `--units-that-include=f` | `--filter 'reading=f'` |
| `--queue-exclude-external`, `--queue-strict-include` | comportamiento por defecto (ya no hacen falta) |

## 6. Del "git diff + script" al filtro nativo

El patrón antiguo (popularizado en artículos de 2023-2024) era: `git diff --name-only origin/main...HEAD` → subir directorios hasta encontrar `terragrunt.hcl` → pasar cada uno con `--terragrunt-include-dir` → manejar a mano los borrados. Problemas: no detecta archivos leídos indirectamente, no maneja destroys de units eliminados ni de stacks generados, y se rompe con stacks explícitos.

Reemplázalo por `--filter '[origin/main...HEAD]'` (o `--filter-affected`) + `--filter-allow-destroy` controlado por aprobación. Mantén el script solo si usas una versión < 1.0 que no puedas actualizar.
