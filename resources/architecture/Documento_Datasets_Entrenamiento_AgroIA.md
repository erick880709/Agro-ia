# AgroIA — Datasets de entrenamiento de los modelos

**Versión:** 1.0 · **Fecha:** 2026-08-29
**Alcance:** trazabilidad de qué datos han entrenado (o entrenarán) cada modelo
de AgroIA: modelo tabular (diagnóstico nutricional/aptitud) y AgroVision
(diagnóstico por foto). Fuente de verdad de artefactos: `apps/ml/models/`,
`datasets/` y `ml_meta.json`.

---

## 1. Modelo tabular — diagnóstico nutricional y aptitud (ML en sombra)

### 1.1 Dataset de entrenamiento principal: sintético etiquetado por reglas

El modelo tabular no entrena con un dataset externo: entrena contra un
**dataset sintético etiquetado por el sistema experto** (el mismo motor de
reglas UPRA/Cenicafé/AGROSAVIA que es la fuente de verdad en producción).

| Campo | Valor |
|---|---|
| Generador | `apps/ml/agroia_ml/train_colombia.py` (modo activo) |
| Reglas de etiquetado | 54 reglas agronómicas · 17 variables · 30 cultivos (`asegurar_reglas` + `load_seeds`) |
| Muestras por modelo | **75.000** por variable de diagnóstico + 1 modelo de aptitud (`ml_aptitud`) |
| Variables modeladas | `ph`, `nitrogeno`, `fosforo`, `potasio`, `calcio`, `magnesio`, `azufre`, `hierro`, `manganeso`, `zinc`, `cobre`, `boro`, `materia_organica`, `cic`, `humedad`, `temperatura_suelo`, `conductividad_electrica` |
| Clases de salida | `DEFICIT` / `EXCESO` / `OK` (diagnóstico por variable) · clasificación UPRA (aptitud) |
| Datos faltantes sintéticos | 35 % (`missingness_sintetico: 0.35`) con imputación por **medianas por variable** (mismas medianas que usa `ml_oracle` en inferencia) |
| Métricas sintéticas | accuracy ≈ 0.95–0.97 · F1 ≈ 0.95–0.97 por variable |
| Fecha de entrenamiento | 2026-08-27 (ver `ml_meta.json`) |

### 1.2 Ground truth real (aprendizaje activo)

El dataset real del modelo se construye con el uso de la plataforma
(`services/ml_labels.py`, visible en `GET /api/v1/ml/etiquetas-doradas`):

| Fuente | Información que aporta | Uso |
|---|---|---|
| **Aceptaciones de recomendación** (`aceptaciones_recomendacion`) | Estados por variable (`DEFICIT/EXCESO/OK`) validados por el agrónomo + perfil de suelo de la última lectura | Etiquetas doradas; peso de muestra real ×10 |
| **Ciclos cerrados** (`historial_ciclos_lote`) | Rendimiento real (t/ha) vs. esperado de ficha | Ground truth de rendimiento; excluye ciclos `rendimiento_atipico` |
| Estado actual (2026-08-27) | 1 aceptación útil + 1 ciclo cerrado útil | Promoción a PRODUCTION exige concordancia real ≥ 0.85; por ahora todos los modelos están en sombra (`promovidas: {}`) |

### 1.3 Baselines Kaggle (cold-start, metodológico — NO producción)

Entrenados al inicio del proyecto como baseline; **no alimentan las
recomendaciones mostradas a usuarios reales** (regla de `datasets/README.md`).

| Dataset | Archivo | Registros | Tamaño | Columnas (información) | Uso |
|---|---|---|---|---|---|
| Crop Recommendation (Kaggle `atharvaingle`) | `datasets/crop-recommendation/Crop_recommendation.csv` | 2.200 | 147 KB | `N, P, K, temperature, humidity, ph, rainfall, label` (cultivo recomendado) | Modelo 2 — predicción de cultivo ideal (baseline metodológico) |
| Crops NPK (Kaggle `javakhan`) | `datasets/crops-npk/sensor_Crop_Dataset (1).csv` | 20.000 | 2,9 MB | `Nitrogen, Phosphorus, Potassium, Temperature, Humidity, pH_Value, Rainfall, Crop, Soil_Type, Variety` | Modelo 3 — deficiencias nutricionales (baseline metodológico) |

### 1.4 Artefactos generados

