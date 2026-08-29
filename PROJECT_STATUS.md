# AgroIA — Estado del Proyecto

> **Fecha:** 2026-08-28 | **Versión:** 0.1.0 | **Pipeline:** janus → epicureo → archi → genesis → builder | **CI:** 🟢 verde | **Producción:** 🌐 https://agroia-backend.onrender.com (Render Free + Neon)
### Módulos v4 — cobertura funcional ampliada (2026-08-27)

Implementación de `context/contextoFuncional/AgroIA_Especificacion_Tecnica_v4.md` (principio rector: ningún reporte se bloquea por falta de datos):

- **Migración `023_modulos_v4`** (023→032): `analisis_agua_riego`, `curvas_extraccion`, `monitoreo_plagas`, `variedades_cultivo`, `compatibilidad_rotacion`, `checklist_bpa`, `periodos_carencia`, `preferencias_notificacion`, Kc en `cultivos`, `resistencia_penetracion_kpa` en `lotes`, rol `Extensionista` + `municipios_asignados`.
- **1.A Agua de riego FAO-29** · **1.B Curvas de extracción** · **1.C Balance hídrico ETo/Kc** (Open-Meteo) · **1.D Monitoreo de plagas MIP** (GBIF) · **1.E Variedades** · **1.F Rotación** · **1.G Trazabilidad BPA** (ICA 30021 + carencias) · **1.H Compactación** · **1.I Notificaciones WhatsApp** (degradación total sin credenciales) · **1.J Rol Extensionista** con «🗺️ Mi zona».
- **Catálogo**: 15 cultivos nuevos con Kc e íconos gobernados (`ICONO_REQUERIDO` en el alta); siembra idempotente `POST /api/v1/admin/v4/sembrar` + `scripts/seed_v4.py`.
- **ML**: `POST /api/v1/admin/ml/reentrenar` encola `train_colombia.py`.
- **Reporte**: secciones R (riego), S (rotación) y B (BPA) junto a Q (labores).
- Validado local: 45 cultivos, balance real (Café Kc 0.85), rotación Maíz→Fríjol/Arveja, plagas con GBIF (20 ocurrencias broca), BPA con carencias, Extensionista ve solo Armenia, reentrenar 202, las 4 secciones del reporte presentes.

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

### Chat asesor con contexto visual (2026-08-27)

- Botón **📎 en el chat** para adjuntar foto del cultivo (JPG/PNG, máx. 4,5 MB) con vista previa y miniatura en el historial.
- `POST /api/v1/chat/consultar` acepta `imagen_base64`; se guarda en `chat_memoria.imagen_base64` (migración 013) como referencia de la finca.
- **Visión**: si `OPENAI_API_KEY` está configurado y el modelo tiene visión (gpt-4o, gpt-4.1, gpt-4o-mini…), la foto se envía al prompt *«Analiza esta foto de cultivo y da un diagnóstico»*. Sin visión, la imagen queda como referencia y el prompt textual lo indica.
- Respuesta incluye `imagen_guardada` e `imagen_analizada`. Validado local y en producción (modo experto-local).

### Fisiología de cultivos (2026-08-27)

- Nuevas columnas en `cultivos` (migración 014): `profundidad_radicular_min_cm`, `gdd_total_requerido` y `dias_ciclo`; cargadas en la ficha técnica con semillas para Café (80 cm / 2000 GDD / 270 d), Maíz, Arroz, Plátano y Papa, y editables vía `PATCH /api/v1/catalogo/cultivos/{id}`.
- **Aptitud**: si la profundidad efectiva del lote es menor a la requerida por el cultivo, se penaliza proporcional al déficit (Crítica si ≥ 15 cm de déficit) con ajuste «profundidad_suelo».
- **Fenología (GDD)**: el orquestador estima el GDD acumulado con la temperatura IDEAM (T base 10 °C) según la etapa fenológica de la finca y compara con `gdd_total_requerido`; avisa *«Faltan ~N GDD para cosecha, optimice riego»*.
- Tarjeta del catálogo en la UI muestra «🌱 raíz ≥ 80 cm · 2000 GDD · 270 días». Validado local y en producción (Café vegetativa → faltan ~1262 GDD).

### Limpieza de BD y finca demo (2026-08-27)

