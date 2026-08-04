# 🌱 AgroIA — AgroInteligente Colombia

Plataforma inteligente de diagnóstico agronómico basada en IA, IoT y datos geoespaciales para el mercado agrícola colombiano.

> **Versión:** 0.1.0 | **Stack:** Python 3.11+ / FastAPI · Angular 21 · PostgreSQL+PostGIS+pgvector · AWS EKS

---

## 🚀 Puesta en marcha local

### Requisitos

- **Python 3.11+** + **Poetry 1.8+**
- **Node.js 20+** + **npm 10+**
- **Docker** + **Docker Compose** (para PostgreSQL, Redis, RabbitMQ)

### 1. Clonar e instalar dependencias

```bash
git clone <repo-url> && cd Agro-ia
cp .env.example .env   # Ajustar variables si es necesario

# Infraestructura (PostgreSQL, Redis, RabbitMQ)
docker compose up -d postgres redis rabbitmq

# Backend — Paquete compartido
cd apps/shared && poetry install && cd ../..

# Backend — Servicio principal
cd apps/backend && poetry install && cd ../..

# Backend — Servicios adicionales (opcional en desarrollo local)
cd apps/auth && poetry install && cd ../..
cd apps/ml && poetry install && cd ../..
cd apps/rag && poetry install && cd ../..
cd apps/iot && poetry install && cd ../..

# Frontend
cd apps/frontend && npm install && cd ../..
```

### 2. Ejecutar

```bash
# Backend principal (puerto 8000)
cd apps/backend && poetry run uvicorn agroia_backend.main:app --reload --port 8000

# Frontend (puerto 4200)
cd apps/frontend && npm start
```

### 3. Verificar

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Swagger UI (solo desarrollo)
open http://localhost:8000/docs
```

### 4. Tests

```bash
cd apps/backend && poetry run pytest
```

### 5. Infraestructura completa con Docker

```bash
docker compose up -d   # Levanta todos los servicios
docker compose down    # Detener
```

---

## 📁 Estructura del repositorio

```
Agro-ia/
├── apps/                          # Código fuente (monorepo)
│   ├── shared/                    # Paquete Python compartido
│   │   └── agroia/               # config, errors, logging, database, health
│   ├── backend/                   # Servicio principal de negocio
│   │   └── agroia_backend/       # FastAPI — recomendaciones, catálogo, dashboards
│   ├── auth/                      # Auth Service — JWT + OAuth2 + RBAC
│   ├── ml/                        # ML Inference — scikit-learn, XGBoost, MLflow
│   ├── rag/                       # RAG Agent — OpenAI GPT-4 + pgvector
│   ├── iot/                       # IoT Ingestion — RabbitMQ consumer
│   └── frontend/                  # SPA Angular 21
├── resources/                     # Documentos vivos de arquitectura y diseño
│   ├── architecture/              # overview, stack, ADRs, diagramas
│   ├── design/                    # data-model, api.md, openapi.yaml
│   └── functional/                # requerimientos, specs refinadas, historias
├── docker/                        # Scripts de inicialización
├── docker-compose.yml             # Stack local completo
├── .env.example                   # Variables de entorno de referencia
└── graphify-out/                  # Knowledge graph del proyecto
```

---

## 🧠 Arquitectura

Ver [`resources/architecture/Documento_Arquitectura_AgroIA.md`](resources/architecture/Documento_Arquitectura_AgroIA.md) para el documento completo con diagramas C4, ADRs y vistas de despliegue.

Ver [`resources/architecture/AgroIA-Arquitectura-C4.drawio`](resources/architecture/AgroIA-Arquitectura-C4.drawio) para los diagramas editables (6 pestañas: C1-C3 + 3 secuencias).

---

## 🔧 Desarrollo

### Convenciones de código

- **Python:** type hints obligatorios, docstrings en español, ruff para linting
- **TypeScript:** strict mode, standalone components (Angular 21)
- **Commits:** conventional commits (`feat:`, `fix:`, `docs:`, `chore:`)
- **Ramas:** `feature/*`, `fix/*`, `docs/*`

### Scripts útiles

```bash
# Actualizar knowledge graph
python -m graphify update . --force

# Regenerar vault de Obsidian
python scripts/graphify2obsidian.py

# Linting
cd apps/backend && poetry run ruff check .
```

---

> **Generado por `genesis` el 2026-08-04 a partir de `Documento_Arquitectura_AgroIA.md`.**
> El repositorio está listo — la siguiente historia de usuario ya puede generarse con `builder`.