`apps/ml/models/`: `ml_aptitud.joblib` + 17 `ml_diagnostico_*.joblib`
(pH, N, P, K, Ca, Mg, S, Fe, Mn, Zn, Cu, B, MO, CIC, humedad, T suelo, CE)
+ `ml_meta.json` (fecha, variables, imputación, cultivos, métricas y
promoción). El backend los carga vía `services/ml_oracle.py` (imports
perezosos; degrada a `None` sin artefactos).

### 1.5 Fuentes tabulares externas para calibración (espec v6 §1)

Enlaces consolidados para el equipo de datos (no son datasets de
entrenamiento directo: calibran `rendimiento_esperado`, umbrales y fichas):

| Fuente | Qué aporta | Acceso |
|---|---|---|
| **FAOSTAT** (producción/rendimiento por cultivo y país) | Valida `rendimiento_esperado` (anti-outliers) | `https://www.fao.org/faostat/en/#data/QCL` (Bulk Downloads → `Production_Crops_Livestock_E_All_Data.zip`) · API: `https://fenixservices.fao.org/faostat/api/v1/es/data/QCL?area=Colombia&item={cultivo}` |
| **datos.gov.co — EVA (UPRA/MinAgricultura)** | Área, producción y rendimiento por municipio/cultivo en Colombia | `https://www.datos.gov.co/browse?q=evaluaciones+agropecuarias+municipales` → endpoint Socrata `https://www.datos.gov.co/resource/{id}.json` (el `{id}` cambia con cada actualización; no hardcodear) |
| **ISRIC SoilGrids v2.0** | pH, CIC, carbono orgánico y textura de referencia por coordenada (250 m) | API punto: `https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lng}&lat={lat}&property=phh2o&property=cec&property=soc&property=clay&property=sand&property=silt` · mapas: `https://files.isric.org/soilgrids/latest/data/` — servicio beta: referencia de calibración, NO dependencia en tiempo real de producción |
| **Agrosavia / Fedepanela / ICA** | Fichas técnicas por cultivo (rangos agronómicos a curar manualmente) | `https://www.agrosavia.co/` · `https://fedepanela.org.co/gremio/` · `https://www.ica.gov.co/` — documentos, no API; se transcriben a `RANGOS[cultivo]` en `train_colombia.py` |

---

## 2. AgroVision — diagnóstico visual (foto)

### 2.1 Estado del entrenamiento

**Primer modelo entrenado con datos reales (2026-08-29)** — baseline sklearn
sobre **DS02 PlantDoc** (CC BY 4.0, campo real):

- Pipeline completo ejecutado: `discover → download → inspect → dedup →
  normalize → split → train`.
- 2.574 imágenes inspeccionadas OK · 59 duplicados descartados (SHA-256 +
  pHash) · 2.508 normalizadas en **10 clases canónicas** (apple_scab,
  bell_pepper_bacterial_spot, corn_leaf_blight, corn_rust, grape_black_rot,
  potato_early_blight, potato_late_blight, tomato_early_blight,
  tomato_late_blight, other_disease).
- Split sin fuga por clusters pHash con déficit relativo por clase:
  1.459 train / 623 val / 421 test.
- **Modelo `baseline-sklearn-20260829-144942`**: HistGradientBoosting con
  features de color/textura — **accuracy en validación 70,8 %** (1.459
  muestras, 10 clases).

Producción sigue operando con el fallback OpenCV/numpy
(`services/vision_fallback.py`, diagnóstico preliminar no confirmatorio):
el baseline sklearn es un hito del pipeline, **no** el modelo operativo. Se
promoverá cuando entrenen DS03–DS08 (café/yuca/arroz) y las métricas superen
los umbrales de promoción. PlantDoc no contiene clase `healthy`; esa clase
llegará con DS01/DS09 y fotos propias.

Próximo: DS23 CocoaMonilia (monilia M1–M3) pendiente de descarga (6,19 GB).

**DS23 CocoaMoniliaDataSet v2 (2026-08-29)** — descargado de Zenodo
(`10.5281/zenodo.17716661`, CC BY 4.0, 6,19 GB): 1.950 fotos de mazorca de
cacao en campo normalizadas en 4 clases (`healthy` 646 · `cocoa_monilia_m1`
436 · `cocoa_monilia_m2` 401 · `cocoa_monilia_m3` 467); split sin fuga
1.341/317/292. Las 3.900 máscaras de segmentación y las anotaciones
COCO/YOLO quedaron preservadas en cuarentena para la etapa de detección.

