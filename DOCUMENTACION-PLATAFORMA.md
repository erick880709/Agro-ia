# AgroIA — Documentación funcional y técnica (estado actual)

> Documento de referencia de **lo que la plataforma hace hoy**. Última actualización: 2026-11-03.
> Complementa (no reemplaza) los documentos de diseño de `resources/` y el catálogo funcional.

---

## 1. Resumen ejecutivo

**AgroIA (AgroInteligente Colombia)** es una plataforma de **diagnóstico agronómico inteligente** basada en IA, IoT y datos geoespaciales, orientada a la agricultura de precisión colombiana. El sistema:

1. **Registra fincas** georreferenciadas (polígonos, perímetro, área) y sus **lotes** productivos.
2. **Ingiere datos de sensores IoT de suelo** (ESP32 NPK 7-en-1), los valida con la **regla del sensor**, los enriquece con capas oficiales (SIG IGAC/UPRA) y los convierte en series temporales.
3. Ejecuta un **motor de recomendación agronómica** (sistema experto de reglas UPRA/Cenicafé/AGROSAVIA + ML en modo sombra) para clasificar aptitud de cultivos y emitir recomendaciones de fertilización/riego/sanidad **sin recetar dosis sin análisis de suelo**.
4. Ofrece un **asesor agronómico conversacional** con **entrada por voz** (RFP-001) y **lectura de respuestas en voz alta** con **voz personalizada clonable** (RFP-002).
5. Cubre el ciclo comercial **AGC-COST**: cotización → estimación de costos → comisión → recomendación → reporte, con **trazabilidad BPA** (Res. ICA 30021/2017).

