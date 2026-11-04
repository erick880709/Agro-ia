# 02 — Referencia HCL de Terragrunt (units y root)

Contenido: bloques y atributos de `terragrunt.hcl`/`root.hcl`, funciones integradas, reglas de merge de `include`, patrones idiomáticos y trampas. Para `terragrunt.stack.hcl` ver `03-stacks.md`.

Tabla de contenido: 1. terraform · 2. remote_state · 3. generate · 4. include · 5. locals · 6. dependency/dependencies · 7. inputs · 8. feature/exclude · 9. errors · 10. atributos sueltos · 11. funciones · 12. orden de evaluación y trampas

---

## 1. `terraform`

```hcl
terraform {
  # Fuente del módulo. El "//" separa repo de subcarpeta: todo el repo se descarga (permite rutas relativas entre módulos).
  source = "git::git@github.com:org/infrastructure-catalog.git//modules/vpc?ref=v1.4.0"
  # Alternativas: "tfr:///terraform-aws-modules/vpc/aws?version=5.8.1", "../..//modules/vpc" (local),
  # registry con constraint (1.2+): source = "tfr:///terraform-aws-modules/vpc/aws" + version = "~> 5.8"

  # Solo en catálogos: reescribe fuentes relativas a referencias cas:: deterministas al generar stacks
  update_source_with_cas = true

  extra_arguments "lock_timeout" {
    commands  = get_terraform_commands_that_need_locking()
    arguments = ["-lock-timeout=20m"]
  }

  extra_arguments "tfvars_comunes" {
    commands           = get_terraform_commands_that_need_vars()
    required_var_files = ["${get_parent_terragrunt_dir()}/common.tfvars"]
    optional_var_files = ["${get_terragrunt_dir()}/override.tfvars"]
  }

  before_hook "tflint" {
    commands = ["plan"]
    execute  = ["tflint", "--minimum-failure-severity=error"]
  }

  after_hook "aviso" {
    commands     = ["apply"]
    execute      = ["echo", "apply terminado"]
    run_on_error = true
  }

  error_hook "fallo_descarga" {
    commands  = ["init-from-module"]
    execute   = ["echo", "No se pudo descargar la fuente"]
    on_errors = [".*"]
  }
}
```

Puntos clave:
- Hooks: `commands`, `execute` (lista), `working_dir`, `run_on_error`, `suppress_stdout`, `if`. Comandos especiales: `read-config` (solo after), `init-from-module` (descarga go-getter), `init` (auto-init).
- Los `before_hook` normales corren en el directorio del módulo descargado (`.terragrunt-cache/...`), no en el del unit: usa rutas absolutas con `get_terragrunt_dir()`.
- `mutable = true` solo si necesitas editar archivos dentro de `.terragrunt-cache` (por defecto son de solo lectura cuando vienen del CAS).
- `include_in_copy` / `exclude_from_copy` (globs) controlan qué archivos del directorio del unit se copian al directorio de trabajo.

## 2. `remote_state`

Va en `root.hcl` para que todos los units lo hereden.

```hcl
remote_state {
  backend = "s3"
  config = {
    bucket       = "org-tfstate-${local.account_id}-${local.aws_region}-an"
    key          = "${path_relative_to_include()}/tf.tfstate"
    region       = local.aws_region
    encrypt      = true
    use_lockfile = true          # bloqueo nativo de S3 (sin DynamoDB) — recomendado con OpenTofu >= 1.10 / Terraform >= 1.10
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}
```

- `key = "${path_relative_to_include()}/..."` es lo que garantiza **un estado por unit**.
- Terragrunt **ya no crea** el backend implícitamente: usa `terragrunt backend bootstrap` o `--backend-bootstrap` (env `TG_BACKEND_BOOTSTRAP=true`). `disable_init = true` evita cualquier gestión del backend.
- `encryption = { key_provider = "pbkdf2" | "aws_kms" | "gcp_kms" | "openbao", ... }` genera el bloque de cifrado de estado de OpenTofu.
- Detalle por backend (azurerm, gcs, opciones de bootstrap) en `07-backends-y-auth.md`.

## 3. `generate`

```hcl
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"   # overwrite | overwrite_terragrunt | skip | error
  contents  = <<EOF
provider "aws" {
  region              = "${local.aws_region}"
  allowed_account_ids = ["${local.account_id}"]
  default_tags { tags = ${jsonencode(local.tags)} }
}
EOF
}
```

Atributos extra: `disable` (bool), `if_disabled` (`skip` por defecto, `remove`, `remove_terragrunt`), `comment_prefix`, `disable_signature`. Úsalo para provider, `versions.tf` con `required_providers`, o archivos auxiliares. `allowed_account_ids` / `subscription_id` explícitos evitan aplicar en la cuenta equivocada.

## 4. `include`

```hcl
include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "envcommon" {
  path           = "${dirname(find_in_parent_folders("root.hcl"))}/_envcommon/mysql.hcl"
  expose         = true            # permite leer include.envcommon.locals.*
  merge_strategy = "deep"          # no_merge | shallow (default) | deep
}
```

