# Patrones de generación: Terraform + Azure DevOps

Usar únicamente después de que el preflight quede `ready`. Son patrones estructurales, no valores
de diseño. Sustituir cada decisión con el valor literal de los documentos fuente; si la fuente no
lo define, registrar conflicto o un `OP-NNN` según las reglas del skill.

## Índice

- [Bootstrap seguro](#bootstrap-seguro)
- [Versions y providers](#versions-y-providers)
- [Módulos](#módulos)
- [Composición de ambientes](#composición-de-ambientes)
- [Observabilidad](#observabilidad)
- [Secretos](#secretos)
- [Pipeline de IaC](#pipeline-de-iac)
- [Pipeline de aplicación](#pipeline-de-aplicación)

## Bootstrap seguro

Generar un script que exija parámetros, no literales con apariencia real:

```bash
#!/usr/bin/env bash
# ORIGEN: infrastructure-as-code/05-state-management.md
set -euo pipefail

: "${AZURE_LOCATION:?AZURE_LOCATION es obligatoria}"
: "${TFSTATE_RESOURCE_GROUP:?TFSTATE_RESOURCE_GROUP es obligatorio}"
: "${TFSTATE_STORAGE_ACCOUNT:?TFSTATE_STORAGE_ACCOUNT es obligatorio}"

az group create \
  --name "$TFSTATE_RESOURCE_GROUP" \
  --location "$AZURE_LOCATION"

az storage account create \
  --name "$TFSTATE_STORAGE_ACCOUNT" \
  --resource-group "$TFSTATE_RESOURCE_GROUP" \
  --location "$AZURE_LOCATION" \
  --sku Standard_LRS \
  --allow-blob-public-access false \
  --min-tls-version TLS1_2 \
  --encryption-services blob

az storage account blob-service-properties update \
  --account-name "$TFSTATE_STORAGE_ACCOUNT" \
  --resource-group "$TFSTATE_RESOURCE_GROUP" \
  --enable-versioning true

POLICY_FILE="$(mktemp)"
trap 'rm -f "$POLICY_FILE"' EXIT
cat > "$POLICY_FILE" <<'JSON'
{
  "rules": [{
    "enabled": true,
    "name": "delete-state-versions-after-retention",
    "type": "Lifecycle",
    "definition": {
      "actions": { "version": { "delete": { "daysAfterCreationGreaterThan": 30 } } },
      "filters": { "blobTypes": ["blockBlob"], "prefixMatch": ["dev/", "qa/", "prod/"] }
    }
  }]
}
JSON
az storage account management-policy create \
  --account-name "$TFSTATE_STORAGE_ACCOUNT" \
  --resource-group "$TFSTATE_RESOURCE_GROUP" \
  --policy "@$POLICY_FILE"

for environment in dev qa prod; do
  az storage container create \
    --name "$environment" \
    --account-name "$TFSTATE_STORAGE_ACCOUNT" \
    --auth-mode login
done
```

Copiar los 30 días solo si la fuente los confirma. `--enable-versioning` no configura retención.

## Versions y providers

Terraform solo carga `.tf` del directorio de trabajo. Un `infra/versions.tf` no se hereda al
ejecutar desde `infra/environments/dev`. El preflight debe exigir una estructura aprobada que
coloque el contrato de versión/provider dentro de cada root module ejecutable, por ejemplo:

```hcl
# infra/environments/<ambiente>/versions.tf (parte del artefacto env-*, no uno global)
# ORIGEN: infrastructure-as-code/04-terraform-structure.md
terraform {
  required_version = "<restricción aprobada>"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "<restricción aprobada>"
    }
    random = {
      source  = "hashicorp/random"
      version = "<restricción aprobada>"
    }
  }
}

provider "azurerm" {
  features {}
}
```

No elegir versiones. Si Vulcano solo declara `infra/versions.tf` y los ambientes son roots
independientes, registrar el conflicto y pedir que Vulcano corrija el contrato.

Después de aprobar constraints, generar y versionar el lockfile por ambiente:

```powershell
terraform -chdir=infra/environments/<ambiente> providers lock `
  -platform=linux_amd64 -platform=windows_amd64
```

Usar las plataformas reales de los agentes/desarrolladores; no copiar esta lista sin verificarla.

## Módulos

Generar `main.tf`, `variables.tf` y `outputs.tf`. La lista de variables y outputs debe ser
exactamente la tabla de `06-modules.md`.

```hcl
# variables.tf
# ORIGEN: infrastructure-as-code/06-modules.md §<módulo>
variable "environment" {
  type        = string
  description = "Ambiente aprobado"

  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "environment debe ser dev, qa o prod."
  }
}

variable "common_tags" {
  type        = map(string)
  description = "Tags exigidos por 03-naming-conventions.md"
}
```

No agregar `name_prefix` si la tabla no lo declara. Un módulo puede derivar un local desde inputs
aprobados dentro de su propio scope:

```hcl
# main.tf
# ORIGEN: infrastructure-as-code/03-naming-conventions.md
locals {
  name_prefix = "psoft-inscripciones-${var.environment}"
}
```

Usar el prefijo literal solo cuando aparezca en la definición del proyecto. `locals.tf` en otro
directorio no comparte `local.*` con el módulo.

## Composición de ambientes

Cada ambiente contiene al menos `versions.tf`, `backend.tf`, `variables.tf`, `locals.tf`,
`main.tf` y su archivo de valores aprobado. Los `locals` pertenecen al ambiente:

```hcl
# infra/environments/<ambiente>/locals.tf
# ORIGEN: infrastructure-as-code/03-naming-conventions.md
locals {
  common_tags = {
    environment = var.environment
    project     = "<valor aprobado>"
    owner       = "<valor aprobado>"
    cost_center = "<valor aprobado>"
    managed_by  = "terraform"
  }
}
```

Las cadenas `<valor aprobado>` de esta referencia significan “copiar de la fuente”; nunca deben
permanecer en un archivo generado.

### Evitar el ciclo Key Vault/App Service

Este es el patrón técnico correcto una vez que Vulcano actualice el contrato para aprobarlo:

```hcl
module "key_vault" {
  source      = "../../modules/key-vault"
  environment = var.environment
  common_tags = local.common_tags
}

module "app_service" {
  source       = "../../modules/app-service"
  environment  = var.environment
  common_tags  = local.common_tags
  key_vault_id = module.key_vault.key_vault_id
  subnet_id    = module.networking.subnet_app_id
}

resource "azurerm_role_assignment" "app_key_vault_secrets_user" {
  scope                = module.key_vault.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = module.app_service.app_service_principal_id
}
```

El módulo Key Vault base no recibe el principal del App Service. El binding se crea cuando ambas
salidas existen. No copiar este patrón mientras `06-modules.md` siga exigiendo el input circular;
en ese estado el artefacto es `conflict`.

## Observabilidad

Separar recursos para evitar que App Service y alertas se dependan mutuamente:

- `observability-base`: Log Analytics, Application Insights y Action Group.
- `app-service`: consume `application_insights_connection_string`.
- `observability-rules`: consume IDs de App Services, PostgreSQL, App Insights y Action Group;
  crea diagnostic settings y alertas `ALT-NNN`.

Cada alerta debe conservar su ID de origen en comentario y declarar scope, severity, frequency,
window, criteria y action group. Convertir receivers del Action Group en variables sensibles u
operativas; no hardcodear correos/teléfonos.

## Secretos

- Declarar outputs sensibles con `sensitive = true`.
- Exponer IDs/URI de secretos, nunca contraseñas planas.
- Documentar que `random_password.result` queda almacenado en Terraform state aunque el output sea
  sensible; proteger backend, RBAC y retención en consecuencia.
- No escribir secretos en `.tfvars`, pipeline YAML ni manifiestos.

## Pipeline de IaC

Usar `scripts/render-bob-pipelines.mjs`; el descriptor seleccionado enruta a Azure DevOps,
GitHub Actions o GitLab CI. Azure DevOps requiere dos variable groups, cron UTC y
`--terraform-version` (versión exacta x.y.z, igual que GitHub/GitLab); GitHub/GitLab requieren
cron y `--terraform-version`. Los renderers incluyen validación, planes por ambiente, plan
inmutable y environment de producción. Registrar las referencias operativas como `OP-NNN`.

Los agentes Microsoft-hosted (`ubuntu-24.04`, GitHub y Azure Pipelines comparten la misma imagen
`runner-images`) NO traen preinstalados Terraform, tflint ni trivy — confirmado contra
`runner-images/Ubuntu2404-Readme.md`. GitHub Actions resuelve esto con `hashicorp/setup-terraform`;
Azure DevOps no tiene un task oficial equivalente sin depender de una extensión de Marketplace que
Bob no puede instalar, así que `render-azure-devops.mjs` genera un step `bash` que descarga el
binario exacto de `releases.hashicorp.com` y lo agrega al PATH del job vía
`##vso[task.prependpath]` — repetido en cada job que invoca `terraform` (`TerraformQuality`,
`CreatePlanDev`/`ApplySavedPlanDev`, y lo mismo para qa/prod), porque cada job de Azure Pipelines
corre en un agente nuevo sin estado compartido. Solo `TerraformQuality` instala además `tflint` y
`trivy`, con los instaladores oficiales de cada proyecto.

Generar además `pipeline-drift` desde el asset declarado por el adaptador: ejecución programada,
`plan -detailed-exitcode`, reporte por ambiente y cero comandos `apply`. Bob crea los YAML pero
nunca los dispara.

`azure-pipelines.terraform.template.yml` declara `parameters: deployQa`/`deployProd` (booleanos,
default `true`) que envuelven las stages `PlanQa`/`ApplyQa` y `PlanProd`/`ApplyProd` en expresiones
de plantilla `${{ if eq(parameters.deployQa, true) }}:` evaluadas en tiempo de COMPILACIÓN — no
usar `stagesToSkip` en runtime para excluir un ambiente de un run, porque Azure DevOps igual
compila y valida el YAML completo (incluidas las service connections referenciadas) antes de
aplicar ese skip. Con `deployQa`/`deployProd` en `false` al encolar (`templateParameters`), esas
stages no entran al YAML compilado y sus referencias a `serviceConnectionQa`/`serviceConnectionProd`
nunca se validan, permitiendo desplegar solo `dev` aunque las conexiones de qa/prod aún no existan.
`ApplyProd.dependsOn` es condicional sobre `deployQa` (depende de `ApplyQa` si corrió, de `ApplyDev`
si no) para no dejar una referencia colgante cuando se salta qa pero no prod.

## Pipeline de aplicación

Para el adaptador actual Node 20 + Express/TypeScript + Angular + App Service, la plantilla a
usar depende de `decisions.pipeline_topology` (vulcano, `06-ci-cd.md`):

- **`single`** (default, compatibilidad hacia atrás): `assets/azure-pipelines.node-angular-app.template.yml`
  — un solo pipeline que construye/testea/despliega backend y frontend juntos.
- **`per_component`**: `assets/azure-pipelines.node-backend-app.template.yml` +
  `assets/azure-pipelines.node-frontend-app.template.yml` — dos pipelines independientes, cada
  uno con su propio `trigger.paths`/`pr.paths` (`backend` / `frontend`) y su propio artefacto
  (`backend-package` / `frontend-package`). El E2E de Playwright vive en la plantilla `frontend`
  (necesita levantar ambos componentes en local) — un cambio que solo toca `backend/**` no
  vuelve a dispararlo automáticamente; ver `06-ci-cd.md` §Etapas del pipeline para el trade-off
  documentado. `render-azure-devops.mjs` selecciona la plantilla correcta con
  `--pipeline-topology per_component` y ubica los archivos con `--app-pipeline-dir <carpeta>`
  (ver `references/adapters.md` §Ubicación de los pipelines de aplicación).

Cualquiera de las tres plantillas materializa:

1. validación temprana de variables operativas;
2. instalación reproducible con `npm ci` y cache por lockfiles;
3. build (backend, frontend, o ambos según topología), Jest/Vitest y Playwright;
4. SCA, secret scanning y SonarQube;
5. paquetes ZIP inmutables por Build ID;
6. promoción del mismo artefacto a dev/qa/prod;
7. deployment slots, health check y swap en producción.

Antes de copiarla, contrastar comandos y rutas con `package.json`, `angular.json`, configuración
Playwright y scripts Sonar reales. Adaptar o quitar el paso `gitleaks` según la decisión final
GHAzDO/gitleaks. Registrar nombres de Service Connections, App Services, Resource Group y health
URLs de backend **y de frontend** por ambiente (dev/qa/staging/prod) como `OP-NNN`: la plantilla
`single` verifica la salud de ambos componentes en cada despliegue; con `per_component`, cada
plantilla verifica solo la salud de su propio componente. Si falta un comando obligatorio,
mantener el/los `pipeline-app*` en `conflict`.
