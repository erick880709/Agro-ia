# 03 — Stacks explícitos (`terragrunt.stack.hcl`)

Contenido: bloques `unit`/`stack`, `values`, `autoinclude`, `expansion`, `enabled`, `include` en stacks, dependencias hacia stacks, CAS en catálogos, comandos `stack *`, límites conocidos.

## 1. Anatomía

```hcl
# live/non-prod/us-east-1/pagos/terragrunt.stack.hcl
locals {
  nombre  = "pagos-dev"
  version = "v1.4.0"                       # tag del catálogo
  catalog = "git::git@github.com:org/infrastructure-catalog.git"
}

unit "db" {
  source = "${local.catalog}//units/postgres?ref=${local.version}"
  path   = "db"
  values = {
    version = local.version                # el unit lo usa para pinear su módulo
    name    = "${local.nombre}-db"
    size    = "db.t4g.medium"
  }
}

unit "service" {
  source = "${local.catalog}//units/ecs-service?ref=${local.version}"
  path   = "service"
  values = { version = local.version, name = local.nombre }

  autoinclude {                            # dependencias sin tocar el catálogo
    dependency "db" {
      config_path = unit.db.path
      mock_outputs = { endpoint = "mock.db.local:5432" }
      mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
    }
    inputs = { db_endpoint = dependency.db.outputs.endpoint }
  }
}

unit "alarmas" {
  enabled = false                          # existe en el diseño, no se genera
  source  = "${local.catalog}//units/alb-alarms?ref=${local.version}"
  path    = "alarmas"
}
```

`terragrunt stack generate` produce:

```
pagos/
├── terragrunt.stack.hcl
└── .terragrunt-stack/            ← artefacto generado (en .gitignore)
    ├── db/{terragrunt.hcl, terragrunt.values.hcl}
    └── service/{terragrunt.hcl, terragrunt.values.hcl, terragrunt.autoinclude.hcl}
```

## 2. Atributos de `unit` y `stack`

| Atributo | Notas |
|---|---|
| etiqueta | Nombre único; dirección en `stack output` |
| `source` | Igual que `terraform.source` (git, local, `//` subcarpeta, `?ref=`) |
| `path` | Relativo a `.terragrunt-stack/` (único por stack) |
| `values` | Mapa → `terragrunt.values.hcl` → `values.x` en el unit/stack hijo |
| `no_dot_terragrunt_stack` | `true`: genera junto al stack file (adopción sin mover estado) |
| `no_validation` | Salta validaciones del componente |
| `enabled` | `false`: no se genera ni aparece en outputs (dirección intacta) |
| `expansion` | `for_each` o `count` (uno de los dos) |
| `autoinclude` | Configuración inyectada en el componente generado |
| `update_source_with_cas` | Fuentes relativas dentro del catálogo → `cas::` deterministas |

`stack` genera otro `terragrunt.stack.hcl` (anidamiento recursivo). Un `terragrunt.values.hcl` presente junto a la fuente actúa como valores por defecto, pero el atributo `values` lo reemplaza completo.

## 3. Unit de catálogo que consume `values`

```hcl
# catalog/units/postgres/terragrunt.hcl
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "git::git@github.com:org/infrastructure-catalog.git//modules/postgres?ref=${values.version}"
}

inputs = {
  name           = values.name
  instance_class = try(values.size, "db.t4g.small")   # opcionales con try()
}
```

Alternativa en catálogo moderno: `source = "../..//modules/postgres"` + `update_source_with_cas = true`, sin pasar `version` (el ref lo fija el stack que referencia el catálogo). La `source` con CAS debe ser literal (sin interpolaciones).

Un unit que lee `values` no puede ejecutarse aislado: exclúyelo de `catalog`/`scaffold` (`.terragrunt-catalog-ignore`) y de los runs (`.terragrunt-filters` con `!./catalog/**` si es monorepo).

## 4. `autoinclude`

