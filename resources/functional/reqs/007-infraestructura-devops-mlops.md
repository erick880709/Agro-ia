---
id: 007
slug: infraestructura-devops-mlops
ia_cierre: 15/100
rondas: 1
estado: lista-para-diseno
fecha: 2026-08-03
---

# NECESIDAD DE NEGOCIO REFINADA

Infraestructura híbrida: datos en servidor local colombiano (cumplimiento Ley 1581 + residencia de datos) + cómputo en AWS EKS (Kubernetes gestionado, sa-east-1 São Paulo). Docker multi-stage, Helm para despliegues, Terraform para IaC. CI/CD con GitHub Actions + SAST/DAST mensual. Observabilidad con CloudWatch + X-Ray (nativo AWS). MLOps con MLflow (tracking + registry), reentrenamiento semi-automático con gate manual. Escalabilidad: 5,000 usuarios registrados, 500-1,000 concurrentes, HPA en EKS. Alta disponibilidad: ≥2 réplicas por servicio, rolling updates, liveness/readiness probes. PostgreSQL RDS + PostGIS + pgvector, S3 para objetos, RabbitMQ para mensajería IoT, ElastiCache (Redis) para caché.

**Stack de infraestructura**
| Componente | Elección |
|-----------|----------|
| Cloud | AWS (cómputo) + servidor local Colombia (datos) |
| Orquestación | EKS (Kubernetes gestionado) |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Observabilidad | CloudWatch + X-Ray |
| MLOps | MLflow Tracking + Registry |
| Despliegue | Helm charts |
| Caché | ElastiCache (Redis) |

**Actores:** Administrador (infraestructura, CI/CD, monitoreo), Investigador IES (MLflow, experimentos)

**Alcance**
- ✅ EKS 2-3 nodos MVP, HPA, ≥2 réplicas, rolling updates, health checks
- ✅ Terraform, GitHub Actions, CloudWatch+X-Ray, MLflow, Helm
- ✅ Datos en Colombia, cómputo en AWS sa-east-1
- ❌ Multi-cloud, presupuesto no definido, reentrenamiento 100% automático

**Métricas**
| Métrica | Meta |
|---------|------|
| Usuarios registrados | 5,000 |
| Concurrentes hora pico | 500-1,000 |
| Disponibilidad | 99.9% |
| Tiempo despliegue | <15 min CI/CD |

**Prioridad:** Must: EKS, Docker, Terraform, GitHub Actions, CloudWatch, MLflow, HPA. Should: Helm, ElastiCache. Won't: Multi-cloud, reentrenamiento automático.

**Brechas:** Presupuesto mensual AWS no estimado, latencia cómputo↔datos en arquitectura híbrida, viabilidad servidor local Colombia

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 34/100
 Ronda 1:           15/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Lista para diseño/estimación**
