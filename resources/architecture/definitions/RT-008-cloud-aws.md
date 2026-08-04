# RT-008: Infraestructura Cloud — AWS (preferido)

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / Cloud
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 7.2

## Descripción
La plataforma debe desplegarse en la nube pública. El proveedor preferido es **AWS** (Amazon Web Services), seleccionado por su elasticidad, alta disponibilidad y modelo de pago por uso. Los servicios AWS contemplados incluyen:

- **Cómputo:** EC2 (nodos Kubernetes) o EKS (Kubernetes gestionado).
- **Almacenamiento de objetos:** S3 para datasets, modelos entrenados, reportes PDF y base documental del RAG.
- **Base de datos:** RDS para PostgreSQL (+ PostGIS).
- **Machine Learning:** SageMaker para entrenamiento y despliegue de modelos (opcional, puede usarse EC2).
- **IoT:** IoT Core para ingesta y gestión de dispositivos de sensores.
- **Mensajería:** SQS/SNS para desacoplamiento de servicios.
- **CDN y DNS:** CloudFront y Route 53.
- **Seguridad:** VPC, subnets privadas/públicas, WAF, Secrets Manager, IAM.

Alternativas viables: Azure y GCP, pero AWS es la opción principal recomendada.

## Criterio medible / restricción concreta
- Infraestructura definida como código (IaC): Terraform o AWS CDK/CloudFormation.
- VPC con subnets privadas para bases de datos y workers de ML.
- Recursos etiquetados para gestión de costos por entorno/proyecto.
- No especificados en el RFP — definir: región AWS (us-east-1 para mejor disponibilidad de servicios, pero considerar latencia desde Colombia; sa-east-1 en São Paulo es la más cercana), presupuesto mensual estimado de infraestructura.

## Impacto en la arquitectura
- Determina los servicios gestionados disponibles y su modelo de costos.
- La elección de AWS condiciona decisiones como: EKS vs. ECS, RDS vs. Aurora, SageMaker vs. EC2 para ML.
- La infraestructura como código (Terraform) es un entregable esperado según la sección 11 del RFP.

## Notas del analista
- La región AWS más cercana a Colombia es sa-east-1 (São Paulo, Brasil), con latencia ~100–150ms. Para una aplicación web, es aceptable. Usar CloudFront como CDN puede reducir la latencia percibida para contenido estático.
- Se recomienda Terraform sobre CloudFormation por ser multi-cloud, lo que facilitaría una migración futura a Azure o GCP si fuera necesario.
- SageMaker es útil para el ciclo de vida de modelos ML, pero añade costo y acoplamiento a AWS. Para el MVP, EC2 + MLflow puede ser suficiente y más portable.
