# Anexo — Fuentes de Datos y Datasets para Entrenamiento de Modelos
## AgroInteligente Colombia (AgroIA)

**Versión:** 1.0 — Complementa el RFP principal
**Fecha:** Agosto 2026

---

## 1. Resumen estratégico

Este anexo responde directamente a dos de las ambigüedades críticas identificadas en el RFP:

1. **"Cold start" del dataset de IA** — con qué datos se entrena el modelo antes de tener histórico propio del piloto.
2. **Umbrales agronómicos concretos por cultivo** — de dónde sale la ficha técnica de cada cultivo.

**Estrategia recomendada (resumen):**

| Fase | Fuente de datos | Qué habilita |
|---|---|---|
| **Día 1 (sin datos propios)** | Datasets públicos de Kaggle/UCI + reglas agronómicas de fuentes oficiales (UPRA, Cenicafé, FAO GAEZ) | Sistema experto basado en reglas + un modelo de ML pre-entrenado con datos globales, para no lanzar "en blanco" |
| **Meses 1–6 (piloto de campo)** | Sensores IoT propios + AGROSAVIA + IDEAM + IGAC, específicos del Quindío/café | Calibración local del modelo, validación de las reglas genéricas contra la realidad del Eje Cafetero |
| **Meses 6+ (operación)** | Datos propios acumulados de la plataforma (multi-tenant, multi-cultivo) | Reentrenamiento periódico (MLOps), mejora continua, expansión a nuevos cultivos y regiones |

Este enfoque evita dos errores comunes: (a) esperar a tener "suficientes datos propios" para lanzar el MVP (puede tardar años), y (b) confiar ciegamente en datasets internacionales sin validarlos contra la agronomía colombiana.

---

## 2. Datasets públicos internacionales listos para entrenamiento (ML)

Útiles para el **Modelo 2 (predicción de cultivo ideal)** y el **Modelo 3 (detección de deficiencias nutricionales)** en su versión inicial (cold start).

| Dataset | Contenido | Fuente | Limitación a considerar |
|---|---|---|---|
| **Crop Recommendation Dataset** | 2,200 registros: N, P, K, temperatura, humedad, pH, lluvia → 22 cultivos | Kaggle (atharvaingle/crop-recommendation-dataset) | Datos de India — climas y unidades de fertilización distintas a Colombia; usar solo como *base metodológica* y reentrenar con datos propios |
| **Crops NPK Dataset** | 20,000 registros: N, P, K, temperatura, humedad, pH, lluvia, tipo de suelo, variedad | Kaggle (javakhan/crops-npk-data-set) | Mismo origen geográfico que el anterior; complementa el tamaño muestral |
| **PlantVillage Dataset** | +50,000 imágenes de hojas sanas y enfermas, 38 clases de cultivo-enfermedad | Dataset académico abierto (ampliamente usado en investigación) | No incluye specíficamente café; para café hay que complementar con datasets propios/literatura (ver sección 5) |

**Uso recomendado:** entrenar una primera versión del Modelo 2 (clasificación/recomendación de cultivo) y validarla contra las reglas agronómicas oficiales colombianas antes de exponerla a usuarios reales. Nunca usar estos datasets como única fuente de verdad para recomendaciones que se muestren al agricultor.

---

## 3. Fuentes oficiales colombianas (datos reales del país)

### 3.1 AGROSAVIA — Datos abiertos de suelos

- **Resultados de Análisis de Laboratorio de Suelos en Colombia**: dataset público con resultados reales del Laboratorio de Química y Física de Suelos de AGROSAVIA (fertilidad, salinidad, nutrientes). Disponible en datos.gov.co.
- **IRAKA** (proyecto AGROSAVIA): mapas de 12 propiedades de suelo para el Altiplano Cundiboyacense, con metodología de mapeo digital de suelos + machine learning, georreferenciados y descargables gratuitamente por municipio.
- AGROSAVIA también ha explorado clasificación no supervisada de suelos agrícolas a partir de imágenes satelitales multiespectrales — antecedente directo y aprovechable para el enfoque de AgroIA.
- Relevante: ya existen iniciativas similares en el ecosistema de datos abiertos colombiano — **Xerelia** (asistente IA para café, cacao y palma basado en fuentes verificadas) y **SueloGuIA** (plataforma de calidad de datos de suelo + agente conversacional para AGROSAVIA) — vale la pena revisarlas como referencia de producto y, potencialmente, como aliados o fuentes de datos.

