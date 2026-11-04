# Adaptadores de Vulcano Bob

Bob es un núcleo de generación local con dimensiones independientes:

| Dimensión | Decisión fuente | Responsabilidad |
|---|---|---|
| `cloud` | `decisions.cloud_provider` | Providers, backend bootstrap y patrones del proveedor. |
| `iac` | `decisions.iac` | Lenguaje, estructura, pruebas y validadores de IaC. |
| `pipeline` | `decisions.devops_platform` | Sintaxis CI/CD, renderer y operador remoto. |
| `gitops` | `decisions.deployment_model: gitops` | Manifiestos de reconciliación (Kustomize/Helm values) y su controlador (ArgoCD/Flux). No sustituye `pipeline`: convive con él para CI, y reemplaza solo el mecanismo de deploy. |
| `chatops` | `decisions.notification_channel` | Notificación de resultado de pipeline y promociones a un canal (Slack/Teams). |

`adapters/registry.json` relaciona cada ID con un descriptor. El descriptor declara `implemented`
o `planned`; Bob solo genera con los implementados. `github` se normaliza a `github_actions`, pero
esa normalización no habilita soporte.

## Selección actual

| Adaptador | Estado | Alcance |
|---|---|---|
| `cloud/azure` | `implemented` | Terraform con `azurerm` o `azapi`. |
| `cloud/aws` | `implemented` | Provider AWS, backend S3 con lockfile y bootstrap seguro. |
| `cloud/gcp` | `implemented` | Provider `google`/`google-beta`, backend GCS con locking nativo y bootstrap seguro (`gcp-backend.bootstrap.template.sh`). |
| `iac/terraform` | `implemented` | Perfil, pruebas plan/mock y validación local. |
| `pipeline/azure_devops` | `implemented` | Tres o cuatro pipelines (según `decisions.pipeline_topology`), renderer local, operador `vulcano-operador`, `supports_progressive_delivery: true` (analysis gate + rollback en `DeployProd`), `supports_policy_as_code: true` (step por ambiente en `infra/pipelines/iac.yml`), `supports_notifications: true` (stage `NotifyResult` final, `condition: always()`) y `supports_pipeline_topology: per_component` (`--pipeline-topology per_component` renderiza `azure-pipelines.node-backend-app.template.yml` + `azure-pipelines.node-frontend-app.template.yml` en vez de la plantilla combinada — cada uno con su propio `paths.include`). Ruta de destino de los pipelines de aplicación parametrizable con `--app-pipeline-dir <carpeta>` (vacío = raíz, comportamiento histórico); Azure DevOps no exige una ubicación fija. |
| `pipeline/github_actions` | `implemented` | Workflows, renderer, OIDC, validación semántica, `supports_progressive_delivery: true`, `supports_policy_as_code: true` (step en el job `plan`), `supports_notifications: true` (job `notify`, `if: always()`, `needs: deploy`) y `supports_gitops: true` (step `deploy` cambia de "Deploy and verify health" a "Update GitOps manifests" con `--deployment-model gitops`). |
| `pipeline/gitlab` | `implemented` | Includes GitLab CI, ID tokens, renderer, validación semántica, `supports_progressive_delivery: true`, `supports_policy_as_code: true` (script en `.terraform_plan`), `supports_notifications: true` (job `application_notify`, `when: always`) y `supports_gitops: true` (mismo swap de script que GitHub Actions). |
| `gitops/argocd` (Bob) | `implemented` | Genera manifiestos Kustomize (base/overlays por ambiente) y `Application` de ArgoCD vía `render-bob-gitops.mjs` — ver `references/gitops.md`. No incluye operación remota. |
| `pipeline/azure_devops` + GitOps | `no soportado` | `render-azure-devops.mjs` rechaza `--deployment-model gitops` explícitamente: la plantilla de referencia despliega a slots de Azure Web App, no a Kubernetes. Ver `references/gitops.md`. |
| `pipeline/github_actions`/`pipeline/gitlab` + `pipeline_topology: per_component` | `no soportado` | Solo `azure_devops` divide la plantilla de aplicación en dos. Registrar `missing_capability` si un manifiesto pide `per_component` con estas plataformas — no improvisar un segundo workflow/job duplicando el existente. |
| `chatops/slack` | `planned` | Catalogado para no bloquear silenciosamente `decisions.notification_channel: slack`; sin integración todavía. |

Un adaptador `planned` no es una promesa de fecha — es una forma de que Bob reconozca la decisión
del arquitecto (`decisions.notification_channel`) y responda `unsupported_adapter` con un mensaje
claro, en vez de ignorarla o improvisar un artefacto sin renderer real detrás. `gitops/argocd` es
`implemented` aquí en Bob (genera manifiestos locales) pero sigue `planned` en
`vulcano-operador` (sin MCP de ArgoCD real para `reconcile`/`sync`) — son capacidades distintas
que pueden madurar en momentos distintos.

## Ubicación de los pipelines de aplicación

`decisions.pipeline_topology` (`vulcano`, `06-ci-cd.md` §Integración Continua) y la carpeta
donde viven los archivos de pipeline **no se asumen** — cada plataforma tiene una restricción
real distinta, no es solo preferencia de organización:

- **Azure DevOps:** sin ubicación fija — `--app-pipeline-dir <carpeta>` en `render-azure-devops.mjs`
  controla dónde se generan (vacío = raíz, compatibilidad hacia atrás). Con
  `pipeline_topology: per_component`, genera `<carpeta>/backend.yml` y `<carpeta>/frontend.yml`
  en vez de un `azure-pipelines.yml` combinado.
- **GitHub Actions:** GitHub solo ejecuta workflows dentro de `.github/workflows/` — no existe
  parámetro de carpeta en `render-github-actions.mjs` porque cualquier otra ubicación produce un
  workflow que la plataforma ignora en silencio.
- **GitLab CI:** `.gitlab-ci.yml` vive en la raíz salvo que el proyecto reconfigure el "CI/CD
  configuration file" en su configuración (un ajuste de plataforma, fuera del alcance de Bob) —
  los `include:` (`iac.yml`, `drift.yml`) sí ya viven organizados en `.gitlab/ci/`.

No generalizar el parámetro de carpeta a GitHub Actions/GitLab solo por simetría con Azure
DevOps: produciría un artefacto que la plataforma no reconoce, peor que mantener la asimetría.

Resolver antes del preflight:

```powershell
node .claude/skills/vulcano-bob/scripts/resolve-bob-adapters.mjs
```

Usar `--allow-planned` únicamente para comprobar una selección futura. El resultado `planned` no
autoriza generación ni operación.

## Incorporar un adaptador

1. Agregar un descriptor y registrarlo, sin modificar el núcleo para una combinación específica.
2. Implementar sus assets, renderer y validación estática con fixtures representativos.
3. Declarar constraints de compatibilidad, como providers requeridos y backends soportados.
4. Cambiar el descriptor a `implemented` solo cuando las pruebas de generación y validación pasen.
5. Extender `vulcano-operador` con el adaptador de plataforma, su allowlist y pruebas MCP; no crear
   otra skill por proveedor.

Una nube no necesita operador propio para generar Terraform. La operación remota siempre se
enruta por un solo `vulcano-operador`. Por eso AWS + GitHub no requiere `vulcano-github` ni
`vulcano-aws-github`.
