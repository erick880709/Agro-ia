---
id: TT-04
type: Tarea Técnica
epic: 001-motor-recomendaciones
priority: Alta
points: 13
---

# TT-04: Entrenar y servir modelos ML (5 modelos + ensemble)

## Descripción
Implementar el pipeline de entrenamiento e inferencia para los 5 modelos de ML usando cold-start con datasets públicos (Kaggle), calibración progresiva con datos del piloto Quindío.

## Criterios de Done
- [ ] Modelo 1: Random Forest — Clasificación del estado del suelo (UPRA: Alta/Media/Baja/No apta), F1 > 0.80
- [ ] Modelo 2: XGBoost — Predicción del cultivo ideal (top 5 con score y confianza), F1 > 0.82
- [ ] Modelo 3: Random Forest — Detección de deficiencias nutricionales, F1 > 0.80
- [ ] Modelo 4: XGBoost + Reglas — Recomendación de fertilización (tipo, kg/ha, frecuencia, costo), F1 > 0.80
- [ ] Modelo 5: Random Forest + LSTM — Predicción de rendimiento (ton/ha, intervalo de confianza), F1 > 0.80
- [ ] Modelo Ensemble: combinación bayesiana de RF + XGBoost + LSTM
- [ ] API de inferencia gRPC (baja latencia) desde el ML Inference Service
- [ ] Modo sombra (semanas 5-8): modelos predicen en paralelo sin mostrar resultados al usuario
- [ ] Activación progresiva (semana 9+): solo modelos con F1 > 0.80 en validación cruzada con datos reales
- [ ] Modelos versionados en MLflow Model Registry

## Subtareas
- [ ] Preparar datasets Kaggle + datos piloto Quindío (limpieza, feature engineering, normalización)
- [ ] Entrenar modelo 1 (Random Forest — clasificación UPRA) con validación cruzada k=5
- [ ] Entrenar modelo 2 (XGBoost — cultivo ideal top 5) con optimización de hiperparámetros
- [ ] Entrenar modelo 3 (Random Forest — deficiencias nutricionales)
- [ ] Implementar modo sombra para calibración con datos reales del piloto

## Dependencias
TT-01
