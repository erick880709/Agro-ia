# Validación estática local

Todos los comandos ejecutados por Bob deben funcionar sin credenciales y sin consultar estado o
recursos de nube. Nunca ejecutar `plan`, `apply`, `az login`, `az pipelines`, llamadas a APIs ni
comandos de despliegue.

## Por artefacto

| Artefacto | Validación local |
|---|---|
| Shell de bootstrap | `bash -n <script>` + `shellcheck <script>` y búsqueda de placeholders/secretos |
| Terraform | `terraform fmt -check -recursive` |
| Módulo reutilizable | copiar a directorio temporal, crear harness si hace falta, `terraform init -backend=false` + `terraform validate` |
| Root module inicializable | validar en copia temporal con `terraform init -backend=false -input=false` y `terraform validate` |
| Pruebas de módulo | `tests/*.tftest.hcl`, cada `run` con `command = plan`, providers con `mock_provider`, luego `terraform test -no-color` |
| Lock de providers | `.terraform.lock.hcl` versionado por cada `env-*`; `terraform providers lock` al generarlo |
| Terraform lint | `tflint` cuando esté instalado |
| Seguridad IaC | `trivy config <iac_root>` (preferido); `tfsec <iac_root>` o `checkov -d <iac_root>` como alternativa cuando esté instalado |
| Pipeline YAML | parseo YAML, grafo de stages, jobs/steps, parámetros, publish/download y ausencia de placeholders |
| Secret scanning | `gitleaks detect --no-git --source <artefacto>` cuando esté instalado |

`terraform init -backend=false` puede descargar providers públicos, pero no debe autenticarse ni
leer un backend remoto. Si la política del entorno prohíbe red, omitirlo con warning y no marcar
`validate: true`.

`tfsec` está en modo mantenimiento desde que Aqua Security migró su motor a Trivy; usar
`trivy config` como primera opción y tratar `tfsec`/`checkov` como alternativas de compatibilidad
cuando `trivy` no esté instalado.

## Reglas bloqueantes

- Falta el manifiesto de Vulcano o de Bob.
- Alguna dimensión del adaptador no existe, está `planned` o es incompatible con el perfil.
- `adapter_selection` no coincide con la resolución de `decisions.cloud_provider`,
  `decisions.iac` y `decisions.devops_platform`.
- `preflight.status` es `blocked`, o existe un artefacto `conflict`.
- Un artefacto `generated` no existe, sale del workspace o referencia una fuente inexistente.
- El hash actual de una fuente difiere del snapshot registrado.
- Dos artefactos apuntan a la misma ruta física.
- El grafo de `depends_on` tiene referencias desconocidas, ciclos o dependencias sin generar.
- Inputs/outputs del contrato están ausentes o duplicados.
- Existe un placeholder `<...>`, pseudocódigo o `TODO` sin un ID real `PD-NNN`/`OP-NNN`.
- Un pipeline no parsea o un deployment job no contiene estrategia y pasos.
- Un pipeline consume un artefacto no publicado, tiene `dependsOn` desconocido, nombres duplicados
  o usa un parámetro operativo con default vacío sin `OP-NNN` registrado.
- Se detecta un secreto probable.
- Falla formato, init, validate, lint o security scan que sí pudo ejecutarse.
- Un módulo no contiene pruebas cuando `test_strategy` las exige, una prueba omite
  `command = plan`, usa apply o no mockea todos los providers requeridos.
- `terraform_profile` difiere de `decisions.terraform`, AVM fue requerido sin capacidad
  `azure_verified_modules`, o `terraform_search_import` no está deshabilitado.

En `--strict-completeness` también bloquean: preflight distinto de `ready`, artefactos `pending`,
validaciones requeridas sin resultado, evidencia de `terraform test` ausente, hashes ausentes,
falta de `.terraform.lock.hcl` en un
ambiente y falta del índice de cierre.

## Herramientas ausentes

Reportar como warning la ausencia de una herramienta opcional. No escribir `true` en el
manifiesto para una comprobación que no se ejecutó. `--skip-tools` solo existe para pruebas no
estrictas y siempre deja un warning visible. Para marcar `generated`, usar
`validate-and-record-bob-artifact.mjs`; la evidencia conserva herramienta, versión, comando,
exit code, timestamp y SHA-256 de la salida.

## Pasos manuales posteriores

1. Ejecutar el bootstrap con una identidad autorizada.
2. Completar las conexiones e identidades requeridas por el adaptador de pipeline.
3. Configurar ambientes y aprobaciones en la plataforma seleccionada.
4. Registrar los pipelines o workflows generados.
5. Invocar el operador remoto seleccionado desde `reconcile`, nunca directamente desde `operate`.

El cierre de Bob informa “código generado y validado localmente”; nunca “infraestructura aplicada”.
