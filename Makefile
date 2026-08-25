# AgroIA Makefile — comandos de desarrollo local
# Uso: make <target>  o  nmake <target> (Windows)

.PHONY: help install migrate test lint run clean docker-up docker-down

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Dependencias ──

install: ## Instala todas las dependencias del monorepo
	cd apps/shared && poetry install
	cd apps/backend && poetry install
	cd apps/auth && poetry install
	cd apps/ml && poetry install
	cd apps/rag && poetry install
	cd apps/iot && poetry install

# ── Base de datos ──

migrate: ## Ejecuta migraciones Alembic
	cd apps/backend && poetry run alembic upgrade head

migrate-create: ## Crea nueva migración (usa MSG="descripcion")
	cd apps/backend && poetry run alembic revision --autogenerate -m "$(MSG)"

# ── Tests ──

test: ## Ejecuta todos los tests
	cd apps/backend && poetry run pytest tests/ -v

test-cov: ## Tests con cobertura
	cd apps/backend && poetry run pytest tests/ -v --cov=agroia_backend --cov-report=html

# ── Lint ──

lint: ## Ejecuta linting en todo el proyecto
	cd apps/shared && poetry run ruff check .
	cd apps/backend && poetry run ruff check .
	cd apps/auth && poetry run ruff check .
	cd apps/ml && poetry run ruff check .
	cd apps/rag && poetry run ruff check .
	cd apps/iot && poetry run ruff check .

format: ## Formatea código automáticamente
	cd apps/shared && poetry run ruff check --fix .
	cd apps/backend && poetry run ruff check --fix .

# ── Ejecutar ──

run-backend: ## Inicia el backend (puerto 8000)
	cd apps/backend && poetry run uvicorn agroia_backend.main:app --reload --port 8000

run-auth: ## Inicia auth service (puerto 8001)
	cd apps/auth && poetry run uvicorn agroia_auth.main:app --reload --port 8001

run-ml: ## Inicia ML service (puerto 8002)
	cd apps/ml && poetry run uvicorn agroia_ml.main:app --reload --port 8002

run-rag: ## Inicia RAG service (puerto 8003)
	cd apps/rag && poetry run uvicorn agroia_rag.main:app --reload --port 8003

run-iot: ## Inicia IoT service (puerto 8004)
	cd apps/iot && poetry run uvicorn agroia_iot.main:app --reload --port 8004

# ── Docker ──

docker-up: ## Levanta infraestructura local (PostgreSQL + Redis + RabbitMQ)
	docker compose up -d postgres redis rabbitmq

docker-down: ## Detiene infraestructura local
	docker compose down

docker-up-all: ## Levanta todos los servicios
	docker compose up -d --build

# ── ML ──

train-baseline: ## Entrena modelo baseline con datasets Kaggle
	cd apps/ml && poetry run python -m agroia_ml.models.train_baseline

mlflow: ## Inicia MLflow tracking server
	docker compose -f apps/ml/docker-compose.mlflow.yml up -d

# ── Utilidades ──

clean: ## Limpia archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

graph-update: ## Actualiza el knowledge graph
	python -m graphify update . --force

obsidian-update: ## Regenera el vault de Obsidian
	python scripts/graphify2obsidian.py

seed: ## Carga datos semilla (cultivos)
	cd apps/backend && poetry run python -m agroia_backend.seeds.cultivos

seed-reglas: ## Carga reglas agronómicas del sistema experto (UC1+UC2)
	cd apps/backend && poetry run python ../../load_seeds.py
