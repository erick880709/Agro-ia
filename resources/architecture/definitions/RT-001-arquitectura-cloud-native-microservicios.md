# RT-001: Arquitectura Cloud-Native basada en Microservicios

**Tipo:** Requisito técnico
**Categoría:** Arquitectura de software
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 7.1; instrucciones del cliente

## Descripción
La plataforma debe diseñarse siguiendo una arquitectura **cloud-native**, basada en **microservicios** y **orientada a eventos**, organizada en las siguientes capas lógicas:

1. **Capa de ingesta de datos** — recepción de datos de sensores IoT (humedad del suelo, pH, NPK) y de APIs externas (IDEAM, IGAC, satelitales).
2. **Capa de servicios de inferencia** — ejecución de los modelos de IA sobre las variables recibidas, con APIs REST para consulta síncrona y procesamiento asíncrono para análisis batch.
3. **Capa de gestión y monitorización** — control del rendimiento del sistema, salud de servicios, métricas de negocio y del modelo (ML observability).
4. **Capa de persistencia** — almacenamiento transaccional (PostgreSQL), geoespacial (PostGIS), de objetos (S3), vectorial (RAG) y de series temporales (datos de sensores).
5. **Capa de seguridad y gobierno** — transversal: autenticación, autorización, cifrado, auditoría, VPC.

## Criterio medible / restricción concreta
- Cada capa debe estar desacoplada de las demás, comunicándose mediante APIs bien definidas o mensajería asíncrona.
- Los microservicios deben ser independientes en su despliegue (cada uno puede actualizarse sin afectar a los demás).
- La arquitectura orientada a eventos debe usar un broker de mensajería para la ingesta IoT y la comunicación asíncrona entre servicios.

## Impacto en la arquitectura
- Define la estructura completa del sistema y la separación de responsabilidades.
- Requiere API Gateway como punto de entrada único.
- Necesita un bus de eventos/mensajería (RabbitMQ, Kafka, AWS SQS/SNS).
- Cada microservicio tiene su propio pipeline CI/CD.

## Notas del analista
- La arquitectura de microservicios es adecuada para este proyecto dado que tiene dominios claramente diferenciados (usuarios, fincas, IoT, IA, reportes) y necesidades de escalado independiente (la inferencia de IA escala distinto que el CRUD de usuarios).
- Para el MVP, se recomienda empezar con un número reducido de microservicios (4–6) y no sobre-ingenierizar la separación. Los bounded contexts se pueden refinar en fases posteriores.
- El patrón orientado a eventos es particularmente útil para la ingesta de datos de sensores (publicar mediciones) y la generación asíncrona de reportes/análisis.
