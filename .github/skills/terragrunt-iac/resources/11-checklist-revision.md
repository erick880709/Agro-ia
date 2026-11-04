# 11 — Checklist de revisión y antipatrones

Contenido: checklist por severidad para revisar repos/PRs de Terragrunt y formato del informe de hallazgos. Ejecuta primero `python scripts/tg_lint.py <ruta>` (cubre los ítems marcados con ⚙) y completa manualmente el resto.

## Formato de cada hallazgo

```
[ALTA] live/prod/us-east-1/rds/terragrunt.hcl:12 — mocks permitidos en apply
Por qué importa: si la dependencia no tiene estado, apply usaría "vpc-mock" y fallaría a mitad o crearía recursos mal configurados.
Cambio: mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
```

Cierra con un resumen: conteo por severidad, top 3 riesgos y orden sugerido de corrección.

## ALTA — riesgo de pérdida de datos, seguridad o despliegue erróneo

- ⚙ `"apply"` o `"destroy"` en `mock_outputs_allowed_terraform_commands`, o `skip_outputs = true` en dependencias usadas en inputs de prod.
- ⚙ Fuentes sin pinear en prod: `?ref=main|master`, sin `ref`, ramas; registry sin `version`.
- ⚙ Credenciales/secretos literales en HCL (`password = "..."`, `client_secret`, `AKIA…`, `access_key`).
- `remote_state` sin `key` única por unit (no usa `path_relative_to_include()`), sin bloqueo (`use_lockfile`/`dynamodb_table`), o sin cifrado.
- Varios units apuntando al mismo estado (copiar/pegar sin cambiar key) o uso de workspaces.
- Provider sin `allowed_account_ids` / `subscription_id` / `project` explícitos → riesgo de aplicar en la cuenta equivocada.
- Bases de datos, KMS, buckets de estado sin `prevent_destroy = true` (o sin `lifecycle.prevent_destroy` en el módulo).
- Pipelines: apply desde ramas, credenciales estáticas, `pull_request_target` ejecutando código del PR, `--filter-allow-destroy` sin aprobación, `--queue-ignore-errors` en apply.
- `run_cmd`/hooks que ejecutan scripts descargados o con entrada no confiable.

## MEDIA — mantenibilidad, compatibilidad, rendimiento

- ⚙ Sintaxis legada: `run-all`, `*-all`, `--terragrunt-*`, `TERRAGRUNT_*`, `hclfmt`, `graph-dependencies`, `render-json`.
- ⚙ Raíz llamada `terragrunt.hcl`; `find_in_parent_folders()` sin argumento; `include` sin etiqueta.
- ⚙ `skip =`, `retryable_errors =` sueltos, `mock_outputs_merge_with_state`, `config_path` a archivo.
- ⚙ `TF_PLUGIN_CACHE_DIR` manual en CI con `run --all`.
- ⚙ Sin `mise.toml` / `terragrunt_version_constraint`.
- Duplicación entre ambientes que podría ir a `_envcommon` o a un stack/unit de catálogo (>70% de líneas iguales).
- Código OpenTofu (`*.tf`) mezclado en el repo live.
- `run_cmd`, `get_aws_account_id()`, `sops_decrypt_file()` en `locals` de muchos units (discovery lento, requiere credenciales para `find`).
- `dependencies` + `dependency` redundantes; dependencias circulares latentes; `dependency` sin uso.
- `count` en `expansion` donde el orden puede cambiar.
- Stacks profundos sin `update_source_with_cas`.
- Falta `.terragrunt-filters` en monorepo con catálogo.
- Pipelines sin filtro por cambios (`run --all` completo en cada PR) o con `fetch-depth: 1` usando filtros Git.

## BAJA — estilo y higiene

- ⚙ `hcl fmt` pendiente.
- `.gitignore` sin `.terragrunt-cache/`, `.terragrunt-stack/`, `terragrunt-debug.tfvars.json`.
- `.terraform.lock.hcl` no versionado.
- Etiquetas inconsistentes, comentarios ausentes en root/stacks, README desactualizado.
- `inputs` que repiten defaults del módulo.

## Antipatrones (y su reemplazo)

| Antipatrón | Reemplazo |
|---|---|
| Terralith: un unit gigante con todo el ambiente | Partir por ciclo de vida y blast radius (red, datos, cómputo, apps) |
| Un unit por recurso (cientos de micro-units) | Agrupar por componente lógico; cada unit debe tener sentido desplegable |
| Workspaces para ambientes | Carpetas por ambiente / stacks con values |
| `_envcommon` con lógica condicional por ambiente (`if env == "prod"`) | Values explícitos por ambiente |
| Mocks "por si acaso" en todos lados | Mocks solo en dependencias que pueden no existir, solo para validate/plan/init |
| Copiar módulos de terceros dentro de live | Catálogo propio o `tfr://` con versión |
| `--queue-ignore-dag-order` para "arreglar" ciclos | Corregir el grafo |
| Scripts de `git diff` para decidir qué correr | `--filter '[base...HEAD]'` |