**Portal:** datos.gov.co (buscar "AGROSAVIA suelos") · agrosavia.co/datos-abiertos

### 3.2 IDEAM — Datos climáticos (con API)

- Catálogo Nacional de Estaciones y **Datos Hidrometeorológicos Crudos** (temperatura, precipitación, humedad, viento) por estación, disponibles en datos.gov.co bajo el formato **Socrata Open Data API (SODA)**.
- IDEAM publicó un **manual oficial para consumir sus datos vía API** (Python + librería `sodapy`), con ejemplos de notebook.
- Portal complementario: **DHIME** (dhime.ideam.gov.co) para consulta y descarga de series temporales hidrometeorológicas oficiales bajo demanda.
- Pronósticos del tiempo y alertas también están disponibles como datos abiertos (pronosticosyalertas.gov.co).

**Acción concreta:** identificar el `dataset ID` (ej. el manual usa el ejemplo `uext-mhny`) de las estaciones más cercanas al Quindío y construir el conector de ingesta vía SODA API desde el arranque del proyecto.

### 3.3 IGAC — Datos edafológicos y geoespaciales

- **Datos Abiertos de Agrología**: Levantamientos Generales de Suelos por departamento (génesis, características físico-químicas, taxonomía) y **Clasificación por Capacidad de Uso de las Tierras**, en formato shapefile, licencia CC-BY-SA 4.0, un conjunto de datos por cada uno de los 32 departamentos.
- Escalas disponibles: 1:100.000 (agrología nacional) y hasta 1:10.000/1:25.000 para zonas específicas vía Colombia en Mapas.
- **Geoportal IGAC**: visor interactivo y descarga directa (geoportal.igac.gov.co).

### 3.4 UPRA — Zonificación de aptitud de tierras (⭐ resuelve la ambigüedad de umbrales)

Este es el hallazgo más relevante para el **Modelo 1 (clasificación del estado del suelo)**: la UPRA (Unidad de Planificación Rural Agropecuaria) ya tiene una **metodología oficial colombiana de evaluación de tierras** que clasifica la aptitud en **Alta / Media / Baja / No apta**, combinando componentes biofísicos (suelo, clima, terreno) y socioeconómicos, a escala 1:100.000 a nivel nacional.

- Zonificaciones ya publicadas y descargables para múltiples cultivos (café incluido en el histórico de zonificaciones UPRA, además de fríjol, yuca, plátano, plantaciones forestales, etc.), vía **SIPRA** (sipra.upra.gov.co) y servicios geográficos (geoservicios.upra.gov.co, formato ArcGIS REST/MapServer).
- **Recomendación directa:** usar la metodología y las categorías de aptitud de la UPRA como el estándar de clasificación del Modelo 1, en lugar de inventar una escala propia (Excelente/Bueno/Regular/Malo/Crítico). Esto además da credibilidad institucional al proyecto frente a MinCiencias y al Comité de Cafeteros.

### 3.5 DANE — Precios y rendimientos (variables económicas del RFP)

- **SIPSA** (Sistema de Información de Precios y Abastecimiento del Sector Agropecuario): precios mayoristas, minoristas e insumos agrícolas (fertilizantes, plaguicidas) por departamento, con series históricas y servicio web de consulta.
- **EVA — Evaluaciones Agropecuarias Municipales**: área sembrada, área cosechada, producción y rendimiento por cultivo y municipio — exactamente el dato de "producción esperada" y "rendimiento histórico" que pide la ficha técnica de cultivos del RFP.
- **Índice de precios de agroinsumos (UPRA + DANE)**: ponderado con Laspeyres, útil para el módulo de rentabilidad estimada.

---

## 4. Fuente agronómica específica para café — Cenicafé

Dado que el piloto se centra en café en el Quindío, **Cenicafé** (Centro Nacional de Investigaciones de Café) es la fuente primaria de verdad agronómica:

