# 08 — CI/CD con Terragrunt

Contenido: flujo recomendado, GitHub Actions (oficial y alternativas del marketplace), plan en PR con comentario, apply en main, drift detection, Azure DevOps, GitLab, controles de seguridad.

## 1. Flujo recomendado (Gruntwork)

```
PR abierto/actualizado ──► checks: hcl fmt --check, hcl validate, tg_lint
                       └─► plan SOLO de lo afectado: --filter '[origin/<base>...HEAD]' (rol plan, read-only)
                           └─► comentario en PR + artefacto de planes + report.json
merge a main ──────────► apply de lo afectado: --filter '[HEAD^...HEAD]' --filter-allow-destroy (rol apply)
                           └─► environment protegido (aprobación manual para prod)
cron diario ───────────► drift: run --all plan -detailed-exitcode ⇒ issue/alerta si exit 2
```

Reglas:
- `main` es la fuente de verdad; nada se aplica desde ramas.
- Un PR = un cambio coherente; evita PRs que toquen non-prod y prod a la vez (promueve en PRs separados).
- `concurrency` por repo/ambiente para que dos applies no compitan por el mismo estado.
- Los destroys requieren `--filter-allow-destroy` **y** aprobación (environment protegido o label).
- `fetch-depth: 0` en checkout (los filtros Git necesitan historia y la rama base).

## 2. Acciones del marketplace

| Action | Qué hace | Cuándo usarla |
|---|---|---|
| `gruntwork-io/terragrunt-action@v3` (oficial) | Instala Terragrunt + OpenTofu con mise (lee `mise.toml`; si no, `tg_version` + `tofu_version`). Opcionalmente ejecuta `tg_command` en `tg_dir`, comenta en el PR (`tg_comment: 1`), agrega `-auto-approve` (`tg_add_approve`), expone `tg_action_output` y `tg_action_exit_code`. Hooks `INPUT_PRE_EXEC_n`/`INPUT_POST_EXEC_n`. Mínimo soportado: TG 0.77.22 | **Default.** Úsala solo para instalar y ejecuta los comandos en `run:` para tener control total de flags |
| `eLco/setup-terragrunt@v1` | Solo instala Terragrunt (`terragrunt_version`, default latest) | Cuando ya instalas tofu/terraform por otro lado (`opentofu/setup-opentofu`, `hashicorp/setup-terraform`) |
| `boogy/terragrunt-runner@v1` | Ejecuta en varias carpetas en paralelo, auto-detecta carpetas desde archivos cambiados, borra comentarios viejos y publica resultados formateados en el PR | Monorepos grandes que quieren comentarios por carpeta; combinable con terragrunt-action para instalar |
| `darzanebor/github-terragrunt-wrapper` | Wrapper mínimo; en `fmt` hace auto-commit | Casos triviales; no recomendado para prod |
| `the-commons-project/terragrunt-github-actions` (y forks como "Run Terragrunt GitHub Action") | Imagen Docker derivada de las antiguas actions de HashiCorp, inputs `tf_actions_*` | **Legado**: no soporta bien CLI 1.x; migrar a la oficial |

Pinea actions de terceros por **SHA** de commit, no por tag.

## 3. Plantilla GitHub Actions

Ver `assets/workflows/terragrunt-github-actions.yml` (completo: checks, plan con comentario, apply por ambiente, OIDC AWS/Azure). Fragmento clave del plan:

```yaml
- uses: actions/checkout@v4
  with: { fetch-depth: 0 }
- uses: gruntwork-io/terragrunt-action@v3     # instala desde mise.toml, sin tg_command
- name: Plan afectado
  env:
    TG_NON_INTERACTIVE: "true"
    TF_IN_AUTOMATION: "1"
  # Monorepo con catálogo: usar --filter "(./live)...[origin/<base>...HEAD]" (ver 05)
  run: |
    terragrunt run --all \
      --filter "[origin/${{ github.base_ref }}...HEAD]" \
      --report-file report.json --report-format json \
      --tf-forward-stdout -- plan -no-color 2>&1 | tee plan.txt
```

Comentario en el PR: `tg_comment: 1` de la action oficial, o `actions/github-script`/`marocchino/sticky-pull-request-comment` con `plan.txt` truncado (los comentarios tienen límite de ~65k caracteres).