**Modelo combinado `baseline-sklearn-20260829-182910` (14 clases)** —
PlantDoc + CocoaMonilia juntos: 2.800 train / 940 val · **accuracy en
validación 59,6 %**. La caída frente al baseline solo-PlantDoc (70,8 %) es
esperable: las etapas monilia M1–M3 son visualmente cercanas entre sí y el
vocabulario crece de 10 a 14 clases. Es un baseline de color/textura para
medir progreso — el modelo operativo seguirá siendo el fallback OpenCV hasta
entrenar con más datasets (DS01/DS03–DS08) y superar los umbrales de
promoción.

### 2.2 Datasets declarados para entrenamiento (manifest v6)

Trazabilidad completa en `datasets/manifest/datasets.yaml`; el lineage de cada
modelo empaquetado queda en `datasets/models/<nombre>/<version>/manifest.json`.

| ID | Dataset | Cultivos | Información por muestra | Licencia / uso comercial |
|---|---|---|---|---|
| DS01 | PlantVillage | Tomate, papa, maíz, uva, manzana… (14) | ~54.305 fotos de hoja, 38 clases (laboratorio) | Dominio abierto — **verificar réplica** |
| DS02 | PlantDoc | 13 especies | 2.598 fotos de **campo real** · ✅ **primer entrenamiento 2026-08-29** | CC BY 4.0 · ✅ |
| DS03 | RoCoLe | Café robusta | 1.560 fotos + máscaras; roya en 4 niveles + ácaro | CC BY 4.0 · ✅ |
| DS04 | BRACOL | Café arábica | 1.747 hojas + 2.147 recortes de síntoma con severidad | CC BY 4.0 · ✅ |
| DS05 | BRACOT | Café | 300 árboles con instancias segmentadas | CC BY 4.0 · ✅ |
| DS06 | Cassava Leaf Disease | Yuca | ~21.000 fotos de campo, 5 clases | **Verificar** (Kaggle) |
| DS07 | Rice Leaf Diseases | Arroz | Fotos de campo (tizón/mancha parda) | **Verificar** |
| DS08 | New Plant Diseases (Augmented) | Varios | PlantVillage aumentado | **Verificar réplica** |
| DS09 | **AgroIA propio** (Cacao/Aguacate) | Cacao, aguacate | Fotos reales de fincas del sistema + `etiqueta_confirmada` del agrónomo (RQ-V6-01) | Propietario · ✅ |
| DS10–DS28 | Complementarios | Café/cacao/multicultivo | Multiespectral, COCO/YOLO/máscaras, VQA, IP102, AgriPath, portales AGROSAVIA/ICA/SIOC | Mixto (NC bloqueados por `license_policy.yaml`) |

### 2.3 Reglas de uso (heredadas de la especificación)

- **Provenance-first**: cada imagen conserva fuente, dataset, versión, URL,
  licencia, hash y etiqueta original (`metadata/lineage.jsonl`).
- **No leakage**: split por grupo (finca/planta/hoja) o clusters pHash.
- **Field-first**: PlantVillage solo pretraining; el test prioriza campo real.
- **Commercial-use gate**: DS16/DS17/DS18/DS22/DS23/DS28 (NC o académico)
  bloqueados de curated/production; DS06/DS07/DS08 y portales requieren
  revisión de licencia antes de promover.
- **DS09**: se entrena cuando haya ≥ 200–300 imágenes confirmadas por clase.

---

## 3. Cómo leer la trazabilidad

1. **Tabular**: `apps/ml/models/ml_meta.json` (fecha, variables, métricas,
   promoción) + `GET /api/v1/ml/estado` (BD + artefactos) +
   `GET /api/v1/ml/etiquetas-doradas` (ground truth real).
2. **Visión**: `datasets/metadata/*.jsonl` (discovery/downloads/inspection/
   duplicates/images/lineage) + `GET /api/v1/vision/admin/dataset-estado`
   (resumen del pipeline) + `datasets/models/<nombre>/<version>/manifest.json`
   (lineage exacto del artefacto: dataset IDs, versiones, hashes, git commit).
3. **Regla de oro**: ninguna métrica de producción se publica basada
   únicamente en datos sintéticos o de laboratorio; la promoción exige
   concordancia con datos reales colombianos.
