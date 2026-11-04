# Seguridad de CI/CD: GitHub Actions y Azure DevOps

El pipeline corre con las credenciales más poderosas del sistema (deploy a prod, acceso
a estado y secretos). Trátalo como código productivo de máxima criticidad. Basado en
las prácticas de `zizmor`, `agentic-actions-auditor` (Trail of Bits) y `cicd-security`.

## Tabla de contenido

1. Inventario y quién dispara
2. GitHub Actions
3. Agentes de IA en el pipeline
4. Azure DevOps
5. Runners
6. Herramientas

## 1. Inventario y quién dispara

Por cada workflow/pipeline: disparadores, quién puede dispararlos (externo, colaborador,
mantenedor), permisos del token, secretos/identidades disponibles, entornos con
aprobación y artefactos que publica. Un job que mezcla **entrada de baja confianza** con
**credenciales de alta confianza** es la forma de casi todos los hallazgos.

## 2. GitHub Actions

- `pull_request_target` o `workflow_run` que hace checkout del código del PR
  (`ref: ${{ github.event.pull_request.head.sha }}`) y lo ejecuta (build, tests, scripts)
  con secretos → ejecución de código de terceros con secretos (critical en repos públicos).
- **Inyección de expresiones**: `${{ github.event.issue.title }}`, `...pull_request.body`,
  `...head_ref`, `...comment.body` interpolados en `run:` → inyección de shell. Remedio:
  pasarlos por `env:` y usar `"$VAR"` entrecomillado.
- `permissions:` ausente (token con permisos por defecto amplios en repos antiguos) o
  `write-all`; define `permissions: {}` a nivel workflow y concede por job.
- Actions de terceros pineadas por tag (`@v3`) en vez de SHA completo; actions de
  mantenedores no verificados en jobs con secretos.
- `secrets: inherit` en reusable workflows de terceros; secretos impresos (`echo`,
  `set -x`) o escritos a artefactos/caché.
- OIDC: `id-token: write` solo en el job que lo necesita; la confianza en la nube se
  revisa en [IaC](iac-terragrunt-nube.md) §3.
- Apply/deploy desde ramas distintas de la protegida, sin `environment` con revisores.
- Cache poisoning: caches compartidas entre `pull_request` y jobs de release.
- `GITHUB_ENV`/`GITHUB_PATH` escritos con contenido no confiable.

## 3. Agentes de IA en el pipeline

(Claude Code Action, Codex, Gemini CLI, Copilot agents, skills ejecutadas en CI)
- Entrada atacante (issues, comentarios, PR) que llega al prompt directamente **o vía
  `env:`** (el vector más omitido: el prompt no muestra `${{ }}` pero recibe el dato).
- Sandbox debilitado (`--dangerously-skip-permissions`, `Bash(*)`, `danger-full-access`,
  `--yolo`) en jobs disparados por terceros.
- Allowlist de usuarios con comodín; herramientas permitidas que permiten exfiltración
  (`curl`, `gh`, escritura a `GITHUB_ENV`).
- Agente con token de escritura al repo o secretos de despliegue en el mismo job.
Remedio: separar el job de análisis (sin secretos, permisos de lectura) del de acción;
humano en el ciclo para efectos; nunca disparar con `pull_request_target` + checkout.

## 4. Azure DevOps

- Variables secretas en YAML en claro o variables no marcadas como secretas; secretos
  pasados como argumentos de línea de comando (quedan en logs).
- Service connections con alcance a toda la suscripción y "Grant access permission to
  all pipelines" activado; preferir Workload Identity Federation sobre secretos de SP.
- Pipelines de PR desde forks con acceso a secretos ("Make secrets available to builds
  of forks").
- Ausencia de *approvals and checks* en entornos productivos; `extends` templates
  obligatorios no exigidos.
- Tareas de marketplace sin verificar; `checkout: self` con `persistCredentials: true`
  innecesario.

## 5. Runners

- Self-hosted runners en repos públicos o compartidos entre niveles de confianza; runners
  persistentes (no efímeros) que conservan credenciales/artefactos entre jobs.
- Runners con rol de instancia amplio (CodeBuild/ECS/VMSS) en vez de identidad por job.
- Archi `17.6` documenta runners propios: verifica aislamiento de red y salida.

## 6. Herramientas

`zizmor` (GitHub Actions, offline y online), `actionlint`, Semgrep `p/github-actions`,
Checkov para Azure Pipelines/GitHub Actions. Candidatos, no veredictos.
