# 04 — CLI de Terragrunt 1.x

Contenido: comandos, flags clave, variables de entorno `TG_*`, caché, reportes, depuración.

## 1. Comandos

| Comando | Uso |
|---|---|
| `terragrunt plan` / `apply` / `destroy` / `output` / `init` / `validate` / `import` / `state` … | Atajos de `run` |
| `terragrunt run -- <cmd> [args]` | Forma explícita; obligatoria para comandos sin atajo (`run -- workspace ls`, `run -- force-unlock ID`) |
| `terragrunt run --all -- plan` | Todos los units del directorio actual en orden DAG (antes `run-all`) |
| `terragrunt run --graph -- apply` | El unit actual y todos sus dependientes (antes `graph`) |
| `terragrunt exec -- <prog>` | Ejecuta cualquier programa con `inputs` como `TF_VAR_*` y credenciales del unit |
| `terragrunt find` / `list` | Descubrimiento sin ejecutar: `--dag`, `--json`, `--dependencies`, `--external`, `--reading`, `list --tree --long` |
| `terragrunt dag graph` | Grafo en DOT (antes `graph-dependencies`) |
| `terragrunt hcl fmt [--check --diff]` | Formato (antes `hclfmt`) |
| `terragrunt hcl validate [--inputs] [--strict] [--json]` | Validación HCL; `--inputs` verifica inputs vs variables (antes `validate-inputs`) |
| `terragrunt render [--format json] [--write] [--all]` | Config resuelta (antes `render-json`) |
| `terragrunt info print` / `info strict` | Info del unit (antes `terragrunt-info`) / controles estrictos |
| `terragrunt stack generate\|run\|output\|clean` | Ver `03-stacks.md` |
| `terragrunt backend bootstrap\|migrate\|delete` | Gestión explícita del backend |
| `terragrunt catalog` / `scaffold <url> [--var k=v]` | Explorar catálogo / generar unit desde módulo (boilerplate) |
| `terragrunt mcp` | Servidor MCP (experimental) |

Comandos eliminados en 1.x: `run-all`, `plan-all`, `apply-all`, `destroy-all`, `output-all`, `validate-all`, `spin-up`, `tear-down`, `hclfmt`, `hclvalidate`, `graph-dependencies`, `render-json`, `terragrunt-info`, `validate-inputs`. Además, desde 0.88 los comandos desconocidos **no** se reenvían a tofu: usa `run --`.

## 2. Flags más usados

| Flag | Env var | Para qué |
|---|---|---|
| `--all` | `TG_ALL` | Ejecutar sobre todo el stack |
| `--non-interactive` | `TG_NON_INTERACTIVE` | CI (sin prompts) |
| `--filter '<expr>'` | `TG_FILTER` | Selección de units (ver `05`) |
| `--filter-affected` | `TG_FILTER_AFFECTED` | = `[<rama-default>...HEAD]` |
| `--filter-allow-destroy` | | Permitir destroy de units/stacks eliminados en el diff |
| `--filters-file` / `--no-filters-file` | | Usar/ignorar `.terragrunt-filters` |
| `--parallelism N` | `TG_PARALLELISM` | Límite de units concurrentes |
| `--backend-bootstrap` | `TG_BACKEND_BOOTSTRAP` | Crear backend si no existe |
| `--tf-path tofu\|terraform` | `TG_TF_PATH` | Binario |
| `--source <ruta>` / `--source-map a=b` / `--source-update` | | Desarrollo local de módulos / refrescar fuentes |
| `--feature k=v` | `TG_FEATURE` | Feature flags |
| `--queue-ignore-errors` / `--queue-ignore-dag-order` | | Continuar con errores / ignorar orden (con cuidado) |
| `--fail-fast` | `TG_FAIL_FAST` | Cortar ante el primer error |
| `--no-auto-approve` | | Evita `-auto-approve` automático en `--all apply/destroy` |
| `--tf-forward-stdout` | | Salida de tofu sin prefijos (útil para comentarios en PR) |
| `--log-level debug\|info\|warn\|error` / `--log-format bare\|pretty\|json\|key-value` | `TG_LOG_LEVEL`/`TG_LOG_FORMAT` | Logs |
| `--inputs-debug` | `TG_INPUTS_DEBUG` | Escribe `terragrunt-debug.tfvars.json` |
| `--report-file r.json --report-format json\|csv`, `--summary-per-unit` | | Reporte de ejecución para CI |
| `--provider-cache` | `TG_PROVIDER_CACHE` | Servidor de caché de providers (runs con `--all`) |
| `--dependency-fetch-output-from-state` (default) / `--no-dependency-outputs` | | Lectura de outputs |
| `--auth-provider-cmd <script>` / `--no-discovery-auth-provider-cmd` | | Credenciales dinámicas por unit |
| `--iam-assume-role arn` / `--iam-assume-role-web-identity-token` | | AWS |
| `--experiment <nombre>` / `--experiment-mode` | `TG_EXPERIMENT` | Experimentos |
| `--strict-mode` / `--strict-control <nombre>` | `TG_STRICT_MODE` | Convertir deprecaciones en errores (útil para preparar upgrades) |
| `--working-dir` | `TG_WORKING_DIR` | Directorio de ejecución |
| `--no-color`, `--no-tips` | | Salida limpia |

