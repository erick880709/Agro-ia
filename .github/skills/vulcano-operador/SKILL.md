---
name: vulcano-operador
metadata:
  display-name: "Operador de plataformas"
  capability: "Operación de plataformas"
  capability-summary: "Verifica y ejecuta operaciones autorizadas en repositorios y plataformas de entrega."
description: >
  Reconcilia, planea, autoriza, ejecuta y verifica operaciones remotas derivadas de artefactos
  cerrados por Vulcano Bob, seleccionando adaptadores independientes de plataforma y nube.
  Usarla cuando bob-manifest.yaml esté completo y pidan observar o cambiar repositorios,
  pipelines/workflows, environments, variables, políticas, runs u otros objetos soportados por
  el adaptador. Trabaja en lectura por defecto, exige autorización explícita por acción, descubre
  capacidades MCP antes de usarlas y nunca crea por MCP recursos administrados por Terraform.
---

# Vulcano Operador

## Agente top-level

El agente [`vulcano-operador`](../../agents/vulcano-operador.agent.md) expone esta skill para operación
remota. Debe iniciarlo el usuario (`disable-model-invocation: true`); este `SKILL.md` mantiene el
contrato canónico y la autorización continúa siendo individual por acción y `scope_hash`.
[`vulcano-orchestrator`](../../agents/vulcano-orchestrator.agent.md) solo puede preparar el handoff: no
invoca esta fase, no autoriza acciones y no opera remotamente.

Operar planos de control remotos sin mezclar generación local, tecnología CI/CD y proveedor de
nube. Mantener el ciclo común:

`reconcile → plan → authorize → operate → verify`

No saltar fases ni interpretar la disponibilidad de un adaptador como permiso para mutar.

## Contrato de entrada

Exigir:

1. `resources/.vulcano/bob-manifest.yaml` con cierre estricto exitoso.
2. `adapter_selection` de Bob coherente con el manifiesto de Vulcano.
3. Adaptadores `platform` y `cloud` con estado `implemented`.
4. Coordenadas requeridas por la plataforma confirmadas, sin credenciales persistidas.

## Instalación y configuración del MCP — antes de `reconcile`

Sin el MCP de plataforma conectado, ningún comando de esta skill puede avanzar más allá de
`missing_capability` (ver §Contrato de entrada). Servidores oficiales, product-supported por
Microsoft — no alternativas de comunidad:

