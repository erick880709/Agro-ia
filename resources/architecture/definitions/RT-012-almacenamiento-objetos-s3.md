# RT-012: Almacenamiento de Objetos (S3)

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / Persistencia
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 7.2

## Descripción
La plataforma debe contar con un servicio de almacenamiento de objetos para guardar:

- **Datasets:** archivos de datos para entrenamiento de modelos (CSV, Parquet, imágenes).
- **Modelos entrenados:** artefactos de MLflow (pickle, ONNX, joblib).
- **Reportes PDF generados:** reportes de análisis de suelo que los usuarios pueden descargar.
- **Base documental del RAG:** documentos PDF, HTML y Markdown que alimentan el índice vectorial del agente conversacional.
- **Fotografías de fincas:** imágenes subidas por los agricultores.
- **Archivos geoespaciales:** shapefiles del IGAC, rasters de NDVI.
- **Logs y backups:** almacenamiento a largo plazo de logs y copias de seguridad.

En AWS, el servicio correspondiente es S3 (Simple Storage Service).

## Criterio medible / restricción concreta
- Versionado de objetos habilitado para datasets y modelos.
- Cifrado en reposo (SSE-S3 o SSE-KMS).
- Políticas de ciclo de vida para mover objetos a almacenamiento de menor costo (S3 Glacier) tras un período configurable.
- No especificados en el RFP — definir: estructura de buckets (por entorno, por tipo de dato), política de retención de reportes antiguos.

## Impacto en la arquitectura
- S3 actúa como el lago de datos (data lake) de la plataforma, centralizando todos los archivos no estructurados.
- Los microservicios acceden a S3 mediante SDK de AWS (boto3 en Python) con credenciales IAM.
- Los reportes PDF se generan, se almacenan en S3 y se entregan a los usuarios mediante URLs prefirmadas (pre-signed URLs).
- Separación clara entre datos estructurados (PostgreSQL) y no estructurados (S3).

## Notas del analista
- Usar S3 como almacenamiento central simplifica la arquitectura: ningún microservicio necesita disco persistente; todo el estado está en PostgreSQL o S3.
- Las URLs prefirmadas permiten descargar reportes de forma segura sin exponer el bucket públicamente, y expiran automáticamente.
- Para el entorno de desarrollo local, MinIO es un reemplazo compatible con la API de S3 que permite desarrollar sin conexión a AWS.
