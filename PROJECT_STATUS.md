# AgroIA — Estado del Proyecto

> **Fecha:** 2026-08-25 | **Versión:** 0.1.0 | **Pipeline:** janus → epicureo → archi → genesis → builder | **CI:** 🟢 verde | **Deploy:** Render blueprint listo (`render.yaml`)

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
| Frontend | **SPA web integrada** en `http://localhost:8000/` (`apps/frontend-web/`) + Angular 21 (`apps/frontend/`, mock, pendiente de conectar) |
| Infra | Docker + GitHub Actions |

## 🚀 Despliegue gratuito (Render + Neon/Supabase)

**Estado:** `render.yaml` (blueprint) listo en la raíz; CI en verde (Lint ✓, Tests ✓, Build Docker ✓).

### Pasos

1. Crear cuenta en [Render](https://render.com) (login con GitHub).
2. Crear Postgres gratis con pgvector en [Neon](https://neon.tech) o [Supabase](https://supabase.com) (ambos con tier gratuito permanente; el Postgres de Render solo es gratis 30 días).
3. En Render: **New + → Blueprint** → seleccionar `erick880709/Agro-ia` → pegar la URL de Neon en `DATABASE_URL` (formato `postgresql+asyncpg://...`).
4. El blueprint levanta el web service en plan **Free** ($0): Docker + migraciones automáticas (`alembic upgrade head`) + health check en `/api/v1/health`. Cada push a `master` redeploya automáticamente.

### Límites del tier gratuito (validados 2026-08-25)

| Servicio | Gratis | Notas |
|----------|--------|-------|
| Render Web Service Free | $0 | 512 MB RAM / 0.1 CPU; **se duerme tras ~15 min sin tráfico** (cold start ~1 min). Usar [UptimeRobot](https://uptimerobot.com) gratis para pinguear cada 10 min y mantenerlo despierto |
| Neon Postgres Free | $0 | 0.5 GB, scale-to-zero, pgvector ✓ |
| Supabase Postgres Free | $0 | 500 MB, pgvector ✓ (alternativa) |
| Render Redis Free | $0 | 25 MB — opcional: el backend funciona sin Redis |
| RabbitMQ | — | Sin tier gratuito viable; solo lo usa el servicio IoT (opcional) |

### Notas técnicas

- El backend sirve el frontend estático (`apps/frontend-web/`) en la raíz y escucha en `$PORT` (soportado en el Dockerfile).
- La app completa (IoT, ML, RAG, Redis, RabbitMQ) sigue disponible localmente vía `docker-compose.yml`.

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

- [ ] Conectar el frontend Angular 21 (`apps/frontend/`) a las APIs (hoy usa mock data)
- [ ] Despliegue en AWS EKS (post-MVP)
- [ ] Pruebas de usabilidad con agricultores (mes 3 del piloto)
- [ ] Validación legal Cenicafé (licencia CC BY-NC-ND)
- [ ] Cobertura LoRaWAN en fincas piloto Quindío

## 🧠 Motor de recomendaciones — Sistema Experto activo (2026-08-25)

Los 2 casos de uso del motor están operativos vía sistema experto determinístico
(reglas UPRA/Cenicafé/AGROSAVIA); el ML (baseline India) queda en modo sombra.

| Caso de uso | Implementación | Endpoint |
|-------------|----------------|----------|
| UC1: sin cultivo → ¿qué sembrar? | `AptitudService` puntúa cultivos con reglas y sugiere top-5 con ajustes | `POST /api/v1/recomendaciones/analyze` sin `cultivo_id` |
| UC2: con cultivo → ¿qué falta/sobra? | `RulesEngine` evalúa 23 reglas y devuelve DEFICIT/EXCESO + acción | `POST /api/v1/recomendaciones/analyze` con `cultivo_id` |

- Carga de conocimiento: `make seed-reglas` (23 reglas: 5 cultivos colombianos + universales).
- RNF-010: actualizar conocimiento sin reentrenar = editar reglas en BD.
- ML shadow mode: se cablea cuando existan datos colombianos etiquetados
  (el dataset AGROSAVIA actual es de forrajes, no sirve para aptitud de cultivos).

## 👥 Roles y permisos por finca (2026-08-25)

- **Administrador**: todas las funciones + registrar fincas + crear usuarios.
- **Agrónomo**: todas las funciones de análisis; no registra fincas ni crea usuarios.
- **Cliente** (solo lectura): ve únicamente los reportes de las fincas a las que
  fue asociado (`fincas_usuarios`); no carga archivos ni genera análisis.
- Acceso por finca aplicado en: `/fincas`, `/iot/lecturas`, `/iot/sensores/status`,
  `/recomendaciones/historial` y `/dashboard`.
- Usuarios demo: `admin@agroia.co`, `agronomo@agroia.co`, clientes con fincas asignadas.

## 📄 Reportes de análisis (2026-08-25)

- `POST /api/v1/reportes/generar` con tipo: **siembra** (UC1), **cultivo** (UC2) o **completo** (UC1+UC2).
- El reporte se genera como **HTML** (estilo informe de laboratorio) y se guarda como **PDF**
  desde el navegador (botón "Guardar PDF" integrado).
- Incluye la sección **"En palabras del campo"**: explicación en lenguaje campesino
  (qué significa cada medición y qué hacer en el terreno), con nota de honestidad
  sobre calibración y confianza.
- Datos de origen: tramas JSON del sensor (`POST /api/v1/iot/sensor`) o carga de archivo.
- Acceso por rol: cliente solo reportes de sus fincas.

---

> **Generado por el pipeline AgroIA:** janus (54 reqs) → epicureo (9 specs IA≤15) → archi (C4+6 ADRs) → genesis (scaffold) → builder (9 épicas)
