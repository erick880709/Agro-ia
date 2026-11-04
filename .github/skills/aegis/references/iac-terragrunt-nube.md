# Seguridad de IaC: Terragrunt / OpenTofu / Terraform en AWS, Azure y GCP

Se apoya en terragrunt-iac (principios y `tg_lint.py`) y en `terragrunt-iac.md` de
code-review. Aegis se ocupa de lo que convierte un error de IaC en exposición: identidad,
red, cifrado, estado y cadena de suministro de módulos.

## Tabla de contenido

1. Cómo analizar
2. Estado remoto y Terragrunt
3. Identidad e IAM
4. Red y exposición
5. Datos y cifrado
6. Registro, detección y protección contra borrado
7. Herramientas de política
8. Checklist rápido por severidad

## 1. Cómo analizar

1. Ejecuta `tg_lint.py` y, si existe, `terragrunt_check.py`; parte de sus ALTA.
2. Analiza **módulos del catálogo** (`*.tf`), no solo el live: los defaults inseguros
   viven en `variables.tf` (`default = true` para acceso público, `default = "*"`).
3. Analiza el **plan** cuando esté disponible (`tofu show -json plan.out`): es la verdad
   de lo que se aplicará, después de `values`, `inputs` y defaults.
4. Verifica contra `17`/`17.6`/`17.7` de archi: una exposición o confianza que la
   arquitectura no aprobó es hallazgo aunque la herramienta no la marque.

## 2. Estado remoto y Terragrunt

- El estado contiene secretos en claro (contraseñas generadas, llaves, outputs
  sensibles): backend S3 con cifrado (SSE-KMS preferido), `block public access`,
  versionado, bloqueo (`use_lockfile = true` o DynamoDB) y política que limite acceso a
  los roles del pipeline. Azure: storage account sin acceso público, `allow_blob_public_access
  = false`, RBAC y `min_tls_version`. GCS: `uniform_bucket_level_access`, sin `allUsers`.
- `inputs`/`values`/`locals` con secretos literales → bloqueante; usa `sops_decrypt_file()`,
  `TF_VAR_*` desde el gestor de secretos o referencias por ARN/ID al secreto.
- `outputs` con secretos sin `sensitive = true` (se imprimen en logs del pipeline).
- `run_cmd` y hooks con entrada no confiable o scripts descargados → ejecución arbitraria
  en el runner con credenciales de nube.
- `source` sin pinear (`ref=main`) en prod: un push al catálogo cambia producción sin revisión.

## 3. Identidad e IAM

- Políticas con `Action: "*"`, `Resource: "*"`, `iam:PassRole` sin condición de recurso,
  `sts:AssumeRole` abierto; roles administrativos asignados a cargas de trabajo.
- Azure: `Owner`/`Contributor` a nivel suscripción para identidades de aplicación;
  `User Access Administrator` innecesario. GCP: `roles/owner`/`roles/editor` primitivos,
  `iam.serviceAccountTokenCreator` amplio, llaves de service account (`google_service_account_key`).
- **OIDC de CI** (GitHub → AWS/Azure/GCP): la condición de confianza debe fijar
  repositorio **y** rama/entorno. AWS: `token.actions.githubusercontent.com:sub` con
  `repo:org/repo:ref:refs/heads/main` o `environment:prod`, nunca `repo:org/*` ni solo
  `aud`. Azure: *federated credential* con `subject` exacto. GCP: Workload Identity
  Federation con `attribute_condition` sobre `assertion.repository` y `assertion.ref`.
  Rol de plan (solo lectura) separado del rol de apply.
- Llaves de acceso estáticas creadas por IaC (`aws_iam_access_key`) → preferir identidades
  de carga de trabajo.

## 4. Red y exposición

- `0.0.0.0/0` o `::/0` en ingreso a puertos administrativos (22, 3389, 5432, 3306, 1433,
  6379, 9200, 27017) → high/critical según servicio.
- Bases de datos/caches con `publicly_accessible = true`, IP pública o sin private
  endpoint; buckets/containers públicos (`acl = "public-read"`, `allUsers`).
- API Gateway/Function URLs/App Service sin autenticación cuando `14.00` declara
  exposición interna; WAF ausente en exposición Internet que la arquitectura exige.
- Load balancers con listeners HTTP sin redirección, políticas TLS antiguas.
- Kubernetes gestionado con endpoint público sin restricción de CIDR.

## 5. Datos y cifrado

- Almacenamiento sin cifrado o con llaves gestionadas por el proveedor cuando la
  clasificación (`16.xx`) exige CMK: RDS/Aurora, EBS, S3, DynamoDB, SQS/SNS, Azure SQL/
  Storage, Cloud SQL/GCS.
- KMS: rotación deshabilitada, política de llave con principal `*`.
- Secretos en `user_data`, variables de entorno de Lambda/App Service/Cloud Run en claro
  en vez de referencias a Secrets Manager/Key Vault/Secret Manager.
- Backups/snapshots compartidos públicamente o sin cifrado; retención menor a la
  regulatoria.

## 6. Registro, detección y protección contra borrado

- CloudTrail/Activity Log/Audit Logs deshabilitados o sin destino protegido; logs de
  acceso de buckets de estado y de datos sensibles.
- `deletion_protection`, `prevent_destroy`, soft delete/purge protection de Key Vault
  ausentes en datos, llaves y estado (impacto de integridad/disponibilidad).

## 7. Herramientas de política

| Herramienta | Uso | Nota |
|---|---|---|
| Checkov | `checkov -d <catálogo>` y `checkov -f plan.json` | Amplio, buen mapeo a CIS |
| Trivy (`trivy config`) | IaC, Dockerfile, K8s en un binario | Sucesor de tfsec |
| KICS / Terrascan | Alternativas | Usa la que el equipo ya tenga |
| OPA/Conftest | Políticas propias sobre el plan JSON | Para reglas del banco (CIDR, tags, CMK) |

Toda alerta es candidato: verifica que el valor marcado es el que corre (el live puede
sobreescribir el default) y que no hay un control compensatorio (SCP, Azure Policy,
Organization Policy) documentado en `17.6`.

## 8. Checklist rápido por severidad

- **Bloqueante:** secreto literal en HCL/estado expuesto; confianza OIDC sin fijar repo
  o rama; IAM `*:*` para cargas; dato sensible público; estado sin cifrado o público.
- **Mayor:** cifrado con llave del proveedor donde se exige CMK; puertos administrativos
  abiertos a rangos amplios internos; logs de auditoría ausentes; sin `prevent_destroy`
  en datos/llaves; refs sin pinear en prod.
- **Menor/hardening:** tags de clasificación faltantes, TLS policy no óptima sin
  exposición, rotación de llaves no configurada en entornos no productivos.
