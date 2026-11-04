# 09 — Migración de Terragrunt 0.x a 1.x

Contenido: plan de migración por fases, tablas de equivalencias (comandos, flags, env vars, HCL), y migración de `_envcommon` a stacks. Ejecuta `scripts/tg_lint.py` para encontrar automáticamente casi todo lo de este documento.

## Fase 0 — Preparación

1. Inventario: `grep -rn "run-all\|--terragrunt-\|TERRAGRUNT_" .github/ pipelines/ scripts/ Makefile` y `python scripts/tg_lint.py .`
2. Pinea la versión actual en `mise.toml` y asegúrate de que `plan` está limpio (sin drift) en todos los ambientes antes de empezar.
3. Prueba en la versión vieja con `--strict-mode` (≥ 0.77) para convertir deprecaciones en errores y ver qué rompe.

## Fase 1 — Cambios sin impacto en estado (un PR)

### Comandos

| 0.x | 1.x |
|---|---|
| `terragrunt run-all plan` | `terragrunt run --all -- plan` |
| `plan-all` / `apply-all` / `destroy-all` / `output-all` / `validate-all` | `run --all -- <cmd>` |
| `terragrunt graph apply` | `terragrunt run --graph -- apply` |
| `terragrunt hclfmt` | `terragrunt hcl fmt` |
| `terragrunt hclvalidate` | `terragrunt hcl validate` |
| `terragrunt validate-inputs` | `terragrunt hcl validate --inputs` |
| `terragrunt render-json` | `terragrunt render --json -w` (o `--format json --write`) |
| `terragrunt terragrunt-info` | `terragrunt info print` |
| `terragrunt graph-dependencies` | `terragrunt dag graph` |
| `terragrunt workspace …` / comandos sin atajo | `terragrunt run -- workspace …` |
| creación implícita del bucket | `--backend-bootstrap` / `terragrunt backend bootstrap` |

### Flags (se elimina el prefijo `--terragrunt-`)

| 0.x | 1.x |
|---|---|
| `--terragrunt-non-interactive` | `--non-interactive` |
| `--terragrunt-working-dir` | `--working-dir` |
| `--terragrunt-source` / `-source-map` / `-source-update` | `--source` / `--source-map` / `--source-update` |
| `--terragrunt-tfpath` | `--tf-path` |
| `--terragrunt-parallelism` | `--parallelism` |
| `--terragrunt-include-dir` | `--filter './dir'` (alias `--queue-include-dir`) |
| `--terragrunt-exclude-dir` | `--filter '!./dir'` (alias `--queue-exclude-dir`) |
| `--terragrunt-excludes-file` | `--queue-excludes-file` → mejor `.terragrunt-filters` |
| `--terragrunt-include-external-dependencies` | `--filter '{./**}...'` |
| `--terragrunt-ignore-external-dependencies`, `--terragrunt-strict-include` | por defecto (eliminar) |
| `--terragrunt-modules-that-include f` / `--queue-include-units-reading f` | `--filter 'reading=f'` |
| `--terragrunt-ignore-dependency-errors` | `--queue-ignore-errors` |
| `--terragrunt-ignore-dependency-order` | `--queue-ignore-dag-order` |
| `--terragrunt-iam-role` | `--iam-assume-role` |
| `--terragrunt-iam-web-identity-token` | `--iam-assume-role-web-identity-token` |
| `--terragrunt-debug` | `--inputs-debug` |
| `--terragrunt-log-level` / `-log-format` / `-no-color` | `--log-level` / `--log-format` / `--no-color` |
| `--terragrunt-forward-tf-stdout` | `--tf-forward-stdout` |
| `--terragrunt-fetch-dependency-output-from-state` | por defecto (`--dependency-fetch-output-from-state`) |
| `--terragrunt-provider-cache` (+ `-dir`, `-hostname`, …) | `--provider-cache` (+ `--provider-cache-dir`, …) |
| `--terragrunt-hclfmt-file` / `-exclude-dir` / `-stdin` | `hcl fmt --file` / `--exclude-dir` / `--stdin` |
| `--terragrunt-check` / `--terragrunt-diff` | `--check` / `--diff` |
| `--terragrunt-no-auto-init` / `-no-auto-retry` / `-no-auto-approve` | `--no-auto-init` / `--no-auto-retry` / `--no-auto-approve` |
| `--terragrunt-fail-on-state-bucket-creation` | eliminado (bootstrap es explícito) |

### Variables de entorno

