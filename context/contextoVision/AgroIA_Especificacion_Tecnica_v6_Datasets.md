# AgroIA — Especificación Técnica v6
### Fuentes de datasets para reentrenamiento: modelo tabular y AgroVision (diagnóstico por foto)
**Fecha:** 2026-08-28 · **Basado en:** Documento Funcional-Técnico v2.14 (secciones 6.22, 10, 11.12) · **Autor:** Revisión agronómica + arquitectura senior

---

## 0. Principio rector (se mantiene igual que en v5)

Todo lo de este documento es **carga de datos para entrenamiento**, no cambio de contrato de API. Ningún dataset nuevo modifica el comportamiento ya validado de `POST /api/v1/vision/analizar-plaga` ni de `POST /recomendaciones/analyze`: mientras no haya modelo propio entrenado para un cultivo, el motor **AgroVision sigue respondiendo con el fallback OpenCV/numpy y abstención explicada** (comportamiento actual), y el sistema experto de reglas sigue siendo la fuente de verdad tabular. Entrenar un modelo nuevo solo **sube el techo de precisión** cuando hay modelo disponible — nunca resta la capacidad de generar diagnóstico y reporte con lo que ya existe.

---

## 1. Reentrenamiento del modelo tabular (sistema experto ↔ ML sombra) — enlaces directos

*(Resumen ejecutivo de lo ya especificado en la v5, con los enlaces de descarga directa consolidados en un solo lugar para el equipo de datos.)*

| Fuente | Qué aporta | Enlace de descarga/consulta directa |
|---|---|---|
| **FAOSTAT** (producción/rendimiento por cultivo y país) | Valida `rendimiento_esperado` (anti-outliers) | Descarga masiva CSV por dominio: `https://www.fao.org/faostat/en/#data/QCL` (botón "Bulk Downloads" → `Production_Crops_Livestock_E_All_Data.zip`) · API: `https://fenixservices.fao.org/faostat/api/v1/es/data/QCL?area=Colombia&item={cultivo}` |
| **datos.gov.co — EVA (UPRA/MinAgricultura)** | Área, producción y rendimiento por municipio/cultivo en Colombia | Portal de búsqueda: `https://www.datos.gov.co/browse?q=evaluaciones+agropecuarias+municipales` → cada dataset trae su botón "Descargar" (CSV/JSON directo) y su endpoint Socrata `https://www.datos.gov.co/resource/{id}.json` (el `{id}` cambia con cada actualización de UPRA — confirmarlo en el portal al momento de integrar, no hardcodear) |
| **ISRIC SoilGrids v2.0** | pH, CIC, carbono orgánico, textura de referencia por coordenada (250 m) | API punto: `https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lng}&lat={lat}&property=phh2o&property=cec&property=soc&property=clay&property=sand&property=silt` · mapas completos (WCS/descarga masiva): `https://files.isric.org/soilgrids/latest/data/` — **nota:** servicio en beta, ISRIC ha reportado cortes; usar como referencia de calibración, no como dependencia en tiempo real de producción |
| **Agrosavia / Fedepanela / ICA** | Fichas técnicas por cultivo (rangos agronómicos a curar manualmente) | `https://www.agrosavia.co/` · `https://fedepanela.org.co/gremio/` · `https://www.ica.gov.co/` — documentos, no API; se transcriben a `RANGOS[cultivo]` en `train_colombia.py` |

---

## 2. Reentrenamiento de AgroVision (diagnóstico por foto) — el foco de este documento

### 2.1 Contexto técnico confirmado en el sistema actual

El pipeline `datasets/` ya existe con el flujo `discover → download → inspect → dedup → normalize → convert_annotations → split → train → evaluate → package_model`, un manifest `DS01–DS22` (hoy sin fuentes reales asignadas, según lo que se pudo verificar), `class_map.yaml` y `license_policy.yaml` con un **gate de uso comercial** — es decir, el sistema ya está preparado para rechazar datasets con licencia incompatible con uso comercial. Esto es correcto y hay que respetarlo: cada fuente de la tabla siguiente incluye su licencia real para que pase ese gate sin sorpresas.

### 2.2 Datasets públicos reales, con enlace de descarga directa, mapeados a DS01–DS22

