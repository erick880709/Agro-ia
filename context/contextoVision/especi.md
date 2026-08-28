Especificación funcional y técnica
Modelo de Visión Agrícola AgroVision
Inventario de datasets + pipeline de ingesta, curación, entrenamiento, evaluación y despliegue
Versión 1.0 | Fecha de verificación de fuentes: 28 de agosto de 2026
1. Objetivo
Definir la especificación para construir el software que permitirá transformar un conjunto controlado de datasets públicos nacionales e internacionales en modelos de visión capaces de realizar diagnósticos visuales preliminares de enfermedades, plagas y severidad en cultivos colombianos. El sistema debe reemplazar progresivamente el estado 'No determinada' del punto 3.1 y, mientras el modelo especializado alcanza desempeño de producción, mantener un fallback basado en visión tradicional/OpenCV.
2. Alcance funcional
Descubrir, registrar y versionar datasets externos mediante un manifest declarativo.
Descargar archivos originales a datasets/raw sin alterar los originales.
Inspeccionar integridad, metadatos, resolución, MIME type, etiquetas y posibles corrupciones.
Deduplicar usando hash criptográfico y hash perceptual sin romper la trazabilidad.
Normalizar nombres de clases, formatos y tamaños; conservar metadata de procedencia.
Convertir anotaciones entre clasificación, COCO, YOLO y máscaras cuando sea técnicamente válido.
Generar splits train/validation/test sin fuga por hoja, planta, finca, fuente o sujeto cuando la metadata lo permita.
Entrenar modelos especializados por cultivo/tarea y modelos base multicultivo.
Evaluar precisión, recall, macro-F1, mAP, IoU, tasa de falsos negativos y calibración de confianza.
Empaquetar modelos versionados para inferencia y publicar artefactos junto con su dataset manifest.
Exponer una inferencia que devuelva diagnóstico preliminar, confianza, evidencia visual y estado de seguridad.
Ejecutar fallback OpenCV cuando no exista modelo aplicable o la confianza esté por debajo del umbral.
3. Principios de diseño
Principio
Regla
Provenance-first
Cada imagen debe conservar source, dataset, versión, URL, licencia, hash, fecha de ingesta y etiqueta original.
No leakage
Nunca dividir variantes o imágenes de la misma hoja/planta/finca entre train y test.
Field-first
El test de producción debe priorizar imágenes reales de campo; PlantVillage se usa principalmente para pretraining.
Specialized models
Preferir modelos por cultivo/tarea frente a un único clasificador monolítico.
Abstention
Cuando la confianza no sea suficiente, el sistema debe abstenerse y solicitar otra evidencia.
Commercial-use gate
Una licencia no verificada bloquea el paso a curated/production.