## 4. Aplicar exactamente lo revisado

`plan` en PR y `apply` en main se ejecutan sobre commits distintos (merge commit). Opciones, de más simple a más estricta:
1. Re-plan + apply en main (`apply` normal); aceptar que pueda diferir si main cambió (mitigar con "require branches up to date").
2. Guardar planes por unit (`--out-dir planes/`) como artefacto y aplicar esos planes en el job de apply del mismo workflow (requiere mismo SHA: apply dentro del PR tras aprobación, estilo Atlantis).
3. Merge queue de GitHub: el plan se ejecuta sobre el commit que realmente entrará.

## 5. Drift detection

```yaml
on: { schedule: [{ cron: "0 6 * * 1-5" }] }
# …
- run: |
    set +e
    terragrunt run --all --non-interactive -- plan -detailed-exitcode -lock=false > drift.txt 2>&1
    echo "exit=$?" >> "$GITHUB_OUTPUT"
```

Con `run --all`, Terragrunt agrega exit codes: `2` indica que algún unit tiene cambios. Abrir issue o notificar (Teams/Slack) con el resumen. Usa el rol de plan.

## 6. Azure DevOps

Ver `assets/workflows/azure-pipelines-terragrunt.yml`. Puntos clave:
- `checkout: self` con `fetchDepth: 0` y `git fetch origin $(System.PullRequest.TargetBranch)` para que exista la referencia base en PRs.
- Instalar con mise (`curl https://mise.run | sh` + `mise install`) o descargar binarios pineados.
- Autenticación: service connection con workload identity federation + `AzureCLI@2` (`addSpnToEnvironment: true`) exportando `ARM_CLIENT_ID`, `ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID`, `ARM_OIDC_TOKEN` (=`$idToken`), `ARM_USE_OIDC=true`.
- Aprobaciones: *Environments* con checks de aprobación para prod.
- Comentarios en PR: API REST de Azure Repos (`pullRequests/{id}/threads`) con `System.AccessToken`.

## 7. GitLab CI

- `GIT_DEPTH: 0`; base en MR: `$CI_MERGE_REQUEST_DIFF_BASE_SHA` → `--filter "[$CI_MERGE_REQUEST_DIFF_BASE_SHA...HEAD]"`.
- OIDC con `id_tokens:` (aud por nube).
- `resource_group:` por ambiente para serializar applies; `when: manual` + environments protegidos para prod.
- El `terragrunt-scale-catalog` incluye stacks de bootstrap `*/gitlab/pipelines-bootstrap`.

## 8. Terragrunt Scale / Gruntwork Pipelines (comercial)

Producto de Gruntwork que implementa este flujo (detección de cambios, plan/apply ordenado, drift, Patcher para actualizaciones). Configuración en `.gruntwork/*.hcl` y workflows `pipelines.yml`/`pipelines-drift-detection.yml`. Mencionarlo como alternativa "llave en mano"; esta skill implementa el flujo con Terragrunt OSS.

## 9. Checklist de seguridad del pipeline

- [ ] OIDC; ningún secreto de nube estático.
- [ ] Rol de plan sin permisos de escritura; rol de apply solo desde `main`/environment protegido.
- [ ] `permissions:` mínimos (`contents: read`, `id-token: write`, `pull-requests: write` solo en el job que comenta).
- [ ] `pull_request` (no `pull_request_target`) para código de forks; nunca ejecutar plan con credenciales sobre forks no confiables (los hooks y `run_cmd` ejecutan código arbitrario).
- [ ] Actions de terceros pineadas por SHA.
- [ ] Planes con salida sensible: no publicar `plan` completo en PRs públicos; marcar outputs `sensitive`.
- [ ] `concurrency` por ambiente; `cancel-in-progress: false` en apply.
- [ ] El runner puede clonar el catálogo privado **incluso en `find`**: con filtros Git y stacks, Terragrunt regenera los stacks en los worktrees y descarga sus fuentes (SSH con deploy key, o HTTPS con token vía `git config url."https://x-access-token:${TOKEN}@github.com/".insteadOf "git@github.com:"`).
