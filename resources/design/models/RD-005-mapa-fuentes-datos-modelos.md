# RD-005: Mapa Fuentes de Datos → Modelos de IA

**Tipo:** Información de diseño
**Fuente:** Anexo-Datasets-Fuentes-Datos.md — Sección 8

## Descripción
Cada uno de los 6 modelos de IA del motor predictivo tiene fuentes de datos recomendadas, tanto para el cold-start como para la operación con datos propios:

| Modelo | Fuente principal (operación) | Fuente cold-start / respaldo |
|---|---|---|
| **1. Clasificación del estado del suelo** | Metodología UPRA (Alta/Media/Baja/No apta) + sensores IoT propios | SoilGrids (ISRIC) para zonas sin dato propio |
| **2. Predicción del cultivo ideal** | FAO/IIASA GAEZ v4/v5 + zonificaciones UPRA por cultivo | Kaggle Crop Recommendation Dataset (ajustado a condiciones colombianas) |
| **3. Detección de deficiencias nutricionales** | Sensores IoT propios + AGROSAVIA (análisis de laboratorio de suelos) | Cenicafé (umbrales para café) |
| **4. Recomendación de fertilización** | Cenicafé (tablas de fertilización N-P-K para café) + DANE-SIPSA (costos de insumos) | — (no aplica sin datos locales) |
| **5. Predicción de rendimiento** | DANE-EVA (históricos de rendimiento por municipio/cultivo) | FAO GAEZ (rendimiento potencial por zona agroecológica) |
| **6. Predicción de enfermedades/plagas** | Datos propios del piloto (clima + incidencia) + literatura Cenicafé sobre roya | PlantVillage (transfer learning para visión artificial) |
| **Agente conversacional (RAG)** | Biblioteca Cenicafé + manuales AGROSAVIA + guías UPRA | — |

## Elementos de referencia
- Este mapa debe guiar la implementación de los conectores de datos externos (RF-008).
- Cada fuente tiene una sección dedicada en el Anexo de Datasets con detalles de acceso (API, portal, formato, licencia).
- Se recomienda crear un diagrama visual (tipo flow diagram) que muestre el pipeline: fuente → conector → preprocesamiento → feature store → modelo → inferencia.

## Notas del analista
- Las fuentes marcadas como "cold-start" no deben usarse para recomendaciones directas al agricultor sin validación local. Son solo para inicializar los modelos.
- Algunas fuentes como Cenicafé (licencia CC BY-NC-ND) requieren validación legal para uso comercial en la plataforma. Ver Sección 9 del Anexo de Datasets.
- La combinación de múltiples fuentes para un mismo modelo (ej. Modelo 2 usa GAEZ + UPRA + Kaggle) requiere un proceso de fusión/ensamblaje que debe diseñarse cuidadosamente para no introducir sesgos.