Reglas:
- **Siempre con etiqueta.** `include {}` sin etiqueta está deprecado (strict control `bare-include`).
- **Un solo nivel**: un archivo incluido no puede tener su propio `include` (en units). Para jerarquías usa `read_terragrunt_config()` dentro de `locals` del root.
- `shallow`: el hijo reemplaza claves del padre (excepto `dependencies`, cuyas rutas se concatenan). `deep`: mezcla mapas recursivamente (útil para `inputs` grandes).
- `find_in_parent_folders()` sin argumento busca `terragrunt.hcl`: siempre pásale `"root.hcl"`.
- En `terragrunt.stack.hcl` también existe `include`, pero con reglas distintas (ver `03-stacks.md`).

## 5. `locals`

- Solo visibles en el archivo que los define (los padres los ven los hijos únicamente vía `include ... expose = true` → `include.<label>.locals.x`).
- Pueden referenciar otros locals, funciones, `feature.*`, `values.*`; **no** pueden referenciar `dependency.*` si se usan en bloques evaluados antes del DAG (`exclude`, `terraform.source` en discovery).
- Lectura de jerarquía (patrón Gruntwork):

```hcl
locals {
  account_vars = read_terragrunt_config(find_in_parent_folders("account.hcl"))
  region_vars  = read_terragrunt_config(find_in_parent_folders("region.hcl"))
  account_id   = local.account_vars.locals.aws_account_id
  aws_region   = local.region_vars.locals.aws_region
}
```

## 6. `dependency` y `dependencies`

```hcl
dependency "vpc" {
  config_path = "../vpc"                       # carpeta de un unit… o de un stack (terragrunt.stack.hcl)

  mock_outputs = {
    vpc_id          = "vpc-00000000"
    private_subnets = ["subnet-00000000"]
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
  mock_outputs_merge_strategy_with_state  = "shallow"   # no_merge (default) | shallow | deep_map_only
}

dependencies {
  paths = ["../iam-baseline"]     # solo orden, sin outputs
}

inputs = {
  vpc_id     = dependency.vpc.outputs.vpc_id
  subnet_ids = dependency.vpc.outputs.private_subnets
}
```

- `enabled = false` desactiva la dependencia; `skip_outputs = true` usa siempre mocks (prefiere `locals` en ese caso).
- `expansion { for_each = toset([...]) }` o `{ count = N }` crea varias dependencias: `dependency.db["web"].outputs.id`.
- Dependencia hacia un stack: `dependency.red.outputs.<unit>.<output>`; con unit expandido: `outputs.vpc["us-east-1"].id`.
- Lectura de outputs: por defecto Terragrunt lee directo del estado cuando el backend lo soporta (S3, GCS, azurerm) — mucho más rápido que `tofu output`. Desactivar con `--no-dependency-fetch-output-from-state`.
- `config_path` a un **archivo** está deprecado (strict control `dependency-config-path-file`).
- Mocks en `apply` = riesgo de aplicar valores falsos. Nunca incluyas `"apply"` en `mock_outputs_allowed_terraform_commands`.

## 7. `inputs`

Mapa que Terragrunt convierte en `TF_VAR_<nombre>` (JSON-encoded para tipos complejos). Precedencia (de menor a mayor): `inputs` del padre → `inputs` del hijo → `TF_VAR_*` del entorno → `-var`/`-var-file` en `extra_arguments`. Depuración: `terragrunt run --inputs-debug -- plan` escribe `terragrunt-debug.tfvars.json`.

## 8. `feature` y `exclude`

```hcl
feature "desplegar_canary" {
  default = false                    # se puede sobrescribir: --feature desplegar_canary=true / TG_FEATURE=desplegar_canary=true
}

exclude {
  if                   = !feature.desplegar_canary.value
  actions              = ["plan", "apply"]       # "all", "all_except_output", comandos concretos
  exclude_dependencies = false
  no_run               = true                    # bloquea también runs de un solo unit (ignorado en --all)
}
```

- `exclude` reemplaza al antiguo `skip = true` (deprecado).
- Los atributos de `exclude` **no** pueden leer `dependency.*` (se evalúa al construir la cola).
- `feature.default` es expresión: puede venir de `run_cmd("--terragrunt-quiet", "...")` para integrar LaunchDarkly/AppConfig.

## 9. `errors`

```hcl
errors {
  retry "transitorios" {
    retryable_errors   = get_default_retryable_errors()   # o regex propias: [".*TooManyRequests.*"]
    max_attempts       = 3
    sleep_interval_sec = 10
  }
  ignore "conocidos" {
    ignorable_errors = [".*Error: safe-to-ignore.*", "!.*Error: critical.*"]
    message          = "Se ignora error conocido"
    signals          = { safe_to_revert = true }   # genera error-signals.json para que CI decida
  }
}
```

Reemplaza a `retryable_errors`/`retry_max_attempts`/`retry_sleep_interval_sec` (deprecados). Orden: primero `ignore`, luego `retry`. También aplica a errores de descarga de fuentes.

## 10. Atributos sueltos

