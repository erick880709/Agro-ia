# AgroIA — Estado del Proyecto

> **Fecha:** 2026-08-25 | **Versión:** 0.1.0 | **Pipeline:** janus → epicureo → archi → genesis → builder | **CI:** 🟢 verde | **Producción:** 🌐 https://agroia-backend.onrender.com (Render Free + Neon)

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

**Estado:** ✅ **EN PRODUCCIÓN** — https://agroia-backend.onrender.com (Render Web Service Free + Neon Postgres Free). CI en verde; auto-deploy en cada push a `master`.

### Brecha económica — plan de fertilización por presupuesto (2026-08-25)

- `presupuesto_cop` (COP/ha) opcional en `POST /api/v1/recomendaciones/analyze`, `POST /api/v1/reportes/generar` y en la UI («🧪 Analizar suelo»).
- **Motor económico** (`services/economia.py`): costos de corrección por variable (COP/ha), severidad = prioridad × desviación del rango ideal, y variables obligatorias (pH/CE y críticas) siempre incluidas aunque excedan el presupuesto.
- **Plan económico vs. ideal**: el reporte y la respuesta muestran costo ideal, costo del plan, cobertura del presupuesto (%), estimación de diferencia de rendimiento y listas de acciones **Incluidas / Aplazadas** (con motivo).
- Validado local y en producción: finca con pH 4.9 → plan prioriza encalado y aplaza P, K, micros según presupuesto (ej. Yuca: ideal $850.000 → plan $700.000, cobertura 82%).

### Retorno de inversión en el reporte (2026-08-27)

- Nueva sección **«E — Análisis económico proyectado — retorno de inversión»** entre el Plano del lote y las Advertencias (HTML y PDF vía impresión).
- Cálculo con precios de referencia de la ficha técnica del cultivo (sin BD nueva): `Ganancia esperada = (Rendimiento × Precio de cosecha) × 1,15` si se aplica el plan; `ROI = (Ganancia − Costo de fertilización) ÷ Costo de fertilización` (costo = plan económico si hay presupuesto, si no el plan ideal).
- Si el **ROI < 1,2** el reporte muestra la alerta *«Inversión justa, considere subvenciones»*; si es ≥ 1,2 indica que la inversión es rentable. Sin ficha económica o sin acciones con costo, la sección degrada con notas explicativas.
- Validado en producción: Café → ingreso $17.280.000/ha, ganancia con plan $19.872.000/ha, costo $700.000/ha, ROI 27,4×.

### Chat asesor agronómico (2026-08-25)

- `POST /api/v1/chat/consultar` — capa conversacional especializada disponible para admin/agrónomo/cliente (acceso limitado a sus fincas).
- **Orquestador agronómico** (`services/agronomo_chat.py::respuesta_orquestada`): detecta intención y enruta a herramientas (cálculo de encalado/fertilizante/riego en `agronomo_kb.py`), clima disponible (época del año + sensores; sin pronóstico inventado), diagnóstico diferencial de problemas, explicación del «por qué» del cultivo recomendado, o conversación general detallada por rol.
- **Respuestas fundamentadas**: qué recomienda · por qué · datos usados · fuentes (Cenicafé/Agrosavia/UPRA/ICA/IDEAM) · qué falta · confianza (Alta/Media/Baja). Anti-alucinación: si falta un dato se declara explícitamente.
- **Memoria de finca**: tabla `chat_memoria` (migración 007) + `GET /api/v1/chat/memoria/{finca_id}`.
- **Modo LLM**: con `OPENAI_API_KEY` el LLM razona sobre el mismo contexto + base de conocimiento con fuentes; sin key corre el motor local determinista.
- Documento de arquitectura y plan: `resources/architecture/plan_chat_agronomico.md`.

### Mapa de calor del lote (2026-08-25)

