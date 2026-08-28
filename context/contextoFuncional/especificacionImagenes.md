Listo. Preparé el paquete técnico para que puedas usarlo como base del desarrollo del **Modelo de Visión Agrícola de AgroVision**.

Durante la validación encontré y corregí algunos datos de la lista original: **JMuBEN actualmente reporta 22.591 imágenes**, no 58.555; **PlantWild v2 reporta 11.488 imágenes y 115 clases**; y **AgriPath-LF16** tiene 111.307 imágenes en su versión completa, mientras que el subset balanceado reportado por el paper 2026 es de **28.482 imágenes**. ([data.mendeley.com][1])

También confirmé fuentes nacionales especialmente importantes: AGROSAVIA publica datasets de **análisis de suelos** y **análisis vegetal/foliar**, mientras que SISFITO es el sistema del ICA para captura, análisis y vigilancia fitosanitaria en Colombia. ([Agrosavia][2])

### Entregables

[📊 Inventario técnico completo en Excel](sandbox:/mnt/data/agrovision_deliverables/inventario_tecnico_datasets_agrovision.xlsx)

[📄 Inventario técnico en CSV](sandbox:/mnt/data/agrovision_deliverables/inventario_datasets_agrovision_colombia.csv)

[📘 Especificación funcional y requerimientos técnicos](sandbox:/mnt/data/agrovision_deliverables/especificacion_funcional_tecnica_modelo_vision_agrovision.docx)

[⚙️ Manifest inicial de datasets](sandbox:/mnt/data/agrovision_deliverables/datasets.yaml)

[📦 Paquete completo ZIP](sandbox:/mnt/data/agrovision_deliverables/agrovision_datasets_pipeline_spec_v1.zip)

### Qué contiene la especificación

La especificación quedó estructurada alrededor de este pipeline:

```text
datasets.yaml
      ↓
DISCOVER
      ↓
DOWNLOAD
      ↓
INSPECT
      ↓
QUARANTINE
      ↓
DEDUPLICATE
      ↓
NORMALIZE
      ↓
ANNOTATE / CONVERT
      ↓
GROUP-AWARE SPLIT
      ↓
CURATED DATASET
      ↓
TRAIN
      ↓
EVALUATE
      ↓
MODEL REGISTRY
      ↓
INFERENCE API
      ↓
DIAGNÓSTICO
      ↓
FALLBACK OPENCV / ABSTENTION
```

La estructura propuesta para tu proyecto es:

```text
datasets/
├── manifest/
├── raw/
├── quarantine/
├── staging/
├── normalized/
├── annotations/
├── curated/
│   ├── classification/
│   ├── detection/
│   └── segmentation/
├── metadata/
├── models/
├── reports/
├── configs/
└── scripts/
```

Además, la especificación define los componentes funcionales:

```text
Quality Gate
     ↓
Crop Detection
     ↓
Disease / Pest Detection
     ↓
Segmentation
     ↓
Severity
     ↓
Soil + Climate + GPS + Temporalidad
     ↓
Agronomic AI Engine
     ↓
Resultado preliminar / diagnóstico
```

### Datasets prioritarios

La primera ola de entrenamiento que recomiendo queda así:

**Café**

* Colombian Coffee Tree Leaves Multispectral — 6.726
* JMuBEN — 22.591
* RoCoLe — 1.560
* Uganda Coffee Leaf Disease — 3.312
* Saposoa Coffee Leaf — 1.500
* Coffee Leaf Roboflow — 1.664

El dataset colombiano multiespectral es especialmente valioso porque tiene RGB y cinco bandas espectrales, y está orientado a roya del café. ([PubMed Central (PMC)][3])

**Cacao**

* CocoaMoniliaDataSet — 1.953
* Black Pod Rot Levels — ~1.000
* Cacao Diseases Roboflow

CocoaMoniliaDataSet es especialmente importante porque contiene **polígonos y formatos COCO, YOLO y máscaras de segmentación**, además de las cuatro clases h0/m1/m2/m3. ([Zenodo][4])

**Multicultivo**

