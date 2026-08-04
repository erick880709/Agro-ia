# AgroIA — Estado del Proyecto

> **Fecha:** 2026-08-04 | **Versión:** 0.1.0 | **Pipeline:** janus → epicureo → archi → genesis → builder

## 🎯 Objetivo

Plataforma inteligente de diagnóstico agronómico para Colombia. Determina la aptitud del suelo para cultivos usando IA, IoT y datos geoespaciales.

## 📊 Estado por épica

| Épica | Estado | Endpoints | Archivos |
|-------|--------|-----------|----------|
| 001 - Motor Recomendaciones | ✅ | POST /analyze, GET /historial | 19 |
| 002 - Catálogo Cultivos | ✅ | 7 CRUD + flujo publicación | 8 |
| 003 - Ingesta IoT | ✅ | 3 ingest + status + enrich | 4 |
| 004 - Seguridad | ✅ | 4 auth + RBAC + RLS | 7 |
| 005 - Dashboards | ✅ | 4 dashboard + PDF + export | 3 |
| 006 - Agente RAG | ✅ | 3 chat + index + health | 4 |
| 007 - Infra DevOps | ✅ | CI/CD + Makefile + check | 3 |
| 008 - Usuarios | ✅ | 6 usuarios + membresías | 3 |
| 009 - Cierre | ✅ | Integración + resumen | 2 |

## 🏗️ Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+ / FastAPI + SQLAlchemy + Alembic |
| Auth | JWT + OAuth2 + RBAC 4 roles + RLS |
| ML | scikit-learn + XGBoost + MLflow + pgvector |
| RAG | OpenAI GPT-4 + MiniLM embeddings |
| IoT | RabbitMQ + LoRaWAN consumer |
| DB | PostgreSQL 15 + PostGIS + pgvector + TimescaleDB |
| Cache | Redis |
| Frontend | Angular 21 (pendiente) |
| Infra | Docker + GitHub Actions |

## 📁 Estructura

```
Agro-ia/
├── apps/
│   ├── shared/         Paquete Python compartido (config, db, errors)
│   ├── backend/        Servicio principal (API REST)
│   ├── auth/           Auth Service (JWT, RBAC)
│   ├── ml/             ML Inference + entrenamiento
│   ├── rag/            Agente conversacional RAG
│   ├── iot/            IoT Ingestion (RabbitMQ)
│   └── frontend/       Angular 21 SPA (pendiente)
├── resources/          Documentos vivos (arquitectura, diseño, funcional)
├── datasets/           Datasets Kaggle para cold-start ML
├── docker-compose.yml  Stack local completo
├── Makefile            20+ comandos de desarrollo
└── README.md
```

## 🚀 Arranque rápido

```bash
cp .env.example .env
make docker-up              # PostgreSQL + Redis + RabbitMQ
make install                # Instalar dependencias
make migrate                # Crear tablas
make run-backend            # Backend en :8000
make mlflow                 # MLflow en :5000
make train-baseline         # Entrenar modelo baseline
curl localhost:8000/api/v1/health
```

## ⬜ Pendiente

- [ ] Frontend Angular 21 (6 pantallas HU-01 a HU-06)
- [ ] Despliegue en AWS EKS (post-MVP)
- [ ] Pruebas de usabilidad con agricultores (mes 3 del piloto)
- [ ] Validación legal Cenicafé (licencia CC BY-NC-ND)
- [ ] Cobertura LoRaWAN en fincas piloto Quindío

---

> **Generado por el pipeline AgroIA:** janus (54 reqs) → epicureo (9 specs IA≤15) → archi (C4+6 ADRs) → genesis (scaffold) → builder (9 épicas)