- El reporte incluye la sección **«M» — Mapa de calor del lote** con **selector de parámetro**: pestañas «🧭 Resumen» (todas las variables a la vez — cada punto se pinta según cuántas variables están fuera de su rango), una pestaña por variable (independiente) y «📋 Ver todos» (apilados, para imprimir).
- **Regla de intensidad por parámetro**: cada variable usa su propia escala min→max del lote; la celda más intensa (verde oscuro) = valor más alto y la más clara = valor más bajo. La leyenda muestra el gradiente con min/max y el rango ideal de referencia.
- **PDF / impresión**: vía `@media print` el reporte muestra **cada matriz por parámetro apilada** (sin pestañas y sin la vista unificada); la vista unificada «Resumen» es solo para la aplicación. Cada matriz usa `break-inside: avoid`.
- **Plano del lote (sección N)**: dibujo SVG de los puntos de muestreo (`pos_x`/`pos_y`; los puntos (0,0) se omiten), silueta del lote como cierre convexo y estimación de **perímetro (m) y área (m²/ha)**; se compara con el área registrada de la finca. Demo sembrada con `demo-lote-forma` (13 puntos en local y producción).
- **Fecha de la toma**: la sección muestra la fecha (o rango) de toma de muestras y cada punto tiene tooltip con su fecha.
- **Clima del día de la muestra (IDEAM)**: si la finca tiene ubicación (coordenadas de Google, enlace corto resuelto o lat/lng registradas), se agrega el clima del día de la toma (temperaturas, precipitación estimada, humedad) con notas para ajustar las recomendaciones. Fuente real IDEAM si `IDEAM_API_URL/KEY` están configurados; si no, climatología de referencia del IDEAM (Atlas 1981-2010) para el mes de la muestra. **Sin ubicación, la sección se omite.**
- Ingesta con posición: `POST /api/sensor` acepta `pos_x`/`pos_y`; la carga de archivo acepta columnas `x,y` (o `pos_x,pos_y`) con varias filas (una por toma) en CSV ancho o JSON array de muestras.
- Modelo: `sensor_readings.pos_x/pos_y` (migración `006_posiciones_muestreo`); demo sembrada con cuadrícula 3×3 (`seed_demo_integral.py`).

### Relación finca ↔ sensor en la trama (2026-08-26)

- `POST /api/sensor` acepta `finca_id` en la trama: la medición y el dispositivo quedan asociados a esa finca (422 `FINCA_NOT_FOUND` si no existe; si el dispositivo ya estaba en otra finca, se reasocia automáticamente).
- Orden de resolución: `finca_id` de la trama → finca registrada del `device_id` → auto-registro a la primera finca (solo si el dispositivo es desconocido).
- La UI muestra el **ID de la finca con botón «Copiar»** al crearla y en la tarjeta de cada finca (pestaña Fincas), para configurarlo en el firmware.
- Import del consumidor IoT portable en dev y en el contenedor (`services/puente_iot.py` + `PYTHONPATH` con `/app/apps/iot`).
- Migración `008_reparar_enums_sensor`: auto-repara tipos enum (p. ej. `texturasuelo`) y la columna `textura` en BDs ya existentes.
- `search_path` garantizado por conexión con `server_settings` de asyncpg (además del listener) y `SET LOCAL` en el consumidor.

### Cómo está montado

- **Render Blueprint** (`render.yaml`): web service Docker desde `apps/backend/Dockerfile`, health check `/api/v1/health`, migraciones `alembic upgrade head` automáticas al arrancar el contenedor (Render free no permite `preDeployCommand`).
- **Neon** (`agroia`): Postgres free con SSL. El backend normaliza la URL (`sslmode=require` → `ssl=require`, solo asyncpg) y pone `agroia` en el `search_path` de cada conexión.
- **Auto-reparación de enums al arranque** (`services/asegurar_enums.py`): si la BD externa fue reiniciada/restaurada después de las migraciones, la API recrea los tipos enum faltantes en cada arranque (además de las migraciones `008_reparar_enums_sensor` y `009_reparar_enums_2`).

### Validación y entrenamiento del modelo de recomendación/diagnóstico (2026-08-26)