* PlantVillage — 54.306
* PlantVillageVQA — 55.448 imágenes y 193.609 pares QA
* PlantDoc — 2.598
* PlantWild v2 — 11.488
* PlantSeg — 11.400+
* AgriPath-LF16 — 111.307
* IP102 — 75.000+

PlantVillage queda como **pretraining**, mientras que PlantDoc, PlantWild y PlantSeg deben tener mucho peso en la adaptación a condiciones reales. PlantSeg aporta además máscaras de las zonas enfermas y metadata de procedencia. ([Hugging Face][5])

### Un punto muy importante de licenciamiento

No hice que el pipeline trate todo lo público como automáticamente reutilizable. Esto es especialmente importante para **IP102**, cuyo repositorio indica uso académico gratuito y solicita contacto para otros usos, y para **PlantWild v2**, que declara CC BY-NC-ND 4.0. ([GitHub][6])

Por eso el pipeline incluye un **license gate**:

```text
download
   ↓
license validation
   ↓
┌───────────────────────────┐
│ licencia válida para uso  │
│ previsto por AgroVision?  │
└────────────┬──────────────┘
        NO   │   SI
        ↓        ↓
 quarantine    curated
```

Esto evita que posteriormente entrenemos un modelo comercial usando inadvertidamente un dataset que no lo permita.

### Las URLs principales quedaron verificadas

Por ejemplo:

* Colombian Coffee: `https://www.kaggle.com/ds/5644659`
* CocoaMonilia: `https://zenodo.org/records/17716661/files/CocoaMoniliaDataSet.zip?download=1`
* PlantVillage: `https://huggingface.co/datasets/mohanty/PlantVillage`
* PlantDoc: `https://github.com/pratikkayal/PlantDoc-Dataset`
* PlantWild v2: `https://tqwei05.github.io/PlantWild/access_v2`
* PlantSeg: `https://doi.org/10.5281/zenodo.17719108`
* IP102: `https://github.com/xpwu95/IP102`
* AGROSAVIA: `https://www.agrosavia.co/nosotros/transparencia-y-acceso-a-informaci%C3%B3n-p%C3%BAblica/datos-abiertos`
* SISFITO: `https://sisfito.ica.gov.co/`

CocoaMonilia, por ejemplo, publica además un ZIP de 6,2 GB y mantiene train/test/validation y anotaciones en COCO/YOLO/máscaras. ([Zenodo][4])

### Recomendación para el siguiente paso

Yo continuaría directamente con la **implementación del repositorio de entrenamiento**, generando los scripts:

```text
scripts/
├── discover.py
├── download.py
├── inspect.py
├── deduplicate.py
├── normalize.py
├── convert_annotations.py
├── split.py
├── train.py
├── evaluate.py
└── package_model.py
```

y el primer `datasets.yaml` completo para que puedas ejecutar algo como:

```bash
python scripts/download.py --dataset DS01
python scripts/inspect.py --dataset DS01
python scripts/deduplicate.py --dataset DS01
python scripts/normalize.py --dataset DS01
python scripts/split.py --dataset DS01
python scripts/train.py --model coffee
```

Eso ya convertiría esta especificación en el **pipeline ejecutable del proyecto**, no solamente en documentación.

[1]: https://data.mendeley.com/datasets/t2r6rszp5c/1 "JMuBEN - Mendeley Data"
[2]: https://www.agrosavia.co/nosotros/transparencia-y-acceso-a-informaci%C3%B3n-p%C3%BAblica/datos-abiertos "AGROSAVIA - Corporación colombiana de investigación agropecuaria"
[3]: https://pmc.ncbi.nlm.nih.gov/articles/PMC11927593/?utm_source=chatgpt.com "Colombian coffee tree leaves multispectral images dataset - PMC"
[4]: https://zenodo.org/records/17716661 "CocoaMoniliaDataSet | Zenodo"
[5]: https://huggingface.co/datasets/mohanty/PlantVillage?utm_source=chatgpt.com "mohanty/PlantVillage · Datasets at Hugging Face"
[6]: https://github.com/xpwu95/IP102?utm_source=chatgpt.com "GitHub - xpwu95/IP102: IP102: A Large-Scale Benchmark Dataset for Insect Pest Recognition · GitHub"
