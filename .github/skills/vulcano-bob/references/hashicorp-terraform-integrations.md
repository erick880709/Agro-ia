# Integraciones oficiales de HashiCorp

Usar esta referencia durante el preflight y al generar Terraform. Las decisiones aprobadas en
`manifest.yaml` siempre prevalecen sobre recomendaciones genéricas o versiones `latest`.

## Proveniencia revisada

- Repositorio: `hashicorp/agent-skills`.
- Revisión de referencia: `8c6573abbd21e8094fab8f538eb5f97db63133fd`.
- Licencia upstream: MPL-2.0.
- No copiar silenciosamente el contenido upstream. Invocar el skill instalado o consultar la
  fuente revisada; registrar una nueva revisión antes de actualizar reglas locales.

## Enrutamiento

| Necesidad | Skill oficial | Regla Vulcano |
|---|---|---|
| Generar/revisar HCL | `terraform-style-guide` | Opcional; el contrato de Vulcano prevalece. |
| Crear pruebas `.tftest.hcl` | `terraform-test` | Opcional como conocimiento; Bob exige plan + mocks localmente. |
| Cumplimiento AVM | `azure-verified-modules` | Obligatorio solo con `module_standard: avm`. |
| Refactor brownfield | `refactor-module` | Opcional con `adoption_mode: moved_import`; generar migración, no ejecutarla. |
| Descubrir/importar recursos | `terraform-search-import` | Deshabilitado en Bob; requiere reconciliación y autorización remota. |
| Terraform Stacks/Policy/providers | skills respectivos | Fuera del adaptador `iac/terraform` actual. |

Registrar cada comprobación con `record-bob-capability.mjs`. Un skill general ausente queda como
`missing` y se aplican las reglas locales; AVM ausente bloquea si fue exigido.

## Terraform MCP

Usarlo solo cuando `registry_mcp: read_only`:

- permitir toolset `registry` para documentación de providers y módulos;
- usar `registry-private` solo si `registry_source` es `private` o `mixed` y la autenticación ya
  está configurada fuera de manifiestos, prompts y argumentos;
- no habilitar el toolset `terraform`, `ENABLE_TF_OPERATIONS`, runs, workspaces ni apply;
- no tratar la respuesta MCP como aprobación de versión: conservar constraint y lockfile;
- registrar `missing` si no está conectado y continuar con validación local, salvo que una fuente
  privada no pueda resolverse sin esa capacidad.

El Terraform MCP no reemplaza Terraform CLI, Azure DevOps MCP ni Azure MCP.

## Política de pruebas locales

- Guardar pruebas unitarias bajo `tests/*.tftest.hcl`.
- Declarar `command = plan` en cada `run`; el default de Terraform Test es apply.
- Declarar `mock_provider` para cada provider requerido por el módulo.
- Ejecutar `terraform test -no-color` en una copia temporal después de `init -backend=false` y
  `validate`.
- Mantener pruebas apply/integración fuera de `tests/`; ejecutarlas solo en pipeline con identidad,
  ambiente y autorización específicos.
