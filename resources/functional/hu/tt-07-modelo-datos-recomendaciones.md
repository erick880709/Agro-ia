---
id: TT-07
type: Tarea Técnica
epic: 001-motor-recomendaciones
priority: Alta
points: 5
---

# TT-07: Crear modelo de datos para recomendaciones

## Descripción
Diseñar e implementar el esquema PostgreSQL para las tablas relacionadas con el motor de recomendaciones: recomendaciones, análisis de suelo, discordancias, reglas agronómicas, modelos ML y métricas.

## Criterios de Done
- [ ] Migraciones SQLAlchemy/Alembic para todas las tablas nuevas
- [ ] Tablas con RLS: `tenant_id` en cada tabla que contiene datos de cliente
- [ ] `recomendaciones`: una por análisis solicitado, con clasificación UPRA, confianza, justificación, estado
- [ ] `discordancias`: casos de conflicto ML vs reglas, con SLA y trazabilidad
- [ ] `reglas_agronomicas`: reglas del sistema experto con versionado
- [ ] `modelos_ml`: registro de modelos entrenados (nombre, tipo, versión, F1, fecha)
- [ ] `metricas_modelo`: evolución de métricas por modelo (drift monitoring)
- [ ] Índices para queries frecuentes: `finca_id`, `cultivo_id`, `estado`, `created_at`
- [ ] PostGIS: columna `ubicacion` en `fincas` para consultas geoespaciales

## Recurso de datos involucrado
### Recursos creados en esta tarea
- **Recomendacion** (ver HU-01)
- **Discordancia** (ver HU-03)
- **ReglaAgronomica** (ver HU-05)
- **ModeloML**: id, nombre, tipo_modelo, version, f1_score, mlflow_run_id, stage, activo, created_at
- **MetricaModelo**: id, modelo_ml_id, metrica, valor, fecha_registro
