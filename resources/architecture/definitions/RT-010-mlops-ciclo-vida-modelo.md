# RT-010: MLOps — Ciclo de Vida del Modelo

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / Machine Learning
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 7.3

## Descripción
La plataforma debe implementar prácticas de MLOps para gestionar el ciclo de vida completo de los modelos de IA:

1. **Registro y versionado:** cada versión de modelo (entrenamiento) se almacena en un repositorio de modelos (MLflow Model Registry) junto con sus metadatos: hiperparámetros, métricas de evaluación, conjunto de datos usado, fecha de entrenamiento, autor.

2. **Despliegue:** los modelos aprobados se despliegan como servicios de inferencia empaquetados en contenedores Docker. El despliegue debe poder realizarse sin interrumpir el servicio (blue/green o canary deployment).

3. **Monitorización:** seguimiento continuo de métricas técnicas (latencia, throughput, uso de recursos) y métricas del modelo (precisión, F1-score, tasa de falsos positivos, data drift, concept drift). Alertas automáticas ante degradación.

4. **Reentrenamiento:** posibilidad de reentrenar modelos ante degradación de desempeño detectada. El pipeline de reentrenamiento debe estar parcialmente automatizado, con gate de aprobación manual en entornos productivos.

## Criterio medible / restricción concreta
- MLflow Tracking Server para registro de experimentos.
- MLflow Model Registry para versionado y stage de modelos (Staging → Production → Archived).
- Dashboard de monitoreo de modelos en Grafana (o herramienta equivalente).
- No especificados en el RFP — definir: ¿cada cuánto se evalúa el drift del modelo?, ¿umbral de degradación que dispara reentrenamiento?, ¿proceso de aprobación de modelos a producción?

## Impacto en la arquitectura
- MLflow requiere almacenamiento de objetos (S3) para artefactos de modelo y base de datos (PostgreSQL) para metadatos.
- El pipeline de MLOps debe integrarse con el CI/CD general (por ejemplo, GitHub Actions para gatillar reentrenamiento programado).
- Los experimentos de los investigadores de la IES deben poder registrarse y compararse en MLflow.

## Notas del analista
- MLflow es la herramienta más adoptada en el ecosistema Python para MLOps y tiene buena integración con FastAPI (serving de modelos).
- Para el MVP, el flujo de MLOps puede ser semi-manual: los investigadores entrenan modelos, registran en MLflow, y el despliegue se hace mediante CI/CD. La automatización completa del reentrenamiento puede venir en fases posteriores.
- Alternativas a considerar: DVC para versionado de datasets, Evidently AI para monitoreo de drift, BentoML para serving de modelos.