| MCP | Capacidad | Paquete | Comando | Autenticación |
|---|---|---|---|---|
| Azure DevOps ([microsoft/azure-devops-mcp](https://github.com/microsoft/azure-devops-mcp)) | `platform_mcp` (obligatorio) | `@azure-devops/mcp` | `npx -y @azure-devops/mcp <organización>` | Interactivo por navegador (default) · `az login` · PAT (`--authentication pat` + `PERSONAL_ACCESS_TOKEN` en base64 `<email>:<pat>`) · token en `ADO_MCP_AUTH_TOKEN` |
| Azure ([Azure MCP Server](https://www.npmjs.com/package/@azure/mcp)) | `cloud_mcp` (opcional, solo si el plan exige verificación de nube) | `@azure/mcp` | `npx -y @azure/mcp@latest server start` | `az login` (Azure CLI) — más simple, evita manejar un PAT |

Registrar en Claude Code (Windows necesita el wrapper `cmd /c` para que `npx` funcione como
proceso stdio):

```powershell
claude mcp add --transport stdio azure-devops --scope project -- cmd /c npx -y @azure-devops/mcp <organización>
claude mcp add --transport stdio azure --scope project -- cmd /c npx -y @azure/mcp@latest server start
```

Si se usa PAT en vez de login interactivo/`az login`, pasar el token vía `--env` (nunca en texto
plano en el comando ni persistido en ningún manifiesto de este kit):

```powershell
claude mcp add --transport stdio azure-devops --scope project --env PERSONAL_ACCESS_TOKEN=<base64 email:pat> -- cmd /c npx -y @azure-devops/mcp <organización> --authentication pat
```

**Después de agregar un MCP server hace falta recargar/reiniciar el cliente de Claude Code antes
de que sus herramientas aparezcan** — no asumir que ya está disponible solo porque el comando de
registro no dio error. Confirmar buscando las herramientas del servidor antes de invocar
`record-reconciliation.mjs`; si siguen sin aparecer tras el reload, registrar `missing_capability`
en vez de reintentar a ciegas.

Resolver antes de inicializar:

```powershell
node .claude/skills/vulcano-operador/scripts/resolve-operator-adapters.mjs
```

Inicializar `resources/.vulcano/operations-manifest.yaml`:

```powershell
node .claude/skills/vulcano-operador/scripts/init-operations-manifest.mjs `
  --organization <org> --project <proyecto> --repository <repo> --branch <rama>
```

Usar `--migrate` para llevar un manifiesto operacional schema v1 a v2 sin perder acciones ni
evidencia. Leer [`references/state-and-migration.md`](references/state-and-migration.md).

## Selección de adaptadores

Leer [`references/adapter-contract.md`](references/adapter-contract.md). Resolver dos dimensiones:

- `platform`: repositorios, pipelines/workflows, environments, políticas, variables y runs.
- `cloud`: verificación posterior de recursos y salud; no reemplaza Terraform.

Usar únicamente adaptadores `implemented`. Actualmente están implementados
`platform/azure_devops`, `platform/github_actions`, `platform/gitlab`, `cloud/azure`, `cloud/aws`
y `cloud/gcp`. `gitops/argocd` y `chatops/slack` están catalogados como `planned` (ver
`references/adapter-contract.md`): resolverlos falla con `missing_capability`, nunca se
improvisa con REST/CLI. El descriptor no sustituye el prerrequisito de conexión MCP: descubrir la
capacidad indicada y fallar con `missing_capability` cuando no exista.

## `reconcile` — lectura predeterminada

Leer la referencia MCP declarada por los adaptadores. Descubrir primero herramientas disponibles;
no inventar nombres ni sustituir MCP por REST/CLI sin autorización expresa. Consultar solo el
estado necesario y guardar un snapshot sanitizado temporal.

Registrar capacidades genéricas; se aceptan flags anteriores solo por compatibilidad:

```powershell
node .claude/skills/vulcano-operador/scripts/record-reconciliation.mjs `
  --platform-mcp available --cloud-mcp available `
  --tool azure-devops-mcp --snapshot-file <ruta>
```

Si falta `platform_mcp`, registrar `missing_capability` y detenerse. `cloud_mcp` puede ser opcional
cuando la acción no requiere verificación de nube.

## `plan` — diff sin efectos

Crear una acción mínima. El tipo debe pertenecer al allowlist del adaptador de plataforma; el
riesgo lo asigna el descriptor, nunca un argumento del usuario.

```powershell
node .claude/skills/vulcano-operador/scripts/plan-operation.mjs `
  --id OP-ACT-001 --type register_pipeline --logical-id pipeline-iac `
  --target-ref org/project/repository/pipeline-iac --desired-file <ruta> `
  --summary "Registrar infra/pipelines/iac.yml"
```

`queue_pipeline`, `approve_deployment` y `promote_release` exigen además `--environment
<dev|qa|prod>` — el script bloquea con `Progresión bloqueada` si se intenta promover a `qa`/`prod`
sin una acción `verified` del ambiente anterior para el mismo `logical_id`. Ver
[`references/operational-safety.md`](references/operational-safety.md) §Progresión de ambiente.

Conservar hashes del estado observado y deseado, no payloads persistentes.

## `authorize` — gate humano

Leer [`references/operational-safety.md`](references/operational-safety.md). Mostrar ID, plataforma,
target, acción, riesgo, diff y `scope_hash`. Exigir confirmación inequívoca para ese ID o target.
La autorización expira y queda ligada al hash de Bob y al alcance exacto.

```powershell
node .claude/skills/vulcano-operador/scripts/authorize-operation.mjs `
  --id OP-ACT-001 --authorized-by <identidad> --confirmation-file <ruta>
```

## `operate` — una acción autorizada

1. Validar el manifiesto y la autorización.
2. Releer el target para evitar duplicados o cambios concurrentes.
3. Ejecutar `begin-operation.mjs --id OP-ACT-NNN` inmediatamente antes del MCP.
4. Invocar exactamente una herramienta MCP para una acción.
5. No ampliar plataforma, nube, target, variables ni rama.
6. Persistir solo evidencia sanitizada y hashes con `record-operation-evidence.mjs`.

Nunca aprobar producción, aplicar Terraform directamente ni recrear con MCP recursos declarados
en IaC. Ante timeout o resultado ambiguo, volver a `reconcile` antes de reintentar.

## `verify` — lectura posterior

Releer mediante el adaptador de plataforma el objeto modificado o run. Usar el adaptador cloud
solo para configuración no secreta y salud posterior. Registrar verificación con el mismo
`scope_hash`; una ejecución exitosa sin lectura posterior queda `succeeded`, no `verified`.

## Cierre

```powershell
node .claude/skills/vulcano-operador/scripts/validate-operations-manifest.mjs --strict
```

Separar observado, propuesto, autorizado, ejecutado, verificado, fallido y bloqueado. No afirmar
una mutación sin evidencia MCP registrada.

## Límites no negociables

- No recibir ni persistir PAT, tokens, contraseñas, secretos o connection strings.
- No autorizar más de una acción con la misma confirmación.
- No aprobar producción ni el propio cambio generado por el agente.
- No usar MCP de nube para crear recursos administrados por Terraform.
- No habilitar adaptadores `planned` con `--allow-planned` para operar; ese flag solo diagnostica.
- No reintentar una mutación ambigua antes de reconciliar.

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "vulcano-operador", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill vulcano-operador --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
