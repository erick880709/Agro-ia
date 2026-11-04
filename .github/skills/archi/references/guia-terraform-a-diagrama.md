# Guía: Generar el diagrama de despliegue desde código Terraform

Aplica en Caso B (y en la parte AS-IS del Caso C) cuando **no existe un documento de arquitectura de despliegue** vigente para el proyecto. Antes de usar esta guía, confirma que de verdad no existe: busca en `/docs`, README, `resources/architecture/` y cualquier `00-Documento_Arquitectura_*.md` / `00-Arquitectura_AS-IS_*.md` previo que ya declare proveedor de nube y componentes. Si existe y es consistente con el código actual, úsalo como fuente de verdad y no regeneres nada de esta guía.

> El `.drawio` que produzca esta guía se guarda dentro de `resources/architecture/` (créala si no existe). Antes de generarlo, valida/configura el MCP de diagramación siguiendo `references/guia-mcp-diagramacion.md` (usa `drawio-remoto` si está disponible).

## Regla de oro

El diagrama se construye **solo con lo que el `.tf` declara explícitamente**. Si un recurso no está en el código (por ejemplo, se creó manualmente en la consola y no está importado a Terraform), no aparece en el diagrama — o aparece marcado como "fuera de Terraform / gestionado manualmente" si hay evidencia indirecta de su existencia (ej. un `data source` que lo referencia). Nunca completes huecos por intuición del nombre de una carpeta o módulo.

## Paso 1 — Localizar el código Terraform

Busca archivos `.tf` y `.tf.json` en el repositorio (rutas típicas: `terraform/`, `infra/`, `infrastructure/`, `iac/`, o la raíz del repo). Si el repo es grande, usa un agente de exploración (`Explore`/`general-purpose`) para listar todos los `.tf` y sus rutas antes de leerlos uno por uno.

Si hay múltiples entornos (`environments/dev`, `environments/prod`, workspaces) o múltiples stacks/módulos raíz, documenta el diagrama del entorno de **producción** por defecto, salvo que el usuario pida otro explícitamente. Si no es identificable cuál es producción, pregúntale.

## Paso 2 — Identificar el proveedor de nube

Busca el bloque `provider` (o `required_providers` en Terraform ≥ 0.13):

```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws" }
  }
}
provider "aws" {
  region = "us-east-1"
}
```

- `provider "aws"` → AWS, resuelve IDs `aws.*` del catálogo curado, materializados con `mxgraph.aws4.*`.
- `provider "azurerm"` → Azure, resuelve IDs `azure.*`, materializados con SVG `img/lib/azure2/...`.
- `provider "google"` / `provider "google-beta"` → GCP, resuelve IDs `gcp.*`, materializados con `mxgraph.gcp3.*`.

Si hay más de un provider (multi-cloud real, no el modo comparativo del Caso A), genera un `.drawio` por proveedor presente, reflejando solo lo que ese provider gestiona.

## Paso 3 — Mapear recursos a componentes del diagrama

La secuencia es obligatoria: **recurso IaC observado → rol arquitectónico → componente `CT-xx` cuando aplique → alias/ID del catálogo → estilo visual**. Nunca inviertas la secuencia para deducir infraestructura a partir de los iconos disponibles. Lee `assets/iconos/aliases_iconos.json` y usa `assets/iconos/catalogo_iconos_curado.json` como fuente canónica de IDs y estilos.

Recorre los bloques `resource "<tipo>" "<nombre>" { ... }` y agrúpalos por función, no por tipo técnico exacto. Tabla de mapeo para los tipos más comunes (AWS; el mismo criterio aplica a `azurerm_*` y `google_*` con sus equivalentes):

