# Orden, contratos y dependencias

El manifiesto v4 es el plan de implementación legible por máquina. Cada artefacto declara ruta,
`depends_on`, inputs, outputs, fuentes y validación. No mantener un segundo plan duplicado.

## Catálogo del adaptador actual

| Orden | `logical_id` | Ruta | Dependencias principales |
|---:|---|---|---|
| 1 | `bootstrap-backend` | `infra/bootstrap/create-backend.sh` | ninguna |
| 2..N | `module-<nombre>` | ruta `Origen` de `06-modules.md` | outputs productores de sus inputs |
| N+1 | `env-dev` | `infra/environments/dev/` | todos los módulos compilados |
| N+2 | `env-qa` | `infra/environments/qa/` | todos los módulos compilados |
| N+3 | `env-prod` | `infra/environments/prod/` | todos los módulos compilados |
| N+4 | `pipeline-iac` | `infra/pipelines/iac.yml` | ambientes completos |
| N+5 | `pipeline-drift` | `infra/pipelines/drift.yml` | ambientes completos, nunca apply |
| N+6 | `pipeline-app` (o `pipeline-app-<componente>` con `decisions.pipeline_topology: per_component`, uno por unidad desplegable) | ruta declarada por el adaptador `pipeline`, ver `references/adapters.md` §Ubicación de los pipelines de aplicación | ambientes y comandos de aplicación |
| N+7 | `secrets-bindings` | condicional — ruta declarada por el adaptador `cloud` seleccionado | `env-*` correspondiente; condicional a `decisions.secrets_manager` ≠ `none` |
| N+8 | `gitops-manifests` | condicional — ruta declarada por el adaptador `gitops` seleccionado | `pipeline-app`; condicional a `decisions.deployment_model: gitops` |
| N+9 | `dora-collector` | condicional — ruta declarada por el adaptador `pipeline` seleccionado | `pipeline-app`; condicional a `decisions.dora_collection_method: automated` |

Las rutas de pipeline son parte del adaptador seleccionado, no del núcleo. Al implementar otro
adaptador se reemplazan esas entradas desde su plantilla, sin duplicar el catálogo de módulos ni
ambientes.

## Artefactos condicionales

Estos tres artefactos no forman parte del catálogo base — solo entran al plan cuando la decisión
que los origina ya quedó resuelta en `resources/.vulcano/manifest.yaml`. Si la decisión sigue
`null`, no se listan ni como `pending`: no existen todavía en el plan, igual que `03-tracing.md`
condicional en Vulcano. Si la decisión está resuelta pero el adaptador de la dimensión (`gitops`,
`chatops`) sigue `planned` (ver `references/adapters.md`), el artefacto sí entra al plan como
`pending` y queda bloqueado con `unsupported_adapter` — la diferencia importa para no ocultarle al
arquitecto una decisión que tomó pero que Bob todavía no puede materializar.

- **`secrets-bindings`**: condicional a `decisions.secrets_manager` ≠ `none`. Contrato: input
  `SECRETS_MANAGER_REFERENCE` (nunca el valor del secreto, solo la referencia/URI), output
  `secret-bindings` consumido por cada `env-*` que declare secretos en `08-secrets-management.md`.
- **`gitops-manifests`**: condicional a `decisions.deployment_model: gitops`. Se genera con
  `node .claude/skills/vulcano-bob/scripts/render-bob-gitops.mjs` (Kustomize base/overlays +
  `Application` de ArgoCD por ambiente) — no con `render-bob-pipelines.mjs`. Contrato: input
  `app-package` (el mismo artefacto que hoy consume `pipeline-app`), output
  `gitops-manifests-<ambiente>` por cada ambiente. Cuando este artefacto está `generated`,
  `pipeline-app` deja de declarar el paso de deploy — pasa a actualizar el tag de imagen en el
  overlay y hacer commit/push, no a desplegar directamente (ya wireado en
  `render-github-actions.mjs`/`render-gitlab.mjs` con `--deployment-model gitops`; rechazado
  explícitamente en `render-azure-devops.mjs`, ver `references/gitops.md`).
- **`pipeline-dora`** (logical_id con prefijo `pipeline-` a propósito, reutiliza la validación
  semántica de pipelines): condicional a `decisions.dora_collection_method: automated`. Se genera
  con `node .claude/skills/vulcano-bob/scripts/render-bob-dora.mjs` — no con
  `render-bob-pipelines.mjs`, que solo cubre `pipeline-iac`/`pipeline-drift`/`pipeline-app`.
  Contrato: sin inputs (usa el token nativo del runtime CI), output `dora-metrics-dataset`
  consumido por `observability/01-monitoring.md` como fuente citable de las cinco métricas. Ver
  `references/dora-collector.md` para el detalle de endpoints, aproximaciones declaradas por
  métrica y el paso manual de registrarlo en `bob-manifest.yaml`.

`pipeline-app` gana, además, un contrato condicional cuando `decisions.deployment_strategy` ≠
`rolling` (canary o blue-green): input adicional `ANALYSIS_METRICS_SOURCE` (de dónde lee la señal
de análisis automático) y output adicional `rollout-status`. No agregar estos campos al contrato
de un adaptador `pipeline` que no declare soporte para despliegue progresivo — ver
`references/adapters.md`.

No existe `terraform-versions`: `versions.tf`, provider configuration y `.terraform.lock.hcl`
pertenecen a cada `env-*`, porque cada ambiente es un root module independiente.

Los módulos de observabilidad son obligatorios cuando los documentos definen Log Analytics,
Application Insights, Action Groups, diagnostic settings o alertas. Si `04-terraform-structure.md`
y `06-modules.md` todavía no los incluyen, el preflight debe devolver esa omisión a Vulcano.

## Grafo

Validar el grafo antes de escribir código:

1. Cada dependencia debe apuntar a un `logical_id` existente.
2. Ningún artefacto puede depender de sí mismo.
3. El grafo debe ser acíclico.
4. Un artefacto `generated` solo puede depender de `generated` u `omitted` justificado.
5. Cada input derivado de otro artefacto debe corresponder a un output declarado por ese artefacto.

Si Vulcano separa observabilidad en base y reglas, conservar esa separación: la base crea
workspace/App Insights/Action Group y las reglas consumen IDs ya creados. Bob no crea esos
módulos por su cuenta; deben existir en `06-modules.md`.

## Contrato de módulos

- Copiar inputs/outputs de la definición aprobada.
- No añadir inputs de conveniencia sin fuente.
- `compile-bob-contract.mjs` solo infiere `depends_on` de dos fuentes verificables: que un input
  coincida por nombre con un output declarado por otro módulo, o una anotación explícita
  `- **Depende de:** \`otro-modulo\`.` (o `- **Depende de:** ninguno.`) en el bloque del módulo,
  entre `Outputs` y `Origen`. Nunca infiere dependencias adivinando el nombre de un módulo dentro
  de un texto libre de descripción: esa heurística producía falsos positivos y negativos cuando
  la prosa no coincidía exactamente con el `logical_id`. Si el nombre en `Depende de` no existe en
  el catálogo, el compilador bloquea con error en vez de generar un grafo incorrecto.
- Agregar IDs necesarios para diagnostic settings o despliegue solo después de que Vulcano los
  incorpore al contrato.
- Si código existente cambia de dirección, usar `moved` blocks; si el recurso ya vive en Azure
  pero no está en state, producir instrucciones de `import`, nunca recrearlo silenciosamente.
- Tratar cambios de dirección, backend o provider como migraciones explícitas con rollback.
