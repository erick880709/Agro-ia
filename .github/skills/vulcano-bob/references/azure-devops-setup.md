# Setup de Azure DevOps (Variable Groups, Environments, Branch Policy)

Condicional a `decisions.devops_platform: azure_devops`. Genera el único objeto que cierra la
brecha verificada del MCP oficial `@azure-devops/mcp` (microsoft/azure-devops-mcp): ningún dominio
de su `docs/TOOLSET.md` expone una herramienta para Variable Groups, Environments/approvals o
Branch Policies — ver `.claude/skills/vulcano-operador/references/azure-devops.md` para el detalle
completo de esa brecha. Este es el comportamiento **por defecto** para `azure_devops`, no algo
condicionado a que el arquitecto lo pida.

## Qué genera

```powershell
node .claude/skills/vulcano-bob/scripts/render-bob-azure-devops-setup.mjs `
  --terraform-variable-group vg-psoft-inscripciones-terraform `
  --application-variable-group vg-psoft-inscripciones-application `
  --pipeline-topology per_component --components backend,frontend `
  --min-reviewers 1
```

Un único archivo: `infra/bootstrap/setup-azure-devops.sh` — idempotente (comprueba por nombre
antes de crear cada objeto, se puede volver a correr sin duplicar nada).

| Flag | Origen | Obligatorio |
|---|---|---|
| `--terraform-variable-group` / `--application-variable-group` | Mismos nombres pasados a `render-bob-pipelines.mjs` | Sí |
| `--pipeline-topology` | `decisions.pipeline_topology` de Vulcano | Sí |
| `--components` | Mismos nombres que `--components` de `render-bob-dora.mjs` | Solo si `per_component` |
| `--min-reviewers` | Cantidad de revisores obligatorios ya decidida en `devops-strategy/04-branching-strategy.md` | Sí — no hay default, "no inventar nombres/valores" aplica igual a números |

## Por qué un Environment por componente, nunca compartido

Con `per_component`, genera `dev-<componente>`/`qa-<componente>`/`prod-<componente>` — nunca un
`prod` genérico compartido entre componentes. Un Environment de Azure DevOps es un objeto único a
nivel de proyecto: si `pipelines/backend.yml` y `pipelines/frontend.yml` apuntaran ambos a
`environment: prod`, sus deployment records quedarían mezclados en el mismo objeto, sin forma de
distinguirlos — rompería cualquier lectura de DORA por componente (`render-bob-dora.mjs
--components`) y contradice "una aprobación por componente" cuando `06-ci-cd.md` lo declara así.
Los templates de pipeline (`azure-pipelines.node-backend-app.template.yml` /
`-node-frontend-app-`) ya usan estos mismos nombres — mantenerlos sincronizados si se cambia uno
de los dos lados.

## Separación entre lo que Bob sabe y lo que solo sabe el owner de plataforma

Bob conoce, en tiempo de generación, la **estructura** (qué Environments/Variable Groups deben
existir y con qué nombre) pero no los **valores reales** de las variables de aplicación (nombres
de App Service, health check URLs) — esos vienen de
`infrastructure-as-code/03-naming-conventions.md`, un documento de prosa que Bob no parsea a
decisiones estructuradas. Por eso el script generado recibe esos valores en tiempo de *ejecución*,
no de generación:

```bash
AZDO_PAT=*** ./infra/bootstrap/setup-azure-devops.sh \
  --org <organizacion> --project <proyecto> --repository-id <guid-del-repo> \
  --target-branch refs/heads/main \
  --terraform-variables-file terraform-variables.json \
  --application-variables-file application-variables.json
```

Los dos JSON (`--*-variables-file`) siguen exactamente el esquema de la REST API de Variable
Groups: `{"nombreVariable": {"value": "...", "isSecret": false}, ...}` — construirlos a partir de
`03-naming-conventions.md` y de los health check endpoints reales del código (verificar la ruta
real, ej. `/api/health`, no asumir `/health` genérico). `notificationWebhookUrl` y cualquier otro
secreto real van en el JSON de `application` marcados `"isSecret": true`; el script nunca los
imprime ni los persiste en ningún otro archivo.

## Salida: Environment IDs

Al final imprime el `id` numérico de cada Environment creado (`nombre -> id`) — cargarlos a mano
en el Variable Group de aplicación como `prodEnvironmentId<Componente>` (usados por
`render-bob-dora.mjs` para leer `environmentdeploymentrecords` por componente vía
`System.AccessToken`).

## Registro en el manifiesto de Bob (manual)

Igual que `pipeline-dora`/`gitops-manifests`, este script no viene pre-sembrado en
`bob-manifest.template.yaml` por depender de una plataforma específica. No se registra como
artefacto propio del catálogo de 26 archivos — anotar su generación en la descripción del
`OP-NNN` correspondiente a los Variable Groups/Environments pendientes.
