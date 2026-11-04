# Terragrunt, OpenTofu/Terraform e IaC

Complementa los ejes generales cuando el cambio toca `terragrunt.hcl`,
`terragrunt.stack.hcl`, `root.hcl`, archivos de jerarquía (`account.hcl`,
`region.hcl`, `env.hcl`), módulos `.tf` o pipelines que ejecutan Terragrunt. Las
reglas coinciden con la skill `terragrunt-iac`, que es quien genera ese código;
code-review es su revisor independiente.

**Por qué la IaC exige más rigor que el código de aplicación.** Un error no
falla en un test: se convierte en un recurso destruido, un estado corrupto o
una cuenta equivocada. Y el código generado por IA es plausible y rápido de
producir; cuando generar cuesta menos, verificar debe costar más. "Lo generó la
herramienta" nunca baja el estándar de revisión.

## Paso 1 — Contexto adicional

Además de lo de [alcance y contexto](scope-and-context.md):

- Versión objetivo: `mise.toml`/`.tool-versions` y `terragrunt_version_constraint`
  del `root.hcl`. Si no existen, es hallazgo `TG-013` y las reglas se aplican
  para Terragrunt 1.x.
- Fuente funcional: spec/AC del cambio y, si existe, el blueprint de
  arquitectura (`17.7-Blueprint-IaC_*` de `archi`) o la línea base
  `Linea_Base_*.md` de `terragrunt-iac`. Se revisa **conformidad**: ningún
  recurso, input o permiso inventado; ninguno omitido.
- Ejecuta `python scripts/terragrunt_check.py <repo> [--base <rama>] [--run-tools]`.
  Igual que `scaffold_check.py`: son pistas, no hallazgos.

## Paso 2 — Gate computacional de IaC

Ninguno requiere credenciales salvo el plan. Regístralos en la tabla del gate:

| Check | Comando | Si falla |
|---|---|---|
| Formato | `terragrunt hcl fmt --check --diff` | `nit` (agrúpalo en un solo hallazgo) |
| Generación de stacks | `terragrunt stack generate` | `bloqueante` |
| Validación HCL | `terragrunt hcl validate` (units de catálogo que leen `values`: desde el stack generado) | `bloqueante` |
| Inputs vs variables | `terragrunt hcl validate --inputs --strict` | `mayor` |
| Orden de ejecución | `terragrunt find --dag` / `terragrunt dag graph` | `bloqueante` si hay ciclo |
| Módulos | `tofu validate` / `terraform validate`, `tflint` | según el error |
| Escáner de configuración | el que el proyecto use (Trivy, Checkov) | según severidad del proyecto |
| Plan de lo afectado | `terragrunt run --all --filter '[<base>...HEAD]' -- plan -detailed-exitcode` | ver "Prueba de plan" |

**Prueba de plan.** Es la evidencia más fuerte de una revisión de IaC y la
única que detecta destrucciones y reemplazos. No basta con "plan exitoso":
lee el resumen (`to add / to change / to destroy`) y contrástalo con la spec.
Cualquier `destroy`/`replace` no pedido, o *churn* de la clave de estado, es
`bloqueante`. En refactors y migraciones el objetivo es **cero cambios**
(`-detailed-exitcode` = 0). Si no hay plan disponible, el check queda
`not_run` y el veredicto no puede ser `aprobado` en cambios a producción
(`no-concluyente` o `aprobado-con-observaciones` con pregunta explícita en
no-prod, según riesgo).

## Paso 3 — Pasadas aplicadas a IaC

| Pasada | Qué buscar en Terragrunt |
|---|---|
| A Cumplimiento | Cada AC se refleja en un unit/stack/input concreto; nada fuera de alcance (otro ambiente, otra cuenta); el cambio llega al pipeline real |
| B Corrección | `include`/`dependency`/`source` que resuelven; mocks con la forma real de los outputs; `for_each` estable; expansión con `path` único; orden de dependencias correcto |
| C Arquitectura | Catálogo vs live; un unit = un estado; raíz `root.hcl`; jerarquía DRY; stacks con `values`/`autoinclude` en vez de copiar HCL; versiones pineadas |
| D Seguridad y datos | Secretos fuera del repo; cifrado y bloqueo del estado; mínimo privilegio; `prevent_destroy`/protección de borrado en datos; pipeline con OIDC y aprobación |
| E Rendimiento | `run_cmd`/llamadas de identidad en `locals` de la raíz (se ejecutan por unit en el discovery); parallelism; caché de providers |
| F Pruebas | Plan revisado; Terratest/`tofu test` cuando el cambio es a un módulo de catálogo; ejemplos actualizados |
| G Mantenibilidad | Sintaxis 1.x; nombres y etiquetas; `inputs` que solo repiten defaults; comentarios engañosos |