| ID sugerido | Cultivo(s) | Dataset | Contenido | Licencia | Enlace de descarga directa |
|---|---|---|---|---|---|
| **DS01** | Multi-cultivo (14 especies: tomate, papa, maíz, uva, manzana, etc.) | **PlantVillage** | ~54.305 imágenes de hoja sana/enferma, 38 clases, condiciones de laboratorio | Dominio abierto (la mayoría de las réplicas están bajo CC0/uso libre — verificar la licencia exacta de la copia específica al descargar) | `https://www.kaggle.com/datasets/emmarex/plantdisease` · mirror académico original: `https://github.com/spMohanty/PlantVillage-Dataset` |
| **DS02** | Multi-cultivo, campo real (13 especies) | **PlantDoc** | 2.598 imágenes tomadas en campo real (no laboratorio) — más representativo de fotos de agricultores que PlantVillage | CC BY 4.0 | `https://github.com/pratikkayal/PlantDoc-Dataset` |
| **DS03** | Café (Robusta) — roya y ácaro | **RoCoLe** | 1.560 imágenes, severidad de roya en 4 niveles + presencia de ácaro rojo, con máscaras de segmentación | CC BY 4.0 (Mendeley Data) | `https://data.mendeley.com/datasets/c5yvn32dzg/2` (DOI: `10.17632/c5yvn32dzg.2`) |
| **DS04** | Café (Arábica) — roya, minador, mancha parda, cercospora | **BRACOL** | 1.747 imágenes de hoja completa + 2.147 recortes de síntoma aislado, con severidad cuantificada | CC BY 4.0 (Mendeley Data) | `https://data.mendeley.com/datasets/yy2k5y8mxg/1` (DOI: `10.17632/yy2k5y8mxg.1`) |
| **DS05** | Café — segmentación de árbol completo (complementario a DS04) | **BRACOT** | 300 imágenes de árboles de café con instancias segmentadas de hojas sanas/enfermas | CC BY 4.0 (Mendeley Data) | `https://data.mendeley.com/datasets/pmkbyjpf6k/1` |
| **DS06** | Yuca | **Cassava Leaf Disease Classification** (Makerere AI Lab / Kaggle) | ~21.000 imágenes de campo real, 5 clases (incluye Mosaico, Rayado Marrón, Bacteriosis) | Verificar términos específicos de la competencia Kaggle antes de uso comercial — algunas ediciones tienen licencia restringida a fines no comerciales/de investigación | `https://www.kaggle.com/competitions/cassava-leaf-disease-classification/data` |
| **DS07** | Arroz | **Rice Leaf Diseases Dataset** | Imágenes de campo, clases de tizón/mancha parda/otras (volumen variable según versión) | Verificar licencia específica en la página del dataset | `https://www.kaggle.com/datasets/vbookshelf/rice-leaf-diseases` |
| **DS08** | Multi-cultivo, versión aumentada de PlantVillage | **New Plant Diseases Dataset (Augmented)** | Versión con aumentación de datos de PlantVillage, útil para ampliar volumen de entrenamiento de los cultivos que ya cubre DS01 | Igual base que PlantVillage — verificar licencia de la réplica | `https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset` |

### 2.3 Gap real y honesto: cultivos sin dataset público maduro

**Cacao y Aguacate — los dos cultivos de mayor relevancia exportadora para Colombia dentro del catálogo — no tienen un dataset público de imágenes de enfermedades tan maduro y curado como el de café.** Existen datasets sueltos de menor calidad/tamaño en repositorios como Kaggle o Roboflow Universe para ambos, pero ninguno con el nivel de curaduría científica de RoCoLe/BRACOL — cualquiera que se use debe evaluarse imagen por imagen antes de confiar en él para producción, y **no se listan aquí como enlace directo confiable** para evitar recomendar una fuente de calidad incierta.

**Estrategia recomendada para cerrar este gap (reutiliza infraestructura que el sistema ya tiene):**
- La tabla `vision_diagnosticos` ya captura `imagen_url` + `requiere_revision` cada vez que un agrónomo usa el módulo. **Este flujo, con revisión y corrección del agrónomo, es en sí mismo un dataset propio en construcción** (el mismo patrón de aprendizaje activo que ya usa el modelo tabular vía `aceptaciones`/`rechazos`).
- **RQ-V6-01 [nuevo, pequeño]:** agregar un campo `etiqueta_confirmada` (texto, nullable) a `vision_diagnosticos`, que el agrónomo complete al revisar un diagnóstico marcado `requiere_review=true`. Con eso, cada revisión de campo se convierte en un ejemplo de entrenamiento etiquetado por un experto real — más valioso para Café/Cacao/Aguacate colombiano que cualquier dataset genérico internacional, porque refleja las condiciones de luz, variedad y fondo reales de las fincas del sistema.
- Una vez acumulados suficientes ejemplos confirmados por cultivo (sugerido: mínimo 200–300 imágenes por clase antes de intentar entrenar, umbral estadístico razonable para fine-tuning, no para entrenar desde cero), se incorporan como `DS09 — AgroIA propio (Cacao/Aguacate Colombia)` al manifest, con su propio `license_policy` interno (dato propietario del sistema, no de terceros).

