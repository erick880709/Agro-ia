---
id: TT-06
type: Tarea Técnica
epic: 001-motor-recomendaciones
priority: Media
points: 3
---

# TT-06: Configurar MLflow para tracking y registry de modelos

## Descripción
Desplegar y configurar MLflow Tracking Server + Model Registry para versionado de experimentos, métricas y artefactos de los 5 modelos de ML.

## Criterios de Done
- [ ] MLflow Tracking Server desplegado (contenedor en EKS o EC2)
- [ ] Backend store: PostgreSQL (misma instancia RDS, schema `mlflow`)
- [ ] Artifact store: S3 bucket `agroia-mlflow-artifacts`
- [ ] Registro de experimentos con: parámetros, métricas (F1, precisión, recall), artefactos (modelo serializado)
- [ ] Model Registry con stages: Staging → Production → Archived
- [ ] API REST para consultar versiones de modelos y métricas desde el backend

## Dependencias
TT-07 (modelo de datos para schema mlflow)