4. Inventario técnico de datasets
El archivo Excel entregado contiene el inventario completo y debe considerarse el catálogo operativo. A continuación se resumen las fuentes críticas y su forma de uso.
DS01 — Colombian Coffee Tree Leaves Multispectral
Imágenes: 6,726. Cultivo(s): Café (Coffea arabica). Enfermedades: Roya / Coffee Leaf Rust (Hemileia vastatrix). Formato: JPG RGB + TIF multiespectral (Blue, Green, Red, Red Edge, NIR). Licencia: CC BY 4.0. Prioridad: P0 - Crítica. Fuente: https://www.kaggle.com/ds/5644659.
DS02 — CocoaMoniliaDataSet v2
Imágenes: 1,953. Cultivo(s): Cacao. Enfermedades: Monilia (Moniliophthora roreri): sano, m1, m2, m3. Formato: COCO 1.0 + YOLO + máscaras PNG. Licencia: CC BY 4.0. Prioridad: P0 - Crítica. Fuente: https://zenodo.org/records/17716661.
DS05 — JMuBEN
Imágenes: 22,591. Cultivo(s): Café arábica. Enfermedades: Sana; Phoma; Roya; Cercospora; Miner (minador). Formato: Imágenes (landing Mendeley; archivos de imagen). Licencia: CC BY 4.0. Prioridad: P0 - Crítica. Fuente: https://data.mendeley.com/datasets/t2r6rszp5c/1.
DS06 — RoCoLe - Robusta Coffee Leaf
Imágenes: 1,560. Cultivo(s): Café Robusta. Enfermedades: Sana; Roya; Araña roja. Formato: Imágenes de campo; anotaciones asociadas al dataset. Licencia: CC BY 4.0. Prioridad: P0 - Crítica. Fuente: https://doi.org/10.17632/c5yvn32dzg.2.
DS07 — PlantVillage
Imágenes: 54,306. Cultivo(s): 14 cultivos. Enfermedades: 26 enfermedades + clases sanas. Formato: JPEG; dataset HF incluye configs y splits. Licencia: CC BY-SA 3.0 (mirror oficial HF actual). Prioridad: P0 - Crítica. Fuente: https://huggingface.co/datasets/mohanty/PlantVillage.
DS09 — PlantDoc
Imágenes: 2,598. Cultivo(s): 13 especies. Enfermedades: Hasta 17 clases de enfermedad + sanas. Formato: Imágenes; dataset GitHub. Licencia: CC BY 4.0. Prioridad: P0 - Crítica. Fuente: https://github.com/pratikkayal/PlantDoc-Dataset.
DS10 — PlantWild v2
Imágenes: 11,488. Cultivo(s): Multicultivo. Enfermedades: 115 clases de enfermedad. Formato: Imágenes + metadata; Hugging Face/Google Drive/UQRDM. Licencia: CC BY-NC-ND 4.0. Prioridad: P0 - Crítica. Fuente: https://tqwei05.github.io/PlantWild/access_v2.
DS11 — PlantSeg
Imágenes: 11,400+. Cultivo(s): 34 hospedantes. Enfermedades: 69 tipos; 115 combinaciones planta-enfermedad. Formato: JPEG + PNG masks + metadata CSV. Licencia: CC BY-NC 4.0. Prioridad: P0 - Crítica. Fuente: https://doi.org/10.5281/zenodo.17719108.
DS12 — IP102
Imágenes: 75,000+. Cultivo(s): Productos agrícolas diversos. Enfermedades: 102 categorías de plagas/insectos. Formato: Imágenes + clases + bounding boxes. Licencia: Libre para uso académico; contacto para otros usos. Prioridad: P0 - Crítica. Fuente: https://github.com/xpwu95/IP102.
DS18 — AGROSAVIA - Resultados de Análisis de Laboratorio Suelos en Colombia
Imágenes: N/A. Cultivo(s): Multicultivo. Enfermedades: N/A. Formato: Datos abiertos / portal datos.gov.co. Licencia: Revisar ficha individual del conjunto. Prioridad: P0 - Crítica. Fuente: https://www.agrosavia.co/nosotros/transparencia-y-acceso-a-informaci%C3%B3n-p%C3%BAblica/datos-abiertos.
DS19 — AGROSAVIA - Análisis vegetal (foliar)
Imágenes: N/A. Cultivo(s): Multicultivo. Enfermedades: Sintomatología foliar; no necesariamente diagnóstico etiológico. Formato: Datos abiertos / portal datos.gov.co. Licencia: Revisar ficha individual del conjunto. Prioridad: P0 - Crítica. Fuente: https://www.agrosavia.co/nosotros/transparencia-y-acceso-a-informaci%C3%B3n-p%C3%BAblica/datos-abiertos.
DS20 — ICA SISFITO
Imágenes: No declarado como dataset de imágenes. Cultivo(s): Multicultivo. Enfermedades: Plagas endémicas/exóticas, importancia económica/cuarentenaria. Formato: Sistema web; consultar exportaciones disponibles. Licencia: Revisar términos/permiso de uso de los datos. Prioridad: P0 - Crítica. Fuente: https://sisfito.ica.gov.co/.
5. Fuentes y URL verificadas para descargar
ID
Dataset
URL de descarga/acceso
Mecanismo
Licencia
Estado
DS01
Colombian Coffee Tree Leaves Multispectral
https://www.kaggle.com/ds/5644659
Kaggle API / descarga ZIP
CC BY 4.0
Verificado
DS02
CocoaMoniliaDataSet v2
https://zenodo.org/records/17716661/files/CocoaMoniliaDataSet.zip?download=1
wget/curl/Zenodo REST
CC BY 4.0
Verificado
DS03
Coffee Leaf Disease Dataset - Uganda
https://data.mendeley.com/datasets/k36wnd6knb/1
Mendeley Data - Download All
CC BY 4.0
Verificado
DS04
Coffee Leaf Dataset by Phytosanitary Class - Saposoa
https://data.mendeley.com/datasets/mfpxg4y65r/1
Mendeley Data - Download All
CC BY 4.0
Verificado
DS05
JMuBEN
https://data.mendeley.com/datasets/t2r6rszp5c/1
Mendeley Data - Download All
CC BY 4.0
Verificado
DS06
RoCoLe - Robusta Coffee Leaf
https://doi.org/10.17632/c5yvn32dzg.2
Mendeley Data DOI
CC BY 4.0
Verificado
DS07
PlantVillage
https://huggingface.co/datasets/mohanty/PlantVillage/resolve/main/data.zip
Hugging Face / Datasets API / ZIP
CC BY-SA 3.0 (mirror oficial HF actual)
Verificado
DS08
PlantVillageVQA
https://huggingface.co/datasets/SyedNazmusSakib/PlantVillageVQA
Hugging Face Hub
CC BY 4.0
Verificado
DS09
PlantDoc
https://github.com/pratikkayal/PlantDoc-Dataset
git clone / GitHub
CC BY 4.0
Verificado
DS10
PlantWild v2
https://huggingface.co/datasets/Voxel51/PlantWild
Hugging Face Hub; alternativa Google Drive/UQRDM
CC BY-NC-ND 4.0
Verificado
DS11
PlantSeg
https://doi.org/10.5281/zenodo.17719108
Zenodo
CC BY-NC 4.0
Verificado
DS12
IP102
https://github.com/xpwu95/IP102
Google Drive/AliyunDrive desde README
Libre para uso académico; contacto para otros usos
Verificado
DS13
Black Pod Rot Levels
https://www.kaggle.com/datasets/zaldyjr/black-pod-rot-levels
Kaggle API / descarga
CC BY-SA 4.0
Verificado
DS14
Cacao diseases - Roboflow Universe
https://universe.roboflow.com/cacao-mev33/cacao-diseases-hrb5y
Roboflow export/API; versionar antes de usar
CC BY 4.0
Verificado
DS15
Coffee Leaf Computer Vision Dataset - Roboflow
https://universe.roboflow.com/coffeleaf/coffee-leaf-y9jn4
Roboflow export/API; versionar antes de usar
CC BY 4.0
Verificado
DS16
AgriPath-LF16 (full)
https://huggingface.co/datasets/hamzamooraj99/AgriPath-LF16
Hugging Face Hub
Revisar ficha/README antes de uso comercial
Verificado
DS17
AgriPath-LF16-30k (subset balanceado)
https://huggingface.co/datasets/hamzamooraj99/AgriPath-LF16
Hugging Face Hub; aplicar subset según paper
Revisar ficha/README antes de uso comercial
Verificado
DS18
AGROSAVIA - Resultados de Análisis de Laboratorio Suelos en Colombia
https://www.datos.gov.co/
Portal datos.gov.co; localizar por nombre exacto; API Socrata cuando aplique
Revisar ficha individual del conjunto
Verificado - portal
DS19
AGROSAVIA - Análisis vegetal (foliar)
https://www.datos.gov.co/
Portal datos.gov.co; localizar por nombre exacto; API Socrata cuando aplique
Revisar ficha individual del conjunto
Verificado - portal
DS20
ICA SISFITO
https://sisfito.ica.gov.co/
Consulta/exportación si está habilitada; posible integración institucional
Revisar términos/permiso de uso de los datos
Verificado - sistema público
DS21
SIOC / MinAgricultura - Cacao, cifras sectoriales e histórica
https://sioc.minagricultura.gov.co/Cacao/
Portal SIOC / descarga de documentos
Revisar ficha/condiciones de cada recurso
Verificado - portal
DS22
Open Plant Disease Dataset (referencia de literatura)
No identificado como repositorio único verificable
Discovery only
No asumir una única licencia; revisar procedencia
No usar aún

