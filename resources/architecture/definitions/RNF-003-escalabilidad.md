# RNF-003: Escalabilidad

**Tipo:** Requerimiento no funcional
**Categoría:** Escalabilidad
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 6.2

## Descripción
La plataforma debe diseñarse con una arquitectura cloud-native que escale horizontalmente para soportar el crecimiento en número de usuarios, fincas, sensores y análisis. En particular:

- Soportar miles de usuarios concurrentes en producción.
- Escalado automático de los servicios de inferencia de IA en función de la carga de solicitudes.
- Capacidad de incorporar nuevos sensores IoT y fuentes de datos sin degradación del rendimiento.

## Criterio medible / restricción concreta
- La arquitectura debe permitir escalar horizontalmente añadiendo más instancias (no solo aumentando recursos de una instancia).
- Los servicios de inferencia deben tener auto-scaling configurado basado en CPU/memoria o profundidad de cola.
- No especificados en el RFP — definir: ¿métrica concreta de "miles de usuarios" (1,000? 10,000? 100,000?) y ¿ventana de tiempo (concurrentes? diarios?).

## Impacto en la arquitectura
- Kubernetes como orquestador (HPA — Horizontal Pod Autoscaler).
- Desacoplamiento de servicios mediante colas de mensajes (ingesta IoT, generación de reportes, inferencia batch).
- Base de datos con read replicas para consultas de dashboard.
- Servicios de inferencia stateless para escalar sin estado compartido.
- Uso de caché distribuida (Redis/ElastiCache) para reducir carga en base de datos.

## Notas del analista
- "Miles de usuarios concurrentes" es ambiguo. Para el mercado agrícola colombiano, una estimación realista podría ser 5,000–10,000 usuarios registrados con 500–1,000 concurrentes en hora pico. Se recomienda definir esto con el cliente.
- El cuello de botella más probable será la inferencia de modelos de IA bajo carga. Se recomienda usar procesamiento asíncrono con colas para los análisis que no requieran respuesta inmediata.