- **Reset de demostración** `POST /api/v1/demo/reset` (solo Admin): elimina fincas, lotes, recomendaciones, chat y dispositivos de prueba; **conserva únicamente las lecturas del sensor real `esp32-npk-001`** y crea la finca demo completa **«Finca Demo — El Vergel»** (Quindío/Armenia, Café 4 años en Fructificación, riego por goteo, validación de laboratorio, historial agronómico, lote de 2,5 ha con suelo de 100 cm de profundidad) con el sensor y sus lecturas asociados.
- Aplicado en **local y producción**: ambas bases quedan con 1 sola finca demo y las lecturas reales del sensor (15 local / 371 prod).

### Recomendación sin bloqueo por falta de parámetros (2026-08-27)

- **Ya no devuelve 422**: si faltan parámetros esenciales, el análisis se genera igual con datos disponibles y queda marcado `estado_validacion = pendiente_validacion` + advertencia *«la recomendación no tiene el 100% de certeza y requiere el aval de un agrónomo»*.
- **Sin ninguna lectura**: recomendación preliminar (confianza 5%) con ranking prioritario del catálogo (UC1) o filas «SIN DATO» por parámetro esencial (UC2).
- **Respuesta**: nuevo campo `variables_faltantes_esenciales`; la confianza real se reduce 15% por cada parámetro esencial faltante.
- **Pantalla de captura**: la UI muestra el bloque «📝 Complete los parámetros esenciales» con inputs para los valores faltantes; el botón «Guardar y reanalizar» los ingesta vía `POST /api/sensor` y reejecuta el análisis (flujo validado: 5% → 41% de confianza al completar pH/N/P/K).
- **Reportes**: `POST /api/v1/reportes/generar` tampoco se bloquea — genera el reporte igual (incluso sin lecturas) y agrega la sección «P — Parámetros faltantes para mayor detalle» indicando que sería bueno contar con los valores faltantes y que el reporte es preliminar (aval de agrónomo). La respuesta incluye `parametros_faltantes` y `preliminar`.
- Validado local y en producción (finca sin datos → reporte completo con sección P y faltantes ph/nitrogeno/fosforo/potasio).

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

### Muestreo inteligente, semáforo de confianza, ROI realista y modo simulación (2026-08-27)

- **Muestreo inteligente** (`services/optimizador_muestreo.py`): Farthest Point Sampling sobre `pos_x/pos_y` de las lecturas. Si el análisis es preliminar por parámetros faltantes, el reporte agrega el bloque **«📌 Muestreo inteligente — ¿dónde tomar la muestra de laboratorio?»** con 3-4 puntos óptimos (cruces rojas en coordenadas del lote), **GeoJSON descargable** (`puntos_muestreo.geojson`) y la instrucción *«Tome muestras compuestas en estos puntos. Al ingresar los resultados de laboratorio, la confianza subirá de 0.55 a 0.82»* (proyección honesta de la confianza actual).
- **Semáforo de 4 barras de confianza**: el diagnóstico muestra 🟢 Calibración del sensor (NPK sin laboratorio = 60 %) · 🟡 Cobertura de fertilidad · 🔴 Violaciones activas · 🟣 Respaldo humano, con la nota *«Para subir la confianza al 80%, complete el análisis de Calcio (barra 2) y valide el NPK en laboratorio (barra 1)»*. Respuesta API: campo `desglose_confianza`.
- **ROI realista**: campo opcional **«Rendimiento actual (t/ha)»** en Recomendaciones y Reportes. Si se declara, la sección económica compara contra ese valor real: *«Con el plan ideal, su rendimiento podría pasar de X a Y t/ha (+Z%). Con su presupuesto actual, pasaría a Y₂ t/ha (+Z₂%)»*; sin declararlo usa el rendimiento de la ficha técnica.
- **Modo Simulación what-if**: nuevo `POST /api/v1/reportes/simular` `{finca_id, soil_modificado}` que reejecuta el RulesEngine con el suelo modificado **sin tocar la BD** (< 200 ms) y devuelve clasificación, confianza, violaciones y advertencias. En Reportes, el panel colapsable **«🧪 Simular enmienda»** precarga 4 sliders (pH/N/P/K) desde el script `datos-reporte` embebido en el HTML y muestra el resultado al instante.
- Validado local y en producción (sin migración nueva: las 4 features no cambian el esquema).