Nota: en Kaggle, Mendeley, Roboflow y Hugging Face la URL puede ser un recurso de acceso y no una URL binaria estática. El software debe utilizar el mecanismo de descarga documentado por el proveedor. Para Roboflow se requiere seleccionar y fijar una versión; para algunos portales gubernamentales se requiere localizar el recurso por nombre exacto y validar la ficha de licencia.
6. Carpeta objetivo del proyecto
datasets/
├── manifest/
│   ├── datasets.yaml
│   ├── class_map.yaml
│   └── license_policy.yaml
├── raw/
│   ├── DS01/
│   │   └── <version>/
│   ├── DS02/
│   └── ...
├── quarantine/
├── staging/
├── normalized/
├── annotations/
├── curated/
│   ├── classification/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   ├── detection/
│   │   ├── images/
│   │   └── labels/
│   └── segmentation/
├── metadata/
│   ├── images.jsonl
│   ├── labels.jsonl
│   ├── duplicates.jsonl
│   └── lineage.jsonl
├── models/
├── reports/
├── configs/
└── scripts/
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
7. Manifest de datasets
datasets:
  - id: DS01
    name: Colombian Coffee Tree Leaves Multispectral
    source_url: https://www.kaggle.com/ds/5644659
    download_url: https://www.kaggle.com/ds/5644659
    download_type: kaggle
    version: "current"
    license: CC-BY-4.0
    enabled: true
    priority: P0
    task: [classification, multispectral]
  - id: DS02
    name: CocoaMoniliaDataSet v2
    source_url: https://zenodo.org/records/17716661
    download_url: https://zenodo.org/records/17716661/files/CocoaMoniliaDataSet.zip?download=1
    download_type: http
    version: "v2"
    license: CC-BY-4.0
    enabled: true
    priority: P0
    task: [detection, segmentation, severity]
  # Continuar con el resto del inventario del Excel.