## Catálogo de reglas

Severidad por defecto; súbela o bájala con evidencia según
[severidad y veredicto](severity-and-verdict.md). Los IDs coinciden con
`terragrunt_check.py`; los marcados con ✋ solo se detectan leyendo.

| ID | Regla | Severidad | Remedio |
|---|---|---|---|
| TG-001 | `mock_outputs_allowed_terraform_commands` incluye `apply`/`destroy` | bloqueante | `["validate", "plan", "init"]` |
| TG-002 | Fuente remota sin `?ref=` o con rama (`main`, `master`) | mayor; bloqueante en prod | Tag semver o SHA |
| TG-003 | Secreto/llave literal en HCL, `values` o `inputs` | bloqueante | `get_env`, `sops_decrypt_file`, gestor de secretos; rotar el expuesto |
| TG-004 | Clave de estado fija (sin `path_relative_to_include()`) | bloqueante | Clave por unit |
| TG-005 | Backend S3 sin bloqueo | mayor | `use_lockfile = true` |
| TG-006 | Comando, flag o variable previa a 1.0 (`run-all`, `--terragrunt-*`, `TERRAGRUNT_*`, `hclfmt`, `validate-inputs`…) | mayor | Forma 1.x (`run --all`, flag sin prefijo, `TG_*`, `hcl fmt`, `hcl validate --inputs`) |
| TG-007 | `include` sin etiqueta, `find_in_parent_folders()` sin argumento, raíz llamada `terragrunt.hcl` | mayor | `include "root"`, `find_in_parent_folders("root.hcl")`, renombrar a `root.hcl` |
| TG-008 | `skip`, `retryable_errors` suelto, `mock_outputs_merge_with_state`, `config_path` a archivo | menor | `exclude {}`, `errors { retry {} }`, `mock_outputs_merge_strategy_with_state`, carpeta |
| TG-009 | `include`, `dependency` o `source` local que no resuelve | bloqueante | Corregir la ruta |
| TG-010 | `dependency` sin `mock_outputs` | menor | Mocks con la forma real del output |
| TG-011 | `skip_outputs = true` | menor | Quitarlo o usar `locals` |
| TG-012 | `run_cmd`/`get_aws_account_id()`/`sops_decrypt_file()` en `root.hcl` | menor | Valor estático o `run_cmd("--terragrunt-global-cache", ...)` |
| TG-013 | Sin versiones pineadas (`mise.toml`, `terragrunt_version_constraint`) | menor | Pinear |
| TG-014 | `.gitignore` sin `.terragrunt-cache/`/`.terragrunt-stack/` | nit | Agregar |
| TG-015 | `hcl fmt` pendiente | nit | `terragrunt hcl fmt` |
| TG-016 | `hcl validate` falla | bloqueante | Corregir |
| TG-020 ✋ | Plan con destroy/replace o cambio de clave de estado no pedidos | bloqueante | Ajustar el cambio; `moved`/`backend migrate` si es intencional |
| TG-021 ✋ | Recurso/input/permiso que no está en la spec o blueprint (invención) u omitido | mayor | Alinear con la fuente funcional |
| TG-022 ✋ | Mocks con forma distinta al output real (tipo, lista vs string) | menor | Copiar la forma del `outputs.tf` |
| TG-023 ✋ | Datos sin `prevent_destroy`/protección de borrado/backups en prod | mayor | Proteger |
| TG-024 ✋ | Permisos con comodines (`*`) sin `DA-xxx` que los justifique | mayor | Acciones y recursos concretos |
| TG-025 ✋ | Provider sin `allowed_account_ids`/`subscription_id`/`project` explícitos | mayor | Fijar la cuenta destino en el `generate "provider"` |
| TG-026 ✋ | `count` en `expansion` donde el orden de la colección puede cambiar | menor | `for_each` |
| TG-027 ✋ | Workspaces de OpenTofu/Terraform para separar ambientes | mayor | Carpetas por ambiente o stacks con `values` |
| TG-028 ✋ | Código `.tf` dentro del repo *live* | menor | Moverlo al catálogo |
| CI-001 | `pull_request_target` en workflow de IaC | bloqueante | `pull_request` |
| CI-002 | Action legada (`the-commons-project/terragrunt-github-actions` y forks como "CN Terragrunt GitHub Actions") | mayor | `gruntwork-io/terragrunt-action@v3` + `mise.toml` |
| CI-003 | Versión `latest` o action referenciada por rama | mayor | Pinear versión/SHA |
| CI-004 | `--filter-allow-destroy` en job sin environment con aprobación | mayor | Environment protegido o quitar el flag |
| CI-005 | `--queue-ignore-errors` en apply | bloqueante | Quitar |
| CI-006 | `fetch-depth: 1` con filtros Git | mayor | `fetch-depth: 0` (plan) / `2` (apply) |
| CI-007 | Credenciales estáticas de nube en el pipeline | mayor | OIDC con roles plan/apply |
| CI-008 | `TF_PLUGIN_CACHE_DIR` manual con `run --all` | menor | Quitar |
| CI-009 ✋ | Apply desde ramas distintas de la principal o sin plan revisado | bloqueante | Apply solo tras merge y aprobación |