### 2.4 Actualización propuesta al manifest (`datasets/VISION.md` y `datasets/manifest/*.yaml`)

```yaml
# Ejemplo de entrada para el manifest DS03 (a repetir por cada dataset de la tabla 2.2)
id: DS03
nombre: "RoCoLe - Robusta Coffee Leaf Images"
cultivo: ["Café"]
clases: ["healthy", "red_spider_mite", "rust_level_1", "rust_level_2", "rust_level_3", "rust_level_4"]
fuente_url: "https://data.mendeley.com/datasets/c5yvn32dzg/2"
doi: "10.17632/c5yvn32dzg.2"
licencia: "CC BY 4.0"
uso_comercial_permitido: true
formato_original: "JPEG + máscaras de segmentación"
notas: "Café robusta, condiciones de campo real (smartphone), útil para transferencia a variedades colombianas."
```

Esto reemplaza los IDs `DS01–DS22` que hoy están vacíos de fuente con entradas reales y verificables, permitiendo que `datasets/scripts/discover.py` y `download.py` (ya existentes en el pipeline) apunten a fuentes concretas en vez de placeholders.

### 2.5 Endpoint de estado del dataset (para trazabilidad, se apoya en lo ya existente)

`GET /api/v1/vision/admin/dataset-estado` — Admin (extiende el ya existente `POST /api/v1/vision/admin/reentrenar`, no lo reemplaza)
```json
{
  "datasets_cargados": [
    { "id": "DS03", "cultivo": "Café", "imagenes": 1560, "clases": 6, "licencia": "CC BY 4.0" },
    { "id": "DS09", "cultivo": "Cacao", "imagenes": 187, "fuente": "AgroIA propio (vision_diagnosticos confirmados)", "estado": "insuficiente_para_entrenar" }
  ],
  "cultivos_sin_cobertura": ["Aguacate", "Panela", "Ñame", "..."],
  "recomendacion": "DS09 (Cacao) necesita ~113 imágenes confirmadas más antes de alcanzar el umbral mínimo de entrenamiento."
}
```

**Regla de degradación (sin cambios):** cualquier cultivo sin dataset suficiente sigue usando el fallback OpenCV/numpy con abstención explicada — el `dataset_lineage` del contrato de inferencia (`POST /vision/diagnose`) simplemente reportará `"fuente": "agrovision_opencv_v1"` en vez de un modelo entrenado, exactamente como ya documenta la sección 6.22 hoy.

---

## 3. Priorización de entrenamiento de AgroVision

| Prioridad | Cultivo | Justificación |
|---|---|---|
| **1** | Café | Dos datasets maduros y bien documentados (RoCoLe + BRACOL), máxima importancia económica del catálogo |
| **2** | Yuca, Arroz | Datasets públicos de volumen razonable ya identificados (DS06, DS07) |
| **3** | Cacao, Aguacate | Sin dataset público maduro — requiere activar la estrategia de auto-curaduría (sección 2.3) antes de poder entrenar con confianza |
| **4** | Resto del catálogo (frutales, hortalizas, cultivos nuevos v4) | Usar PlantVillage/PlantDoc/New Plant Diseases (DS01/02/08) donde el cultivo esté cubierto por esas fuentes genéricas; para el resto, misma estrategia de auto-curaduría que Cacao/Aguacate |

---

## 4. Nota de cierre sobre licencias

Varios de los datasets de la tabla 2.2 (Cassava Kaggle, Rice Leaf Diseases, New Plant Diseases) tienen historial de licencias que varían entre ediciones o no siempre son explícitamente comerciales — dado que el propio pipeline de AgroIA ya tiene un `license_policy.yaml` con gate de uso comercial, **la recomendación es dejar que ese gate haga su trabajo automáticamente** al momento de la ingesta (`discover → inspect`), en vez de asumir aquí con certeza absoluta el estado legal de cada uno. Los marcados como "CC BY 4.0 (Mendeley Data)" (RoCoLe, BRACOL, BRACOT) son los de licencia más clara y segura para uso comercial de los listados.
