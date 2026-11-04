# 06 — Layouts de repositorio

Contenido: live clásico, live con stacks, catálogo, scale-catalog, variantes Azure/GCP, monorepo vs multirepo, versionado, archivos raíz.

## 1. Live clásico (stacks implícitos) — `terragrunt-infrastructure-live-example`

```
infrastructure-live/
├── root.hcl                    # provider + remote_state + catalog
├── _envcommon/                 # config común por componente (sin ambiente)
│   ├── mysql.hcl               # locals.base_source_url + inputs por defecto
│   └── webserver-cluster.hcl
├── non-prod/
│   ├── account.hcl             # locals { account_name, aws_account_id }
│   └── us-east-1/
│       ├── region.hcl          # locals { aws_region }
│       ├── qa/
│       │   ├── env.hcl         # locals { environment = "qa" }
│       │   ├── mysql/terragrunt.hcl
│       │   └── webserver-cluster/terragrunt.hcl
│       └── stage/…
└── prod/…
```

Unit típico:

```hcl
include "root" { path = find_in_parent_folders("root.hcl") }
include "envcommon" {
  path   = "${dirname(find_in_parent_folders("root.hcl"))}/_envcommon/mysql.hcl"
  expose = true
}
terraform { source = "${include.envcommon.locals.base_source_url}?ref=v0.8.0" }
inputs = { instance_class = "db.t3.medium" }   # solo diferencias del ambiente
```

## 2. Live con stacks — `terragrunt-infrastructure-live-stacks-example` (recomendado)

```
infrastructure-live/
├── mise.toml                   # terragrunt = "1.2.1", opentofu = "1.13.1"
├── root.hcl
├── .terragrunt-filters         # opcional
├── .gitignore                  # .terragrunt-cache/ .terragrunt-stack/ …
├── non-prod/
│   ├── account.hcl
│   └── us-east-1/
│       ├── region.hcl
│       └── stateful-lambda-service/terragrunt.stack.hcl
└── prod/ (misma forma)
```

Diferencias con el clásico: no hay `_envcommon` ni un `terragrunt.hcl` por unit; cada servicio es un `terragrunt.stack.hcl` que referencia units del catálogo con `values` y conecta dependencias con `autoinclude`. El ambiente puede ser el nivel de cuenta (non-prod/prod) o agregarse `env.hcl` bajo región.

## 3. Catálogo — `terragrunt-infrastructure-catalog-example`

```
infrastructure-catalog/
├── modules/<nombre>/{main.tf,variables.tf,outputs.tf,versions.tf,README.md}
│   └── .boilerplate/           # opcional: plantilla para `terragrunt scaffold`
├── units/<nombre>/terragrunt.hcl          # include root + source ../..//modules/x + inputs desde values
├── stacks/<nombre>/terragrunt.stack.hcl   # compone units con autoinclude
├── examples/
│   ├── tofu/<modulo>/                     # uso directo del módulo (tests)
│   └── terragrunt/{root.hcl, units/…, stacks/…}   # uso real con Terragrunt (tests)
├── test/                       # Terratest (Go) por módulo, unit y stack
├── .terragrunt-catalog-ignore  # units/** y examples/** no se ofrecen en `catalog`
├── .pre-commit-config.yaml
└── mise.toml
```

Reglas:
- Módulos sin provider ni backend (los genera live).
- Units sin valores de ambiente: todo entra por `values` (obligatorios directos, opcionales con `try(values.x, default)`).
- Release por tag semver (`v1.4.0`); CHANGELOG con breaking changes de inputs/outputs; guías de migración por versión (`docs/1.2-migration-guide.md`).
- `update_source_with_cas = true` en units/stacks con rutas relativas (`../..//modules/x`).

## 4. Scale catalog — `terragrunt-scale-catalog`

Catálogo público de Gruntwork para bootstrap de pipelines con OIDC: `modules/{aws,azure,gcp}`, `units/<nube>/{oidc,state}`, `stacks/<nube>/<github|gitlab>/pipelines-bootstrap` y plantillas boilerplate (`.gruntwork/environment-*.hcl`, `root.hcl`, workflows). Útil como **referencia de mínimo privilegio** (roles plan vs apply separados, credenciales federadas por rama) aunque no se use Terragrunt Scale. Ver `07-backends-y-auth.md`.

## 5. Variantes por nube

| Nube | Nivel 1 | Nivel 2 | Archivo de jerarquía |
|---|---|---|---|
| AWS | cuenta (`account.hcl`: `aws_account_id`) | región (`region.hcl`) | `env.hcl` opcional |
| Azure | suscripción (`sub.hcl`: `subscription_id`, `tenant_id`) | región/location (`region.hcl`) | `env.hcl` |
| GCP | proyecto (`project.hcl`: `project_id`) | región (`region.hcl`) | `env.hcl` |

Un nivel `_global/` (por cuenta/suscripción) aloja recursos sin región (IAM, Entra ID, DNS raíz).

## 6. Monorepo vs multirepo

| | Multirepo (catalog + live) | Monorepo (`catalog/` + `live/`) |
|---|---|---|
| Versionado | Tags del catálogo, promoción explícita | Rutas locales; promoción por PR |
| Riesgo | Bajo: prod fija versión | Un cambio de módulo afecta a todos los ambientes a la vez |
| Recomendado para | Equipos de plataforma, varios consumidores | Equipos pequeños, arranque |

En monorepo: `.terragrunt-filters` con `!./catalog/**` y, si se necesita promoción, referenciar el propio repo por git con `?ref=`.

## 7. Archivos raíz recomendados

- `mise.toml` — versiones pineadas (leído por `gruntwork-io/terragrunt-action`).
- `.gitignore` — `.terragrunt-cache/`, `.terragrunt-stack/`, `.terraform/`, `*.tfstate*`, `terragrunt-debug.tfvars.json`, `backend.tf`/`provider.tf` generados si se generan en el unit, `error-signals.json`, `report.*`.
- `.terragrunt-filters`, `.pre-commit-config.yaml`, `CODEOWNERS` (prod requiere aprobación de plataforma), `README.md` con cómo ejecutar.
