---
name: terragrunt-iac
metadata:
  display-name: "Experto en Infraestructura como Código"
  capability: "Infraestructura como código"
  capability-summary: "Diseña, genera, revisa, migra y automatiza IaC Terragrunt 1.x y sus pipelines de CI/CD."
description: Experto en Terragrunt 1.x (Gruntwork) sobre OpenTofu/Terraform para diseñar, generar, revisar, migrar y automatizar infraestructura como código. Usa esta skill siempre que el usuario mencione Terragrunt, terragrunt.hcl, terragrunt.stack.hcl, root.hcl, units, stacks, infrastructure-live, infrastructure-catalog, run --all, run-all, dependency/mock_outputs, remote_state, include, _envcommon, Terragrunt Scale, Gruntwork Pipelines, gruntwork-io/terragrunt-action, o pida pipelines de IaC (GitHub Actions, Azure DevOps, GitLab) que ejecuten plan/apply sobre múltiples módulos, filtrado por cambios de Git (--filter, --filter-affected), migración de Terragrunt 0.x a 1.x, o estructurar repos multi-cuenta/multi-región/multi-ambiente para AWS, Azure o GCP — aunque no diga "Terragrunt" explícitamente pero hable de "mantener DRY el estado remoto/providers de Terraform" o "orquestar muchos módulos de Terraform".
---

# terragrunt-iac

Skill para trabajar con Terragrunt **1.x** (última verificada: v1.2.1, oct-2026) como orquestador de OpenTofu/Terraform. Cubre cinco modos de trabajo; identifica primero en cuál estás, porque cada uno carga recursos distintos y entrega artefactos distintos.

## Fuentes de verdad

La skill está construida sobre los repositorios oficiales de Gruntwork y las GitHub Actions del marketplace:

- `gruntwork-io/terragrunt` (docs en `docs/src/content/docs` y `docs/src/data`) — referencia HCL, CLI, filtros, stacks, migraciones.
- `gruntwork-io/terragrunt-infrastructure-live-stacks-example` — layout *live* moderno con `terragrunt.stack.hcl`.
- `gruntwork-io/terragrunt-infrastructure-live-example` — layout *live* clásico (`_envcommon`, una carpeta por unit).
- `gruntwork-io/terragrunt-infrastructure-catalog-example` — catálogo `modules/` → `units/` → `stacks/` con Terratest.
- `gruntwork-io/terragrunt-scale-catalog` — bootstrap OIDC para pipelines (AWS/Azure/GCP × GitHub/GitLab).
- Actions: `gruntwork-io/terragrunt-action@v3` (oficial), `boogy/terragrunt-runner`, `eLco/setup-terragrunt`, `darzanebor/github-terragrunt-wrapper`, `the-commons-project/terragrunt-github-actions` (legado).

Terragrunt evoluciona rápido (1.0 → 1.2 en pocos meses estabilizó stacks, filtros, CAS, autoinclude, expansion). Si el usuario reporta un comportamiento distinto al documentado aquí, pídele `terragrunt --version` y, si hay acceso a red, verifica contra el repo oficial antes de insistir.

## Paso 0 — Línea base del proyecto

Antes de generar nada, busca un archivo `Linea_Base_<Proyecto>.md` en el directorio de trabajo o en los archivos que adjuntó el usuario. Si existe, léelo y respeta sus decisiones (nube, backend, layout, versiones, CI). Si no existe y la tarea es de diseño o generación (modos A, B o C), créalo al final usando `assets/Linea_Base_template.md`: así la próxima sesión no tiene que volver a preguntar lo mismo.

Datos mínimos que necesitas (pregunta solo lo que falte y no se pueda inferir del código):

1. Nube(s) y modelo de cuentas: AWS cuentas / Azure suscripciones / GCP proyectos; regiones.
2. Ambientes (dev/qa/stage/prod, non-prod/prod).
3. Motor y versiones: OpenTofu o Terraform; versión de Terragrunt (default: pinear `1.2.x` vía `mise.toml`).
4. Backend de estado: S3, azurerm o GCS; si Terragrunt debe crearlo (`--backend-bootstrap`).
5. Plataforma de CI/CD: GitHub Actions, Azure DevOps, GitLab; autenticación (OIDC preferido).
6. ¿Existe ya un catálogo de módulos? ¿Repo separado o monorepo?

## Paso 1 — Identifica el modo y carga los recursos

