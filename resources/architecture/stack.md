# Stack Tecnológico — AgroIA

> Generado por `genesis` a partir de `Documento_Arquitectura_AgroIA.md`.
> Actualizar cuando cambie la versión de algún componente.

## Contenedores

| Contenedor | Lenguaje | Framework | ORM/Driver | Puerto |
|-----------|----------|-----------|------------|--------|
| **backend** | Python 3.11+ | FastAPI 0.115 | SQLAlchemy 2.0 (async) + asyncpg | 8000 |
| **auth** | Python 3.11+ | FastAPI 0.115 | SQLAlchemy 2.0 (async) | 8000 |
| **ml** | Python 3.11+ | FastAPI 0.115 | SQLAlchemy 2.0 (async) + gRPC | 8000 |
| **rag** | Python 3.11+ | FastAPI 0.115 | pgvector 0.3 | 8000 |
| **iot** | Python 3.11+ | FastAPI 0.115 | aio-pika 9.4 (RabbitMQ) | 8000 |
| **frontend** | JavaScript (SPA vanilla) | `apps/frontend-web` — servida por el backend en `/` (productiva) | — | — |
| **frontend (prototipo)** | TypeScript 5 | Angular 21 | — | 4200 |

> **Realidad productiva (2026-08-31):** el frontend que corre en producción
> es la **SPA web integrada** (`apps/frontend-web/`, vanilla JS + service
> worker PWA) servida por el propio backend; Angular (`apps/frontend`) es un
> prototipo parcial. Despliegue real en **Render Free + Neon Postgres**
> (auto-deploy en cada push a `master`, migraciones `alembic upgrade head`
> al arranque). AWS EKS/Terraform corresponde a la arquitectura objetivo
> (ver `Documento_Arquitectura_AgroIA.md`).

## Infraestructura

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Base de datos | PostgreSQL + PostGIS + pgvector | 15 |
| Caché | Redis | 7 |
| Mensajería | RabbitMQ | 3 (management) |
| Orquestación | AWS EKS | — |
| IaC | Terraform | — |
| CI/CD | GitHub Actions | — |
| Observabilidad | CloudWatch + X-Ray | — |
| MLOps | MLflow | 2.17 |

## Dependencias compartidas (apps/shared)

| Paquete | Versión | Uso |
|---------|---------|-----|
| fastapi | ^0.115 | Framework web |
| pydantic | ^2.0 | Validación de datos |
| sqlalchemy | ^2.0 | ORM asíncrono |
| asyncpg | ^0.30 | Driver PostgreSQL async |
| alembic | ^1.14 | Migraciones |
| redis | ^5.0 | Caché |
| python-jose | ^3.3 | JWT |
| passlib | ^1.7 | Hashing de passwords |
| structlog | ^24.0 | Logging estructurado |
| tenacity | ^9.0 | Retry/circuit breaker |
