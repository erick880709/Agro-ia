# RNF-006: Observabilidad

**Tipo:** Requerimiento no funcional
**Categoría:** Operaciones / Observabilidad
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 6.4

## Descripción
La plataforma debe contar con un sistema integral de observabilidad que permita monitorear su funcionamiento en producción. Esto incluye tres pilares:

**Logs centralizados:**
- Todos los servicios deben emitir logs estructurados (JSON) a un sistema centralizado.
- Los logs deben ser consultables y filtrables (por servicio, nivel, timestamp, trace ID).

**Métricas de rendimiento técnico:**
- Latencia de endpoints (p50, p95, p99).
- Throughput (solicitudes por segundo).
- Uso de recursos (CPU, memoria, disco, red) por servicio.
- Tasas de error (4xx, 5xx).

**Métricas del modelo de IA:**
- Precisión (accuracy, F1-score).
- Tasa de falsos positivos / falsos negativos.
- Detección de drift del modelo (degradación de métricas en el tiempo).
- Latencia de inferencia.

**Trazabilidad distribuida:**
- Cada solicitud debe tener un trace ID que permita seguir su recorrido a través de los microservicios.

## Criterio medible / restricción concreta
- Dashboards de monitoreo en tiempo real para el equipo de operaciones.
- Alertas automáticas ante condiciones anómalas (latencia elevada, tasa de error > umbral, drift de modelo).
- No especificados en el RFP — definir: stack concreto de observabilidad (Prometheus+Grafana, ELK, Datadog, CloudWatch), umbrales específicos de alerta.

## Impacto en la arquitectura
- Sidecar o agente de logging en cada pod de Kubernetes.
- Prometheus para recolección de métricas + Grafana para visualización.
- OpenTelemetry para trazabilidad distribuida.
- Sistema de alertas (AlertManager o equivalente).
- Panel específico para monitoreo de modelos ML (drift detection, data quality).

## Notas del analista
- La observabilidad de modelos de IA (ML monitoring) es un requisito diferenciador. No todos los proyectos lo consideran desde el inicio. Se recomienda implementarlo desde el MVP con herramientas como Evidently AI, Great Expectations o MLflow.
- Para el entorno AWS, CloudWatch + X-Ray pueden cubrir logs, métricas y trazabilidad de forma nativa, reduciendo la carga operativa inicial.