`TERRAGRUNT_<X>` → `TG_<X>` (p. ej. `TERRAGRUNT_NON_INTERACTIVE` → `TG_NON_INTERACTIVE`, `TERRAGRUNT_TFPATH` → `TG_TF_PATH`, `TERRAGRUNT_PARALLELISM` → `TG_PARALLELISM`). Excepción notable: `TERRAGRUNT_DEBUG` → `TG_INPUTS_DEBUG`. Revisa CI, `.envrc`, Makefiles y Dockerfiles.

### GitHub Actions

- `the-commons-project/terragrunt-github-actions` → `gruntwork-io/terragrunt-action@v3` + `mise.toml`.
- `gruntwork-io/terragrunt-action@v1/v2` con `tg_command: 'run-all plan'` → `@v3` con `tg_command: 'run --all plan'`.

## Fase 2 — Cambios HCL (sin cambiar claves de estado)

| Antes | Después |
|---|---|
| raíz `terragrunt.hcl` | `root.hcl` |
| `include { path = find_in_parent_folders() }` | `include "root" { path = find_in_parent_folders("root.hcl") }` |
| `skip = true` | `exclude { if = true, actions = ["all"] }` |
| `retryable_errors = [...]`, `retry_max_attempts`, `retry_sleep_interval_sec` | `errors { retry "x" { retryable_errors = [...], max_attempts = N, sleep_interval_sec = S } }` |
| `dependency { config_path = "../x/terragrunt.hcl" }` | `config_path = "../x"` |
| `mock_outputs_merge_with_state = true` | `mock_outputs_merge_strategy_with_state = "shallow"` |
| `dynamodb_table` en S3 | `use_lockfile = true` (con OpenTofu/Terraform ≥ 1.10; puedes tener ambos durante la transición) |
| `TF_PLUGIN_CACHE_DIR` manual en CI | quitar (auto provider cache / `--provider-cache`) |
| dos `dependency` con la misma etiqueta | renombrar (strict control `duplicate-dependency-labels`) |

**Cuidado con el renombre de la raíz:** `path_relative_to_include()` se calcula respecto del archivo incluido; si `root.hcl` queda en la misma carpeta que el viejo `terragrunt.hcl` raíz, las `key` de estado no cambian. Si cambias de carpeta la raíz, cambian todas las claves. Verifica con `terragrunt run --all -- plan` que no hay recursos a recrear (`init` pediría migrar estado si la key cambia: aborta y revisa).

## Fase 3 — Actualizar binario

1. `mise.toml` → `terragrunt = "1.2.1"`; agrega `terragrunt_version_constraint = ">= 1.2.0, < 2.0.0"` en `root.hcl`.
2. `terragrunt hcl fmt --check && terragrunt hcl validate && terragrunt run --all -- plan` en todos los ambientes: esperar **0 cambios**.
3. Revisar cambios de comportamiento: comandos desconocidos ya no se reenvían (0.88), backend no se crea solo, outputs de dependencias se leen del estado, CAS activado (`.terragrunt-cache` en solo lectura: hooks que escriben en el módulo necesitan `mutable = true`).
4. `base64gzip()` cambió bytes en 1.1.4/1.2: si un recurso compara el valor codificado (`user_data_base64` con `replace_on_change`), usa `base64gzip_compat()` (experimento `base64gzip-compat`).

## Fase 4 (opcional) — `_envcommon` → stacks explícitos

1. Crear en el catálogo `units/<x>/terragrunt.hcl` que lea `values.*` (mover el contenido de `_envcommon/<x>.hcl`).
2. En live, crear `terragrunt.stack.hcl` en la carpeta del ambiente con un `unit` por componente, `path` = nombre de la carpeta actual y `no_dot_terragrunt_stack = true` ⇒ el unit se genera **en la misma ruta** ⇒ misma key de estado.
3. Borrar los `terragrunt.hcl` manuales de esos componentes, regenerar y verificar `plan` sin cambios.
4. Pasar dependencias a `autoinclude` con `unit.<x>.path`.
5. Más adelante, si quieres los units dentro de `.terragrunt-stack/`, quita `no_dot_terragrunt_stack` y migra estado con `terragrunt backend migrate`.

Guía oficial de referencia: `terragrunt-infrastructure-live-stacks-example/docs/migration-guide.md`.

## Fase 5 — Pipelines con filtros

Reemplaza scripts de `git diff` + `--terragrunt-include-dir` por `--filter '[origin/main...HEAD]'` / `--filter-affected` y gestiona destroys con `--filter-allow-destroy` (ver `05` y `08`).