### Administración de fincas, lotes y usuarios + auditoría de acciones (2026-08-27)

- **Editar finca** `PUT /api/v1/fincas/{id}` (Admin): datos básicos vía modal en la pestaña 🏡 Fincas.
- **Eliminar finca** `DELETE /api/v1/fincas/{id}` (Admin): borrado en cascada — recomendaciones + discordancias, lecturas de sensores, dispositivos IoT, lotes, chat y relaciones finca-usuario — con resumen de lo eliminado en la respuesta.
- **Lotes por finca** (cada lote con características propias): `POST /fincas/{id}/lotes` (Admin/Agrónomo, nombre/área/geometría/profundidad de suelo/pedregosidad; marca la finca como multi-lote), `PATCH …/lotes/{lote_id}` (editar) y `DELETE …/lotes/{lote_id}` (Admin, desactivación lógica; rechaza `ULTIMO_LOTE` si es el último activo). UI: botón «🗂️ Lotes» por tarjeta de finca con panel de alta/edición/borrado.
- **Usuarios**: `PUT /api/v1/usuarios/{id}` (Admin, nombre/email/rol/activo + reemplazo de fincas) y `DELETE /api/v1/usuarios/{id}` (desactivación Ley 1581). Protecciones: el admin no puede desactivarse ni eliminarse a sí mismo (`SELF_DEACTIVATE`/`SELF_DELETE`). UI: botones «✏️ Editar» y «🗑️ Desactivar» por usuario, badge «Inactivo».
- **Auditoría** (migración 015, tabla `agroia.auditoria`): registra `auth.login`, `finca.*`, `lote.*`, `usuario.*` y `demo.reset` con quién (email/nombre/rol), cuándo, IP y detalle JSONB. `GET /api/v1/auditoria` (Admin) con filtros por entidad/acción y búsqueda; pestaña «🕵️ Auditoría» con tabla paginada.
- Validado local y en producción (la migración corre sola en el deploy de Render).

### Finca integral de demostración en producción (2026-08-27)

- **«Finca Integral El Nogal — 3 ha»** (Quindío/Armenia, producción): registrada con TODOS los parámetros (agronómicos, fenológicos, riego, georreferenciación con polígono de 3 ha calculada, validación de laboratorio) y **81 lecturas completas** de las 17 variables + textura — **72 puntos por el perímetro del lote + 9 puntos interiores repartidos en retícula** — con dispositivo `esp32-integral-3ha` calibrado contra laboratorio.
- Resultado: **Apta · Validada · confianza 99% · 0 violaciones · 0 faltantes**; reporte completo con mapa de calor «21 × 21 tomas (81 puntos)», plano del lote, semáforo de 4 barras en 100% y telemetría «Validado en laboratorio».
- Verificación de bugs en producción: se endureció la búsqueda de ficha económica (sin filtro de enum en SQL, fragilidad Neon) y el encabezado del diagnóstico ahora muestra el nombre del cultivo aunque el `cultivo_id` sea desconocido (usa el cultivo sembrado de la finca). Reporte evidencia: `reports/reporte_finca_integral_3ha.html`.

### Historial de ciclos productivos por lote (2026-08-27)

- **Tabla relacional** `agroia.historial_ciclos_lote` (migración 016): un registro por **ciclo productivo** del lote — `lote_id` (FK lotes ON DELETE CASCADE), `cultivo_id`, `fecha_siembra` (obligatoria) / `fecha_cosecha`, `rendimiento_tn_ha NUMERIC(8,2)`, `calidad_cosecha` (Premium/Estándar/Rechazo), `aplicaciones` JSONB, `incidencias` JSONB, `practicas_riego`, `observaciones`, timestamps — con índice `idx_ciclos_lote (lote_id, fecha_siembra)`.
- **API**: `GET/POST /api/v1/fincas/{id}/lotes/{lote_id}/ciclos`, `PATCH/DELETE …/ciclos/{ciclo_id}` — crear/editar Admin/Agrónomo, eliminar Admin; valida fechas (cosecha ≥ siembra), cultivo del catálogo y enums; auditoría `ciclo.*`.
- **UI**: botón «🔄 Ciclos» por lote en la pestaña 🏡 Fincas → historial + formulario de registro (cultivo, fechas, rendimiento, calidad, riego, aplicaciones/incidencias JSON, observaciones) con edición en modal y eliminación.
- Validado local (CRUD completo + auditoría + guardas de fechas) y pendiente de validación final en producción tras el deploy.