- En `unit`: puede contener `dependency`, `inputs` y cualquier bloque válido de unit (`generate`, `errors`, `feature`, `remote_state`…). Prohibido: `locals`, `values`, `autoinclude` anidado.
- Variables disponibles: `local.*`, `values.*`, `unit.<n>.path`, `stack.<n>.path` (solo componentes del mismo archivo). Se resuelven en generación y quedan literales; solo `dependency.*` queda verbatim.
- Funciones de directorio se evalúan respecto del stack file (`get_terragrunt_dir()` = carpeta del stack).
- Merge: shallow, gana el autoinclude; un `dependency` con el mismo nombre que en el unit lo reemplaza.
- En `stack`: genera `terragrunt.autoinclude.stack.hcl` y solo admite `unit`/`stack` (agrega o sobrescribe componentes). No admite `dependency`.
- No edites `terragrunt.autoinclude.hcl` a mano.

## 5. `expansion`

```hcl
locals { regiones = toset(["us-east-1", "us-west-2"]) }

unit "vpc" {
  expansion { for_each = local.regiones }
  source = "../catalog/units/vpc"
  path   = "vpc/${each.key}"               # obligatorio que varíe por instancia
  values = { region = each.key }
}

unit "app" {
  source = "../catalog/units/app"
  path   = "app"
  autoinclude {
    dependency "vpc" {
      expansion { for_each = local.regiones }
      config_path  = unit.vpc[each.key].path
      mock_outputs = { vpc_id = "vpc-mock-${each.key}" }
    }
    inputs = { vpc_ids = { for r, v in dependency.vpc : r => v.outputs.vpc_id } }
  }
}
```

- Prefiere `for_each` sobre `count`: quitar un elemento del medio con `count` renumera y destruye/recrea.
- `enabled` decide si existe; `expansion` cuántos.
- Direcciones: `terragrunt stack output 'vpc["us-east-1"].vpc_id'`.
- Achicar una expansión deja componentes huérfanos: con filtros Git y `--filter-allow-destroy` Terragrunt los destruye desde el worktree anterior (ver `05`). Si la expansión depende de algo fuera del repo (env var), no se detecta: destruye manualmente.

## 6. `include` dentro de stacks

```hcl
include "compartido" { path = "../compartido.stack.hcl" }
```

Solo agrega bloques `unit`/`stack`; el archivo incluido no puede tener `locals` ni `include`; nombres no pueden colisionar; no acepta `expose`/`merge_strategy`. Para compartir un patrón completo, anida un `stack`.

## 7. Depender de un stack

```hcl
# app/terragrunt.hcl
dependency "red" {
  config_path = "../red"                         # carpeta con terragrunt.stack.hcl
  mock_outputs = { vpc = { id = "vpc-mock" }, privada = { id = "subnet-mock" } }
  mock_outputs_merge_strategy_with_state = "shallow"   # stack parcialmente aplicado
}
inputs = { vpc_id = dependency.red.outputs.vpc.id }
```

Los stacks en sí **no** pueden declarar dependencias: declara la dependencia en cada unit (fuente o `autoinclude`).

## 8. Comandos

| Comando | Qué hace |
|---|---|
| `terragrunt stack generate` | Genera `.terragrunt-stack` recursivamente (`--filter 'name=x \| type=stack'` limita qué stacks) |
| `terragrunt stack run plan` | Genera y ejecuta sobre los units del stack |
| `terragrunt run --all plan` | Descubre units y stacks (genera automáticamente) — forma recomendada en CI |
| `terragrunt stack output [--format json\|raw] ['addr']` | Outputs agregados por unit |
| `terragrunt stack clean` | Borra `.terragrunt-stack` |
| `terragrunt render --json -w` | Configuración final resuelta (previsualización) |
| `--source-update` | Refresca fuentes y limpia archivos obsoletos al regenerar |
| `--no-stack-generate` | Usa lo ya generado (p. ej. en `stack output`) |

## 9. Patrones y límites

- **Promoción entre ambientes**: mismo stack de catálogo, `ref` distinto por ambiente (`non-prod` → `v1.5.0` primero, `prod` después en otro PR).
- **Adopción gradual**: convierte un árbol implícito existente a stack con `no_dot_terragrunt_stack = true` y los mismos `path`; la `key` de estado no cambia porque la ruta relativa es igual. Verifica con `plan` sin cambios antes de seguir.
- **Mover units dentro de `.terragrunt-stack`** cambia la `key` → requiere `terragrunt backend migrate <origen> <destino>` o `tofu state` manual.
- Generaciones profundas son lentas: usa `update_source_with_cas = true` en el catálogo.
- Estado local con stacks: pon el path del estado fuera de `.terragrunt-stack` (se borra con `stack clean`).
