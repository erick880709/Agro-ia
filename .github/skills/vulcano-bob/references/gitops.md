# GitOps (Kustomize + ArgoCD)

Condicional a `decisions.deployment_model: gitops` en `resources/.vulcano/manifest.yaml` (decisión
de `vulcano`, ver `devops-strategy/06-ci-cd.md`). Con `push_pipeline` o sin resolver, no generar
nada de esto.

## Supuesto de arquitectura

GitOps asume un target Kubernetes/contenedores orquestados. Antes de generar, confirmar que el
target real sea Kubernetes — si el proyecto sigue desplegando a Azure Web Apps/App Service o a
una VM, `deployment_model: gitops` es una decisión inconsistente que hay que devolver a Vulcano,
no forzar.

## Qué genera

```powershell
node .claude/skills/vulcano-bob/scripts/render-bob-gitops.mjs `
  --app-name checkout-api --container-port 8080 `
  --image-repository ghcr.io/acme/checkout-api `
  --manifests-repo-url https://github.com/acme/checkout-api `
  --initial-image-tag placeholder `
  --replicas-dev 1 --replicas-qa 2 --replicas-prod 3
```

| Ruta | Contenido |
|---|---|
| `infra/gitops/base/{deployment,service,configmap,kustomization}.yaml` | Base Kustomize — imagen placeholder (`<app-name>:placeholder`), sin namespace ni réplicas fijas (las define cada overlay). |
| `infra/gitops/overlays/{dev,qa,prod}/kustomization.yaml` | Un overlay por ambiente: namespace `<app-name>-<ambiente>`, transformer `images:` que fija el repositorio/tag real, transformer `replicas:` con el conteo operativo de ese ambiente. |
| `infra/gitops/argocd/application-{dev,qa,prod}.yaml` | Un `Application` de ArgoCD por ambiente, apuntando a `infra/gitops/overlays/<ambiente>` con `syncPolicy.automated` (prune + selfHeal). |

Todos los valores (`--app-name`, `--container-port`, `--image-repository`,
`--manifests-repo-url`, réplicas por ambiente) son operativos y obligatorios — no hay defaults
inventados, igual que el resto de flags de los renderers de Bob. Validar el resultado con
`kubectl kustomize infra/gitops/overlays/<ambiente>` (o `kustomize build`) antes de cerrar el
artefacto; si ninguna de las dos herramientas está disponible, degradar a warning como cualquier
otra validación opcional de `references/validacion-estatica.md`.

## Secretos

El `ConfigMap` generado (`base/configmap.yaml`) es solo para configuración no sensible. Los
secretos nunca van al repositorio de manifiestos — se inyectan en runtime desde
`decisions.secrets_manager` (Key Vault / AWS Secrets Manager / Vault) mediante un CSI driver o
External Secrets Operator, fuera del alcance de lo que este renderer genera.

## Cambio en `pipeline-app`: de deploy directo a actualizar manifiestos

Cuando `decisions.deployment_model: gitops`, `pipeline-app` deja de ejecutar un deploy directo —
el step de deploy pasa a actualizar el tag de imagen en el overlay correspondiente y hacer commit/
push, dejando que ArgoCD reconcilie. Renderizado automáticamente por `render-github-actions.mjs` /
`render-gitlab.mjs` con `--deployment-model gitops` (swap del step "Deploy and verify health" por
"Update GitOps manifests" / `ci-deploy.sh` por `ci-update-gitops-manifests.sh`).

**Supuesto declarado:** en modo GitOps, `ci-build.sh` (el script app-specific que el repo ya
posee) es responsable de construir y publicar la imagen de contenedor con el tag `$IMAGE_TAG`
(GitHub Actions: `github.sha`; GitLab: `$CI_COMMIT_SHA`) — Bob nunca genera lógica de `docker
build`/`docker push`, igual que nunca generó el contenido real de `ci-deploy.sh`. Si el build job
del pipeline sigue produciendo solo un `dist/` sin imagen, GitOps no tiene nada que reconciliar;
devolver esa inconsistencia a Vulcano antes de generar.

**Plataforma no soportada:** `pipeline/azure_devops` con la plantilla de referencia
(`azure-pipelines.node-angular-app.template.yml`) despliega a slots de Azure Web App, no a
Kubernetes — `render-azure-devops.mjs` rechaza `--deployment-model gitops` explícitamente en vez
de generar un pipeline inconsistente. Esto es una limitación de esa plantilla de referencia, no de
Azure DevOps como plataforma: un proyecto Azure DevOps + AKS + ArgoCD es válido, simplemente no
está wireado en este adaptador todavía (ver `references/adapters.md`, "Incorporar un adaptador").

## Operación remota (ArgoCD)

`vulcano-operador` mantiene `gitops/argocd` como `planned` — no hay un MCP de ArgoCD ampliamente
adoptado equivalente al de GitHub/GitLab/Azure DevOps. Ver
`.claude/skills/vulcano-operador/references/gitops-argocd.md` para el contrato REST documentado
(pendiente de wiring MCP real) de `reconcile_gitops_app`/`sync_gitops_app`.

## Registro en el manifiesto de Bob (manual)

Igual que `pipeline-dora` (ver `references/dora-collector.md`), `gitops-manifests` no viene
pre-sembrado en `bob-manifest.template.yaml` por ser condicional. Al generarlo, agregar una
entrada `gitops-manifests` a `artifacts` con `depends_on: ["pipeline-app"]`, contrato
`inputs: ["app-package"]` / `outputs: ["gitops-manifests-dev", "gitops-manifests-qa",
"gitops-manifests-prod"]`, y cerrarla localmente (validación de YAML/Kustomize, no de un
`logical_id` con prefijo reconocido por `validate-and-record-bob-artifact.mjs` — registrar el
resultado como evidencia manual hasta que ese script gane un adaptador de validación dedicado).