8. Flujo funcional de ingesta
Etapa
Comportamiento
Discover
Lee datasets.yaml y comprueba HTTP/DOI/endpoint, versión y términos.
Download
Descarga a raw/ con reintentos, resume, checksum y log.
Inspect
Verifica extensiones, MIME, imagen legible, dimensiones, profundidad de bits y labels.
Quarantine
Mueve elementos corruptos, licencia dudosa o estructura inesperada fuera del dataset utilizable.
Deduplicate
SHA-256 para exactos; pHash/aHash para duplicados visuales; registra el ganador y el descartado.
Normalize
Mapea clases al catálogo AgroVision; conserva original_label.
Annotate/Convert
Convierte COCO↔YOLO o máscaras solo cuando se mantenga la semántica.
Split
Genera splits por grupo; nunca por archivo aislado cuando existe group_id.
Curate
Publica un dataset reproducible con manifest, metadata y hashes.

9. Requerimientos funcionales
ID
Requerimiento
RF-01
El sistema debe cargar un catálogo YAML/JSON de datasets.
RF-02
Debe soportar HTTP/HTTPS, Kaggle, Hugging Face, Mendeley, Zenodo y repositorios Git; adaptadores adicionales deben ser plug-in.
RF-03
Debe impedir descargar automáticamente fuentes cuyo mecanismo requiera credenciales inexistentes.
RF-04
Debe registrar dataset_id, versión, fecha de descarga, URL, licencia, checksum y tamaño.
RF-05
Debe validar que cada archivo de imagen sea decodificable.
RF-06
Debe calcular SHA-256 y pHash.
RF-07
Debe mantener lineage entre imagen original y imagen normalizada.
RF-08
Debe mapear clases a una taxonomía canónica de cultivo, órgano, enfermedad, plaga y estado.
RF-09
Debe convertir anotaciones COCO, YOLO y máscaras a un esquema interno común.
RF-10
Debe permitir splits 70/15/15 por defecto y reglas específicas por dataset.
RF-11
Debe entrenar al menos clasificación y detección; segmentación debe ser soportada para los datasets correspondientes.
RF-12
Debe producir métricas por clase, cultivo, dataset de origen y dominio campo/laboratorio.
RF-13
Debe tener un umbral de abstención y activar fallback cuando el modelo no sea aplicable o no tenga confianza suficiente.
RF-14
Debe generar un reporte HTML/JSON/CSV del entrenamiento.
RF-15
Debe empaquetar el modelo con versión, hash, configuración e información de datasets usados.