| Modo | Señales típicas | Recursos a leer |
|---|---|---|
| **A. Diseñar repositorio** | "estructura", "cómo organizo", "multi-cuenta", repo nuevo | `01-modelo-conceptual.md`, `06-layouts-repositorio.md`, `07-backends-y-auth.md` |
| **B. Escribir/editar configuración** | "crea un unit/stack", "dependency", "mock_outputs", "include", errores de HCL | `02-hcl-referencia.md`, `03-stacks.md` |
| **C. CI/CD** | "pipeline", "GitHub Actions", "Azure DevOps", "plan en PR", "solo lo que cambió" | `08-cicd.md`, `05-filtros-y-git.md`, `07-backends-y-auth.md` |
| **D. Migrar** | `run-all`, `--terragrunt-*`, `TERRAGRUNT_*`, root `terragrunt.hcl`, `skip`, `retryable_errors`, `_envcommon` → stacks | `09-migracion-0x-a-1x.md` + ejecutar `scripts/tg_lint.py` |
| **E. Revisar/diagnosticar** | "revisa", "por qué falla", "está bien esto", PR de IaC | `11-checklist-revision.md`, `04-cli-v1.md`, `10-testing-y-calidad.md` + `scripts/tg_lint.py` |

Los modos se combinan (p. ej. diseñar repo + pipeline = A + C). Lee solo lo necesario; cada recurso indica al inicio qué contiene.

## Paso 2 — Principios no negociables al generar código

Estos principios salen de las mejores prácticas de Gruntwork y evitan los errores más caros (estado corrupto, destroys accidentales, drift). Explica el porqué al usuario cuando uno de ellos cambie su diseño.

1. **Separar catálogo y live.** El código OpenTofu/Terraform vive en un *catalog* (`modules/`, `units/`, `stacks/`) versionado con tags; el repo *live* solo contiene Terragrunt (`root.hcl`, `*.hcl` de jerarquía, `terragrunt.stack.hcl` o `terragrunt.hcl`) y referencia el catálogo con `?ref=vX.Y.Z`. Nunca `ref=main` en prod.
2. **Un unit = un estado.** No uses workspaces de OpenTofu/Terraform; el aislamiento de estado lo da la ruta del unit (`key = "${path_relative_to_include()}/tf.tfstate"`).
3. **Raíz se llama `root.hcl`**, nunca `terragrunt.hcl` en la raíz, e `include "root" { path = find_in_parent_folders("root.hcl") }` siempre con etiqueta (las includes sin etiqueta están deprecadas).
4. **DRY por jerarquía**: `account.hcl` / `region.hcl` / `env.hcl` (o `sub.hcl`, `project.hcl`) leídos con `read_terragrunt_config(find_in_parent_folders(...))` desde `root.hcl`; provider y backend generados con `generate`/`remote_state.generate`.
5. **Preferir stacks explícitos** (`terragrunt.stack.hcl` + `values` + `autoinclude`) para proyectos nuevos; usar stacks implícitos (árbol de carpetas) cuando el equipo lo prefiera o en migraciones graduales (`no_dot_terragrunt_stack = true` para adopción sin mover estado).
6. **Mocks acotados**: todo `dependency` que pueda no estar aplicado lleva `mock_outputs` y `mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]` (nunca permitir mocks en `apply`).
7. **Trunk-based + `main` como fuente de verdad**: plan en PR, apply al merge; filtrar por diff de Git (`--filter '[origin/main...HEAD]'` o `--filter-affected`) y no permitir destroys sin `--filter-allow-destroy` explícito y aprobación. En monorepos con `catalog/` usa la frontera inline `--filter '(./live)...[origin/main...HEAD]'` (verificado en v1.2.1: sin ella, los stacks del catálogo se intentan generar y fallan).
8. **Versiones pineadas** de Terragrunt y OpenTofu/Terraform en `mise.toml` (lo consume `gruntwork-io/terragrunt-action@v3`) y `terragrunt_version_constraint` en `root.hcl`.
9. **Sintaxis 1.x siempre**: `run --all`, `run -- <cmd>`, flags sin prefijo `--terragrunt-`, env vars `TG_*`, `hcl fmt`, `hcl validate`, `dag graph`, `exclude {}` en vez de `skip`, `errors {}` en vez de `retryable_errors`.
10. **Secretos fuera del código**: OIDC en CI, `TF_VAR_*`/gestores de secretos o `sops_decrypt_file()`; nunca credenciales en `inputs` ni en `values`.

## Paso 3 — Genera los artefactos

- Usa las plantillas de `assets/` como punto de partida (están validadas con `terragrunt hcl fmt` y `hcl validate`):
  - `assets/live-stacks/` — repo live con stacks (root.hcl, account.hcl, region.hcl, stack de ejemplo, `mise.toml`, `.terragrunt-filters`, `.gitignore`).
  - `assets/catalog/` — módulo, unit y stack de catálogo con `values`, `autoinclude` y `update_source_with_cas`.
  - `assets/workflows/` — GitHub Actions (`terragrunt-github-actions.yml`: PR plan / main apply; `terragrunt-drift.yml`) y Azure DevOps (`azure-pipelines-terragrunt.yml` + `templates/instalar-terragrunt.yml`).
  - `assets/Linea_Base_template.md` — plantilla de línea base del proyecto.
