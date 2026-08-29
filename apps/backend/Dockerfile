FROM python:3.11-slim

WORKDIR /app

# ── Instalar dependencias del sistema ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# ── Instalar Poetry ──
RUN pip install --no-cache-dir poetry==1.8.4

# ── Copiar dependencias ──
COPY apps/shared/pyproject.toml apps/shared/poetry.lock* /app/apps/shared/
COPY apps/shared/ /app/apps/shared/
COPY apps/backend/pyproject.toml apps/backend/poetry.lock* /app/apps/backend/

# ── Instalar dependencias del proyecto ──
WORKDIR /app/apps/shared
RUN poetry install --no-interaction --no-ansi --no-root

WORKDIR /app/apps/backend
RUN poetry install --no-interaction --no-ansi --no-root

# ── Copiar código fuente ──
COPY apps/ /app/apps/
COPY .env.example /app/.env
# Manifest del pipeline AgroVision (read-only) para /vision/admin/dataset-estado
COPY datasets/manifest /app/datasets/manifest

# ── Python path para que alembic/uvicorn encuentren agroia y agroia_backend ──
ENV PYTHONPATH="/app/apps/shared:/app/apps/backend:/app/apps/iot"
ENV AGROIA_DATASETS_DIR="/app/datasets"

# ── Health check ──
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f "http://localhost:${PORT:-8000}/api/v1/health" || exit 1

# ── Ejecutar: migraciones automáticas y luego la API ──
# (Render free tier no permite preDeployCommand, por eso las migraciones
#  corren aquí de forma idempotente en cada arranque).
EXPOSE 8000
CMD ["sh", "-c", "cd /app/apps/backend && poetry run alembic upgrade head && exec poetry run uvicorn agroia_backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
