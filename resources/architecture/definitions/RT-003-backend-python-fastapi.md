# RT-003: Stack Backend — Python (FastAPI/Flask)

**Tipo:** Requisito técnico
**Categoría:** Stack tecnológico / Backend
**Fuente:** Instrucción directa del cliente (sobrescribe RFP original que sugería .NET 8)

## Descripción
El backend de la plataforma debe desarrollarse en **Python**, utilizando frameworks modernos de API REST. Este requisito es vinculante y fue definido explícitamente por el cliente, sobrescribiendo la recomendación original del RFP que mencionaba .NET 8.

Se recomienda **FastAPI** como framework principal por su:
- Alto rendimiento (basado en Starlette y Uvicorn).
- Tipado estático con Pydantic para validación de datos.
- Documentación automática de API con Swagger/OpenAPI.
- Soporte nativo para async/await (útil para llamadas a APIs externas como IDEAM).
- Buena integración con el ecosistema Python de ML/IA.

Flask puede usarse para microservicios más simples. La combinación de ambos es viable según la complejidad de cada servicio.

## Criterio medible / restricción concreta
- Python 3.11+ como versión mínima del runtime.
- FastAPI como framework principal para APIs REST.
- Pydantic v2 para validación de esquemas de datos.
- SQLAlchemy 2.0+ como ORM para PostgreSQL.
- Alembic para migraciones de base de datos.
- Tests unitarios con pytest, cobertura > 80%.
- Contenedores Docker con imágenes Python slim para producción.

## Impacto en la arquitectura
- Unifica el stack de backend con el de modelos de IA (todo en Python), simplificando el desarrollo y el despliegue.
- FastAPI expone los modelos de IA como servicios REST de forma nativa.
- La async/await de FastAPI permite manejar eficientemente múltiples conexiones IoT simultáneas.
- El ecosistema Python (pandas, numpy) es ideal para el procesamiento de datos agronómicos.

## Notas del analista
- La unificación del backend y los modelos de IA en Python es una ventaja significativa: reduce la fricción entre equipos, simplifica el CI/CD y permite compartir código de procesamiento de datos.
- FastAPI ha ganado amplia adopción en proyectos de ML Engineering por su facilidad para exponer modelos como APIs.
- Para tareas asíncronas (generación de reportes, ingesta batch de datos), Celery con Redis como broker es la combinación estándar en el ecosistema Python.
