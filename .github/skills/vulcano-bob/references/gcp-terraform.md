# Adaptador GCP para Terraform

## Contrato

- Requerir provider `google` (o `google-beta` para recursos en preview) con constraint explícito.
- Crear el estado en Cloud Storage mediante `assets/gcp-backend.bootstrap.template.sh`.
- Habilitar versionado y `uniform-bucket-level-access` + `public-access-prevention` en el bucket.
  El backend `gcs` de Terraform bloquea de forma nativa (no existe un `TFSTATE_KMS_KEY` sin
  clave, ni una tabla de locking equivalente a DynamoDB que crear aparte).
- Usar un prefijo distinto por ambiente (`state_prefix`); no compartir state entre `dev`, `qa` y
  `prod` dentro del mismo bucket.
- Pasar `bucket` y `prefix` como configuración parcial del backend. Nunca escribir claves de
  cuenta de servicio, tokens ni secretos en HCL, `-backend-config` o plan files.
- Preferir Workload Identity Federation (OIDC desde el pipeline) sobre claves de cuenta de
  servicio descargadas; permisos mínimos (`roles/storage.objectAdmin` acotado al bucket de
  estado, no a nivel de proyecto).
- Si `TFSTATE_KMS_KEY` está definido, usarlo como `default-encryption-key` del bucket (Cloud KMS);
  sin esa variable, el bucket queda con el cifrado gestionado por Google por defecto.

Renderizar el bootstrap idempotente sin ejecutar llamadas cloud:

```powershell
node .claude/skills/vulcano-bob/scripts/render-bob-bootstrap.mjs
```

```hcl
terraform {
  backend "gcs" {
    bucket = "__TFSTATE_BUCKET__"
    prefix = "terraform/dev"
  }
}
```

Fuentes oficiales: [backend GCS de Terraform](https://developer.hashicorp.com/terraform/language/backend/gcs)
y [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation).
