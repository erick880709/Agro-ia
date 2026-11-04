# 07 — Backends de estado y autenticación

Contenido: S3, azurerm, GCS; bootstrap; migración de estado; OIDC en CI por nube (modelo plan/apply separado del scale-catalog).

## 1. Principios

- Un backend por cuenta/suscripción/proyecto (y opcionalmente por región); la `key`/`prefix` = `path_relative_to_include()`.
- Bloqueo siempre activo; versionado y cifrado del bucket/cuenta de almacenamiento.
- Bootstrap explícito: `terragrunt backend bootstrap` (una vez, con rol privilegiado) o `--backend-bootstrap`. En CI de apply rutinario, déjalo apagado para no requerir permisos de creación.
- Roles separados: **plan** (solo lectura + lectura/lock de estado) y **apply** (escritura), con confianza OIDC restringida por rama/ambiente.

## 2. AWS S3

```hcl
remote_state {
  backend = "s3"
  config = {
    bucket       = "org-tfstate-${local.account_id}-${local.aws_region}-an"  # sufijo -an = namespace regional de cuenta (TG >= 1.2.0)
    key          = "${path_relative_to_include()}/tf.tfstate"
    region       = local.aws_region
    encrypt      = true
    use_lockfile = true            # lock nativo S3; reemplaza dynamodb_table
    # kms_key_id = "alias/tfstate"
  }
  generate = { path = "backend.tf", if_exists = "overwrite_terragrunt" }
}
```

- `dynamodb_table` sigue soportado (repos existentes) pero `use_lockfile` es la recomendación actual.
- Opciones solo-Terragrunt para bootstrap: `skip_bucket_versioning`, `skip_bucket_ssencryption`, `skip_bucket_root_access`, `skip_bucket_enforced_tls`, `skip_bucket_public_access_blocking`, `accesslogging_bucket_name`, `s3_bucket_tags`, `skip_bucket_accesslogging`. No las desactives en prod.
- Multi-cuenta: `iam_role` en `root.hcl` (`arn:aws:iam::${local.account_id}:role/terragrunt-apply`) o perfil por cuenta.

## 3. Azure (azurerm)

```hcl
remote_state {
  backend = "azurerm"
  config = {
    subscription_id      = local.subscription_id
    resource_group_name  = "rg-tfstate-${local.env}"
    storage_account_name = "sttfstate${local.env}${local.sufijo}"   # 3-24 minúsculas/números, único global
    container_name       = "tfstate"
    key                  = "${path_relative_to_include()}/tofu.tfstate"
    use_azuread_auth     = true
    use_oidc             = true            # en CI con identidad federada
    # Solo bootstrap (no se pasan a tofu):
    location                   = "eastus2"
    account_replication_type   = "GRS"
    enable_soft_delete         = true
    soft_delete_retention_days = 30
    assign_blob_data_role      = false     # true si el bootstrapper tiene roleAssignments/write
  }
  generate = { path = "backend.tf", if_exists = "overwrite_terragrunt" }
}
```

- Con `use_azuread_auth` el identity necesita **Storage Blob Data Contributor** en la cuenta (Contributor de control plane no basta).
- Orden de credenciales: SAS → access key → service principal (secret) → managed identity → OIDC (`use_oidc`, `ARM_OIDC_TOKEN`/`ARM_USE_OIDC`) → Azure AD / `az login`.
- Bootstrap crea RG, cuenta y contenedor, habilita versionado; con SAS/key no puede crear RG ni cuenta.
- `backend migrate` solo dentro de la misma cuenta de almacenamiento.
- Provider generado: incluye `features {}` y `subscription_id` explícito.

## 4. GCP (gcs)

```hcl
remote_state {
  backend = "gcs"
  config = {
    project  = local.project_id
    location = "us"
    bucket   = "org-tfstate-${local.project_id}"
    prefix   = "${path_relative_to_include()}"
    # Bootstrap: enable_bucket_policy_only = true, gcs_bucket_labels = {…}
  }
  generate = { path = "backend.tf", if_exists = "overwrite_terragrunt" }
}
```

GCS bloquea de forma nativa. Autenticación con Workload Identity Federation en CI.

## 5. Cifrado de estado (OpenTofu)

```hcl
remote_state {
  # …
  encryption = {
    key_provider = "aws_kms"          # pbkdf2 | aws_kms | gcp_kms | openbao
    kms_key_id   = "alias/tofu-state"
    region       = local.aws_region
    key_spec     = "AES_256"
  }
}
```

Solo OpenTofu. Planifica la rotación y no pierdas la clave: sin ella el estado es irrecuperable.

## 6. Operaciones de backend

```bash
terragrunt backend bootstrap                 # crea recursos del backend del unit actual
terragrunt backend bootstrap --all           # todos los units
terragrunt backend migrate old/unit new/unit # mueve estado al renombrar/mover units
terragrunt backend delete [--force]          # borra el archivo de estado (requiere versionado o --force)
```

## 7. OIDC en CI (sin secretos de larga duración)

| Nube | Recurso de confianza | En el pipeline |
|---|---|---|
| AWS | IAM OIDC provider `token.actions.githubusercontent.com` + roles `*-plan` / `*-apply` con condición `sub` | `aws-actions/configure-aws-credentials` con `role-to-assume`; permisos `id-token: write` |
| Azure | App registration / SP + **federated identity credential** (`repo:org/repo:ref:refs/heads/main`, `:pull_request`, `:environment:prod`) | `azure/login` con `client-id`, `tenant-id`, `subscription-id`; `ARM_USE_OIDC=true` |
| GCP | Workload Identity Pool + Provider + SA con `roles/iam.workloadIdentityUser` | `google-github-actions/auth` con `workload_identity_provider` |
| Azure DevOps | Service connection con *Workload identity federation* | `AzureCLI@2` con `addSpnToEnvironment: true` → exportar `ARM_*` |

Modelo del `terragrunt-scale-catalog`:
- Rol/SP **plan**: lectura en la suscripción/cuenta + acceso a estado; confía en cualquier rama/PR del repo.
- Rol/SP **apply**: permisos de escritura; confía solo en `main` (o en el `environment` protegido).
- GitHub ahora soporta *subject claims* inmutables con IDs numéricos (`repo:org@<org_id>/repo@<repo_id>:…`): úsalos para evitar suplantación por renombre de repos.

En Terragrunt, para AWS también puedes usar `--iam-assume-role-web-identity-token` / `iam_web_identity_token` o `--auth-provider-cmd` (script que devuelve credenciales JSON por unit).
