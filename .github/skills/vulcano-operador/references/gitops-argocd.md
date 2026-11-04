# Operación de ArgoCD (planned — sin MCP confirmado)

`gitops/argocd` permanece `planned`: a diferencia de GitHub/GitLab/Azure DevOps, no hay un MCP de
ArgoCD ampliamente adoptado y estandarizado — descubrir la capacidad (`argocd_mcp`) antes de
asumir que existe, y fallar con `missing_capability` si no aparece. No sustituir por llamadas
directas a la REST API de ArgoCD ni por `argocd` CLI sin autorización explícita: el mismo
principio de "descubrir MCP antes de usarlo" que rige el resto de esta skill aplica aquí.

Este documento fija el contrato **objetivo** (qué debería hacer cada acción cuando exista un MCP
real) para que habilitar el adaptador, el día que la capacidad aparezca, sea agregar routing —
no rediseñar el contrato.

## Acciones objetivo

| Acción lógica | Riesgo | Mapeo REST de ArgoCD (referencia, no invocar directo sin MCP) |
|---|---|---|
| `reconcile_gitops_app` | `configure` | `GET /api/v1/applications/{name}` — lee estado de sync/health actual, sin mutar. |
| `sync_gitops_app` | `execute` | `POST /api/v1/applications/{name}/sync` — aplica el estado ya reconciliado por Kustomize (generado por `vulcano-bob`, ver `references/gitops.md`); nunca crea recursos fuera de lo que el repositorio de manifiestos ya declara. |

`reconcile_gitops_app` es de solo lectura pese a clasificarse `configure` (no `read`): en el
modelo de esta skill, forzar una resincronización (`refresh`) cambia el estado interno del
`Application` aunque no toque el cluster, así que sigue el mismo ciclo de autorización que
cualquier acción `configure`.

## Requisitos antes de habilitar

1. Confirmar que existe un MCP de ArgoCD real, mantenido, con alcance documentado — no una
   integración ad hoc.
2. `required_target_fields`: `organization`/`repository` (repo de manifiestos) + `application`
   (nombre del `Application` de ArgoCD, uno por ambiente — ver `application-<ambiente>.yaml` que
   genera `vulcano-bob`).
3. Sanitizar cualquier token/credential del cluster de destino; el operador nunca recibe
   kubeconfig ni credenciales del cluster.
4. Fixtures de reconcile/sync/autorización/verificación equivalentes a las que ya existen para
   GitHub/GitLab/Azure DevOps, antes de cambiar `status` a `implemented`.

## Relación con Terraform

Si el cluster de Kubernetes en sí (AKS/EKS/GKE) está declarado en Terraform, `sync_gitops_app`
nunca reemplaza esa capa — solo reconcilia los manifiestos de aplicación (Deployment/Service/
ConfigMap) contra el cluster ya existente. Ver la regla general en `SKILL.md` §Límites no
negociables: "No usar MCP de nube para crear recursos administrados por Terraform" aplica igual
aquí para el propio cluster.
