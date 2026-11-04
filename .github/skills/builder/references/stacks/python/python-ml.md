# Machine Learning en Python

Guía para cambios que tocan componentes de ML. Builder implementa y valida; no
rediseña la arquitectura ML (eso es `archi`). Aplica a modelos, pipelines,
entrenamiento, evaluación, serving y monitoring.

## Ciclo de vida (qué tocar según el cambio)

| Cambio | Foco |
|---|---|
| Añadir/ajustar un modelo | Datos, entrenamiento, validación, métricas |
| Exponer un modelo | Serving, contratos, latencia, versionado |
| Mantener un pipeline | Reproducibilidad, drift, retraining |
| Corregir un bug de ML | Diagnóstico, causa raíz, prueba de regresión |

## Herramientas por capa

- **Datos/features:** `pandas`, `polars`, `numpy`; feature stores si el proyecto los usa.
- **Modelos:** `scikit-learn` (tablas), `lightgbm`/`xgboost` (gradient boosting),
  `pytorch` (deep learning).
- **Validación:** `scikit-learn` (cross-validation, métricas), `statsmodels`/`scipy`.
- **HPO:** `optuna` (o grid/random search si es lo que el proyecto usa).
- **Tracking/versionado:** `mlflow`, `dvc` (si ya están en el repo).
- **Serving:** `bentoML`, FastAPI, `onnxruntime`; respeta lo que el proyecto ya usa.

## Guardrails de ML (de `ml4t/skills` y `ml-engineer`)

Detecta y evita estos fallos antes de dar el cambio por cerrado:

1. **Data leakage:** el preprocesado (escalado, imputación, codificación) se
   ajusta SOLO con el split de entrenamiento. Ajustar con todo el dataset es un bug.
2. **Lookahead:** ninguna feature usa información del futuro (en series temporales,
   nunca uses `shift(-1)` ni joins con datos posteriores).
3. **Overfit de backtest/evaluación:** no elijas el "mejor" resultado histórico sin
   corrección por múltiples hipótesis; reporta validación fuera de muestra.
4. **Cross-validation correcta:** en series temporales, split cronológico
   (`TimeSeriesSplit`), nunca `KFold` aleatorio; en grupos, `GroupKFold`.
5. **Métricas por clase/sesgo:** en desbalanceo, reporta precisión/recall/F1 por
   clase o métricas como ROC-AUC/PR-AUC, no solo accuracy.
6. **Reproducibilidad:** semillas fijas y registradas; versiona datos, código y
   modelo (dvc/mlflow si el proyecto lo usa).
7. **Drift:** en sistemas en producción, el monitoring de drift es un requisito
   implícito; no lo implementes de oficio salvo que el encargo lo pida.

## Patrón de validación de un cambio de ML

1. Reproduce el estado previo (métrica de referencia) antes de tocar nada.
2. Haz el cambio mínimo (feature, hiperparámetro, pipeline).
3. Re-evalúa con el MISMO split y la MISMA semilla.
4. Compara con la referencia y registra la evidencia (métrica, dataset, comando).

Nunca declares mejora sin comparar contra la métrica de referencia en el mismo
split. Un cambio que solo mejora el split de entrenamiento no es una mejora.

## Anti-patrones

- `dropna()` global o imputación con estadísticas del dataset completo antes del split.
- `pd.get_dummies` sobre todo el dataset antes de separar train/test.
- Seleccionar features con la variable objetivo incluida.
- `random_state` sin fijar en entrenamiento y split.
