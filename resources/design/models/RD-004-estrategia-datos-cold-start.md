# RD-004: Estrategia de Datos Cold-Start (3 Fases)

**Tipo:** Información de diseño
**Fuente:** Anexo-Datasets-Fuentes-Datos.md — Secciones 1, 2, 3, 8

## Descripción
La plataforma enfrenta el desafío del "cold start": ¿cómo entrenar modelos de IA sin tener datos históricos propios del piloto? La estrategia definida en el Anexo de Datasets propone 3 fases progresivas:

### Fase 1: Día 1 (sin datos propios)
- **Sistema experto:** reglas agronómicas de fuentes oficiales colombianas (Cenicafé para café, UPRA para clasificación de tierras).
- **Modelos ML base:** entrenados con datasets públicos internacionales:
  - Kaggle Crop Recommendation Dataset (2,200 registros, 22 cultivos).
  - Crops NPK Dataset (20,000 registros).
  - SoilGrids (ISRIC) para datos de suelo globales.
- **Uso:** solo como baseline interno. Las recomendaciones al agricultor se basan principalmente en reglas, no en estos modelos.

### Fase 2: Meses 1–6 (piloto de campo Quindío)
- **Datos propios:** sensores IoT instalados en fincas del piloto + datos climáticos IDEAM + datos edafológicos IGAC.
- **Calibración local:** reentrenamiento de modelos con datos reales colombianos del Quindío.
- **Validación:** comparación de recomendaciones del sistema contra criterio de ingenieros agrónomos del Comité de Cafeteros y Cenicafé.
- **Objetivo:** modelos calibrados para café en el Eje Cafetero.

### Fase 3: Meses 6+ (operación)
- **Datos acumulados de la plataforma:** multi-tenant, multi-cultivo, multi-región.
- **Reentrenamiento periódico (MLOps):** gatillado por degradación de métricas o incorporación de nuevos datos.
- **Expansión:** nuevos cultivos (más allá de café), nuevas regiones de Colombia, incorporación de datos de nuevos sensores.

## Elementos de referencia
- Ver mapa detallado fuente de datos → modelo de IA en el Anexo de Datasets (Sección 8) y en RD-005.
- Las fuentes de datos abiertos del Estado colombiano (AGROSAVIA, IDEAM, IGAC, DANE, UPRA) están identificadas con URLs y métodos de acceso.

## Notas del analista
- Esta estrategia evita dos errores comunes: (a) esperar a tener "suficientes datos propios" para lanzar (puede tardar años), y (b) confiar ciegamente en datos internacionales sin validación local.
- Los datasets de Kaggle (India) tienen diferencias importantes con la agronomía colombiana (unidades de fertilización, tipos de suelo, clima tropical de altura). Por eso se usan solo como base metodológica, no como fuente de recomendaciones directas.
- Para el piloto, se recomienda priorizar la calibración de los modelos 1 (clasificación de suelo) y 2 (cultivo ideal), ya que son los que generan recomendaciones visibles al agricultor.
