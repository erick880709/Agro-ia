# Adaptadores Azure DevOps y Azure

## Prioridad MCP

1. Usar Azure DevOps MCP para organización, proyecto, repositorio, pipelines y runs.
2. Usar Azure MCP únicamente para descubrir o verificar recursos Azure y salud posterior.
3. Si falta una herramienta, registrar `missing_capability`; no inventar su nombre ni construir
   una llamada REST equivalente.

## Brecha verificada: acciones sin herramienta MCP real

El servidor oficial `@azure-devops/mcp` (microsoft/azure-devops-mcp) carga **todos sus dominios
por defecto** (`core`, `work`, `work-items`, `search`, `test-plans`, `repositories`, `wiki`,
`pipelines`, `advanced-security`) — no hay un flag `-d` limitándolos en una instalación estándar.
Verificado 2026-07-21 contra `docs/TOOLSET.md` del propio repo: **ninguno de esos dominios expone
una herramienta para Variable Groups, Environments/approvals, Service Connections ni Branch
Policies**, incluso con permisos de administrador de organización — no es una restricción de
permisos del usuario, es que el servidor no las implementó. `pipelines_write` cubre
`run_pipeline`/`create_pipeline`/`update_build_stage`, nada más.

`create_environment`, `update_variable_group`, `configure_branch_policy`, `approve_deployment` y
`tag_release` están declarados en `mcp_unsupported_actions` de
`adapters/platforms/azure-devops.json` — `plan-operation.mjs` los rechaza con `missing_capability`
antes de llegar siquiera al chequeo de progresión de ambiente. Estos objetos se gestionan hoy
solo desde el portal de Azure DevOps:

| Acción | Dónde hacerlo manualmente |
|---|---|
| `create_environment` | Pipelines > Environments > New environment |
| `update_variable_group` | Pipelines > Library > (grupo) |
| `configure_branch_policy` | Repos > Branches > (rama) > Branch policies |
| `approve_deployment` | Notificación de approval pendiente / Pipelines > Environments > (environment) > Approvals and checks |
| `tag_release` | Repos > Tags > New tag, o `git tag` + push |

Si una versión futura del servidor agrega estas herramientas, quitar la entrada correspondiente
de `mcp_unsupported_actions` en vez de dejarla obsoleta.

### Comportamiento por defecto: generar el script REST, no derivar al portal

Para `platform/azure_devops` específicamente, **el default ya no es el portal manual** — es
generar `infra/bootstrap/setup-azure-devops.sh` con
[`vulcano-bob`](../../vulcano-bob/scripts/render-bob-azure-devops-setup.mjs) (`render-bob-azure-devops-setup.mjs`),
sin necesidad de que el arquitecto lo pida explícitamente. La razón: ya está verificado que el MCP
nunca va a poder hacer esto (no es una brecha temporal), y el script es idempotente y de bajo
riesgo (no toca `approve_deployment` ni nada que requiera aprobar producción). Generarlo apenas se
detecta `create_environment`/`update_variable_group`/`configure_branch_policy` como
`missing_capability` en el `plan` de esta skill.

```powershell
node .claude/skills/vulcano-bob/scripts/render-bob-azure-devops-setup.mjs `
  --terraform-variable-group <nombre> --application-variable-group <nombre> `
  --pipeline-topology <single|per_component> [--components backend,frontend] `
  --min-reviewers <n>