### Inicio rápido de ciclo desde Recomendaciones (2026-08-27)

- **Botón «🌱 Registrar nuevo ciclo»** sobre «🧪 Analizar suelo» (Admin/Agrónomo): modal con cultivo (preseleccionado), fecha de siembra (obligatoria), variedad y densidad (plantas/ha, opcionales).
- **`POST /api/v1/fincas/{id}/ciclo/iniciar`**: en una transacción crea el ciclo en `historial_ciclos_lote` sobre el lote principal y **actualiza `fincas.cultivo_sembrado`** + **`lotes.fecha_siembra`/`variedad`/`densidad_siembra_plantas_ha`** para el análisis actual; auditoría `ciclo.iniciar`.
- **Migración 017**: columnas `fecha_siembra`, `variedad`, `densidad_siembra_plantas_ha` en `lotes` y `variedad`/`densidad_siembra_plantas_ha` en `historial_ciclos_lote`.
- Validado local (API + UI con preselección y actualización de finca/lote) y en producción.

### Cierre del ciclo — Cosechar (2026-08-27)

- **Dashboard (P1)**: con ciclo abierto, la tarjeta «⚡ Acciones rápidas» muestra el bloque «🔄 Ciclo activo» y el botón **«✏️ Cosechar ciclo»** (Admin/Agrónomo).
- **Historial (P6)**: el mismo bloque y botón aparecen arriba del listado de recomendaciones cuando hay ciclo abierto.
- **Modal de cierre**: fecha de cosecha (hoy por defecto) · **rendimiento obligatorio** (kg/ha o t/ha, normalizado a t/ha — alimenta el ROI futuro) · calidad opcional · textarea de aplicaciones con **parser simple** («Urea 150kg, DAP 80kg» → JSONB `[{producto, dosis_kg_ha, unidad, tipo}]`, gramos → kg) · **carga de CSV pequeño** (`Producto,Dosis,Unidad`) que se convierte al mismo formato.
- **API**: `GET /api/v1/fincas/{id}/ciclo/activo` y `POST /api/v1/fincas/{id}/ciclo/cosechar` — guardas `NO_CICLO_ACTIVO` y `FECHAS_INVALIDAS`; auditoría `ciclo.cosechar`.
- Validado local (API + UI completa iniciar→cosechar) y en producción.

### Carga masiva del historial de ciclos (CSV, 2026-08-27)

- **P4 (Cargar archivo)**: nueva tarjeta «🗂️ Carga masiva — historial de ciclos (CSV)» para grandes fincas: CSV con los últimos 5 años (`lote, cultivo, fecha_siembra, fecha_cosecha, rendimiento, aplicaciones_texto`) + plantilla de ejemplo descargable.
- **`POST /api/v1/fincas/{id}/ciclos/carga-csv`** (Admin/Agrónomo): ingesta en bloque — crea lotes que no existan, resuelve cultivos por nombre, fechas ISO o DD/MM/YYYY, rendimiento en t/ha, aplicaciones texto → JSONB; reporta filas con error sin abortar. Auditoría `ciclo.carga_csv`.
- Validado local (API: 3 creados + 1 lote nuevo + 2 errores reportados; UI con plantilla y resumen) y en producción.

### Historial de ciclos en el reporte — predicción de rendimiento y alerta de P (2026-08-27)

- **Sección N**: tabla «📜 Historial de ciclos — línea de tiempo (Siembra → Aplicaciones → Cosecha → Rendimiento)» con los últimos 3 ciclos del lote principal.
- **Sección 05**: 📈 Predicción de rendimiento — promedio histórico × 1,15 (plan optimizado) y × 1,25 (plan ideal). Ejemplo validado: promedio 14.2 → «16.3 t/ha (+15%)» y «17.8 t/ha (+25%)».
- **Sección 04**: alerta «⚠️ Histórico de P alto (últimos 2 ciclos > 120 kg/ha)» cuando los ciclos tienen aplicaciones fosforadas altas (DAP/fosfatos).
- Validado local y en producción; sin ciclos las tres piezas se omiten.