10. Requerimientos no funcionales
ID
Requisito
RNF-01 Seguridad
No guardar tokens de Kaggle/HF/Roboflow en el repositorio; usar variables de entorno o secret manager.
RNF-02 Reproducibilidad
Toda corrida debe poder reconstruirse con config + versión de código + hashes.
RNF-03 Observabilidad
Logs estructurados JSON, métricas por etapa y trazabilidad de errores.
RNF-04 Rendimiento
Inferencia CPU debe ser objetivo para un modelo ligero; benchmark explícito antes de elegir producción.
RNF-05 Escalabilidad
Separar ingestión, curación y entrenamiento para ejecutar local, CI o GPU remota.
RNF-06 Calidad
Fallar rápido ante datos corruptos, labels inválidos o mismatch imagen/anotación.
RNF-07 Auditoría
Conservar dataset card, license evidence y manifest del artefacto del modelo.

11. Pipeline de datos detallado
Etapa
Especificación
11.1 Discover
Validar que la URL responde, resolver DOI, registrar versión, licencia y tipo de descarga.
11.2 Download
Guardar original intacto. Usar archivo temporal .part, checksum SHA-256 y reintentos exponenciales.
11.3 Inspect
Pillow/OpenCV para JPEG/PNG/TIF; tifffile/rasterio para multispectral; pycocotools para COCO.
11.4 Dedup
Primero exactos por SHA-256; después similares por pHash con umbral configurable. Nunca borrar físicamente del raw.
11.5 Normalize
Convertir a RGB para modelos RGB; preservar TIF multiespectral 16-bit aparte; normalizar dimensiones del entrenamiento.
11.6 Labels
Crear class_map canónico: crop, plant_part, health_state, disease, pest, severity.
11.7 Augmentation
Aplicar durante training, no escribir aumentaciones en raw; rotación, crop, brillo/contraste, blur/ruido, perspectiva.
11.8 Split
Group-aware split por leaf_id/plant_id/farm/source_url según disponibilidad.
11.9 Balance
Usar class weights o sampling; evitar sobre-repetir imágenes sintéticas o aumentadas.

12. Taxonomía canónica propuesta
La taxonomía debe desacoplar el nombre original del dataset de la etiqueta utilizada por el modelo. Ejemplo:
crop:
  coffee
  cacao
  banana
  plantain
  potato
  tomato
  avocado
  maize
  other

plant_part:
  leaf
  pod
  fruit
  stem
  whole_plant

health_state:
  healthy
  symptomatic
  unknown

severity:
  none
  mild
  moderate
  severe
  critical
  unknown

diagnostic_class:
  coffee_rust
  coffee_phoma
  coffee_cercospora
  coffee_miner
  red_spider_mite
  cocoa_monilia_m1
  cocoa_monilia_m2
  cocoa_monilia_m3
  cocoa_black_pod
  cocoa_phytophthora
  other_disease
  other_pest
13. Arquitectura de modelos
Se recomienda una estrategia jerárquica: (1) quality gate; (2) identificación de cultivo/órgano; (3) modelo especializado de enfermedad o plaga; (4) estimación de severidad; (5) motor agronómico contextual.
Componente
Objetivo
Quality Gate
Blur, exposición, tamaño mínimo, presencia de planta/órgano.
Crop Classifier
Identifica café/cacao/etc. y reduce clases posibles.
Disease/Pest Classifier
EfficientNet-B0/MobileNetV3 u otra arquitectura ligera validada.
Object Detector
YOLO/RT-DETR para plagas o lesiones cuando existen bounding boxes.
Segmentation
U-Net/DeepLabV3+/SegFormer o modelo equivalente para área afectada.
Severity
Modelo ordinal/regresión con área afectada y/o clases M1-M3.
Context Engine
Combina visión con GPS, clima, suelo y temporalidad; no reetiqueta visualmente sin evidencia.

14. Fallback OpenCV para el punto 3.1
Mientras se entrena el modelo, el sistema debe proporcionar un resultado preliminar. No debe presentarlo como diagnóstico definitivo.
Regla
Implementación
Segmentación HSV
Detectar región foliar y separar fondo.
Clorosis
Medir proporción de píxeles amarillos sobre el área verde.
Necrosis/manchas
Detectar regiones marrón/oscuro con operaciones morfológicas y contornos.
Textura
GLCM/LBP para caracterizar rugosidad y heterogeneidad.
Área afectada
Aproximar porcentaje del órgano con lesión.
Score
Combinar características con reglas parametrizadas y devolver confidence_visual.

