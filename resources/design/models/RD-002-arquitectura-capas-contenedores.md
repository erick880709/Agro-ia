# RD-002: Arquitectura en Capas — Vista de Contenedores

**Tipo:** Información de diseño
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 7.1; contextAgro.md (Visión)

## Descripción
La plataforma se organiza en una arquitectura de 5 capas lógicas, que sirven como guía para la descomposición en contenedores (nivel C4 — Contenedores):

### Capa 1: Ingesta de Datos
- **IoT Ingestion Service:** recibe datos de sensores vía LoRaWAN → message broker.
- **External API Connectors:** conectores para IDEAM (clima), IGAC (suelos), Copernicus (NDVI), Google Maps (geolocalización). Cada conector es un microservicio independiente.
- **Message Broker:** RabbitMQ/Kafka para desacoplar ingesta de procesamiento.

### Capa 2: Servicios de Inferencia
- **Model Serving API (FastAPI):** expone cada uno de los 6 modelos de IA como endpoints REST.
- **Inference Worker (Celery):** procesamiento asíncrono para análisis batch y generación de reportes.
- **Recommendation Engine:** combina salidas de modelos ML con reglas del sistema experto para generar la recomendación final.

### Capa 3: Gestión y Monitorización
- **Admin Service:** CRUD de usuarios, membresías, cultivos, reglas agronómicas.
- **Monitoring Dashboard:** Grafana/Prometheus para métricas técnicas y de modelo.
- **Alerting Service:** evalúa condiciones de alerta (sensor offline, modelo degradado) y dispara notificaciones.

### Capa 4: Persistencia
- **PostgreSQL + PostGIS:** datos transaccionales y geoespaciales.
- **TimescaleDB** (opcional): series temporales de sensores.
- **Vector Database (pgvector/Qdrant):** embeddings para el RAG.
- **Object Storage (S3/MinIO):** datasets, modelos, reportes PDF, documentos RAG.

### Capa 5: Seguridad y Gobierno (transversal)
- **API Gateway:** punto de entrada único, autenticación JWT, rate limiting.
- **Auth Service:** emisión y validación de tokens.
- **Audit Logger:** registro de operaciones relevantes para seguridad.
- **Vault/Secrets Manager:** gestión de credenciales.

## Elementos de referencia
- Esta vista de contenedores debe detallarse en un diagrama C4-Containers durante la fase de arquitectura.
- Cada contenedor es una aplicación desplegable independientemente (Docker + Kubernetes).

## Notas del analista
- La separación en 5 capas es una guía lógica, no implica que cada capa sea un microservicio separado. Durante el diseño detallado se definirán los bounded contexts y el granularidad de los servicios.
- La capa de seguridad es transversal: todos los servicios deben implementar sus hooks de autenticación, autorización y auditoría.
