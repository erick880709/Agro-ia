# RF-012: Motor Predictivo — Modelos de Inteligencia Artificial

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.9, 5.10; RFP-inicial.md — Sección 3 (Motor Predictivo)
**Prioridad:** Alta (Crítica — núcleo del negocio)

## Descripción
La plataforma debe ejecutar modelos de Inteligencia Artificial especializados en el dominio agronómico. Los modelos requeridos son:

1. **Clasificación del estado del suelo** — Entrada: variables de sensor (pH, NPK, humedad, CIC, materia orgánica). Salida: clasificación de aptitud según metodología UPRA (Alta / Media / Baja / No apta) para el cultivo evaluado.

2. **Predicción del cultivo ideal** — Entrada: variables de suelo, clima y geografía. Salida: top 5 cultivos recomendados con score y nivel de confianza.

3. **Detección de deficiencias nutricionales** — Entrada: datos de sensores. Salida: lista de nutrientes faltantes o en exceso, cantidad requerida para corregir y nivel de prioridad.

4. **Recomendación de fertilización** — Entrada: deficiencias detectadas, tipo de cultivo, fase del cultivo. Salida: tipo de fertilizante, cantidad (kg/ha), frecuencia de aplicación, costo estimado.

5. **Predicción de rendimiento** — Entrada: variables de suelo, clima, cultivo y manejo. Salida: toneladas por hectárea estimadas, intervalo de confianza, factores limitantes del rendimiento.

6. **Predicción de enfermedades y plagas** — Entrada: clima (humedad, temperatura), tipo de cultivo, historial de la finca. Salida: nivel de riesgo (bajo/medio/alto/crítico) y recomendaciones preventivas.

**Técnicas requeridas:** Random Forest, XGBoost y LSTM (para series temporales climáticas). Validación cruzada (cross-validation). Métricas: RMSE para regresión y F1-score para clasificación.

## Actores involucrados
- Investigador IES — entrena, valida y administra modelos
- Técnico Agrónomo — valida las predicciones contra conocimiento de campo
- Cliente — recibe los resultados como recomendaciones

## Criterios de aceptación
- Cada modelo expone una API REST para inferencia.
- Las predicciones incluyen nivel de confianza.
- Se monitorea drift del modelo en producción (degradación de métricas).
- Los modelos pueden reentrenarse sin interrumpir el servicio.
- No especificados en el RFP — definir: thresholds de aceptación para cada métrica (ej. F1 > 0.80), frecuencia de reentrenamiento, estrategia de validación con datos locales (piloto Quindío).

## Dependencias / relacionados
- RF-007: Captura de sensores IoT
- RF-008: Integración con APIs externas
- RF-009: Catálogo de cultivos
- RF-010: Motor de conocimiento agronómico
- RT-004: Stack Python para modelos de IA
- RT-010: MLOps
- RD-005: Mapa fuentes de datos → modelos

## Notas del analista
- El stack tecnológico para modelos de IA es **Python** (por definición del cliente), usando bibliotecas como scikit-learn, XGBoost y TensorFlow/PyTorch para LSTM.
- La estrategia cold-start propuesta en el Anexo de Datasets permite tener modelos funcionales desde el día 1 usando datasets públicos internacionales + reglas agronómicas oficiales colombianas, mientras se acumulan datos propios del piloto.
- Para el Modelo 1, se recomienda adoptar la clasificación UPRA (Alta/Media/Baja/No apta) en lugar de la escala propia (Excelente/Bueno/Regular/Malo/Crítico) mencionada en el RFP inicial, para dar respaldo institucional.
- El manejo de overfitting y drift del modelo es un requisito explícito del RFP — debe incluirse en el pipeline de MLOps desde el inicio.
