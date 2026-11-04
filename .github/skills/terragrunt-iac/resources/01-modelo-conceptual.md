# 01 — Modelo conceptual de Terragrunt 1.x

Contenido: terminología oficial, relación entre módulo/unit/stack, catálogo vs live, DAG, y guía de decisión.

## Terminología

| Término | Qué es | Archivo |
|---|---|---|
| **Módulo** | Código OpenTofu/Terraform reutilizable (`main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`). No sabe de ambientes. | `modules/<nombre>/` (catálogo) |
| **Unit** | Una instancia desplegable de un módulo con **su propio estado**. Directorio con `terragrunt.hcl`. Es la unidad atómica de despliegue. | `terragrunt.hcl` |
| **Stack** | Colección de units que se gestionan juntas. Puede ser **implícito** (un árbol de directorios con units) o **explícito** (un `terragrunt.stack.hcl` que genera units). | carpeta o `terragrunt.stack.hcl` |
| **Root config** | Configuración compartida incluida por todos los units (provider, backend, catálogo). | `root.hcl` |
| **Values** | Parámetros que un stack pasa a un unit/stack generado; el unit los lee como `values.<x>`. | `terragrunt.values.hcl` (generado) |
| **Catalog** | Repo (o carpeta) con módulos, units y stacks reutilizables y versionados. | `infrastructure-catalog` |
| **Live** | Repo que representa la infraestructura *realmente desplegada* por cuenta/región/ambiente. | `infrastructure-live` |
| **Run queue / DAG** | Grafo dirigido acíclico construido a partir de `dependency`/`dependencies`; define orden de `apply` (dependencias primero) y de `destroy` (inverso). | — |
| **Run report** | Resumen por unit de resultados de `run --all` (`--report-file`). | `report.csv/json` |
| **CAS** | Content Addressable Storage: caché deduplicada de fuentes (git, http, s3, oci…) en `~/.cache/terragrunt/cas`. | — |

## Cómo encaja todo

```
infrastructure-catalog (versionado: v1.4.0)
├── modules/vpc            ← OpenTofu puro
├── units/vpc              ← terragrunt.hcl que envuelve modules/vpc y lee values.*
└── stacks/red-base        ← terragrunt.stack.hcl que compone units/vpc + units/subnet…

infrastructure-live
├── root.hcl               ← provider + backend + catalog (DRY)
├── non-prod/account.hcl
│   └── us-east-1/region.hcl
│       └── red/terragrunt.stack.hcl   ← stack "red-base?ref=v1.4.0" con values de non-prod
└── prod/…                             ← mismo stack, otros values, otro ref cuando se promueve
```

Al ejecutar `terragrunt run --all plan` en live, Terragrunt: (1) descubre configuraciones, (2) genera los stacks explícitos en `.terragrunt-stack/`, (3) construye el DAG, (4) por cada unit descarga la fuente (vía CAS), genera `provider.tf`/`backend.tf`, pasa `inputs` como `TF_VAR_*`, hace `init` automático y ejecuta el comando en paralelo respetando el orden.

## Stack implícito vs explícito

| Criterio | Implícito (árbol de `terragrunt.hcl`) | Explícito (`terragrunt.stack.hcl`) |
|---|---|---|
| Qué se versiona en live | Un `terragrunt.hcl` por unit | Un archivo por stack; los units se generan |
| Reutilización entre ambientes | `_envcommon/*.hcl` + include con `expose` | Mismo stack de catálogo con distintos `values` |
| Dependencias | `dependency` en cada unit | `autoinclude { dependency … config_path = unit.x.path }` en el stack |
| Visibilidad en code review | Total (todo está en el repo) | Hay que ejecutar `stack generate` o `render` para ver el resultado |
| Adopción en repos existentes | Natural | Gradual con `no_dot_terragrunt_stack = true` (sin mover estado) |
| Recomendación Gruntwork 2025-2026 | Válido y soportado | **Preferido para proyectos nuevos** |

Regla práctica:
- Equipo pequeño, pocos ambientes, mucha personalización por ambiente → implícito.
- Patrones repetidos (mismo servicio en N ambientes/regiones/clientes), catálogo maduro, plataforma interna → explícito.
- Se pueden mezclar en el mismo repo: un `run --all` descubre ambos.

## El DAG en la práctica

- `dependency "x" { config_path = "../x" }` crea arista y expone `dependency.x.outputs`.
- `dependencies { paths = [...] }` crea arista **sin** leer outputs (orden puro).
- `apply` corre dependencias primero; `destroy` corre dependientes primero.
- `run --all plan` en un repo nuevo falla si una dependencia no tiene estado y no hay `mock_outputs` permitidos para `plan`.
- Un stack completo puede ser dependencia: `config_path` apuntando a una carpeta con `terragrunt.stack.hcl` (outputs agrupados por nombre de unit: `dependency.red.outputs.vpc.id`).
- Ver el grafo: `terragrunt find --dag`, `terragrunt list --tree --dag`, `terragrunt dag graph | dot -Tsvg > dag.svg`.

## Qué NO es Terragrunt

- No reemplaza a OpenTofu/Terraform: los ejecuta. Errores de recursos se diagnostican en la capa de módulo.
- No es un gestor de secretos.
- No necesita workspaces: el aislamiento lo dan las rutas de los units.
- Terragrunt Scale / Gruntwork Pipelines son productos comerciales encima de Terragrunt OSS; todo lo de esta skill funciona sin ellos, salvo donde se indique.
