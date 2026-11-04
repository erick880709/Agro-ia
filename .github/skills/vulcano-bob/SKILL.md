---
name: vulcano-bob
metadata:
  display-name: "Constructor de infraestructura"
  capability: "Generación de infraestructura"
  capability-summary: "Genera y valida archivos de infraestructura y automatización de entregas desde un diseño aprobado."
description: >
  Genera y valida localmente los artefactos de infraestructura y CI/CD que Vulcano ya definió.
  Úsala cuando exista resources/.vulcano/manifest.yaml y pidan materializar la definición como
  IaC, módulos, ambientes o pipelines; continuar una generación previa;
  reconciliar código generado con los documentos; o cerrar el segundo paso de Vulcano. Primero
  comprueba que la definición esté completa, sea internamente consistente y resuelva adaptadores
  implementados de nube, IaC y CI/CD, incluido el perfil de versiones, pruebas y Registry. No
  redecide arquitectura ni resuelve contradicciones:
  devuelve esos bloqueos a Vulcano. En su modo predeterminado solo escribe archivos y ejecuta
  validaciones locales. Cuando pidan reconciliar, registrar o ejecutar en una plataforma remota,
  cierra primero la generación y delega al operador indicado por el adaptador de pipeline.
---

# Vulcano Bob

## Agente top-level

El agente [`vulcano-bob`](../../agents/vulcano-bob.agent.md) ejecuta esta skill en un worktree aislado.
Este `SKILL.md` conserva el contrato canónico; el agente materializa y valida archivos locales, pero no
redecide la definición de Vulcano ni convierte el cierre en autorización remota.
[`vulcano-orchestrator`](../../agents/vulcano-orchestrator.agent.md) puede iniciar esta fase después del
gate de Vulcano y comprobar su cierre, sin editar directamente los artefactos.

Actuar como ingeniero de plataforma que convierte la definición aprobada por `vulcano` en código
ejecutable. Mantener tres estados separados:

1. **Definido:** los documentos requeridos existen y están marcados `generated` u `omitted`.
2. **Implementable:** las decisiones no son ambiguas, contradictorias ni cíclicas.
3. **Generado:** los archivos existen, conservan trazabilidad y pasan validación local.

No declarar un artefacto generado cuando solo existe un esqueleto, comentario o placeholder.

## Prerrequisitos

Todos los scripts leen/escriben YAML delegando en Python; sin esto, ningún comando de esta skill
funciona:

- **Python 3 con PyYAML** (`pip install pyyaml`). Obligatorio: sin él, cualquier script falla al
  cargar o guardar `bob-manifest.yaml`.
- **`jsonschema`** (`pip install jsonschema`). Opcional: sin él, `validate-vulcano-bob.mjs` solo
  aplica sus validaciones internas y deja un warning.

Para marcar un artefacto `generated`, `validate-and-record-bob-artifact.mjs` exige la herramienta
real correspondiente; sin ella el comando falla en vez de fabricar éxito:

- **Terraform CLI**, obligatorio para `module-*` y `env-*`.
- **Bash**, obligatorio para `bootstrap-backend`.

Opcionales, degradan a warning/`skipped` si faltan (no bloquean el cierre no estricto, pero quedan
visibles como evidencia ausente):

- `tflint` (lint Terraform), `trivy` (`trivy config`, preferido), `tfsec` o `checkov` como
  alternativas (seguridad IaC), `shellcheck` (lint del bootstrap), `gitleaks` (secret scanning
  especializado). **Excepción:** si `decisions.policy_engine` en el manifiesto de Vulcano es
  distinto de `none` (`opa` o `conftest`), la CLI correspondiente deja de ser opcional para ese
  proyecto — su ausencia bloquea la generación de artefactos de IaC en vez de degradar a warning,
  porque el arquitecto ya decidió que ese gate es parte del pipeline.
- Skills oficiales `terraform-style-guide`, `terraform-test`, `azure-verified-modules` y
  `refactor-module`, según el perfil. AVM es obligatorio cuando Vulcano lo seleccionó.
- Terraform MCP para consultar Registry en lectura. No es requisito para Registry público; una
  dependencia privada no resoluble puede convertir su ausencia en bloqueo.

