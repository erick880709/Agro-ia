# 🌱 AgroIA — AgroInteligente Colombia

Plataforma inteligente de diagnóstico agronómico basada en IA, IoT y datos geoespaciales para el mercado agrícola colombiano.

> **Versión:** 0.2.0 (2026-08-31) | **Stack:** Python 3.11+ / FastAPI · **SPA web integrada** (`apps/frontend-web`, productiva) + Angular 21 (`apps/frontend`, prototipo) · PostgreSQL 15 (+pgvector) · Docker
> **Estado:** ✅ en producción — https://agroia-backend.onrender.com (Render + Neon) · CI verde · 65 pruebas backend

## 🔑 Credenciales de demostración (producción)

| Rol | Email | Contraseña |
|-----|-------|------------|
| Administrador | admin@agroia.co | Admin123! |
| Agrónomo | agronomo@agroia.co | Agronomo123! |
| Cliente | cliente@agroia.co | Cliente123! |

**Set demo:** `POST /api/v1/demo/reset` (Admin) — 8 fincas (2 ejemplos completos + 6 por etapa fenológica), 8 comisiones, precios de insumos/cosecha y lecturas del sensor real `esp32-npk-001`.

**Documentación de estado:** `PROJECT_STATUS.md` (bitácora completa por fecha) · `resources/architecture/Documento_Funcional_Tecnico_AgroIA.md` (fuente de verdad funcional-técnica) · `resources/architecture/` (arquitectura C4, datasets, pantallas).

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
# Backend principal (puerto 8000) — sirve la SPA en /
cd apps/backend && poetry run uvicorn agroia_backend.main:app --reload --port 8000

# Frontend SPA productivo: se sirve desde el backend (no requiere servidor aparte)
# Prototipo Angular (opcional): cd apps/frontend && npm start
```

### 3. Verificar

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Swagger UI (solo desarrollo)
open http://localhost:8000/docs

# Pruebas backend (venv de la raíz)
$env:PYTHONPATH="$PWD\apps\backend;$PWD\apps\shared;$PWD"
.venv\Scripts\python.exe -m pytest apps\backend\tests -q
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