- Para generar el esqueleto completo de una vez: `python scripts/scaffold.py --tipo live|catalog --nube aws|azure|gcp --destino <ruta> [--ambientes non-prod,prod] [--region us-east-1] [--ci github|azure-devops|ninguno]`.
- Adapta nombres, regiones e IDs a la línea base; no dejes valores de ejemplo de Gruntwork (`acme`, `123456789012`) en lo entregado sin marcarlos como `# TODO`.
- Cuando el usuario trabaje sobre archivos existentes, aplica los cambios directamente sobre los archivos y entrega el resultado (zip si son varios archivos).

## Paso 4 — Valida antes de entregar

1. Ejecuta `python scripts/tg_lint.py <ruta>`: detecta sintaxis legada, refs sin pinear, mocks peligrosos, includes sin etiqueta, raíz mal nombrada, secretos aparentes, etc. Corrige todo lo de severidad ALTA.
2. Si hay red o binarios disponibles, instala y valida (los comandos no requieren credenciales de nube):
   ```bash
   # instala versiones pineadas (o usa mise install)
   curl -sSL -o /usr/local/bin/terragrunt https://github.com/gruntwork-io/terragrunt/releases/download/v1.2.1/terragrunt_linux_amd64 && chmod +x /usr/local/bin/terragrunt
   terragrunt hcl fmt --check --diff
   terragrunt stack generate            # si hay terragrunt.stack.hcl
   terragrunt hcl validate              # sintaxis HCL de Terragrunt
   terragrunt find --dag                # orden de ejecución esperado
   ```
   `hcl validate` puede fallar en units de catálogo que leen `values` (solo existen al generarse dentro de un stack); valida esos desde el stack generado.
   Para probar filtros Git sin nube: crea un repo temporal, haz un commit con el cambio y ejecuta `terragrunt find --filter '[HEAD^...HEAD]'` (necesita poder descargar las fuentes de los stacks).
3. Si la skill `aegis` está disponible y la entrega crea o cambia IAM, confianzas OIDC, redes/exposición pública, cifrado, backend de estado o pipelines con credenciales de nube, solicita su modo `iac`/`pipeline` antes de entregar y corrige sus hallazgos `confirmed` de severidad media o superior. Sin `aegis`, el checklist ALTA de `11-checklist-revision.md` sigue siendo el mínimo.
4. Resume al usuario: qué se generó, decisiones tomadas, supuestos (`# TODO`) y el comando exacto para el primer `plan`.

## Formato de respuesta

- Código HCL/YAML completo y listo para copiar, con comentarios en español donde aporten.
- Árbol de directorios cuando se cree o cambie la estructura.
- En revisiones: hallazgos con severidad (ALTA/MEDIA/BAJA), archivo:línea, por qué importa y el cambio propuesto (formato de `11-checklist-revision.md`).
- Cuando el usuario pida varios archivos, entrégalos como archivos (zip si son muchos), no solo en el chat.

## Índice de recursos

| Archivo | Contenido |
|---|---|
| `resources/01-modelo-conceptual.md` | Unit, stack (implícito/explícito), catálogo vs live, DAG, cuándo usar qué |
| `resources/02-hcl-referencia.md` | Bloques (`terraform`, `remote_state`, `include`, `locals`, `dependency`, `dependencies`, `generate`, `feature`, `exclude`, `errors`, hooks), atributos y funciones |
| `resources/03-stacks.md` | `terragrunt.stack.hcl`: `unit`, `stack`, `values`, `autoinclude`, `expansion`, `enabled`, `include` en stacks, dependencias hacia stacks, CAS |
| `resources/04-cli-v1.md` | `run`, `--all`, `--graph`, `find`/`list`, `stack *`, `hcl *`, `render`, `dag graph`, `backend *`, `exec`, flags y env vars `TG_*`, caché de providers, reportes |
| `resources/05-filtros-y-git.md` | Lenguaje `--filter` completo, expresiones de Git, `--filter-affected`, `--filter-allow-destroy`, `.terragrunt-filters` |
| `resources/06-layouts-repositorio.md` | Layout live clásico y con stacks, catálogo, scale-catalog, `mise.toml`, versionado |
| `resources/07-backends-y-auth.md` | S3 (`use_lockfile`), azurerm, GCS, bootstrap, OIDC por nube |
| `resources/08-cicd.md` | GitHub Actions (oficial y alternativas), patrón PR→plan / main→apply, drift, Azure DevOps, GitLab |
| `resources/09-migracion-0x-a-1x.md` | Tablas de equivalencias y plan de migración |
| `resources/10-testing-y-calidad.md` | Terratest de catálogo, pre-commit, tflint, `hcl validate`, convenciones |
| `resources/11-checklist-revision.md` | Checklist de revisión por severidad y antipatrones |

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "terragrunt-iac", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill terragrunt-iac --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