**Instalación — resolver primero cuáles aplican a *este* proyecto, no instalar la tabla completa
por reflejo.** Cada fila es condicional a algo del manifiesto de Vulcano o del código generado:

| Herramienta | Aplica cuando | Windows (winget) | macOS (Homebrew) | Linux (apt, si existe paquete) |
|---|---|---|---|---|
| tflint | `decisions.iac: terraform` (casi siempre, es la única IaC soportada hoy) | `winget install TerraformLinters.tflint` | `brew install tflint` | sin paquete oficial — ver [instrucciones del proyecto](https://github.com/terraform-linters/tflint#installation) |
| trivy | igual que arriba, y es la opción **preferida** de seguridad IaC — no instalar también `tfsec`/`checkov` sin motivo | `winget install AquaSecurity.Trivy` | `brew install trivy` | requiere el repo APT de Aqua Security — ver [instrucciones del proyecto](https://aquasecurity.github.io/trivy/latest/getting-started/installation/) |
| tfsec / checkov | solo si el proyecto ya usa uno de estos en vez de `trivy` (no instalar los tres) | — | `brew install tfsec` / `brew install checkov` | ver instrucciones de cada proyecto |
| shellcheck | el proyecto genera scripts bash (`bootstrap-backend`, `ci-*.sh` de notificación/rollback/policy) — comprobar `ls scripts/*.sh infra/bootstrap/*.sh` antes de instalar si no es obvio | `winget install koalaman.shellcheck` | `brew install shellcheck` | `apt install shellcheck` |
| gitleaks | prácticamente siempre útil (secret scanning genérico, no depende de una decisión puntual) | `winget install Gitleaks.Gitleaks` | `brew install gitleaks` | sin paquete oficial — descargar binario del [release](https://github.com/gitleaks/gitleaks/releases) |
| opa | `decisions.policy_engine: opa` — deja de ser opcional para ese proyecto (bloquea IaC sin ella) | `winget install open-policy-agent.opa` | `brew install opa` | descargar binario del [release](https://github.com/open-policy-agent/opa/releases) |
| conftest | `decisions.policy_engine: conftest` — igual de obligatoria si es la elegida | sin paquete en winget — descargar binario del [release](https://github.com/open-policy-agent/conftest/releases) | `brew install conftest` | descargar binario del [release](https://github.com/open-policy-agent/conftest/releases) |

Con `decisions.policy_engine: none` (como en la mayoría de proyectos que aún no lo necesitan), no
instalar ni `opa` ni `conftest` — no aplican y quedarían sin uso. Antes de instalar cualquier fila,
confirmar la decisión real en `resources/.vulcano/manifest.yaml` en vez de asumir el perfil de otro
proyecto.

**Config opcional de `gitleaks`:** si el repo define `.gitleaks.toml` en su raíz, este validador lo
pasa explícito con `--config` (gitleaks no lo autodescubre al invocarse con `--no-git --source
<ruta>` fuera de cwd) — útil para un `[allowlist]` de falsos positivos conocidos (ej. fixtures
`*.tftest.hcl` que comparan nombres de secretos, no valores reales) sin tocar el ruleset por
defecto. Ver `.gitleaks.toml` de este repo como ejemplo.

## Límites

- Separar siempre las dimensiones `cloud`, `iac`, `pipeline`, `gitops` y `chatops`; no crear una
  implementación por producto cartesiano como `vulcano-aws-github`.
- Usar únicamente adaptadores con `status: implemented` en `adapters/`. Actualmente están
  implementados `cloud/azure`, `cloud/aws`, `cloud/gcp`, `iac/terraform`, `pipeline/azure_devops`,
  `pipeline/github_actions`, `pipeline/gitlab` y `gitops/argocd` (genera manifiestos Kustomize y
  `Application` locales vía `render-bob-gitops.mjs`; no incluye operación remota — ver
  `vulcano-operador`, donde `gitops/argocd` sigue `planned` para `reconcile`/`sync`).
  `chatops/slack` está catalogado como `planned`: existe para que Bob reconozca la decisión y
  falle con `unsupported_adapter`, no para generar con él.
- Detenerse con `unsupported_adapter` o `incompatible_adapter` cuando falte una dimensión o el
  perfil no sea compatible. No traducirla improvisando. Esto incluye
  `decisions.notification_channel` distinto de `none` mientras su adaptador siga `planned`:
  generar solo el `pipeline-app` de CI/CD tradicional y registrar la brecha como
  `missing_capability`, nunca simular integración de notificaciones sin renderer real.
- No ejecutar `terraform plan`, `terraform apply`, comandos de despliegue, login, llamadas a
  Azure DevOps ni validadores que requieran credenciales.
- No crear Service Connections, Environments, approvals ni registros de pipelines.
- No sobrescribir código existente que contradiga la definición. Marcar `conflict` e informar.
- No inventar SKUs, nombres, comandos, IDs o valores para un `PD-NNN`/`OP-NNN`.
- No usar ningún MCP de nube para crear directamente recursos administrados por Terraform.
- No convertir una solicitud de generación en permiso para registrar o ejecutar pipelines.
- No habilitar el toolset operativo de HCP Terraform ni `ENABLE_TF_OPERATIONS`; Bob solo puede
  consultar Registry mediante MCP.
- No ejecutar `terraform-search-import`; generar moved/import blocks no autoriza discovery,
  importación, state mutation ni apply.

## Modos y delegación

- `generate` es el único modo propio de Bob y conserva todos los límites locales de esta skill.
- `reconcile`, `plan`, `authorize`, `operate` y `verify` pertenecen al operador remoto registrado
  en `adapter_selection.remote_operator`, nunca al núcleo de Bob.
- Si el usuario pide una fase remota, terminar primero el cierre estricto con `--write-summary`.
  Solo después invocar explícitamente
  [`$vulcano-operador`](../vulcano-operador/SKILL.md), pasando la selección de adaptadores; no
  copiar sus permisos ni herramientas MCP dentro de Bob.
- Si el operador o los MCP no están disponibles, entregar los artefactos locales y reportar
  `missing_capability`; no improvisar REST, CLI ni credenciales.

## Estado persistente

Usar `resources/.vulcano/bob-manifest.yaml` con esquema v4, separado del manifiesto de Vulcano. Leer
[`references/estado-y-validacion.md`](references/estado-y-validacion.md) al iniciar, reanudar y
cerrar. Crear el manifiesto desde [`assets/bob-manifest.template.yaml`](assets/bob-manifest.template.yaml)
si aún no existe, preferiblemente con:

```powershell
node .claude/skills/vulcano-bob/scripts/init-bob-manifest.mjs
```

Si ya existe un manifiesto schema v3, usar `--migrate-adapters`; `--migrate-profile` se conserva
como alias compatible. No usar `--force`, porque perdería el estado de artefactos. Repetir el
preflight después de migrar.

El inicializador ejecuta `compile-bob-contract.mjs` cuando existe `06-modules.md`: reemplaza el
catálogo de módulos de la plantilla por módulos, rutas, inputs, outputs y dependencias derivados
de esa definición. Repetir el compilador después de cada cambio aprobado del contrato.

Cada artefacto debe tener:

- `logical_id` estable y una sola ruta física;
- dependencias acíclicas y contratos explícitos de inputs/outputs;
- estado `pending`, `generated`, `conflict` u `omitted`;
- documentos fuente;
- hash SHA-256 de cada documento fuente al marcarlo `generated`;
- resultado real de validación, sin fabricar éxitos para herramientas ausentes.

## Fase 0: preflight obligatorio

### 0.1 Cargar el contrato

Leer completamente:

1. `resources/.vulcano/manifest.yaml`.
2. Los ocho documentos de `resources/infrastructure-as-code/`.
3. `resources/devops-strategy/05-environments.md`, `06-ci-cd.md`,
   `07-continuous-testing.md` y `08-security.md`.
4. Los documentos de observabilidad que creen recursos de infraestructura.
5. El manifiesto de Bob y el código existente, si existen.
6. [`references/practicas-implementacion.md`](references/practicas-implementacion.md) para
   idempotencia, migraciones, state, seguridad y criterio de terminado.
7. [`references/hashicorp-terraform-integrations.md`](references/hashicorp-terraform-integrations.md)
   para skills oficiales, Terraform MCP y política de pruebas plan/mock.

Confirmar que `resources_root`, proyecto y manifiesto fuente coincidan. La ausencia del
manifiesto de Vulcano o del de Bob es un error del validador; durante una invocación de la skill,
crear primero el de Bob desde la plantilla.

### 0.2 Comprobar definición completa

Para cada artefacto seleccionado, verificar en el manifiesto de Vulcano que sus documentos
fuente existen y tienen estado `generated`, o `omitted` con razón cuando sean condicionales.
Un `PD-NNN` solo permite continuar si puede representarse como parámetro requerido sin cambiar
la arquitectura. En otro caso bloquea el artefacto.

### 0.3 Comprobar implementabilidad

Construir el grafo de dependencias en `bob-manifest.yaml` desde inputs y outputs documentados.
Validar que cada input derivado tenga un output productor y que el grafo sea acíclico. Detener la generación y
registrar `conflict` cuando ocurra cualquiera de estos casos:

- ciclo de datos entre módulos;
- archivo compartido que la herramienta no hereda entre directorios raíz;
- input u output usado pero no declarado en el documento fuente;
- selección ambigua entre dos servicios o modos incompatibles;
- estructura que no permite inicializar o validar cada root module;
- pipeline que exige un comando, credencial o mecanismo de despliegue no definido.

`depends_on` solo ordena recursos sin dependencia de datos; nunca lo usar para justificar un
ciclo. Devolver contradicciones de arquitectura a Vulcano antes de escribir código dependiente.

### 0.4 Comprobar el adaptador

Leer [`references/adapters.md`](references/adapters.md) y resolver la selección antes de generar:

```powershell
node .claude/skills/vulcano-bob/scripts/resolve-bob-adapters.mjs
```

Copiar el resultado a `adapter_selection`; no inferir la plataforma desde nombres de archivos.
Leer únicamente las referencias del adaptador seleccionado. Para un adaptador `planned`, informar
qué implementación falta y no generar artefactos parciales. `--allow-planned` sirve solo para
evaluar el enrutamiento, nunca para generar.

Exigir `decisions.terraform` completo y copiarlo sin reinterpretar a `terraform_profile` en el
manifiesto de Bob. Comprobar las capacidades disponibles y registrarlas, por ejemplo:

```powershell
node .claude/skills/vulcano-bob/scripts/record-bob-capability.mjs `
  --capability terraform_registry_mcp --status available
node .claude/skills/vulcano-bob/scripts/record-bob-capability.mjs `
  --capability terraform_test --status available
```

Usar `missing`, no fingir disponibilidad. Si `registry_mcp` es `read_only`, limitar Terraform MCP
a `registry` y, solo cuando corresponda, `registry-private`. Las decisiones y lockfiles locales
prevalecen sobre cualquier recomendación de versión obtenida del Registry.

## Fase 1: plan de artefactos

Leer [`references/orden-y-dependencias.md`](references/orden-y-dependencias.md) y clasificar cada
artefacto:

- `pending`: aún no existe;
- `generated`: existe, coincide con las fuentes y está validado;
- `conflict`: existe pero contradice el contrato, o la fuente no es implementable;
- `omitted`: no aplica y tiene razón documentada.

Si el usuario pide generar "todo", avanzar automáticamente en el orden de dependencias. Preguntar
solo cuando falte una decisión que cambie el resultado; representar nombres operativos todavía
desconocidos como parámetros requeridos asociados a un `OP-NNN`.

## Fase 2: generar y validar

Procesar un artefacto por vez, aunque se encadenen sin pausas:

1. Citar sus documentos y secciones fuente.
2. Verificar que sus dependencias estén `generated`.
3. Generar un archivo funcional, sin `<placeholders>`, pseudocódigo ni `TODO` sin ID real.
4. Conservar la lista exacta de inputs/outputs documentados. Si la implementación correcta
   requiere cambiarla, registrar conflicto y volver a Vulcano.
5. Ejecutar la validación local aplicable descrita en
   [`references/validacion-estatica.md`](references/validacion-estatica.md).
6. Solo después, validar y actualizar estado, hashes y evidencia de forma determinista:

   ```powershell
   node .claude/skills/vulcano-bob/scripts/validate-and-record-bob-artifact.mjs `
     --logical-id <id>
   ```

Este comando ejecuta las herramientas y conserva versión, comando, código de salida, fecha y hash
de la salida. `record-bob-artifact.mjs` solo administra `pending`, `conflict` y `omitted`.

Para preguntas operativas, consultar
[`references/preguntas-por-artefacto.md`](references/preguntas-por-artefacto.md). No repetir una
pregunta cuya respuesta ya esté en los manifiestos, documentos o repositorio.

## Reglas Terraform

- Tratar cada `infra/environments/<ambiente>` como root module independiente.
- No asumir que `locals.tf`, `versions.tf` o providers ubicados en otro directorio se heredan.
- Mantener `versions.tf`, provider configuration y `.terraform.lock.hcl` en cada root module.
- Validar módulos reutilizables mediante una copia temporal/harness; no confiar en booleanos
  escritos manualmente en el manifiesto.
- No agregar inputs como `name_prefix` si `06-modules.md` no los declara.
- Marcar secretos como `sensitive`, evitar outputs planos y recordar que valores generados por
  Terraform permanecen en el state.
- Separar recursos base de bindings de acceso cuando una identidad se conoce después de crear el
  recurso consumidor; no construir ciclos entre módulos.
- Generar `moved` blocks o instrucciones de importación para recursos existentes; nunca recrearlos
  silenciosamente por un cambio de dirección Terraform.
- Implementar observabilidad como código: base (workspace/App Insights/Action Group) y reglas
  dependientes de compute/database, evitando ciclos.
- Generar `tests/*.tftest.hcl` por módulo con cada `run` en `command = plan` y `mock_provider`
  para todos los providers requeridos. El validador rechaza el default apply.
- Ejecutar `terraform test -no-color` en copia temporal y conservar evidencia. Las pruebas apply
  o de integración solo pertenecen a un pipeline autorizado y no viven bajo `tests/`.
- Aplicar `terraform-style-guide` cuando esté disponible sin cambiar constraints aprobados.
  Aplicar `azure-verified-modules` solo con `module_standard: avm`.
- Con `adoption_mode: moved_import`, usar `refactor-module` como apoyo y generar un plan de
  migración revisable; no ejecutar state/import desde Bob.

## Reglas de pipelines

- Aplicar estas reglas comunes y después las reglas específicas de `adapter_selection.pipeline`.
- Renderizar únicamente con el renderer declarado por el adaptador. No usar una plantilla de Azure
  DevOps para producir GitHub Actions ni viceversa.
- Un archivo físico corresponde a un solo artefacto lógico. Si contiene CI y CD, usar
  `pipeline-app`, no dos entradas que apunten al mismo archivo.
- Todo job de deployment debe contener estrategia y pasos ejecutables.
- Publicar el paquete o plan en el job productor y descargar exactamente ese artefacto en el job
  consumidor.
- Aplicar el plan guardado; no recalcularlo en el job de apply.
- Incluir `checkout: self` en todo deployment job que ejecute Terraform desde el repositorio.
- Generar `pipeline-drift` separado y programado; puede ejecutar `plan -detailed-exitcode`, nunca
  `apply`.
- Derivar comandos de scripts reales del repositorio o documentos aprobados. Si falta un comando
  obligatorio, bloquear el artefacto en vez de dejar pseudocódigo.
- Los approvals viven en Environments de Azure DevOps/GitHub o protected environments de GitLab
  y quedan como configuración remota del operador.
- Validar parámetros operativos, cachear por lockfile, publicar resultados y promover el mismo
  artefacto sin reconstruirlo.
- Renderizar con `render-bob-pipelines.mjs`. Azure DevOps requiere variable groups y cron;
  GitHub/GitLab requieren cron. Todos son valores operativos resueltos, no defaults inventados.
  Pasar `--deployment-strategy <rolling|canary|blue_green>` igual a `decisions.deployment_strategy`
  del manifiesto de Vulcano; se omite (equivale a `rolling`) solo cuando esa decisión sigue sin
  resolver. Con `canary`/`blue_green`, los tres renderers agregan el step/job de análisis y
  abort/rollback automáticamente — no escribirlos a mano ni duplicar la lógica del renderer.
  Pasar también `--policy-engine <opa|conftest|none>` igual a `decisions.policy_engine` (agrega el
  gate de policy as code al job/stage de `plan`, antes de publicar el `tfplan`) y
  `--notification-channel <slack|teams|none>` igual a `decisions.notification_channel` (agrega un
  job/stage final que notifica el resultado del pipeline de aplicación, `if: always()`/
  `condition: always()`, independiente del resultado del deploy). Ambos se omiten (equivalen a
  `none`) solo cuando la decisión sigue sin resolver.
- Cuando `decisions.dora_collection_method: automated`, renderizar además con
  `render-bob-dora.mjs` (no con `render-bob-pipelines.mjs`) — ver
  [`references/dora-collector.md`](references/dora-collector.md) para el contrato completo,
  el pipeline programado por plataforma y el paso manual de registrar `pipeline-dora` en
  `bob-manifest.yaml`.
- Pasar `--deployment-model <push_pipeline|gitops>` igual a `decisions.deployment_model` a
  `render-github-actions.mjs`/`render-gitlab.mjs` (cambia el step de deploy de `pipeline-app` de
  "Deploy and verify health" a "Update GitOps manifests"). `render-azure-devops.mjs` rechaza
  `gitops` explícitamente — ver [`references/gitops.md`](references/gitops.md). Cuando
  `deployment_model: gitops`, renderizar además con `render-bob-gitops.mjs` (manifiestos Kustomize
  + `Application` de ArgoCD) y registrar `gitops-manifests` manualmente en `bob-manifest.yaml`.
- En producción, ejecutar health check posterior al slot swap y rollback coordinado de
  backend/frontend. Publicar resultados JUnit cuando el runner los soporte.

## Fase 3: cierre

1. Ejecutar:

   ```powershell
   node .claude/skills/vulcano-bob/scripts/validate-vulcano-bob.mjs `
     --strict-completeness --write-summary
   ```

2. Corregir todos los errores. Registrar las herramientas locales ausentes como warnings.
3. Crear o actualizar el índice de cierre de forma determinista:

   ```powershell
   node .claude/skills/vulcano-bob/scripts/generate-bob-index.mjs
   ```
4. Mostrar separadamente: generado, validado, bloqueado y pasos manuales.
5. Nunca usar las palabras "desplegado" o "aplicado" para describir este cierre.
6. Si se solicitó operación remota, transferir el control a `adapter_selection.remote_operator`:
   comenzar en `reconcile` y dejar claro que aún no existe ninguna mutación autorizada.

## Referencias

- Estado, esquema y reconciliación: [`references/estado-y-validacion.md`](references/estado-y-validacion.md)
- Catálogo y dependencias: [`references/orden-y-dependencias.md`](references/orden-y-dependencias.md)
- Preguntas operativas: [`references/preguntas-por-artefacto.md`](references/preguntas-por-artefacto.md)
- Patrones Terraform/Azure DevOps: [`references/plantillas-codigo.md`](references/plantillas-codigo.md)
- Validación y límites: [`references/validacion-estatica.md`](references/validacion-estatica.md)
- Prácticas expertas: [`references/practicas-implementacion.md`](references/practicas-implementacion.md)
- Skills y MCP oficiales de HashiCorp:
  [`references/hashicorp-terraform-integrations.md`](references/hashicorp-terraform-integrations.md)
- Selección y extensión de adaptadores: [`references/adapters.md`](references/adapters.md)
- Colector de métricas DORA: [`references/dora-collector.md`](references/dora-collector.md)
- GitOps (Kustomize/ArgoCD): [`references/gitops.md`](references/gitops.md)
- Setup de Azure DevOps (Variable Groups/Environments/Branch Policy vía REST,
  comportamiento por defecto cuando `devops_platform: azure_devops`):
  [`references/azure-devops-setup.md`](references/azure-devops-setup.md)

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "vulcano-bob", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill vulcano-bob --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
