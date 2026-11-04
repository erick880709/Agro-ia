---
proyecto: <Proyecto>
skill: terragrunt-iac
actualizado: <AAAA-MM-DD>
---

# Línea base IaC — <Proyecto>

Documento vivo con las decisiones de infraestructura como código. La skill `terragrunt-iac` lo lee antes de generar o revisar código y lo actualiza al cerrar cada sesión de diseño.

## 1. Contexto
- Cliente / dominio:
- Equipo dueño:
- Repos: live = `<url>` · catálogo = `<url>` (¿monorepo? sí/no)

## 2. Nube y organización
| Nube | Nivel 1 (cuenta/suscripción/proyecto) | Regiones | Ambientes |
|---|---|---|---|
| AWS/Azure/GCP | | | |

## 3. Versiones (fuente: `mise.toml`)
- Terragrunt: `1.2.x` · OpenTofu/Terraform: `` · Providers principales: ``
- `terragrunt_version_constraint`: ``

## 4. Layout
- Tipo: stacks explícitos / implícito (`_envcommon`) / mixto
- Jerarquía: `root.hcl` → `account|sub|project.hcl` → `region.hcl` → `env.hcl`
- Convención de nombres de units y stacks:

## 5. Estado remoto
- Backend: s3 (`use_lockfile`) / azurerm / gcs
- Nombre de bucket/cuenta: `` · Key: `${path_relative_to_include()}/tf.tfstate`
- Bootstrap: manual (`terragrunt backend bootstrap`) / automático (`--backend-bootstrap`)
- Cifrado de estado (OpenTofu): sí/no — key provider:

## 6. Catálogo
- Versión vigente por ambiente: non-prod `v` · prod `v`
- Política de releases y promoción:

## 7. CI/CD
- Plataforma: GitHub Actions / Azure DevOps / GitLab
- Autenticación: OIDC — identidad plan: `` · identidad apply: ``
- Filtro de cambios: `(./live)...[origin/main...HEAD]`
- Aprobaciones: · Drift: cron ``
- Política de destroys:

## 8. Decisiones (ADR breve)
| Fecha | Decisión | Motivo | Alternativas descartadas |
|---|---|---|---|

## 9. Pendientes / TODO
-