- **Biblioteca digital abierta** (biblioteca.cenicafe.org): acceso sin registro a guías técnicas completas, entre ellas *"Fertilidad del suelo y nutrición del café en Colombia: Guía práctica"* y el capítulo *"Nutrición de cafetales"* del Manual Anual del Cafetero Colombiano — con tablas de recomendación de fertilización nitrogenada y fosfórica según niveles de materia orgánica del suelo.
- Umbrales ya confirmados en la propuesta MinCiencias adjunta: pH ideal 5.5–6.5, humedad de suelo óptima 60–80% de capacidad de campo, temperatura ideal 18–24°C (Arcila et al., 2007; Wintgens, 2009).
- **Avances Técnicos Cenicafé** y **Memorias del Seminario Científico Cenicafé**: publicaciones periódicas con recomendaciones actualizadas de fertilización, sirven para mantener el RAG actualizado sin reentrenar modelos.

**Acción concreta:** descargar y procesar la biblioteca de Cenicafé (documentos con licencia CC BY-NC-ND, de libre consulta) como corpus base del sistema RAG del agente conversacional para el cultivo de café, y como fuente de las reglas del sistema experto.

---

## 5. Datos satelitales y de teledetección (NDVI, imágenes)

| Fuente | Qué ofrece | Acceso |
|---|---|---|
| **Copernicus / Sentinel-2** | Imágenes multiespectrales gratuitas, 10m de resolución, revisita cada 5 días — base del índice NDVI | Copernicus Browser / Copernicus Data Space Ecosystem (gratuito, requiere cuenta) |
| **Sentinel Hub / EO Browser** | Visualización y descarga con cálculo de índices al vuelo (NDVI, humedad, estrés hídrico) | sentinel-hub.com, gratuito para uso básico |
| **Google Earth Engine** | Plataforma más potente para análisis a gran escala; permite programar consultas sobre todo el histórico satelital (desde 1984) vía JavaScript/Python | Gratuito con cuenta registrada — recomendado para el pipeline de procesamiento NDVI en producción |
| **Landsat 8/9 (NASA/USGS)** | Alternativa gratuita a Sentinel-2, resolución algo menor | earthexplorer.usgs.gov |

**Nota de arquitectura:** para producción, Google Earth Engine (o su API) es la opción más escalable para automatizar el cálculo periódico de NDVI por finca sin descargar/procesar imágenes manualmente.

---

## 6. Datos globales de suelo y aptitud de cultivos (para cultivos sin ficha nacional)

Para cultivos que aún no tengan una ficha técnica oficial colombiana (fuera de café), estas fuentes globales permiten poblar el catálogo de cultivos sin esperar investigación propia:

- **SoilGrids (ISRIC)**: mapas globales gratuitos de 250m de resolución con pH, materia orgánica, densidad, textura, CIC, nitrógeno total, en 6 profundidades estándar — API REST pública (`rest.isric.org/soilgrids/v2.0`) y librería Python/R disponibles. Útil como respaldo cuando no hay dato de sensor o de laboratorio disponible para una finca.
- **FAO/IIASA GAEZ (Global Agro-Ecological Zones), v4/v5**: base de datos mundial de **aptitud de tierras y rendimiento potencial para 51–53 cultivos**, bajo condiciones de secano y riego, con distintos niveles de manejo (alto/bajo insumo). Es prácticamente un "Modelo 2" ya construido a nivel mundial por FAO — se puede usar como *baseline* o para validar cruzadamente las predicciones propias del sistema.
- **NASA POWER API**: datos meteorológicos y agroclimáticos globales gratuitos (radiación solar, temperatura, precipitación), diseñados específicamente para alimentar modelos de cultivos ("Agroclimatology Archive") — buena alternativa/complemento a IDEAM para variables climáticas donde no haya estación cercana.

---

## 7. Visión artificial para detección de plagas/enfermedades (funcionalidad futura)

Relevante para la funcionalidad futura "detección de plagas mediante visión artificial" del RFP, y en particular para el riesgo de roya del café (Hemileia vastatrix), identificado como uno de los tres factores de mayor correlación con pérdidas productivas en el Eje Cafetero:

