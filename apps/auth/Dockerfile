FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry==1.8.4
COPY apps/shared/ /app/apps/shared/
COPY apps/auth/ /app/apps/auth/
WORKDIR /app/apps/shared
RUN poetry install --no-interaction --no-ansi --no-root
WORKDIR /app/apps/auth
RUN poetry install --no-interaction --no-ansi --no-root
COPY .env.example /app/.env
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/api/v1/health || exit 1
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "agroia_auth.main:app", "--host", "0.0.0.0", "--port", "8000"]
