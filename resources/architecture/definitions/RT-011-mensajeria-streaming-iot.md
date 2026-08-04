# RT-011: Mensajería y Streaming para IoT

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / Integración
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 7.2

## Descripción
La plataforma debe contar con un sistema de mensajería o streaming para manejar la ingesta de datos desde sensores IoT de forma desacoplada y escalable. Este componente permite:

- Recibir datos de miles de sensores IoT publicando mediciones periódicas sin bloquear al emisor.
- Desacoplar la ingesta del procesamiento: los datos se publican en una cola/tópico y múltiples consumidores pueden procesarlos (almacenamiento, inferencia de modelos, generación de alertas).
- Garantizar la entrega de mensajes (al menos una vez) y manejar picos de carga sin pérdida de datos.

## Criterio medible / restricción concreta
- Throughput mínimo: capacidad de ingestar 10,000 mensajes/segundo (escalable).
- Persistencia de mensajes en caso de fallo de consumidores.
- No especificados en el RFP — definir: broker concreto (RabbitMQ para colas de tareas, Kafka para streaming de alto volumen, AWS SQS+SNS para solución gestionada).

## Impacto en la arquitectura
- Los sensores publican en un tópico/cola; los servicios de procesamiento consumen de él.
- Patrón pub/sub para notificar a múltiples servicios (ej. una medición nueva la consumen el almacenador, el motor de inferencia y el sistema de alertas).
- Permite escalar consumidores independientemente según la carga.

## Notas del analista
- Para el MVP con un número limitado de sensores (piloto Quindío), RabbitMQ es suficiente y más simple de operar que Kafka.
- Si la plataforma escala a miles de sensores a nivel nacional, Kafka es más adecuado por su capacidad de retención de mensajes, re-procesamiento histórico y alto throughput.
- AWS SQS + SNS es una alternativa gestionada que elimina la carga operativa de mantener un broker, aunque con menos funcionalidades que Kafka.