Contrato de salida sugerido: {"status":"preliminary","diagnosis":"coffee_rust_compatible","confidence":0.72,"evidence":["orange-brown lesions","leaf area affected 11%"],"requires_review":true}.
15. Estrategia de entrenamiento
Etapa
Fuentes / objetivo
Etapa A - Base
PlantVillage + AgriPath: aprender representaciones generales de enfermedad.
Etapa B - Campo
PlantDoc + PlantWild/PlantSeg: adaptación a fondos y condiciones in-the-wild.
Etapa C - Café
DS01 + DS03 + DS04 + DS05 + DS06 + DS15: especializar café.
Etapa D - Cacao
DS02 + DS13 + DS14: especializar cacao.
Etapa E - Colombia
AGROSAVIA + ICA/SISFITO + datos propios consentidos: contexto y evaluación colombiana.
Etapa F - Hard cases
Recolectar fallos reales del producto y entrenar una ronda de hard-negative mining.

16. Splitting y prevención de data leakage
La unidad de partición recomendada es un grupo biológico o de captura, no una imagen. Prioridad: farm_id > plant_id > leaf_id > source_url > dataset_id. Cuando no exista metadata de grupo, aplicar al menos perceptual hashing antes de separar. Los datos aumentados deben derivarse después del split.
Split por defecto: train 70%, validation 15%, test 15%. Para datasets que ya traen splits oficiales, conservarlos y registrar la regla.
17. Métricas y criterios de aceptación
Tarea
Métricas obligatorias
Clasificación
Macro-F1, balanced accuracy, precision/recall por clase, matriz de confusión.
Detección
mAP50, mAP50-95, precision/recall por clase.
Segmentación
mIoU, Dice/F1, área relativa de lesión.
Calibración
ECE/Brier y curva de reliability.
Seguridad
False negative rate de enfermedades prioritarias.
Campo
Resultados separados para imágenes de campo y laboratorio.

Criterios iniciales sugeridos, sujetos a validación por cultivo: macro-F1 >= 0.90 en clases maduras del test; recall >= 0.95 para enfermedades prioritarias; ECE <= 0.05; y tasa de abstención controlada. No publicar métricas de producción basadas únicamente en PlantVillage.
18. Contrato de inferencia
POST /api/v1/vision/diagnose
Request:
{
  "image_uri": "...",
  "crop_hint": "coffee",
  "location": {"lat": 4.5, "lon": -75.7},
  "capture_timestamp": "2026-08-28T10:00:00-05:00"
}

Response:
{
  "model_version": "coffee-vision-1.0.0",
  "status": "model" | "fallback" | "abstain",
  "crop": {"label":"coffee","confidence":0.99},
  "diagnosis": {"label":"coffee_rust","confidence":0.93},
  "severity": {"label":"moderate","confidence":0.81},
  "evidence": [{"type":"lesion_mask","uri":"..."}],
  "recommend_review": true,
  "dataset_lineage": ["DS01","DS05","DS06"]
}
19. MLOps y versionado
Git para código y configuración.
DVC o equivalente para datasets grandes y artefactos.
MLflow o equivalente para experimentos y métricas.
Model Registry para promover candidate -> staging -> production.
Artifact manifest con dataset IDs, versiones, hashes, git commit y parámetros de entrenamiento.
Docker para entorno reproducible de entrenamiento/inferencia.
20. Seguridad y cumplimiento
No incorporar una fuente al entrenamiento productivo solo porque sea públicamente accesible. Se debe registrar y revisar la licencia, especialmente para fuentes CC BY-NC-ND, academic-only o datasets agregados de terceros. IP102, por ejemplo, declara acceso gratuito para uso académico y solicita contacto para otros usos. PlantWild v2 usa CC BY-NC-ND 4.0, mientras que PlantSeg declara CC BY-NC 4.0.
La plataforma debe tratar el resultado de visión como apoyo a la decisión. La respuesta de usuario debe distinguir entre diagnóstico confirmado, compatible/preliminar y abstención.
21. CI/CD del pipeline
Evento
Acción
PR
Lint + unit tests + schema tests + pruebas de conversión de labels.
Nightly
Check de disponibilidad de URLs y cambios de metadata/licencia.
Data build
Download -> inspect -> dedup -> normalize -> split -> dataset manifest.
Training job
Entrenamiento reproducible con configuración versionada.
Evaluation gate
No publicar modelo si no supera mínimos de métricas y test de leakage.
Release
Publicar model package + metrics + dataset manifest + changelog.