### Módulo de labores / órdenes de trabajo (2026-08-27)

- **Tabla `agroia.labores`** (migración 018): título, tipo (Fertilización/Enmienda/Riego/Control Fitosanitario), producto/dosis, fechas programada/ejecución, responsable, estado y observaciones — FK a lotes y recomendaciones.
- **P5**: botón «📋 Generar órdenes de trabajo» junto a «Aceptar recomendación» → cada acción del diagnóstico se vuelve una labor individual (`POST /fincas/{id}/labores/generar`, tipo inferido del texto).
- **P1**: widget «📋 Tareas pendientes de hoy» con «✔️ Completar» (fecha de ejecución automática) y «🚫 Cancelar» (`PATCH /labores/{id}`).
- **Identificación y detalle (2026-08-27)**: cada orden del widget muestra su **finca y lote** (🏡/🗂️ — la API responde `finca_nombre`/`lote_nombre` en `GET /fincas/{id}/labores` y `pendientes-hoy`); al **seleccionar una orden** (clic en la fila o «👁️ Ver detalle») se abre el modal con finca, lote, tipo, producto, dosis, fechas, observaciones y foto.
- **Reporte**: nueva sección **«Q — Órdenes de trabajo (labores)»** con la tabla Finca · Lote · Tipo · Tarea · Producto · Dosis · Programada · Ejecución · Estado.
- Auditoría `labor.generar/actualizar/completar/eliminar`. La PWA (punto 5) se conectará a estos endpoints con geolocalización y foto.
- Validado local (API: 6 acciones → 6 labores con tipos correctos; completar registra fecha; auditoría) y UI (generar desde P5 y completar en P1) — pendiente validación en producción.

### Alertas climáticas proactivas (pronóstico + fenología + labores, 2026-08-27)

- **Fuente**: Open-Meteo Forecast (gratis, sin API key) para el pronóstico de 7 días; el diseño admite conmutar a IDEAM/NASA POWER (el servicio recibe pronóstico normalizado `[{fecha, precipitacion_mm, temp_min_c, temp_max_c}]`).
- **Servicio programado** cada 6 h (tarea asyncio en el `lifespan`; primer ciclo a los 45 s) + `POST /api/v1/alertas-climaticas/evaluar` manual (Admin, con pronóstico inyectable para pruebas deterministas).
- **Reglas**: (1) lluvia > 20 mm/24h en los próximos 3 días + labor de Fertilización pendiente → «Aplace la aplicación…, riesgo de lixiviación»; (2) T mín < 5 °C + etapa Floración + cultivo sensible → «Riesgo de helada, active riego por aspersión».
- **Tabla `agroia.alertas_climaticas`** (migración 019): tipo/severidad/mensaje/fecha/pronóstico JSONB/activa; las alertas previas del mismo tipo se desactivan en cada evaluación.
- **UI**: banner de colores en P1 (azul lluvia, rojo helada) vía `GET /fincas/{id}/alertas-climaticas/activas`; reporte sección N con «⛅ Pronóstico extendido (7 días)» y avisos de umbral.
- Validado local y en producción: reglas con pronóstico inyectado (ambas alertas), camino real Open-Meteo sin fallas, banner en P1, desactivación automática cuando el pronóstico deja de cumplir la regla, y pronóstico extendido en la sección N del reporte.

### Aprendizaje activo — promoción del ML por variable (2026-08-27)

