---
id: HU-04
type: Historia de Usuario
epic: 001-motor-recomendaciones
priority: Alta
points: 8
---

# HU-04: Administrar modelos de Machine Learning

## Como
Investigador IES

## Quiero
Entrenar, versionar y monitorear los 5 modelos de ML del motor de recomendaciones

## Para
Mantener y mejorar la precisión de las predicciones agronómicas

## Criterios de Aceptación
- [ ] CA1: Puede subir datasets de entrenamiento (CSV/Parquet) y asociarlos a un modelo
- [ ] CA2: Puede ejecutar entrenamiento con parámetros configurables (hiperparámetros, split ratio, validación cruzada)
- [ ] CA3: Ve métricas por modelo: F1-score, precisión, recall, matriz de confusión
- [ ] CA4: Los modelos se versionan automáticamente en MLflow (Staging → Production → Archived)
- [ ] CA5: Puede activar/desactivar un modelo en producción sin afectar el servicio (A/B o shadow mode)

## Subtareas
- [ ] Construir UI de administración de modelos (lista, detalle, métricas)
- [ ] Integrar MLflow API para consulta de experimentos y modelos
- [ ] Implementar pipeline de entrenamiento con parámetros configurables
