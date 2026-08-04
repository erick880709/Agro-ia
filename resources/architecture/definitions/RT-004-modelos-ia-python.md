# RT-004: Stack de Modelos de IA — Python (scikit-learn, XGBoost, TensorFlow/PyTorch)

**Tipo:** Requisito técnico
**Categoría:** Stack tecnológico / Machine Learning
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.9, 7.2; instrucciones del cliente

## Descripción
Los modelos de Inteligencia Artificial del motor predictivo deben implementarse en Python, utilizando bibliotecas estándar de la industria para machine learning y deep learning:

- **Random Forest y XGBoost:** para modelos de clasificación (estado del suelo, cultivo ideal) y regresión (rendimiento, fertilización). Bibliotecas: `scikit-learn`, `xgboost`.
- **LSTM (Long Short-Term Memory):** para series temporales climáticas y predicción de enfermedades/plagas. Biblioteca: `TensorFlow` o `PyTorch`.
- **Validación y métricas:** validación cruzada (cross-validation) con `scikit-learn`, RMSE para regresión, F1-score para clasificación.
- **Manejo de overfitting:** regularización, early stopping, validación con datos locales del piloto.
- **Monitoreo de drift:** detección de degradación del modelo en producción (data drift, concept drift).

## Criterio medible / restricción concreta
- Modelos serializados en formato pickle, joblib o ONNX para despliegue.
- Cada modelo debe exponerse como un servicio REST (FastAPI) para inferencia.
- Los experimentos de entrenamiento deben registrarse con MLflow (o equivalente) para trazabilidad.
- No especificados en el RFP — definir: thresholds de métricas para aceptación de modelos, estrategia de feature engineering, manejo de datos faltantes en producción.

## Impacto en la arquitectura
- Servicio de inferencia independiente por modelo o grupo de modelos.
- MLflow Tracking Server para registro de experimentos y versionado de modelos.
- Model Registry para gestionar la promoción de modelos a producción (staging → production).
- Pipeline de datos para feature engineering previo a inferencia.

## Notas del analista
- La elección de Random Forest + XGBoost es adecuada para datos tabulares (sensores) con buena interpretabilidad. LSTM es adecuado para series temporales climáticas.
- Para el cold-start, se entrenarán modelos iniciales con datasets públicos (Kaggle Crop Recommendation) como baseline, que luego se refinarán con datos reales del piloto.
- Se recomienda MLflow por su integración nativa con el ecosistema Python y su capacidad de servir modelos como APIs REST, aunque el serving final se haga con FastAPI para mayor control.