- **Ground Truth** (`services/ml_labels.py`): aceptaciones humanas (estados DEFICIT/OK/EXCESO por variable, unidas a la última lectura de la finca) + ciclos cerrados (rendimiento real vs. `rendimiento_esperado` de la ficha → etiqueta de aptitud verificada en campo).
- **Pipeline `train_colombia.py --active-learning`**: combina sintéticos (peso 1.0) + doradas (peso 10.0, `sample_weight`), partición por finca sin fuga, y calcula `precision_real` por variable sobre el holdout dorado. Promoción **por variable** con precisión ≥ 0.85 y ≥ 5 muestras → `RF_diagnostico_<var>_colombia_activo` en PRODUCTION; el resto en STAGING honesto.
- **Validador ML en runtime**: el oráculo lee `ml_meta.json.promovidas`; el orquestador compara ML vs. reglas por variable promovida — acuerdo → +0.02 de confianza (máx +0.06) y 5.ª barra en el semáforo; desacuerdo → prevalecen las reglas y se registra en `validacion_ml`. P5 muestra el banner «🤖 Validador ML activo».
- **Transparencia**: `GET /api/v1/ml/etiquetas-doradas` (Admin) y `variables_promovidas` en `GET /api/v1/ml/estado`.
- Validado local: siembra de etiquetas doradas (aceptación + ciclo cerrado), entrenamiento `--active-learning --registrar` (75 000 sintéticos + doradas, 0 promovidas con 1 muestra — comportamiento honesto), validador runtime con promoción simulada (desacuerdos P/K → reglas mandan) y banner en P5. Validado en producción: `variables_promovidas` en `/ml/estado`, `/ml/etiquetas-doradas` (Admin), `validacion_ml` en el analyze y UI sirviendo `v=20260827-mlactivo`.

### Capas oficiales IGAC/UPRA — enriquecimiento SIG (2026-08-27)

- **`services/sig_suelos.py`**: 11 zonas de referencia del Estudio General de Suelos del IGAC + zonificaciones UPRA/SIPRA (textura, M.O., CIC, drenaje, profundidad efectiva, pedregosidad, capas limitantes — ej. posible fragipán en Cundinamarca). El polígono GeoJSON se intersecta por centroide (`resolver_zona_sig`).
- **Relleno automático**: fila en `sensor_readings` con `calidad = 'estimado_por_sig'` (`sensor_id = 'sig-igac-upra'`) precarga textura/MO/CIC y completa profundidad/pedregosidad del lote. Migración 020 amplía el enum `texturasuelo` con clases IGAC.
- **Precedencia**: `SueloAdapter.get_latest` hace merge — el **sensor gana SIEMPRE**; el SIG solo rellena faltantes (marcados en `estimaciones_sig`). En el diagnóstico, confiabilidad «Estimado por SIG (IGAC/UPRA)»; en el Dashboard, badge «🗺️ estimado SIG».
- **Endpoints**: `POST /fincas/{id}/enriquecer-sig` (manual, idempotente, auditoría `sig.enriquecer`), `GET /fincas/{id}/enriquecimiento-sig`; `POST /fincas` lo ejecuta automáticamente si hay coordenadas. Geoservicio WMS/WFS real opcional vía `SIG_IGAC_WMS_URL`.
- Validado local y en producción: enriquecimiento Eje Cafetero (Franco-arcillosa, MO 9.5 %, CIC 24), violaciones SIG → filas con confiabilidad «Estimado por SIG (IGAC/UPRA)», sensor (MO 3.0/CIC 5.0) sobreescribe al SIG, badge «🗺️ estimado SIG» en Dashboard (local y prod) y UI sirviendo `v=20260827-sig`.

### Precios de insumos dinámicos — ROI actualizable (2026-08-27)

- **Tabla `agroia.precios_insumos`** (migración 021): `producto` (clave única), `precio_kg_cop`, `fecha_actualizacion`, `fuente`.
- **Cálculo dinámico** en `services/economia.py`: `calcular_plan_economico(..., precios_insumos)` convierte COP/kg → COP/ha con `DOSIS_PRODUCTO_VARIABLE` (N = Urea 60 kg/ha, P = DAP 35 kg/ha, K = KCl 45 kg/ha…); el orquestador (UC1/UC2) y el reporte cargan la tabla en cada análisis. Sin registro → fallback estático + `advertencia_precios` «Precios de referencia desactualizados» (P5 y reporte).
- **Endpoints solo Admin**: `GET/PUT /api/v1/admin/precios-insumos` (upsert con fecha = hoy, auditoría `precios.actualizar`); página propia **«💰 Administrar insumos»** dentro del menú ⚙️ Administración (tabla editable de 14 insumos).
- Validado local y en producción: 403 para Cliente, advertencia con tabla vacía, tras PUT (Urea 3 500) el costo de N pasa 180 000 → 210 000 COP/ha, P 150 000 → 168 000 (DAP 4 800), K 160 000 → 189 000 (KCl 4 200), sin advertencia; en prod el analyze usa `precios_fuente = precios_insumos` (ideal 357 000) y el panel admin sirve con `v=20260827-precios`.

