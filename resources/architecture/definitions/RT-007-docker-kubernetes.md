# RT-007: Contenedores Docker y Orquestación Kubernetes

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / DevOps
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 6.5, 7.2

## Descripción
Todos los componentes de la plataforma deben empaquetarse como contenedores Docker y orquestarse mediante Kubernetes. Esto incluye:

**Docker:**
- Imágenes optimizadas (multi-stage builds para reducir tamaño).
- Imágenes base oficiales y mantenidas (python:3.11-slim, node:21-alpine para Angular).
- Escaneo de vulnerabilidades en imágenes como parte del CI/CD.

**Kubernetes:**
- Escalado automático horizontal (HPA — Horizontal Pod Autoscaler) basado en CPU/memoria o métricas personalizadas (profundidad de cola).
- Alta disponibilidad mediante múltiples réplicas de cada servicio.
- Despliegues sin tiempo de inactividad (rolling updates, blue/green o canary).
- Aislamiento de recursos: requests y limits de CPU/memoria por contenedor.
- Políticas de red (Network Policies) para segmentar servicios por nivel de sensibilidad.
- Health checks (liveness y readiness probes) para auto-recuperación.

## Criterio medible / restricción concreta
- Imágenes Docker publicadas en un registro de contenedores privado.
- Mínimo 2 réplicas por servicio en producción para alta disponibilidad.
- Uso de namespaces en Kubernetes para separar entornos (dev, staging, prod).
- No especificados en el RFP — definir: distribución de Kubernetes (EKS en AWS, AKS, GKE, o auto-gestionado), herramienta de despliegue (Helm, Kustomize, ArgoCD).

## Impacto en la arquitectura
- Kubernetes es el estándar de orquestación cloud-native. Su adopción permea todo el ciclo de vida: desarrollo, CI/CD, despliegue, monitoreo y operación.
- Necesidad de un clúster de Kubernetes gestionado (EKS en AWS como preferido) para producción.
- Helm charts o Kustomize para definición declarativa de cada servicio.

## Notas del analista
- AWS EKS es la opción más coherente si el proveedor cloud elegido es AWS, ya que se integra con IAM, VPC, CloudWatch y demás servicios.
- Para el MVP/piloto, un clúster pequeño (2–3 nodos) es suficiente. La arquitectura permite escalar horizontalmente añadiendo nodos.
- Kubernetes añade complejidad operativa. Si el equipo es pequeño, evaluar AWS ECS Fargate como alternativa más simple (sin nodos que gestionar), aunque se perdería parte de la flexibilidad de Kubernetes.