- Existen estudios académicos ya publicados con datasets propios (imágenes de hojas de café sanas vs. con roya, minador de la hoja, phoma, Cercospora) y comparativas de modelos (ResNet18+SVM, Random Forest, XGBoost) con precisiones reportadas entre 83% y >90% según el estudio.
- El dataset **PlantVillage** es el estándar de referencia en la literatura para enfermedades foliares en general (no específico de café), útil para pre-entrenar el extractor de características (transfer learning) antes de afinar con imágenes reales de café.
- **Recomendación:** para esta funcionalidad (fuera del MVP), planear una campaña propia de captura de imágenes durante el piloto de campo, ya que no existe un dataset público robusto específico para roya del café en el contexto colombiano.

---

## 8. Mapa: fuente de datos → modelo de IA del RFP

| Modelo (RFP, sección 5.9) | Fuente de datos principal recomendada | Fuente de respaldo/cold start |
|---|---|---|
| 1. Clasificación del estado del suelo | Metodología UPRA (Alta/Media/Baja/No apta) + sensores propios | SoilGrids (ISRIC) para zonas sin dato propio |
| 2. Predicción del cultivo ideal | FAO/IIASA GAEZ + UPRA (zonificaciones por cultivo) | Kaggle Crop Recommendation Dataset (ajustado) |
| 3. Detección de deficiencias nutricionales | Sensores IoT propios + AGROSAVIA (análisis de laboratorio) | Cenicafé (umbrales café) |
| 4. Recomendación de fertilización | Cenicafé (tablas de fertilización N-P-K) + SIPSA (costos de insumos) | — |
| 5. Predicción de rendimiento | DANE-EVA (históricos de rendimiento por municipio/cultivo) | FAO GAEZ (rendimiento potencial) |
| 6. Predicción de enfermedades/plagas | Datos propios del piloto (clima + incidencia) + literatura Cenicafé/roya | PlantVillage (transfer learning, visión artificial) |
| Agente conversacional (RAG) | Biblioteca Cenicafé + manuales AGROSAVIA | — |

---

## 9. Consideraciones legales y de licenciamiento

- Los datos de **AGROSAVIA, IDEAM, IGAC, DANE y UPRA** son datos abiertos del Estado colombiano — de uso libre, aunque conviene revisar la licencia específica de cada dataset en datos.gov.co (la mayoría bajo licencias abiertas tipo CC).
- Los datos de **IGAC** (agrología) están explícitamente bajo licencia **CC-BY-SA 4.0** — requiere atribución y compartir bajo la misma licencia si se redistribuyen derivados.
- La biblioteca de **Cenicafé** está bajo licencia **CC BY-NC-ND** (no comercial, sin obras derivadas) — apta para alimentar el RAG interno del agente (uso no comercial de consulta), pero **debe validarse con Cenicafé/FNC** el uso si la plataforma se comercializa, dado que el proyecto sí contempla venta por membresías.
- Los datasets de **Kaggle** (Crop Recommendation, Crops NPK) tienen licencias variables por dataset — verificar cada uno antes de su uso en un producto comercial.
- **SoilGrids** es CC-BY 4.0 (requiere atribución, uso comercial permitido).
- **Copernicus/Sentinel** y **NASA POWER** son de uso abierto y gratuito, incluido uso comercial, con atribución.

---

## 10. Próximos pasos sugeridos

1. Registrar cuentas de desarrollador en: IDEAM (Socrata/datos.gov.co), Copernicus Data Space Ecosystem, Google Earth Engine, NASA POWER.
2. Descargar y estructurar el dataset de AGROSAVIA (análisis de suelos) e IRAKA como primer dataset real colombiano para calibrar el Modelo 1.
3. Contactar formalmente a Cenicafé/FNC para validar el uso de su biblioteca técnica en el RAG y aclarar condiciones de uso comercial (relevante dado el modelo de membresías).
4. Adoptar oficialmente la metodología y clases de aptitud de la **UPRA** como estándar del Modelo 1, en vez de definir una escala propia sin respaldo institucional.
5. Descargar la capa de café de **GAEZ v4/v5** y las zonificaciones de café de UPRA como *ground truth* inicial del Modelo 2, antes de tener datos propios suficientes del piloto.
6. Evaluar acuerdo/convenio con AGROSAVIA (SueloGuIA/Xerelia) — ya existen iniciativas afines dentro del mismo ecosistema de datos abiertos que podrían ser aliados en lugar de competencia directa.