### Menú «Administración» y página propia de insumos (2026-08-28)

- **Nueva navegación (Admin):** las secciones administrativas se agrupan en un **desplegable ⚙️ Administración** con submenús: **🏡 Registrar finca** (wizard completo de 3 pasos en su propia vista), **🗂️ Fincas**, **📜 Historial**, **👥 Administrar usuarios**, **💰 Administrar insumos** (página propia con la tabla de precios dinámicos) y **🕵️ Auditoría**. Para el Admin, «Fincas» e «Historial» **se quitaron de la barra superior** (quedan solo en el menú, sin duplicarse); para Agrónomo y Cliente, «Historial» sigue en la barra superior.
- **Comportamiento del menú:** panel <b>flotante</b> (`position: fixed`) que se despliega <b>sobre el body</b> (escapa del `overflow-x` del nav), se abre hacia arriba si no cabe abajo, se reposiciona en scroll/resize y se cierra al elegir una opción o al hacer clic fuera. El desplegable no aparece para Agrónomo ni Cliente (el botón no compite con la lógica de pestañas por rol).
- **Assets**: `app.js`/`styles.css` con cache-busting `?v=20260827-adminnav4`.
- Validado local y en producción: submenú abre/cierra flotando sobre el contenido, navegación a registrar-finca (wizard visible), fincas (solo listado), historial (12 filas), usuarios (7 tarjetas), insumos (15 filas con precios guardados) y fincas (solo listado).

### Menú «Ayuda» — manuales de usuario por rol (2026-08-28)

- **Nuevo menú ❓ Ayuda** (todos los roles) con los manuales de usuario según el rol: 👑 Administrador, 🧑‍🌾 Agrónomo y 👤 Cliente. El Admin ve los tres; Agrónomo y Cliente solo el suyo (filtrado por `data-roles`). Solo el Admin ve el menú ⚙️ Administración.
- **Manuales** (`ayuda-admin.html`, `ayuda-agronomo.html`, `ayuda-cliente.html`): guías paso a paso en orden lógico según el alcance de cada rol, con capturas reales de la aplicación, **GIF animados** de los flujos principales (login, registro de finca, análisis, precios) y un **reproductor de video** (▶/⏸ con barra de progreso).
- **Media**: capturas y GIF en `apps/frontend-web/media-ayuda/` servidos por el mount estático del frontend; GIF generados con `scripts/gen_ayuda_gifs.py` (Pillow).
- **Assets**: `?v=20260827-adminnav4`.
- Validado local: menú Ayuda flotante por rol (Admin 3 opciones, Agrónomo/Cliente solo la suya), los 3 manuales cargan con 0 imágenes rotas (16/10/8 pasos) y el reproductor de video funciona.

### Imágenes fuera de la BD y validación de rendimiento (2026-08-27)

- **Chat — job programado**: `services/mantenimiento.py::limpiar_imagenes_chat()` (UPDATE `imagen_base64 = NULL` para `ts` > 90 días) corre cada 24 h en el lifespan y manualmente vía `POST /api/v1/admin/chat/limpiar-imagenes` (Admin). Validado: 2 imágenes viejas liberadas.
- **Labores — fotos en disco**: migración 022 agrega `labores.imagen_url`; `POST /api/v1/labores/{id}/foto` (multipart, JPEG/PNG/WebP, máx 5 MB) guarda el archivo en `media/labores/` (o `AGROIA_MEDIA_DIR`) y solo persiste la ruta; FastAPI sirve `/media`. Validado: subida y descarga de PNG con `imagen_url` en la BD.
- **Rendimiento atípico (anti-outliers)**: al cosechar, si declarado > esperado×2 o < esperado×0.3 → `rendimiento_atipico = true` (migración 022) + `advertencia_rendimiento` (banner amarillo en la UI, no bloquea). `ml_labels.etiquetas_ciclos` excluye los atípicos del Ground Truth. Validado: café 50 t/ha → atípico excluido; 2.1 t/ha → normal incluido (doradas = normales).
- Validado en producción: job chat (200, 0 liberadas), foto de labor subida a disco y servida por `/media` (200 image/png) con solo `imagen_url` en BD, y cosecha de 50 t/ha marcada atípica con advertencia (ciclo/labor de prueba limpiados).