| Atributo | Uso |
|---|---|
| `terragrunt_version_constraint = ">= 1.2.0, < 2.0.0"` | En `root.hcl`; falla temprano con versiones incompatibles |
| `terraform_version_constraint = ">= 1.10"` | Versión de OpenTofu/Terraform |
| `terraform_binary = "terraform"` | Forzar binario (default `tofu`); en CI prefiere `--tf-path`/`TG_TF_PATH` |
| `prevent_destroy = true` | Bloquea `destroy` del unit (bases de datos, KMS, estado) |
| `iam_role`, `iam_assume_role_duration`, `iam_assume_role_session_name`, `iam_web_identity_token` | Asumir rol AWS por unit (OIDC con `iam_web_identity_token`) |
| `download_dir` | Cambiar ubicación de `.terragrunt-cache` |
| `catalog { urls = [...] }` | Repos que lista `terragrunt catalog` |
| `engine { source = ..., version = ... }` | IaC engines (experimental) |

## 11. Funciones integradas

Todas las funciones de OpenTofu (`jsonencode`, `merge`, `try`, `lookup`, `templatefile`, `file`, `fileset`, etc.) más:

| Función | Devuelve / uso |
|---|---|
| `find_in_parent_folders("root.hcl")` | Ruta absoluta del primer archivo con ese nombre hacia arriba |
| `path_relative_to_include()` | Ruta del unit relativa al archivo incluido (clave del estado) |
| `path_relative_from_include()` | Inverso del anterior |
| `get_terragrunt_dir()` | Directorio del `terragrunt.hcl` actual |
| `get_parent_terragrunt_dir()` | Directorio del archivo incluido (root) |
| `get_original_terragrunt_dir()` | Directorio del unit original aunque se lea vía `read_terragrunt_config` |
| `get_repo_root()`, `get_path_from_repo_root()`, `get_path_to_repo_root()` | Rutas relativas al repo git |
| `get_working_dir()` | Directorio de trabajo real (`.terragrunt-cache/...`) |
| `get_env("NOMBRE", "default")` | Variable de entorno (sin default ⇒ error si falta) |
| `get_platform()` | `linux`, `darwin`, `windows` |
| `get_terraform_command()`, `get_terraform_cli_args()` | Comando y args actuales |
| `get_terraform_commands_that_need_vars/input/locking/parallelism()` | Listas para `extra_arguments` |
| `get_aws_account_id()`, `get_aws_account_alias()`, `get_aws_caller_identity_arn()`, `get_aws_caller_identity_user_id()` | Identidad AWS (requiere credenciales al parsear) |
| `get_default_retryable_errors()` | Regex de errores transitorios por defecto |
| `run_cmd("--terragrunt-quiet", "cmd", "arg")` | Ejecuta comando y usa su stdout (cacheado por args); `--terragrunt-global-cache`, `--terragrunt-no-cache` |
| `read_terragrunt_config(path, default)` | Parsea otro HCL y expone `locals`, `inputs`, `dependency`, etc. |
| `read_tfvars_file(path)` | Lee `.tfvars` como JSON (usar con `jsondecode`) |
| `sops_decrypt_file(path)` | Descifra con SOPS (KMS/age/PGP) |
| `deep_merge(a, b, ...)` | Merge recursivo de mapas |
| `mark_as_read(path_abs)`, `mark_glob_as_read(glob)` | Declara archivos leídos para filtros `reading=` (usar en `locals`) |
| `constraint_check(version, ">= 2.0.0")` | Compara versiones semver |
| `get_terragrunt_source_cli_flag()` | Valor de `--source` (para lógica de desarrollo local) |

## 12. Orden de evaluación y trampas frecuentes

1. Orden oficial de parseo: `include` → `locals` → atributos `iam_*` → `dependencies` → `dependency` (aquí se leen outputs) → todo lo demás → config incluida → merge. Por eso **no** puedes usar `dependency.*` dentro de `locals`, `include` ni `dependencies`, pero sí `local.*` dentro de `dependency`. Con `--all` hay una primera pasada (include, locals, dependency sin outputs) para armar el DAG.
2. Durante el *discovery* de `run --all` se parsea **todo** el árbol: cualquier `run_cmd`, `get_aws_account_id()` o `sops_decrypt_file` en `locals` se ejecuta para cada unit (lento y requiere credenciales). Muévelos donde no bloqueen el descubrimiento o usa `--no-discovery-auth-provider-cmd`.
3. Leer archivos en `inputs` no los marca como leídos; hazlo en `locals`.
4. `TF_PLUGIN_CACHE_DIR` manual + `run --all` produce condiciones de carrera: deja que Terragrunt gestione la caché (auto provider cache dir con OpenTofu ≥ 1.10, o `--provider-cache`).
5. `.terragrunt-cache/`, `.terragrunt-stack/`, `terragrunt-debug.tfvars.json`, `backend.tf`/`provider.tf` generados → `.gitignore`. El `.terraform.lock.hcl` sí se versiona (Terragrunt lo copia de vuelta al unit).
6. `--source ../../catalog//modules/x` (o `--source-map`) para probar cambios locales del catálogo sin publicar tag.
