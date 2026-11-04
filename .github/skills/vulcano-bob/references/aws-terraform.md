# Adaptador AWS para Terraform

## Contrato

- Requerir provider `aws` con constraint explícito.
- Crear el estado en S3 mediante `assets/aws-backend.bootstrap.template.sh`.
- Habilitar versionado, bloqueo público, cifrado y `use_lockfile = true` en cada backend.
- Usar una key distinta por ambiente; no compartir state entre `dev`, `qa` y `prod`.
- Pasar `bucket`, `region` y `key` como configuración parcial del backend. Nunca escribir access
  keys, tokens ni secretos en HCL, `-backend-config` o plan files.
- Preferir roles federados/OIDC y permisos mínimos sobre el bucket, state y archivo `.tflock`.
- No crear DynamoDB para locking nuevo: ese mecanismo está deprecado.

Renderizar el bootstrap idempotente sin ejecutar llamadas cloud:

```powershell
node .claude/skills/vulcano-bob/scripts/render-bob-bootstrap.mjs
```

```hcl
terraform {
  backend "s3" {
    key          = "terraform/dev/terraform.tfstate"
    use_lockfile = true
    encrypt      = true
  }
}
```

Fuentes oficiales: [backend S3 de Terraform](https://developer.hashicorp.com/terraform/language/backend/s3)
y [roles IAM con OIDC](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html).