| Tipo de recurso Terraform | Rol en el diagrama | ID de catálogo sugerido |
|---|---|---|
| `aws_instance`, `aws_launch_template`, `aws_autoscaling_group` | Cómputo | `aws.ec2` |
| `aws_ecs_service`, `aws_ecs_task_definition` | Cómputo en contenedores | `aws.ecs` |
| `aws_lambda_function` | Función | `aws.lambda` |
| `aws_lb`, `aws_alb` | Balanceador | `aws.application-load-balancer` |
| `aws_apigatewayv2_api`, `aws_api_gateway_rest_api` | API Gateway | `aws.api-gateway` |
| `aws_db_instance`, `aws_rds_cluster` | Base de datos | `aws.rds` |
| `aws_dynamodb_table` | Base de datos NoSQL | `aws.dynamodb` |
| `aws_elasticache_cluster`, `aws_elasticache_replication_group` | Cache | `aws.elasticache` |
| `aws_s3_bucket` | Almacenamiento | `aws.s3` |
| `aws_sqs_queue` | Cola | `aws.sqs` |
| `aws_sns_topic` | Notificación/eventos | `aws.sns` |
| `aws_cloudfront_distribution` | CDN | `aws.cloudfront` |
| `aws_vpc` | Contenedor de red | límite neutro de VPC; usa icono solo si aporta información |
| `aws_subnet` | Subred (pública si tiene ruta a IGW, privada si no) | agrupación dentro de la VPC |
| `aws_cognito_user_pool` | Identidad | `aws.cognito` |
| `aws_rds_cluster` (engine `aurora-*`) | Base de datos Aurora | `aws.aurora` |
| `aws_eks_cluster`, `aws_eks_node_group` | Kubernetes | `aws.eks` |
| `aws_ecr_repository` | Registro de imágenes | `aws.ecr` |
| `aws_lb` (`load_balancer_type = "network"`) | Balanceador de red | `aws.network-load-balancer` |
| `aws_internet_gateway` | Entrada/salida pública de la VPC | `aws.internet-gateway` |
| `aws_nat_gateway` | Egress privado | `aws.nat-gateway` |
| `aws_vpc_endpoint` | Acceso privado a servicios | `aws.vpc-endpoints` (o `aws.privatelink` si expone un servicio propio) |
| `aws_ec2_transit_gateway`, `aws_ec2_transit_gateway_vpc_attachment` | Hub de ruteo / adjunto | `aws.transit-gateway` / `aws.transit-gateway-attachment` |
| `aws_networkmanager_core_network`, `aws_networkmanager_vpc_attachment` | Red global Cloud WAN | `aws.cloud-wan` (la política se documenta en `17.6`) |
| `aws_networkfirewall_firewall` | Inspección | `aws.network-firewall` |
| `aws_wafv2_web_acl` | WAF | `aws.waf` |
| `aws_route53_zone`, `aws_route53_resolver_endpoint` | DNS | `aws.route-53` |
| `aws_dx_connection`, `aws_dx_gateway` / `aws_vpn_connection` | Conectividad híbrida | `aws.direct-connect` / `aws.site-to-site-vpn` |
| `aws_vpclattice_service_network` | Red de servicios | `aws.vpc-lattice` |
| `aws_kms_key` | Llaves | `aws.kms` |
| `aws_iam_role` usado entre cuentas | Confianza entre cuentas | `aws.iam` (documenta ambos lados en `17.6`) |
| `aws_sfn_state_machine` | Orquestación | `aws.step-functions` |
| `aws_kinesis_stream` | Streaming | `aws.kinesis-data-streams` |
| `aws_codebuild_project` (webhook de GitHub Actions) | Runner de CI/CD | `aws.codebuild` |
| `aws_cloudtrail`, `aws_config_*`, `aws_guardduty_detector`, `aws_securityhub_account` | Auditoría y detección | `aws.cloudtrail`, `aws.config`, `aws.guardduty`, `aws.security-hub` |
| `aws_organizations_organization` / `aws_organizations_account` | Organización/cuenta | límite `aws.group-account`; `aws.organizations` solo en vistas de plataforma |

Para `azurerm_*`: `azurerm_linux_virtual_machine`/`azurerm_windows_virtual_machine` → VM, `azurerm_app_service` → App Service, `azurerm_kubernetes_cluster` → AKS, `azurerm_postgresql_flexible_server`/`azurerm_mssql_database` → base de datos, `azurerm_redis_cache` → cache, `azurerm_storage_account` → storage, `azurerm_servicebus_namespace` → mensajería, `azurerm_virtual_network` → contenedor de red.