Regla de migración: `TERRAGRUNT_X` → `TG_X` (excepciones: `TERRAGRUNT_DEBUG` → `TG_INPUTS_DEBUG`). Lista completa en `09`.

## 3. Comportamientos de `run --all`

- `apply`/`destroy` agregan `-auto-approve` automáticamente (stdin compartido). Revisa plan antes; en CI aplica solo tras plan aprobado.
- `plan` falla si una dependencia nunca se aplicó y no hay mocks permitidos para `plan`.
- No setees `TF_PLUGIN_CACHE_DIR` manualmente con `--all`.
- Errores de un unit hacen saltar a sus dependientes; el resumen final y `--report-file` muestran qué pasó.
- `-out` en `run --all plan` se escribe por unit; usa `--out-dir` / `--json-out-dir` para centralizar planes (útil para aplicar exactamente lo revisado).

## 4. Caché y rendimiento

- **Auto provider cache dir** (default con OpenTofu ≥ 1.10): sin configuración.
- **Provider cache server** (`--provider-cache`): para repos grandes / Terraform / NFS; puede empeorar runs de un solo unit.
- **CAS** (default desde 1.1): clona una vez y hace hard-links. `--no-cas` lo desactiva; `--cas-offline` usa solo caché.
- **Descubrimiento**: evita `run_cmd`/`get_aws_account_id()` en `locals` de miles de units; limita con `--discovery-boundary` o filtros.
- **Paralelismo**: empieza sin límite; baja con `--parallelism` si el proveedor aplica rate limiting.

## 5. Depuración

```bash
terragrunt run --log-level debug --inputs-debug -- plan
terragrunt render --format json                     # ¿qué config quedó tras includes?
terragrunt find --dag --json | jq                   # ¿qué se va a ejecutar y en qué orden?
terragrunt info print                               # rutas de cache, config, working dir
rm -rf .terragrunt-cache && terragrunt run --source-update -- init
```

Errores típicos:
- `Unknown command` → usar `run -- <cmd>`.
- `Found remote_state settings ... but the bucket does not exist` → `--backend-bootstrap` o `backend bootstrap`.
- `Unsupported attribute; This object does not have an attribute named "outputs"` → dependencia expandida sin clave, o dependencia no aplicada sin mocks.
- `Detected dependency cycle` → revisar `dependency`/`dependencies`; `terragrunt dag graph`.
- `values` no definido al validar un unit de catálogo → validar desde el stack generado.