**Producción:** backend en **Render** (https://agroia-backend.onrender.com), base de datos **Neon PostgreSQL**, CI/CD con GitHub Actions.

---

## 2. Arquitectura general

```
Clientes (navegador, PWA)
        │
        ▼
┌─────────────────────────────────────────────────┐
│  apps/frontend-web  — SPA vanilla JS (productiva) │  ← index.html + app.js/voz.js/lectura.js/costeo.js/offline.js
│  apps/frontend     — Angular 21 (prototipo)       │
└───────────────────┬─────────────────────────────┘
                    │ HTTPS /api/v1 (JWT Bearer)
                    ▼
┌─────────────────────────────────────────────────┐
│  apps/backend — FastAPI (agroia_backend)         │
│  42 routers · 50+ modelos · 60+ servicios        │
└──────┬──────────┬──────────┬──────────┬─────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
  PostgreSQL    auth       ml         rag         iot
  (Neon,       (JWT,      (MLflow,   (RAG chat   (consumer
  esquema      RLS)       modelos     vectorial)  RabbitMQ)
  "agroia")               .joblib)
```

- **Monolito modular**: el backend agrupa API + dominio + reglas en una sola app FastAPI; los servicios de infraestructura (auth, ML, RAG, IoT) están separados como contenedores con sus propios Dockerfiles.
- **Base de datos única** con esquema `agroia` y `search_path` explícito (crítico en Neon por los casts de enums de SQLAlchemy).

---

## 3. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11, FastAPI 0.115, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Base de datos | PostgreSQL 15+ (Neon), extensión pgvector, TimescaleDB (hipertabla para sensores), PostGIS |
| Frontend productivo | Vanilla JS (SPA sin framework), Leaflet (mapas), Service Worker (PWA/offline), Web Speech API (voz) |
| Frontend prototipo | Angular 21 (apps/frontend) |
| Servicios satélite | auth (JWT RS256/HS256), ml (scikit-learn + MLflow), rag (chat con recuperación), iot (consumidor) |
| Voz | Web Speech API (motor por defecto), OpenAI TTS (respaldo), Chatterbox Multilingual V3 (clonación, MIT) |
| CI/CD | GitHub Actions (lint ruff + tests pytest + build Docker) · Render auto-deploy desde `master` |
| Infra | Render (web free) + Neon (Postgres) + RabbitMQ (cola IoT) + Redis (caché) |

---

## 4. Componentes (`apps/`)

| Directorio | Rol |
|---|---|
| `backend/` | Aplicación principal FastAPI (`agroia_backend`): API, modelos, servicios, migraciones. |
| `frontend-web/` | SPA productiva en vanilla JS. |
| `frontend/` | Prototipo Angular 21 (no productivo). |
| `auth/` | Servicio de autenticación JWT + políticas RLS (`rls_policies.sql`). |
| `ml/` | Entrenamiento e inferencia ML (scikit-learn, MLflow, modelos `.joblib`). |
| `rag/` | Servicio RAG para el chat (recuperación vectorial). |
| `iot/` | Consumidor de mensajes del sensor (`consumer.py`), normalización y persistencia. |
| `voice-clone/` | Wrapper Docker de clonación de voz (Chatterbox Multilingual V3, contrato HTTP). |
| `shared/` | Paquete `agroia` compartido: config (pydantic-settings), database, logging, health, tenant. |
| `models/` | Artefactos de modelo serializados (`.pkl`). |

---

## 5. Base de datos (esquema `agroia`, 41 migraciones → head `049`)

### Entidades núcleo

| Tabla (modelo) | Descripción |
|---|---|
| `fincas` | Predio georreferenciado: GPS, altitud, geometría GeoJSON, área/perímetro calculados, tipo de área, multi-lote, riego, fenología. |
| `lotes` | Unidad productiva dentro de una finca: geometría, `area_ha`, `perimetro_m`, profundidad, pedregosidad, siembra/variedad. |
| `usuarios` | Cuentas por rol (Admin/Agrónomo/Cliente/Extensionista) con bcrypt. |
| `sensor_readings` | Series temporales del sensor (18 variables de suelo + ambiente), `pos_x/pos_y` (m), `calidad`, `sensor_id`. |
| `dispositivos_iot` | Registro de dispositivos (device_id → finca), calibración NPK, telemetría. |
| `cultivos` / `variedad_cultivo` | Catálogo agronómico (45 cultivos). |
| `reglas_agronomicas` | Reglas del sistema experto por cultivo (variable, umbrales, acción, prioridad, fuente). |
| `comision` / `estimaciones` / `cobros` | Ciclo comercial AGC-COST. |
| `recomendacion` / `aceptacion_recomendacion` | Recomendaciones emitidas y aceptación humana. |
| `checklist_bpa` / `checklist_bpa_visitas` | Trazabilidad BPA (Res. ICA 30021/2017). |
| `metrica_voz` / `parametro_voz` | Métricas y parámetros de la entrada por voz (RFP-001). |
| `preferencia_lectura_voz` / `metrica_lectura_voz` / `voz_personalizada` | Lectura en voz alta y voz clonada (RFP-002). |
| `analisis_laboratorio` / `analisis_agua_riego` | Resultados de laboratorio (prioridad sobre el sensor). |
| `alerta_climatica`, `monitoreo_plaga`, `labor`, `ciclo_lote`, `equipo_trabajo`, `novedad_equipo` | Soporte de clima, sanidad, labores y equipo. |
| `auditoria`, `token_auth`, `sync_registro` | Auditoría, refresh tokens, idempotencia offline. |

---

## 6. Módulos funcionales (lo que hace hoy)

### 6.1 Gestión de fincas y lotes
- Registro asistido (wizard 3 pasos): datos → **ubicación (GPS / mapa Leaflet / enlace Google Maps)** → características del suelo.
- **Georreferenciación**: dibujo del lindero con cálculo de **área y perímetro** (Gauss/Haversine). Desde 2026-11-03: **múltiples lotes**, cada uno dibujado por separado con su color, su propio **perímetro y área**, y persistido con geometría.
- Validación en cadena (departamento, municipio, coordenadas, área, precisión).
- Enriquecimiento **SIG** (IGAC/UPRA): precarga textura/MO/CIC oficiales con `calidad = estimado_por_sig` (el sensor gana si mide).

### 6.2 Sensores IoT (ingesta y calidad del dato)
- Ingesta por `POST /api/v1/sensor` y `/api/v1/iot/ingest`, y por el **consumidor** (`apps/iot`) desde RabbitMQ.
- Normalización de tramas, resolución de dispositivo→finca, conversión **GPS→metros relativos** al centroide.
- **Calibración NPK** (factores por dispositivo) y marcado `npk_no_calibrado`.
- **Regla del sensor (JXBS-3001-NPK-RS, 7 en 1)**: solo son válidas las lecturas dentro del rango objetivo — pH 3–9 (excluye saturación 9,0), CE 0,01–10 dS/m, NPK 1–1.999 mg/kg — y fuera de la coordenada por defecto del firmware. Las inválidas se marcan `calidad = invalidada` y quedan **excluidas de análisis y reportes**.
- Reparación de coordenadas históricas en grados (`reparacion_geo`).

### 6.3 Motor de recomendación agronómica
- **Sistema experto** (`rules_engine.py`): evalúa el suelo contra **reglas con fuente** (UPRA/Cenicafé/AGROSAVIA) por cultivo. Clasifica `Apta / Moderadamente apta / No apta`.
- **Orquestador** (`orchestrator.py`): pipeline completo — lectura de suelo, contexto de finca, laboratorio reciente (<90 días), advertencias de calidad, ML modo sombra, antagonismos, GDD (IDEAM), confianza con cobertura de datos y validación humana.
- **ML** (`ml_oracle.py`): modelos scikit-learn en **modo sombra**; variables con precisión real ≥ 0,85 **validan** las reglas (acuerdo/desacuerdo).
- `aptitud.py` (preselección climática/altitudinal) y `justification.py` (explicabilidad).

### 6.4 Reportes
- `POST /reportes/generar`: reporte HTML completo (suelo, mapa de calor, plano del lote con puntos de muestreo, recomendaciones, plan económico).
- Simulación de enmienda (`/reportes/simular`).
- Los reportes usan **solo lecturas válidas** (excluyen `invalidada` y `estimado_por_sig`).

### 6.5 Asesor conversacional + voz (RFP-001 y RFP-002)
- **Chat** (`agronomo_chat.py`): responde con el sistema experto (manejo de fechas, clima "llover", consultas conceptuales, ubicación), evita respuestas sin finca seleccionada y sin datos.
- **Entrada por voz** (`voz.js` + `/voz/*`): Web Speech API + transcripción en servidor (OpenAI), medidor de nivel, parámetros y métricas.
- **Lectura en voz alta** (`lectura.js` + `/lectura/*`): speechSynthesis por defecto, respaldo en servidor, preferencias por usuario, velocidad, métricas.
- **Voz personalizada** ("Mi voz"): grabación de muestra, consentimiento (Ley 1581/2012), clonación con **Chatterbox Multilingual V3** (adaptador `clonacion_voz.py` + wrapper `voice-clone`), estado `procesando→activa`.

### 6.6 AGC-COST (ciclo comercial)
- Cotización → **estimación de costos** (F2–F7) → emisión/aceptación → **comisión** → trabajo de campo → **recomendación** → **reporte**.
- Parámetros de costeo administrables, precios de insumos/cosecha, documentos de cobro.

### 6.7 Trazabilidad BPA
- Checklist de 11 ítems (Res. ICA 30021/2017) por finca, visitas de verificación con línea de tiempo, reporte de trazabilidad, períodos de carencia.

### 6.8 Sanidad, clima y catálogo
- **Visión de plagas** (`vision_engine.py`): diagnóstico por imagen con fallback.
- **Clima y alertas**: fases lunares, alertas climáticas (IDEAM), balance hídrico.
- **Catálogo**: 45 cultivos, variedades, curvas de extracción, compatibilidad de rotación.
- **Labores y ciclos**: registro de labores, ciclos del lote, monitoreo de plagas.

### 6.9 Administración y operación
- Usuarios y roles, auditoría completa, precios, equipo de trabajo, comisiones, lista de trabajos, reentrenamiento ML, parámetros/métricas de voz y lectura.
- **Offline/PWA**: manifest + service worker + sincronización (`/sync/*`, idempotencia).

---

## 7. API (resumen por router)

| Router (prefijo) | Propósito |
|---|---|
| `/auth` | Login (JWT), refresh, logout. |
| `/fincas` (+ `/lotes`) | CRUD de fincas y lotes, georreferenciación. |
| `/iot` + `/sensor` | Ingesta, lecturas, dispositivos, estado de sensores. |
| `/reportes` | Generar reporte HTML, simular enmienda. |
| `/recomendaciones` | Recomendaciones y aceptación. |
| `/comisiones`, `/estimaciones`, `/cobros`, `/costeo*` | Ciclo comercial AGC-COST. |
| `/voz`, `/lectura` | Entrada por voz y lectura en voz alta. |
| `/bpa` | Checklist, visitas, trazabilidad. |
| `/catalogo`, `/variedades`, `/curvas`, `/rotacion` | Catálogo agronómico. |
| `/plagas`, `/vision` | Sanidad y visión de plagas. |
| `/laboratorio`, `/agua_riego` | Análisis de laboratorio. |
| `/clima` (vía alertas/balance_hidrico), `/calendario` | Clima, fases lunares. |
| `/usuarios`, `/auditoria`, `/equipo`, `/lista_trabajos`, `/dashboard` | Administración. |
| `/sync` | Sincronización offline. |
| `/location`, `/sig` | Geocodificación, enriquecimiento SIG. |
| `/ml`, `/demo`, `/mantenimiento` | ML, demo reset, mantenimiento. |

> Contrato formal en `resources/design/openapi.yaml` (v0.6.0) y `resources/design/api.md`.

---

## 8. Seguridad

- **JWT** (HS256 o RS256 si hay claves PEM), access token 8 h + refresh token 30 días (hash persistido).
- **Roles**: Admin / Agrónomo / Extensionista / Cliente, con control de acceso por finca (`services/acceso.py`).
- **RLS** en PostgreSQL (políticas en `auth/sql/rls_policies.sql`).
- Auditoría de acciones sensibles con IP y user-agent.
- Encabezados legacy (`X-User-Role`/`X-User-Email`) solo fuera de producción.
- `search_path` fijado a `public, agroia` en cada conexión (evita casts de enum rotos en Neon).

---

## 9. Despliegue y CI/CD

- **Render Blueprint** (`render.yaml`): servicio `agroia-backend` (Docker), health check `/api/v1/health`, variables de entorno (DATABASE_URL, ENVIRONMENT, JWT_SECRET, CLONACION_VOZ_URL/TOKEN…).
- **Neon Postgres**: esquema `agroia`; la URL usa `postgresql+asyncpg://` con `ssl=require`.
- **GitHub Actions** (`.github/workflows/ci.yml`): lint (ruff) → tests (pytest con Postgres) → build Docker (backend/auth/ml/rag/iot).
- **Migraciones**: `alembic upgrade head` se ejecuta al arrancar el contenedor (head actual: `049_lote_perimetro`).
- **Voz clonada**: wrapper en `apps/voice-clone` desplegable en RunPod/HF Spaces; se conecta vía `CLONACION_VOZ_URL`/`CLONACION_VOZ_TOKEN`.

---

## 10. Estado de los RFP / épicas

| Épica | Alcance | Estado |
|---|---|---|
| **RFP-AGROIA-001** (interacción por voz) | Transcripción, parámetros, métricas de voz. | ✅ Desplegado en producción. |
| **RFP-AGROIA-002** (lectura en voz alta) | Preferencias, síntesis, métricas, voz personalizada clonable (TT-06: adaptador + wrapper Chatterbox). | ✅ Desplegado (clonación real pendiente de cuenta GPU). |
| **AGC-COST** | Cotización → reporte (F1–F7). | ✅ Productivo. |
| **Calidad del dato del sensor** | Regla de rango objetivo JXBS-3001 (marcado `invalidada`, exclusión en análisis/reportes). | ✅ Productivo. |
| **Lotes por separado** | Dibujo multi-lote con perímetro/área por lote. | ✅ Productivo. |

---

## 11. Principios de dominio (no negociables)

1. **Sin análisis de suelo no hay dosis de fertilizante** (solo criterios y rangos orientativos).
2. **No recetar plaguicidas** (manejo integrado + remisión al registro ICA y a ingeniero agrónomo).
3. **Enfermedades de control oficial** (Fusarium R4T, Moko, HLB): notificar al ICA, no diagnosticar con certeza.
4. **Citar la fuente** de cada umbral (Cenicafé/AGROSAVIA/UPRA).
5. **La ubicación da hipótesis, no nutrientes** (solo pH/MO/N/textura modelados; pedir análisis de suelo).
6. **Separar lo general de lo local** (un rango de la zona cafetera no aplica a Nariño).

---

*Documento generado para referencia del equipo. Los detalles de contrato y diseño viven en `resources/design/` y `resources/architecture/`.*