Para `google_*`: `google_compute_instance` → Compute Engine, `google_cloud_run_service` → Cloud Run, `google_container_cluster` → GKE, `google_cloudfunctions_function` → Cloud Functions, `google_sql_database_instance` → Cloud SQL, `google_firestore_database` → Firestore, `google_storage_bucket` → Cloud Storage, `google_pubsub_topic` → Pub/Sub, `google_compute_network` → VPC.

Si aparece un `resource` que no tiene equivalente evidente en la tabla, no lo omitas: usa el `fallback` genérico del proveedor con su tipo real como etiqueta y registra la brecha de catálogo, en vez de forzarlo a una categoría incorrecta.

## Paso 4 — Reconstruir las relaciones

Las conexiones del diagrama salen de las referencias entre recursos dentro del propio `.tf` (no de suposiciones):
- Un recurso que referencia el `id`/`arn` de otro (ej. `subnet_id = aws_subnet.privada.id`, `vpc_security_group_ids = [aws_security_group.api.id]`) implica una relación de red/pertenencia.
- Variables de entorno o configuración que apuntan a un endpoint (ej. `environment { variables = { DB_HOST = aws_db_instance.principal.address } }`) implican una relación de comunicación aplicativa — inclúyela como flecha con la etiqueta del propósito (ej. "Lee/escribe", "SQL").
- Si dos recursos están en el mismo `.tf` pero no hay ninguna referencia cruzada entre ellos, no dibujes una conexión — no está soportada por el código.

## Paso 5 — Generar el archivo y documentar hallazgos

1. Genera `17.1-Despliegue_AWS_<Proyecto>.drawio`, `17.2-Despliegue_Azure_<Proyecto>.drawio` o `17.3-Despliegue_GCP_<Proyecto>.drawio` según el proveedor, siguiendo `references/drawio-iconos-nube.md`.
2. Valídalo con `scripts/validate_drawio_catalog.py --drawio <archivo> --provider <proveedor> --strict`; cada recurso cloud debe declarar un `archiIconId` coherente con el catálogo.
3. En `17-Vista-de-Despliegue.md`, referencia el archivo y anota explícitamente: "Diagrama generado a partir del código Terraform en `<ruta>`, módulo/entorno `<nombre>`". Registra también hash, versión del catálogo, fecha y resultado del validador.
4. Si durante el análisis encuentras recursos con configuración hardcodeada, ausencia de tags, secretos en texto plano, o módulos sin versión fijada, regístralo en `21-Riesgos-y-Deuda-Tecnica.md`.

## Terragrunt y CloudFormation

- **Terragrunt**: un `terragrunt.hcl` es un unit con su propio estado; su `terraform.source` apunta al módulo que declara los recursos (lee el módulo en la versión pineada de `?ref=`). Un `terragrunt.stack.hcl` genera units: ejecuta `terragrunt stack generate` o lee los `unit` declarados para inventariarlos. Los bloques `dependency` son relaciones entre units; los archivos `account.hcl`/`region.hcl`/`env.hcl` dan cuenta, región y ambiente de cada recurso. La jerarquía de carpetas del repo *live* suele reflejar cuenta → región → ambiente: úsala como evidencia de los límites del diagrama.
- **CloudFormation/SAM/CDK**: el tipo `AWS::Service::Resource` define el rol (por ejemplo `AWS::EC2::TransitGateway` → `aws.transit-gateway`, `AWS::NetworkFirewall::Firewall` → `aws.network-firewall`, `AWS::ECR::Repository` → `aws.ecr`). Las relaciones salen de `Ref`, `Fn::GetAtt`, `Fn::ImportValue` y `DependsOn`; los `Outputs`/`Export` entre stacks son dependencias entre módulos. En CDK sintetiza (`cdk synth`) y analiza la plantilla resultante, no el código fuente.

## Si no hay Terraform ni documento previo

Antes de dejar `17-Vista-de-Despliegue.md` vacío, busca otras señales de IaC (CloudFormation `.yaml`/`.json` con `AWSTemplateFormatVersion`, ARM/Bicep, Pulumi, manifiestos de Kubernetes con anotaciones de nube, `serverless.yml`). Si encuentras alguna, aplica el mismo criterio adaptado. Si no hay evidencia, pregunta al usuario o documenta en `04-Supuestos.md` que la infraestructura no pudo determinarse.