22. Casos de error y comportamiento esperado
Evento
Comportamiento
URL caída
Retry; si falla, marcar source_unavailable y no romper todo el pipeline.
Licencia no verificable
Quarantine; no promover a curated.
Imagen corrupta
Quarantine + registro.
Label desconocido
Mapear si existe alias; de lo contrario quarantine.
Duplicado
Conservar un master y registrar vínculo duplicate_of.
Confianza baja
Abstain y pedir nueva imagen/confirmación.
Modelo no disponible
Activar fallback OpenCV.
Cultivo no soportado
Respuesta controlled_unknown, nunca inventar enfermedad.

23. Backlog técnico de implementación
Sprint
Entrega
SPRINT 1
Repo + manifest + downloader + inspector + checksum + estructura datasets/.
SPRINT 2
Dedup + normalization + class map + conversion COCO/YOLO/masks.
SPRINT 3
Fallback OpenCV + quality gate + API de inferencia preliminar.
SPRINT 4
Pretraining PlantVillage/AgriPath + benchmark.
SPRINT 5
Fine-tuning café + validación de campo.
SPRINT 6
Fine-tuning cacao + detección/segmentación.
SPRINT 7
Evaluation gate + registry + Docker + observabilidad.
SPRINT 8
Integración con clima/suelo/GPS y motor agronómico.

24. Criterios de aceptación del punto 3.1
Una foto válida nunca termina en 'No determinada' simplemente porque el modelo de CNN aún no esté disponible; se utiliza fallback o abstención explicada.
El sistema identifica y registra el modelo exacto y su versión.
Existe un mecanismo de abstención cuando confidence < threshold.
El diagnóstico visual preliminar se marca explícitamente como preliminar/no confirmatorio.
Existe evidencia visual: máscara, región, porcentaje afectado o explicación de rasgos detectados.
El entrenamiento final incluye al menos una fuente colombiana de imágenes y una fuente de campo internacional.
Existe evaluación separada por origen/dataset y un test de no leakage.
25. Fuentes primarias consultadas
Fuente
URL
Colombian Coffee Tree Leaves Multispectral
https://pmc.ncbi.nlm.nih.gov/articles/PMC11927593/
CocoaMoniliaDataSet v2
https://zenodo.org/records/17716661
Uganda Coffee Leaf Disease
https://data.mendeley.com/datasets/k36wnd6knb/1
Saposoa Coffee Leaf
https://data.mendeley.com/datasets/mfpxg4y65r/1
JMuBEN
https://data.mendeley.com/datasets/t2r6rszp5c/1
RoCoLe
https://doi.org/10.17632/c5yvn32dzg.2
PlantVillage
https://huggingface.co/datasets/mohanty/PlantVillage
PlantVillageVQA
https://huggingface.co/datasets/SyedNazmusSakib/PlantVillageVQA
PlantDoc
https://github.com/pratikkayal/PlantDoc-Dataset
PlantWild v2
https://tqwei05.github.io/PlantWild/access_v2
PlantSeg
https://doi.org/10.5281/zenodo.17719108
IP102
https://github.com/xpwu95/IP102
Black Pod Rot Levels
https://www.kaggle.com/datasets/zaldyjr/black-pod-rot-levels
AgriPath-LF16
https://huggingface.co/datasets/hamzamooraj99/AgriPath-LF16
AGROSAVIA Datos Abiertos
https://www.agrosavia.co/nosotros/transparencia-y-acceso-a-informaci%C3%B3n-p%C3%BAblica/datos-abiertos
ICA SISFITO
https://sisfito.ica.gov.co/
SIOC Cacao
https://sioc.minagricultura.gov.co/Cacao/


Control de cambios: v1.0. Este documento debe actualizarse cada vez que cambie una URL, versión, licencia, taxonomía, arquitectura o criterio de producción.