### Migraciones destacadas

- `004_crear_enums` — crea los 12 tipos enum con los nombres que esperan los modelos SQLAlchemy (las migraciones 001/002 los referenciaban con `create_type=False` y nombres snake_case).
- `005_fix_enum_values` — renombra valores de enums creados por 003 (valores → nombres de miembro: `Admin` → `ADMIN`).
- `015_auditoria` — tabla `agroia.auditoria` (bitácora de acciones: usuario, acción, entidad, detalle JSONB, IP, fecha).
- `016_historial_ciclos_lote` — tabla `agroia.historial_ciclos_lote` + índice `idx_ciclos_lote` (ciclos productivos por lote).
- `017_ciclo_inicio` — `fecha_siembra`/`variedad`/`densidad_siembra_plantas_ha` en `lotes`; `variedad`/`densidad_siembra_plantas_ha` en `historial_ciclos_lote`.
- `018_labores` — tabla `agroia.labores` (órdenes de trabajo con estado, responsable y fechas).
- `019_alertas_climaticas` — tabla `agroia.alertas_climaticas` (alertas meteorológicas proactivas con pronóstico JSONB).
- `020_texturas_sig` — enum `agroia.texturasuelo` ampliado con clases granulométricas IGAC (FRANCA, FRANCO_ARENOSA, FRANCO_ARCILLOSA, FRANCO_LIMOSA).
- `021_precios_insumos` — tabla `agroia.precios_insumos` (precios dinámicos COP/kg para el ROI del plan económico).
- `022_imagenes_y_rendimiento` — `labores.imagen_url` (fotos en disco) y `historial_ciclos_lote.rendimiento_atipico` (anti-outliers del Ground Truth).

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
### Almanaque Bristol + primer modelo de visión con datos reales (2026-08-29)

- **Módulo Almanaque Bristol (v3.4)** (`context/contextoVision/bristo.md`): calendario lunar como capa cultural complementaria. Servicio `services/calendario_lunar.py` con jerarquía de fuentes **skyfield → US Navy → tabla estática** (degradación automática, precisión < 1 %); en producción `BRISTOL_MODO=static`.
- **API**: `GET /api/v1/calendario-lunar/actual` (fase + recomendación), `/pronostico?dias=7`, **`/mes?anio=&mes=`** (calendario navegable, efemérides analíticas sin red), `/estado` (Admin) y `GET|PUT /api/v1/usuarios/preferencias-bristol` (toggle por usuario; migración 043 + tabla `preferencias_bristol`).
- **Alertas programadas**: regla 3 en `clima_alertas.py` (cada 6 h) crea `siembra_lunar` solo con fase favorable + 7 días sin lluvias > 20 mm ni heladas < 5 °C; no se duplica y respeta el toggle.
- **Reportes**: sección «📅 Calendario Lunar» después del plano del lote, con disclaimer cultural; se omite si el usuario la desactivó.
- **Frontend**: pestaña renombrada a «🌙 Alertas clima y fases lunares» con tarjeta de fase actual, **calendario mensual navegable** (fase lunar por día, hoy resaltado, cache por mes) y toggle de preferencias. `sw.js` en v7.
- **Primer entrenamiento de visión con datos reales**: pipeline `datasets/` ejecutado sobre **DS02 PlantDoc** (CC BY 4.0): 2.574 imágenes → inspect OK → dedup pHash (DCT-II corregido) 59 duplicados → normalize 2.508 en 10 clases → split sin fuga (déficit relativo por clase). **Modelo sklearn baseline: accuracy 70,8 %** en validación (1.459 train / 623 val), guardado en `datasets/models/baseline-sklearn-20260829-144942/`. Es baseline con features de color/textura — el modelo operativo seguirá siendo el fallback OpenCV hasta entrenar con más datasets (DS03–DS08) y alcanzar métricas de promoción.
- **DS23 CocoaMonilia (6,19 GB)**: pendiente de descarga por espacio en disco (~13 GB requeridos).
- **Pruebas**: 57 pruebas backend en verde (13 + 2 nuevas del módulo Bristol).

---
> **Generado por el pipeline AgroIA:** janus (54 reqs) → epicureo (9 specs IA≤15) → archi (C4+6 ADRs) → genesis (scaffold) → builder (9 épicas)