- **Diagnóstico actual**: el motor en producción es el **sistema experto** (23 reglas activas, 9 variables, 5 cultivos con reglas específicas) — determinístico y trazable; el ML corría solo como baseline (India) y no estaba conectado.
- **Entrenamiento con datos simulados colombianos** (`apps/ml/agroia_ml/train_colombia.py`): 75 000 perfiles de suelo etiquetados por el sistema experto → RandomForest por variable (diagnóstico DEFICIT/OK/EXCESO) + clasificador de aptitud UPRA.
- **Precisión obtenida (holdout)** — F1 por modelo: CIC 0.9999 · CE 1.0 · humedad 0.9946 · MO 0.9905 · temp. suelo 0.977 · pH 0.9742 · K 0.9374 · P 0.9423 · N 0.9302 · **aptitud UPRA 0.9759** (CV 5-fold 0.8213).
- **Concordancia con datos reales del sensor** (etiquetas del sistema experto): Café 0.59 · Papa 0.45 · Maíz 0.43 · Arroz 0.36 · Plátano 0.32 — limitada por lo dispersos que son los datos reales (muchas variables faltantes) y por el desbalance; es honesto: el sistema experto sigue siendo la fuente de verdad.
- **Oráculo ML en sombra** (`services/ml_oracle.py`): carga los artefactos (`apps/ml/models/*.joblib`, ~18 MB) y alimenta la detección de discordancia del orquestador; si faltan artefactos, opera solo con reglas. `GET /api/v1/ml/estado` expone modelos, métricas y artefactos.
- **Plan de mejora propuesto**: (1) ampliar reglas a más cultivos/variables (fuente de verdad), (2) imputación de variables faltantes en el entrenamiento para subir la concordancia en datos reales, (3) reentrenar cuando la BD acumule más lecturas calibradas y promover a stage PRODUCTION.
- **Datos sembrados**: 30 cultivos, 23 reglas, usuarios (admin/agrónomo/cliente), 4 fincas y finca demo integral con lecturas. Scripts: `load_seeds.py`, `scripts/seed_cloud.py`, `scripts/seed_demo_integral.py` (apuntan a `DATABASE_URL`).

### Plan de mejora ejecutado (2026-08-27)

1. **Reglas ampliadas** (`services/asegurar_reglas.py`, idempotente al arranque): 8 reglas universales nuevas (Ca, Mg, S, Fe, Mn, Zn, Cu, B) + reglas específicas para Aguacate, Cacao, Fríjol, Tomate y Yuca. Total: **54 reglas activas, 17 variables, 10 cultivos con reglas específicas**.
2. **Imputación de faltantes**: `train_colombia.py` imputa con la mediana por variable (guardada en `ml_meta.json`) y enmascara 35 % de las muestras sintéticas para que el modelo aprenda con datos incompletos; el oráculo (`ml_oracle.py`) usa las mismas medianas al predecir.
3. **Reentrenamiento**: 75 000 muestras → **17 modelos de diagnóstico** (F1 0.82–0.99, ahora cubre Ca/Mg/S/Fe/Mn/Zn/Cu/B) + aptitud UPRA (F1 0.9111). Concordancia media en datos reales **0.6591 < 0.85** → permanece en **STAGING** de forma honesta; se promoverá a PRODUCTION cuando la BD acumule más lecturas calibradas (umbral de calidad 0.85).
4. **UI**: la tabla «🌾 Cultivos sugeridos (ranking del motor)» ahora incluye la columna **«Descripción de reglas aplicadas»** (variable, estado, rango ideal, acción correctiva y prioridad por regla), además del conteo. Los ajustes pasaron de 3 a 5 y los rangos unilaterales se muestran como `≥ x` / `≤ y`.

### Aceptación humana de recomendaciones (human-in-the-loop) y 12 mejoras al reporte (2026-08-27)