## Falsos positivos frecuentes

- Units de catálogo que leen `values.*` no validan solos: no es `TG-016`; valídalos
  desde el stack generado.
- Plantillas con marcadores (`{{bucket}}`, `${...}` de scaffolding) no son
  secretos ni claves fijas.
- `run_cmd("--terragrunt-quiet", ...)` y `--terragrunt-global-cache` son
  parámetros vigentes de `run_cmd`, no flags previos a 1.0.
- Nombrar una forma obsoleta para advertir sobre ella (documentación, mensajes
  de error, reglas de lint) no es usarla.
- `skip_outputs` con dependencias puramente de orden puede ser intencional:
  pregunta antes de reportarlo.
- Un `ref=main` en un repo de ejemplos o sandbox explícito es `menor`, no
  bloqueante.

## Revisar la propia skill `terragrunt-iac`

Cuando el encargo es validar la skill generadora (sus plantillas, scripts o
workflows) y no un repo de infraestructura:

1. Ejecuta `terragrunt_check.py --run-tools` sobre `assets/live-stacks`,
   `assets/catalog` y un repo generado con su `scaffold.py` para cada nube. Lo
   esperado es cero hallazgos en alcance; cualquier hallazgo es un defecto de
   la skill, porque se replicará en cada proyecto que la use.
2. Verifica que sus reglas y las de este catálogo no se contradigan (por
   ejemplo, ambos prohíben mocks en `apply`). Si divergen, repórtalo como
   `mayor` en la skill que esté desalineada con la documentación de Terragrunt.
3. Comprueba que sus scripts propios (`tg_lint.py`) detectan las mismas
   violaciones sobre `evaluations/fixtures/terragrunt-defects` aplicado sobre
   `terragrunt-base`.
4. Revisa que no afirme como "versión actual" un número que caduca; las
   versiones deben salir de `mise.toml`/`terragrunt --version`.

## Fuentes

- Documentación de Terragrunt 1.x (`gruntwork-io/terragrunt`, docs y strict controls).
- `kevin-burns/terragrunt-skill`: política post-1.0, auditoría de Terragrunt
  generado por máquina (conformidad, plan sin cambios, validar barato primero) y
  chequeo de formas previas a 1.0.
- `jfr992/terragrunt-skill` y `kvdomingo/dotrepo`: convenciones de catálogo,
  stacks y CAS; mocks obligatorios para plan/validate.
- `gruntwork-io/ai-skill-setup`: nunca inventar sintaxis; ante duda, consultar
  la referencia oficial.
- `awesome-skills/code-review-skill`: revisión por categorías con severidad.
- Marketplace "CN Terragrunt GitHub Actions": ejemplo de action legada basada
  en `the-commons-project`, versiones `latest` y referencias `@master`.
