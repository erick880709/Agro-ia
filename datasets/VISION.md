# AgroVision — Pipeline de visión agrícola

Implementación de la especificación `context/contextoVision/especi.md` v1.0
(28-ago-2026) y del mapeo de fuentes de la
`context/AgroIA_Especificacion_Tecnica_v6_Datasets.md`: ingesta, curación,
entrenamiento, evaluación y despliegue de modelos de visión para diagnóstico
preliminar de enfermedades/plagas en cultivos colombianos.

## Manifest v6

- **DS01–DS08**: fuentes públicas reales y verificables (PlantVillage,
  PlantDoc, RoCoLe, BRACOL, BRACOT, Cassava, Rice, PlantVillage aumentado).
- **DS09**: dataset propio AgroIA (Cacao/Aguacate Colombia) en construcción
  por aprendizaje activo: `POST /api/v1/vision/diagnosticos/{id}/confirmar`
  alimenta `vision_diagnosticos.etiqueta_confirmada` (RQ-V6-01).
- **DS10–DS28**: fuentes complementarias del inventario previo.
- `uso_comercial_permitido` + `license_policy.yaml` gobiernan el paso a
  curated/production; DS06–DS08 y DS24–DS27 quedan en revisión de licencia.

## Estructura (sección 6 de la especificación)

```
datasets/
├── manifest/          datasets.yaml (catálogo DS01-DS22), class_map.yaml, license_policy.yaml
├── configs/           pipeline.yaml (umbrales/splits), train_classification.yaml
├── raw/               originales intactos por <DS>/<version>/
├── quarantine/        corruptos, licencia dudosa, labels sin alias
├── staging/           extracción intermedia de descargas
├── normalized/        RGB + clase canónica; TIF multiespectral aparte
├── annotations/       esquema interno común (labels.jsonl)
├── curated/           classification/{train,val,test}, detection, segmentation
├── metadata/          images.jsonl, labels.jsonl, duplicates.jsonl, lineage.jsonl, ...
├── models/            artefactos empaquetados <nombre>/<version>/manifest.json
├── reports/           reportes JSON/CSV/HTML
└── scripts/           discover, download, inspect, deduplicate, normalize,
                       convert_annotations, split, train, evaluate,
                       package_model, fallback_opencv
```

## Flujo (sección 8)

| Etapa | Script | Salida |
|-------|--------|--------|
| Discover | `scripts/discover.py` | metadata/discovery.jsonl |
| Download | `scripts/download.py` | raw/<DS>/<version>/ + metadata/downloads.jsonl |
| Inspect | `scripts/inspect.py` | metadata/inspection.jsonl + quarantine/ |
| Dedup | `scripts/deduplicate.py` | metadata/duplicates.jsonl (nunca borra raw) |
| Normalize | `scripts/normalize.py` | normalized/ + images.jsonl + lineage.jsonl |
| Convert | `scripts/convert_annotations.py` | annotations/<DS>/labels.jsonl |
| Split | `scripts/split.py` | curated/classification/{train,val,test}/ + manifest |
| Train | `scripts/train.py` | datasets/models/ + reports/ |
| Evaluate | `scripts/evaluate.py` | reports/evaluation/{metrics.json,metrics.csv,report.html} |
| Package | `scripts/package_model.py` | models/<nombre>/<version>/manifest.json |

## Ejemplos

```powershell
# Correr desde la raíz del repo con el venv del proyecto.
cd datasets
python scripts/discover.py --ids DS02            # valida URL/licencia
python scripts/download.py --ids DS02 --extraer  # descarga y extrae
python scripts/inspect.py --ids DS02
python scripts/deduplicate.py --ids DS02
python scripts/normalize.py --ids DS02
python scripts/split.py --ids DS02
python scripts/fallback_opencv.py hoja.jpg --crop coffee
```

## Principios aplicados

- **Provenance-first**: cada imagen conserva source, dataset, versión, URL,
  licencia, hash y etiqueta original (lineage.jsonl).
- **No leakage**: split por grupo (farm_id > plant_id > leaf_id > source_url);
  sin metadata de grupo se agrupa por pHash antes de particionar.
- **Commercial-use gate**: license_policy.yaml bloquea DS10/DS11/DS12/DS16/
  DS17/DS22 de curated/production; DS18-DS21 requieren revisión de ficha.
- **Abstention**: el fallback nunca se presenta como definitivo
  (`requires_review=true`); fotos inválidas → `status=abstain` con motivo.
- **Field-first**: PlantVillage solo para pretraining; el test de producción
  prioriza imágenes de campo.

## Inferencia (sección 18)

`POST /api/v1/vision/diagnose` (backend) devuelve diagnóstico preliminar,
confianza, evidencia visual y estado (`model|fallback|abstain`). El endpoint
`POST /api/v1/vision/analizar-plaga` persiste el diagnóstico por finca. El
motor vive en `apps/backend/agroia_backend/services/vision_engine.py` y el
fallback OpenCV/numpy en `services/vision_fallback.py` (mismo código usado
por `scripts/fallback_opencv.py`).

## Dependencias

Los scripts corren con `numpy` + `Pillow` (opcional: cv2, torch, PyYAML,
kaggle CLI, git). Sin ellas degradan graciosamente: YAML con parser propio,
pHash con DCT numpy, entrenamiento con backend sklearn.