- **Aceptación con feedback al modelo**: al final de la página Recomendaciones, Admin/Agrónomo ven el botón «✅ Aceptar recomendación» + caja de texto para ampliar acciones. `POST /api/v1/recomendaciones/aceptar` persiste la aceptación (tabla `aceptaciones_recomendacion`, migración 010) y cada aceptación suma **+0.02 de confianza** al modelo para esa finca/cultivo (máx +0.10). El análisis muestra `respaldos` y `/ml/estado` expone `validaciones_humanas`.
- **Migración 010**: nuevos campos en `fincas` (pendiente %, drenaje, historial agronómico JSONB, validación de laboratorio, cultivo sembrado, edad, etapa fenológica) + tabla de aceptaciones. `PATCH /api/v1/fincas/{id}` (Admin/Agrónomo) los actualiza.
- **12 mejoras al reporte** (validado en `reports/test_mejoras_demo.html`):
  1. Calidad NPK en 3 niveles (Validado en laboratorio / Calibrado de fábrica / Sin validar) — la cabecera muestra el nivel más bajo, nunca "Calibrado" a secas.
  2. pH contextualizado: "ácido en escala general, pero dentro/fuera del rango óptimo para <cultivo> [a–b]".
  3. Acciones sobre NPK sin validar marcadas como **condicional a confirmación de laboratorio**.
  4. Variables de fertilidad faltantes (MO, CIC, Ca, Mg, S, Fe, Mn, Zn, Cu, B) reducen la confianza global y etiquetan la clasificación como **preliminar**.
  5. Cultivos sensibles a drenaje (aguacate, cacao, cítricos, palma) sin textura → "sujeta a confirmación de textura".
  6. Plano del lote muestra pendiente (%) y drenaje junto al área/perímetro.
  7. Bloque "Historial de manejo del lote" (cultivo anterior, fertilización, encalado, dosis).
  8. Plan ejecutable por variable (fuente, frecuencia, dosis) — dosis "a definir por técnico agrónomo tras análisis de laboratorio" sin validación lab.
  9. Ajustes por etapa fenológica (vegetativa/floración/fructificación/cosecha).
  10. Alerta fitosanitaria específica cuando la HR > 78 % (Phytophthora en aguacate, moniliasis en cacao, roya en café…).
  11. Metodología de muestreo del mapa de calor (grilla ciega vs puntos dirigidos).
  12. Umbral duro de confianza < 80 % → la clasificación se muestra como **Pendiente de validación técnica** (no "Apta" a secas).

### Registro de finca en 3 secciones + cadena de validación + separación Finca/Lote (2026-08-27)

- **Wizard de 3 secciones** en «🏡 Fincas»: 1) Información básica (nombre, propietario, teléfono, email, departamento, municipio, vereda) · 2) Ubicación (📍 Usar mi ubicación con GPS del navegador, 🗺️ seleccionar en mapa con Leaflet y polígono del lindero, 🔗 pegar enlace Google Maps; muestra latitud, longitud, altitud y precisión) · 3) Características del predio (tipo de área, área registrada, **área georreferenciada calculada automáticamente del polígono**, ¿varios lotes?).
- **Migración 011**: nuevas columnas en `fincas` (`vereda, precision_gps, fuente_geolocalizacion, geometria (GeoJSON), area_declarada_ha, area_calculada_ha, perimetro_m, tipo_area, tiene_multiples_lotes, fecha_georreferenciacion`) + tabla `lotes` (separación arquitectónica Finca ≠ Lote). Al guardar se crea el **lote principal** y `GET /fincas/{id}/lotes` los lista.
- **Cadena de validación al guardar** (`services/geografia.py`, catálogo de 32 departamentos + municipios con centroides, espejo de `departamentos.js`): 1 departamento existe → 2 municipio pertenece → 3 coordenadas válidas → 4 coinciden con el municipio (≤ 50 km del centroide) → 5 área razonable (0.01–100 000 ha) → 6 precisión aceptable (≤ 100 m). Cada paso se devuelve y se pinta en la UI (✅/⚠️/❌); el error 422 `VALIDACION_FINCA` incluye la lista de pasos. `GET /api/v1/location/catalogo` expone el catálogo.

### Migraciones destacadas

- `004_crear_enums` — crea los 12 tipos enum con los nombres que esperan los modelos SQLAlchemy (las migraciones 001/002 los referenciaban con `create_type=False` y nombres snake_case).
- `005_fix_enum_values` — renombra valores de enums creados por 003 (valores → nombres de miembro: `Admin` → `ADMIN`).

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