```

Genera Environments **separados por componente** cuando `pipeline_topology: per_component`
(`dev-<c>`/`qa-<c>`/`prod-<c>`, nunca un `prod` compartido — mezclaría los deployment records de
los componentes en el mismo objeto). El script resultante toma en su propia CLI, en tiempo de
ejecución (no en tiempo de generación): `AZDO_PAT` (env var), `--org`, `--project`,
`--repository-id`, `--target-branch`, y dos archivos JSON (`--terraform-variables-file`/
`--application-variables-file`) con los valores reales de cada Variable Group — Bob no inventa
nombres de recursos (`03-naming-conventions.md`), solo la estructura y los nombres de los
Environments/Variable Groups en sí. Ver `.claude/skills/vulcano-bob/references/azure-devops-setup.md`.

**Única excepción al default:** si el arquitecto pide explícitamente el provider Terraform
`microsoft/azuredevops` en su lugar (`azuredevops_variable_group`, `azuredevops_environment`,
`azuredevops_branch_policy_min_reviewers`, `azuredevops_serviceendpoint_*`) — porque el proyecto va
a mantener esto a mediano plazo y prefiere IaC unificado. Extender el alcance de IaC del proyecto a
"plataforma DevOps como código" es una decisión de arquitectura: volver a `vulcano` antes de que Bob
genere ese provider, no asumirlo aquí. Azure CLI (`az pipelines variable-group create`) no es una
alternativa completa — no tiene comando nativo para crear Environments.

Endpoints REST que usa el script (verificados contra Microsoft Learn, no asumidos):

| Objeto | Método + URL | Notas |
|---|---|---|
| Variable Group | `POST https://dev.azure.com/{org}/_apis/distributedtask/variablegroups?api-version=7.1` | A nivel de organización — el scope a un proyecto va en `variableGroupProjectReferences`, no en la URL. |
| Environment | `POST https://dev.azure.com/{org}/{project}/_apis/distributedtask/environments?api-version=7.1` | Body `{name, description}`; la respuesta trae `id` numérico (necesario para variables tipo `prodEnvironmentId`). |
| Branch policy (mínimo de revisores) | `POST https://dev.azure.com/{org}/{project}/_apis/policy/configurations?api-version=7.1` | `type.id = "fa4e907d-c16b-4a4c-9dfa-4906e5d171dd"` ("Minimum approval count"); `settings.scope[].repositoryId` necesita el GUID del repo, no el nombre. |

## Lecturas por acción

| Acción | Lectura previa | Lectura posterior |
|---|---|---|
| `register_pipeline` | repo, rama, pipeline por nombre | pipeline y ruta YAML |
| `create_environment` | environment por nombre | environment e ID |
| `update_variable_group` | grupo y claves, nunca secretos — cubre también rotar una referencia de secreto (URI/path del gestor externo), nunca el valor | grupo y claves |
| `configure_branch_policy` | rama y policies | policy e ID |
| `queue_pipeline` | pipeline, rama, commit y gates | run, logs y artefactos |
| `cancel_pipeline_run` | run y estado | run final |
| `approve_deployment` | approval pendiente del stage/environment | approval e ID, estado del release |
| `promote_release` | release/artefacto ya construido y stage destino; reusa el mecanismo de `queue_pipeline` fijado a ese artefacto, registrado como acción distinta por su riesgo y evidencia | release, stage y estado tras la promoción |
| `rollback_deployment` | último build/artefacto verificado como bueno; reusa el mecanismo de `queue_pipeline` fijado a esa versión anterior | release, stage y estado tras el rollback |
| `tag_release` | rama y commit liberado; verificar que el ref de tag no exista | ref de tag creado |

Habilitar solo dominios MCP necesarios. Sanitizar tokens, headers, valores secretos, connection
strings, URLs firmadas y contenido completo de logs. Conservar IDs, estados, timestamps, commit,
nombres y hashes.

Azure DevOps MCP y Azure MCP son capacidades distintas. La primera es obligatoria para operar
la plataforma; la segunda es opcional salvo que el plan exija verificación cloud.

Fuentes para las acciones de release: [Approvals API](https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/approvals)
y [Git refs API](https://learn.microsoft.com/en-us/rest/api/azure/devops/git/refs) para
`tag_release`. `promote_release` y `rollback_deployment` no tienen endpoint propio: se modelan
como `queue_pipeline` con parámetros distintos (stage destino o versión anterior) y se registran
como acciones lógicas separadas porque su riesgo, evidencia y aprobación requerida son distintos
de un run de CI ordinario.
