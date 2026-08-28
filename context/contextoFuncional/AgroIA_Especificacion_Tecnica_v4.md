# AgroIA — Especificación Técnica v4
### Ampliación de cobertura funcional, catálogo de cultivos, roles y menú
**Fecha:** 2026-08-27 · **Autor:** Revisión agronómica + arquitectura senior · **Repositorio base:** `erick880709/Agro-ia` (rama `master`)

---

## 0. Alcance y principio rector

Este documento detalla, con contrato de endpoint (request/response), fuente de datos externa (URL real, gratuita o pública), migración de base de datos, ubicación en el menú y matriz de roles, cada una de las mejoras validadas en la revisión funcional-técnica previa.

**Principio rector — no negociable, se aplica a TODOS los módulos nuevos de este documento:**

> Ninguna recomendación ni ningún reporte se bloquea por falta de un parámetro. Todo módulo nuevo debe seguir el mismo patrón que ya usa el sistema para pH/CE/textura/SIG: si el dato no está disponible, el análisis se genera igual, marcado como preliminar/estimado, con el dato faltante listado explícitamente en la sección `P` (parámetros faltantes) del reporte. Esto permite medir avance real (qué falta, qué mejorar) en vez de ocultar el estado incompleto del sistema.

Cada módulo de la sección 1 declara explícitamente su **regla de degradación** siguiendo este principio.

**Convenciones de contrato usadas en este documento** (consistentes con el resto de la API):
- Todas las rutas van bajo `/api/v1`.
- Cabecera `X-User-Role` obligatoria en cada request; `X-User-Email` cuando el rol es Cliente.
- Errores en formato `{ "detail": { "code": "CODIGO_ERROR", "message": "..." } }`.
- Toda escritura relevante genera un registro en `agroia.auditoria`.

---

## 1. Nuevos módulos funcionales

### 1.A · Análisis de agua de riego

**Objetivo:** evaluar la calidad del agua usada para riego (CE, RAS/SAR, cloruros, boro, pH) — hoy completamente ausente del sistema pese a que `fincas.tipo_riego` ya existe.

**Fuente de datos externa:** no existe una API pública en tiempo real de calidad de agua agrícola en Colombia. La clasificación se hace contra las **tablas de referencia FAO-29** (Ayers & Westcot, *Water Quality for Agriculture*, FAO Irrigation and Drainage Paper 29 — documento público de dominio abierto: `https://www.fao.org/4/t0234e/t0234e00.htm`). Estas tablas se cargan como datos estáticos versionados en el sistema (igual que las tablas de pH óptimo por cultivo), **no como llamada externa**. El dato de laboratorio (CE, RAS, cloruros, boro) se captura manualmente porque no hay servicio gratuito que lo mida a distancia.

**Migración `023_analisis_agua_riego.sql`:**
```sql
CREATE TABLE agroia.analisis_agua_riego (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finca_id UUID NOT NULL REFERENCES agroia.fincas(id) ON DELETE CASCADE,
    lote_id UUID REFERENCES agroia.lotes(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    ce_agua_ds_m NUMERIC(6,3),
    ras NUMERIC(6,2),                 -- Relación de Adsorción de Sodio
    cloruros_mg_l NUMERIC(8,2),
    boro_mg_l NUMERIC(6,3),
    ph_agua NUMERIC(4,2),
    fuente VARCHAR(20) DEFAULT 'laboratorio',  -- laboratorio | manual | sin_dato
    clasificacion_restriccion VARCHAR(30),     -- calculada: ninguna | leve_moderada | severa
    creado_por UUID REFERENCES agroia.usuarios(id),
    creado_en TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_agua_riego_finca ON agroia.analisis_agua_riego(finca_id, fecha DESC);
```

**Endpoints:**

`POST /api/v1/fincas/{finca_id}/agua-riego` — Admin/Agrónomo

Request:
```json
{
  "lote_id": "uuid | null",
  "fecha": "2026-08-27",
  "ce_agua_ds_m": 1.8,
  "ras": 6.2,
  "cloruros_mg_l": 120.0,
  "boro_mg_l": 0.4,
  "ph_agua": 7.1
}
```
Response `201`:
```json
{
  "id": "uuid",
  "clasificacion_restriccion": "leve_moderada",
  "detalle": [
    { "parametro": "CE", "valor": 1.8, "rango_ninguna": "<0.7", "rango_severa": ">3.0", "estado": "leve_moderada" },
    { "parametro": "RAS", "valor": 6.2, "estado": "ninguna" }
  ],
  "recomendacion": "Vigilar acumulación de sales en el perfil; considerar lavado periódico del suelo."
}
```

`GET /api/v1/fincas/{finca_id}/agua-riego` — historial, todos los roles con acceso a la finca.

**Regla de degradación:** si no hay análisis registrado, el reporte agrega a la sección `P` (parámetros faltantes): *"Sin análisis de calidad de agua de riego — recomendado si el sistema usa fuente de pozo o reservorio con posible salinidad"*. No bloquea nada.

**Menú:** nueva pestaña dentro del panel de una finca → **"💧 Agua de riego"** (junto a "🗂️ Lotes"), visible cuando `tipo_riego ≠ Secano`.

**Roles:** Admin/Agrónomo registran y editan; Cliente solo lectura.

---

### 1.B · Curvas de extracción nutricional por etapa fenológica

**Objetivo:** ponderar las acciones de fertilización según cuánto nutriente extrae realmente el cultivo en la etapa fenológica actual (ya capturada en `fincas.etapa_fenologica`), en vez de comparar siempre contra un rango estático fijo.

**Fuente de datos:** no existe API. Debe curarse manualmente por el equipo agronómico desde fuentes documentales públicas:
- Agrosavia — fichas técnicas por cultivo: `https://www.agrosavia.co/`
- Cenicafé — manual del cafetero, curva de absorción de café: `https://www.cenicafe.org/es/publications/`
- FAO — boletines de nutrición vegetal y fertilización por cultivo (serie *Fertilizer and Plant Nutrition Bulletins*): `https://www.fao.org/soils-portal/en/`

**Migración `024_curvas_extraccion.sql`:**
```sql
CREATE TABLE agroia.curvas_extraccion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cultivo_id UUID NOT NULL REFERENCES agroia.cultivos(id) ON DELETE CASCADE,
    etapa_fenologica VARCHAR(30) NOT NULL,  -- Vegetativo | Floración | Fructificación | Cosecha
    nutriente VARCHAR(10) NOT NULL,         -- N | P | K | Ca | Mg | S
    pct_extraccion_acumulado NUMERIC(5,2) NOT NULL,  -- 0-100
    fuente TEXT,
    UNIQUE(cultivo_id, etapa_fenologica, nutriente)
);
```

**Endpoints:**

`GET /api/v1/cultivos/{cultivo_id}/curva-extraccion` → lista completa por etapa/nutriente.

`PUT /api/v1/cultivos/{cultivo_id}/curva-extraccion` — Admin/Agrónomo (carga o corrección editorial)
```json
{ "puntos": [
  { "etapa_fenologica": "Floración", "nutriente": "K", "pct_extraccion_acumulado": 35.0, "fuente": "Cenicafé, manual del cafetero cap. 4" }
]}
```

**Regla de degradación:** si el cultivo/etapa no tiene curva cargada, el motor sigue usando el rango estático genérico (comportamiento actual) y la fila del diagnóstico muestra `"curva_extraccion": "no_disponible"` — la acción se genera igual, solo sin el matiz de ponderación por etapa.

**Menú:** dentro de Catálogo → ficha de cultivo → pestaña **"📈 Curva de extracción"** (Admin/Agrónomo editan; consulta libre).

---

### 1.C · Balance hídrico (ETo/Kc) — necesidad real de riego

**Objetivo:** pasar de "se pronostica lluvia" a "su cultivo necesita X mm esta semana", cruzando evapotranspiración de referencia con el coeficiente de cultivo (Kc) por etapa.

**Fuente de datos — real, gratuita, ya integrada parcialmente (Open-Meteo ya se usa para clima/alertas):**

`GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&daily=et0_fao_evapotranspiration,precipitation_sum&timezone=America%2FBogota&forecast_days=7`

Open-Meteo expone <cite index="26-1">ET₀ Reference Evapotranspiration, calculado con el método estándar de la industria FAO-56 Penman-Monteith a partir de temperatura, viento, humedad e irradiación solar</cite>, en <cite index="26-1">milímetros, disponible como suma diaria además de valores horarios</cite>. Es gratuita para uso no comercial/open-source, sin necesidad de API key (mismo proveedor ya usado para `fetch_pronostico_open_meteo`).

Response de ejemplo (recortado):
```json
{
  "daily": {
    "time": ["2026-08-27", "2026-08-28"],
    "et0_fao_evapotranspiration": [4.1, 3.8],
    "precipitation_sum": [2.0, 15.0]
  }
}
```

**Kc (coeficiente de cultivo):** tabla pública FAO-56 (`Allen, Pereira, Raes, Smith — Crop evapotranspiration, FAO Irrigation and Drainage Paper 56`, dominio público: `https://www.fao.org/3/x0490e/x0490e00.htm`). Se carga como campos estáticos por cultivo, no vía API:

**Migración `025_kc_cultivo.sql`:**
```sql
ALTER TABLE agroia.cultivos
  ADD COLUMN kc_inicial NUMERIC(3,2),
  ADD COLUMN kc_medio NUMERIC(3,2),
  ADD COLUMN kc_final NUMERIC(3,2);
```

**Endpoint nuevo:**

`GET /api/v1/fincas/{finca_id}/balance-hidrico?lote_id=&dias=7`

Response:
```json
{
  "finca_id": "uuid",
  "cultivo": "Aguacate",
  "etapa_fenologica": "Floración",
  "kc_aplicado": 0.85,
  "dias": [
    { "fecha": "2026-08-27", "et0_mm": 4.1, "etc_mm": 3.49, "precipitacion_mm": 2.0, "deficit_mm": 1.49 },
    { "fecha": "2026-08-28", "et0_mm": 3.8, "etc_mm": 3.23, "precipitacion_mm": 15.0, "deficit_mm": 0 }
  ],
  "deficit_acumulado_7d_mm": 1.49,
  "recomendacion": "Riego suplementario de ~1.5 mm en los próximos días; el resto de la semana la lluvia cubre la demanda."
}
```

**Regla de degradación:** si el cultivo no tiene `kc_*` cargado, se usa un Kc genérico por categoría (frutal perenne 0.75 / cereal 0.90 / hortaliza 0.95 / tubérculo 0.85) y la respuesta marca `"kc_aplicado_generico": true`. Si no hay coordenadas de finca, el bloque se omite (mismo patrón que el clima IDEAM actual).

**Menú:** nuevo bloque **"💧 Necesidad de riego (7 días)"** en el Dashboard (P1) y en la sección N del reporte, junto al pronóstico extendido ya existente.

**Roles:** lectura para todos los roles con acceso a la finca; sin escritura (es cálculo derivado).

---

### 1.D · Monitoreo Integrado de Plagas (MIP)

**Objetivo:** pasar de alerta puramente predictiva (clima+cultivo) a monitoreo real de campo, retroalimentando las alertas fitosanitarias con datos de incidencia observada.

**Fuentes de datos externas, reales y gratuitas:**

1. **GBIF (Global Biodiversity Information Facility)** — ocurrencias históricas reportadas de una especie/plaga en Colombia, gratis y sin API key:
`GET https://api.gbif.org/v1/occurrence/search?scientificName={nombre_cientifico_plaga}&country=CO&limit=50`

2. **EPPO Data Services** — fichas de plagas reguladas (distribución, hospederos, código EPPO), gratis con token de registro (`https://data.eppo.int/`, registro de token sin costo):
`GET https://data.eppo.int/api/rest/1.0/tools/search?kw={nombre_plaga}&authtoken={token}`

Ambas se usan como **enriquecimiento informativo** (contexto de distribución/hospedero), no como fuente primaria del diagnóstico — la fuente primaria sigue siendo el registro de campo del agrónomo/agricultor.

**Migración `026_monitoreo_plagas.sql`:**
```sql
CREATE TABLE agroia.monitoreo_plagas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finca_id UUID NOT NULL REFERENCES agroia.fincas(id) ON DELETE CASCADE,
    lote_id UUID REFERENCES agroia.lotes(id) ON DELETE CASCADE,
    cultivo_id UUID REFERENCES agroia.cultivos(id),
    fecha DATE NOT NULL,
    plaga_nombre VARCHAR(120) NOT NULL,
    plaga_nombre_cientifico VARCHAR(150),
    metodo VARCHAR(30),          -- trampa | inspeccion_visual | otro
    severidad VARCHAR(10),       -- Baja | Media | Alta
    incidencia_pct NUMERIC(5,2),
    observaciones TEXT,
    foto_url VARCHAR(500),
    creado_por UUID REFERENCES agroia.usuarios(id),
    creado_en TIMESTAMPTZ DEFAULT now()
);
```

**Endpoints:**

`POST /api/v1/fincas/{finca_id}/lotes/{lote_id}/monitoreo-plagas` — Admin/Agrónomo
```json
{
  "cultivo_id": "uuid",
  "fecha": "2026-08-27",
  "plaga_nombre": "Broca del café",
  "plaga_nombre_cientifico": "Hypothenemus hampei",
  "metodo": "trampa",
  "severidad": "Media",
  "incidencia_pct": 8.5,
  "observaciones": "12 trampas revisadas, promedio 3 individuos/trampa/semana"
}
```
Response `201` incluye `enriquecimiento_gbif` (conteo de ocurrencias reportadas en la zona, si la consulta tuvo resultados) como dato informativo adicional, sin afectar la clasificación.

`GET /api/v1/fincas/{finca_id}/lotes/{lote_id}/monitoreo-plagas` — historial.

**Regla de degradación:** sin registros de monitoreo, la alerta fitosanitaria sigue funcionando solo con el cruce clima+cultivo+fenología ya existente (comportamiento actual). Con registros, si `incidencia_pct` supera el umbral económico de daño del cultivo (tabla a cargar por cultivo, igual criterio que Kc/curvas), la prioridad de la alerta sube de "vigilancia" a "acción requerida".

**Menú:** nuevo submenú **"🐛 Monitoreo de plagas"** dentro del panel de lote (junto a "🔄 Ciclos" y "🗂️ Lotes"). Admin/Agrónomo registran; Cliente solo lectura.

---

### 1.E · Recomendación de variedades/cultivares

**Objetivo:** recomendar variedad, no solo especie, según altitud de la finca (ya georreferenciada).

**Fuente de datos:** ICA publica el Registro Nacional de Cultivares Comerciales, pero **no como API** — es consulta/documento en el portal institucional (`https://www.ica.gov.co/areas/agricolas/servicios/semillas`). Debe descargarse y curarse manualmente por el equipo agronómico, igual que Cenicafé para variedades de café (`https://www.cenicafe.org/es/index.php/nuestras_publicaciones/`).

**Migración `027_variedades_cultivo.sql`:**
```sql
CREATE TABLE agroia.variedades_cultivo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cultivo_id UUID NOT NULL REFERENCES agroia.cultivos(id) ON DELETE CASCADE,
    nombre_variedad VARCHAR(100) NOT NULL,
    resistencias TEXT,             -- ej. "Resistente a roya (Hemileia vastatrix)"
    altitud_min_msnm INT,
    altitud_max_msnm INT,
    mercado_objetivo VARCHAR(60),  -- consumo interno | exportación | industrial
    fuente TEXT
);
```

**Endpoints:**

`GET /api/v1/cultivos/{cultivo_id}/variedades?altitud_msnm=1450` — filtra por compatibilidad con la altitud dada (si se pasa el parámetro).

Response:
```json
{
  "cultivo": "Café",
  "variedades_compatibles": [
    { "nombre_variedad": "Castillo", "resistencias": "Roya, algo de broca", "altitud_min_msnm": 1200, "altitud_max_msnm": 2000, "mercado_objetivo": "exportación especial" }
  ]
}
```

**Regla de degradación:** sin variedades cargadas para el cultivo, la sección se omite silenciosamente del reporte (mismo patrón que ciclos/historial vacío).

**Menú:** nueva pestaña **"🌾 Variedades"** en la ficha de cada cultivo del Catálogo.

---

### 1.F · Rotación de cultivos (recomendación activa)

**Objetivo:** convertir el dato pasivo de `cultivo_anterior` (ya registrado en el historial) en una sugerencia activa de rotación.

**Fuente de datos:** no requiere API externa — es una tabla de reglas agronómicas internas (fijación de N por leguminosas, ruptura de ciclos de plagas por familia botánica), curada por el equipo agronómico con apoyo de literatura Agrosavia/FAO.

**Migración `028_compatibilidad_rotacion.sql`:**
```sql
CREATE TABLE agroia.compatibilidad_rotacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cultivo_actual_id UUID NOT NULL REFERENCES agroia.cultivos(id),
    cultivo_siguiente_id UUID NOT NULL REFERENCES agroia.cultivos(id),
    beneficio VARCHAR(20),  -- fijacion_n | ruptura_plaga | recuperacion_estructura
    motivo TEXT
);
```

**Endpoint:** `GET /api/v1/fincas/{finca_id}/recomendacion-rotacion` — usa el último ciclo cerrado del lote principal + esta tabla.

Response:
```json
{
  "cultivo_actual": "Maíz",
  "sugerencias": [
    { "cultivo": "Fríjol", "beneficio": "fijacion_n", "motivo": "Leguminosa: aporta N al suelo tras un cereal exigente en nitrógeno" }
  ]
}
```

**Regla de degradación:** sin historial de ciclos o sin reglas de compatibilidad cargadas para ese cultivo, el bloque se omite.

**Menú:** nuevo bloque **"🔄 Rotación sugerida"** dentro de la sección 02 del reporte (Recomendación de siembra) y en el panel de "Registrar nuevo ciclo".

---

### 1.G · Trazabilidad BPA / certificación para exportación

**Objetivo:** convertir el registro de labores (ya existente) en un reporte de trazabilidad usable para certificación (Buenas Prácticas Agrícolas, período de carencia de agroquímicos).

**Fuente normativa:** Resolución ICA 30021 de 2017 (BPA) — documento público, no API: `https://www.ica.gov.co/getattachment/8232ac8a-f0be-4463-a0e9-2fa62c8b7dc4/2017r30021.aspx`. Se convierte en checklist estático versionado.

**Migración `029_checklist_bpa.sql`:**
```sql
CREATE TABLE agroia.checklist_bpa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finca_id UUID NOT NULL REFERENCES agroia.fincas(id) ON DELETE CASCADE,
    item VARCHAR(200) NOT NULL,
    categoria VARCHAR(60),      -- suelo_agua | agroquimicos | trabajadores | poscosecha
    cumple BOOLEAN,
    evidencia_url VARCHAR(500),
    fecha_verificacion DATE,
    verificado_por UUID REFERENCES agroia.usuarios(id)
);
```

**Endpoints:**

`GET/PUT /api/v1/fincas/{finca_id}/bpa/checklist` — Admin/Agrónomo diligencian.

`GET /api/v1/fincas/{finca_id}/bpa/reporte-trazabilidad` — arma el reporte combinando `labores` (producto/dosis/fecha) con período de carencia por producto (tabla nueva `agroia.periodos_carencia`, producto → días) y el estado del checklist.

**Regla de degradación:** sin checklist diligenciado, el reporte se genera igual marcando cada ítem como "pendiente de verificación" — no bloquea, sirve para ver avance.

**Menú:** nuevo ítem **"📋 Trazabilidad / BPA"** dentro del menú ⚙️ Administración (Admin) y visible en solo-lectura para Agrónomo.

---

### 1.H · Compactación del suelo

**Objetivo:** complementar `profundidad_suelo_cm` y `pedregosidad` (ya existentes) con resistencia a la penetración — no hay fuente pública, es dato de campo (penetrómetro).

**Migración `030_compactacion_lote.sql`:**
```sql
ALTER TABLE agroia.lotes ADD COLUMN resistencia_penetracion_kpa NUMERIC(6,2);
```

**Endpoint:** se agrega como campo opcional a `PATCH /api/v1/fincas/{id}/lotes/{lote_id}` (endpoint ya existente, no requiere ruta nueva).

**Regla de degradación:** campo opcional; sin dato no afecta ninguna clasificación existente, solo se muestra "sin medir" en el detalle del lote.

**Menú:** campo nuevo en el formulario ya existente de edición de lote — no requiere ítem de menú nuevo.

---

### 1.I · Notificaciones WhatsApp / SMS

**Objetivo:** el canal real de adopción rural no es el dashboard web — es WhatsApp.

**Fuente/servicio — WhatsApp Business Cloud API (Meta), gratuita hasta un umbral de conversaciones iniciadas por el negocio por mes (verificar tarifario vigente de Meta al integrar, ya que cambia periódicamente); requiere cuenta de WhatsApp Business verificada:**

`POST https://graph.facebook.com/v20.0/{phone_number_id}/messages`
```json
{
  "messaging_product": "whatsapp",
  "to": "57XXXXXXXXXX",
  "type": "template",
  "template": { "name": "alerta_lluvia_aplicacion", "language": { "code": "es_CO" },
    "components": [{ "type": "body", "parameters": [{ "type": "text", "text": "Urea" }, { "type": "text", "text": "28/08/2026" }] }] }
}
```

**SMS (fallback, servicio de pago, no hay gratuito real a escala en Colombia):** Twilio (`https://www.twilio.com/docs/sms`) o proveedores locales (Infobip). Se documenta como alternativa, no como requisito de la primera versión.

**Migración `031_preferencias_notificacion.sql`:**
```sql
CREATE TABLE agroia.preferencias_notificacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES agroia.usuarios(id),
    finca_id UUID REFERENCES agroia.fincas(id),
    canal VARCHAR(20) DEFAULT 'ninguno',  -- whatsapp | sms | email | ninguno
    telefono VARCHAR(20),
    activo BOOLEAN DEFAULT true
);
```

**Endpoints:**

`PUT /api/v1/fincas/{finca_id}/notificaciones/preferencias`
```json
{ "canal": "whatsapp", "telefono": "573001234567", "activo": true }
```

El servicio `services/notificaciones.py::enviar_whatsapp()` se invoca desde el mismo job de alertas climáticas (sección 6.13 del documento funcional) y desde el vencimiento próximo de `labores` — reutiliza disparadores existentes, no crea un nuevo scheduler.

**Regla de degradación:** sin canal configurado, el sistema sigue funcionando solo con el dashboard (comportamiento actual). No bloquea nada.

**Menú:** nuevo panel **"🔔 Notificaciones"** en el perfil de usuario / dentro de la ficha de finca.

**Roles:** cada usuario configura su propio canal; Admin puede configurar el de cualquier finca.

---

### 1.J · Rol Extensionista / Asatec (multi-finca por zona)

**Objetivo:** cubrir el modelo de extensión rural (Asatec, técnicos de asociaciones/cooperativas) que necesitan ver varias fincas de su zona, sin ser Admin global.

**Migración `032_rol_extensionista.sql`:**
```sql
ALTER TYPE agroia.rolusuario ADD VALUE 'Extensionista';
ALTER TABLE agroia.usuarios ADD COLUMN municipios_asignados TEXT[];
```

**Endpoint:** `GET /api/v1/extensionista/dashboard-zona` — Extensionista
```json
{
  "municipios": ["Circasia", "Filandia"],
  "fincas": [
    { "id": "uuid", "nombre": "Finca Demo Integral", "cultivo_sembrado": "Aguacate", "ultima_recomendacion": { "clasificacion": "Apta", "confianza": 0.57 }, "alertas_activas": 1 }
  ],
  "resumen": { "total_fincas": 12, "alertas_climaticas_activas": 3, "recomendaciones_pendientes_validacion": 5 }
}
```

`services/acceso.py::fincas_permitidas_ids` se extiende: para rol Extensionista, filtra por `finca.municipio IN usuario.municipios_asignados` (no `None`/todas como Admin/Agrónomo, ni solo email como Cliente).

**Menú:** nueva pestaña **"🗺️ Mi zona"**, visible solo para este rol, como landing tras login.

Ver matriz completa de permisos en la sección 4.

---

## 2. Ampliación del catálogo de cultivos (Colombia)

Cultivos a incorporar, con ícono propuesto siguiendo la misma regla de gobernanza definida en la especificación v3 (usar carácter Unicode exacto cuando exista sin ambigüedad; marcar "ícono custom pendiente" cuando no exista, nunca dejar 🌱 de forma permanente en catálogo activo).

| Cultivo nuevo | Ícono propuesto | Justificación / fuente de ficha técnica de referencia |
|---|---|---|
| **Panela / Caña panelera** *(separar de Caña de azúcar)* | ✅ `img/iconos/panela.svg` (creado — bloque de panela) | Fedepanela: `https://fedepanela.org.co/` · UPRA ficha de zonificación de caña panelera |
| Ñame | 🍠 *(aproximado — tubérculo, no exacto)* | Agrosavia / Corpoica Caribe — ficha regional Córdoba-Sucre |
| Chontaduro | ✅ `img/iconos/chontaduro.svg` (creado — racimo de frutos de palma) | Agrosavia — zona Pacífico/Amazonía |
| Lulo | ✅ `img/iconos/lulo.svg` (creado — fruto naranja con cáliz) | Agrosavia — ficha técnica lulo de Castilla |
| Mora | 🫐 *(aproximado — mora de zarza real distinta a blueberry, sin emoji exacto)* | Agrosavia — mora de Castilla |
| Guayaba | ✅ `img/iconos/guayaba.svg` (creado — fruto verde con hojas) | Corpoica / cadena guayaba-bocadillo Santander |
| Granadilla / Curuba | ✅ `img/iconos/granadilla.svg` (creado — fruto naranja punteado) | Agrosavia — frutales pasifloráceas |
| Arveja | 🫛 | FAO / Agrosavia — leguminosas de clima frío |
| Habichuela | ✅ `img/iconos/habichuela.svg` (creado — vaina verde) | Agrosavia — hortalizas Cundinamarca-Boyacá |
| Ahuyama / Auyama | ✅ `img/iconos/ahuyama.svg` (creado — cucurbitácea naranja) | Agrosavia — hortalizas |
| Fresa | 🍓 | Agrosavia — frutales de clima frío moderado |
| Coco | 🥥 | Agrosavia — Caribe y Pacífico |
| Caucho | ✅ `img/iconos/caucho.svg` (creado — árbol con copa de látex) | Agrosavia / programas de sustitución de cultivos (Meta, Caquetá) |
| Fique | ✅ `img/iconos/fique.svg` (creado — roseta de agave) | Agrosavia — fibra Cauca/Nariño/Santander |
| Quinua | 🌾 *(compartido con cereales — ambigüedad ya señalada en v3, reforzar necesidad de set custom)* | Agrosavia — Nariño/Boyacá |

**Endpoint de alta de cultivo (ya existe, `POST /api/v1/cultivos` — extender el contrato para exigir ícono explícito):**
```json
{
  "nombre": "Panela / Caña panelera",
  "nombre_cientifico": "Saccharum officinarum (var. panelera)",
  "icono": "custom:panela_v1",
  "descripcion": "Principal producto agrícola exclusivamente colombiano; ~200.000 ha, 350.000 familias.",
  "fisiologia": { "profundidad_radicular_min_cm": 60, "dias_ciclo": 450 }
}
```
**Regla de validación en el endpoint:** el backend debe **rechazar** con `422 ICONO_REQUERIDO` cualquier alta de cultivo activo sin campo `icono` explícito — así se evita que 🌱 quede como valor por defecto permanente (cierra el gap señalado en la especificación v3, sección 4.2).

---

## 3. Reentrenamiento del modelo ML con los cultivos nuevos

**Realidad a documentar con honestidad:** no existe un dataset descargable, listo para entrenar, específico de NPK/pH por cultivo para estos 15 cultivos nuevos. El mismo método ya usado para los 30 cultivos actuales (75.000 perfiles sintéticos generados con `RANGOS` por variable, sección 10.1 del documento funcional) es el camino correcto — se trata de **curar los rangos de referencia**, no de descargar un dataset externo listo.

**Fuentes documentales para curar los `RANGOS` de cada cultivo nuevo** (no APIs, son publicaciones a consultar por el equipo agronómico):
- Agrosavia — fichas técnicas por cultivo: `https://www.agrosavia.co/`
- Fedepanela — ficha técnica de caña panelera: `https://fedepanela.org.co/gremio/`
- UPRA — zonificación de aptitud por cultivo (incluye rangos edafoclimáticos): `https://upra.gov.co/`
- ICA — requisitos fitosanitarios y de semillas por cultivo: `https://www.ica.gov.co/`

**Fuente pública para validar `rendimiento_esperado` (usado en la validación anti-outliers, sección 6.17 del documento funcional):**
- FAOSTAT (producción y rendimiento por cultivo y país, API gratuita): `https://fenixservices.fao.org/faostat/api/v1/es/data/QCL?area=Colombia&item={cultivo}`
- UPRA / EVA — rendimiento por departamento en Colombia, portal de datos abiertos (Socrata, gratuito): `https://www.datos.gov.co/resource/{dataset_id}.json` (dataset "Evaluaciones Agropecuarias Municipales EVA" — verificar el identificador vigente del dataset en `datos.gov.co` al integrar, ya que UPRA publica versiones actualizadas periódicamente).

**Flujo de reentrenamiento propuesto:**
1. El equipo agronómico completa `RANGOS[cultivo_nuevo]` en `apps/ml/agroia_ml/train_colombia.py` con los rangos curados de las fuentes anteriores.
2. Se agrega el cultivo al catálogo (sección 2) con `activo=true`.
3. Se dispara el reentrenamiento.

**Endpoint nuevo (hoy el reentrenamiento es solo CLI — se propone exponerlo para trazabilidad y control de acceso):**

`POST /api/v1/admin/ml/reentrenar` — solo Admin
```json
{ "cultivos_incluidos": ["uuid-panela", "uuid-lulo", "uuid-fresa"], "modo": "active-learning" }
```
Response `202`:
```json
{ "job_id": "uuid", "estado": "en_cola", "mensaje": "Reentrenamiento encolado; ejecuta train_colombia.py --registrar --active-learning con los cultivos indicados" }
```
Ejecuta el mismo script ya existente como tarea en background; registra auditoría `ml.reentrenar` con el detalle de qué cultivos se agregaron.

**Regla de degradación:** un cultivo nuevo sin modelo ML propio (STAGING vacío) sigue recomendándose por el **sistema experto de reglas** (que es la fuente de verdad, sección 2 del documento funcional) — el ML en sombra simplemente no tendrá predicción para ese cultivo hasta el próximo reentrenamiento. No bloquea el análisis ni el reporte.

**Menú:** dentro de ⚙️ Administración, nuevo ítem **"🤖 Reentrenar modelo"** con selector de cultivos nuevos/pendientes y estado del último job.

---

## 4. Matriz de roles y permisos actualizada

| Módulo / acción | Admin | Agrónomo | **Extensionista (nuevo)** | Cliente |
|---|---|---|---|---|
| Ver fincas | Todas | Todas | Solo su(s) municipio(s) asignado(s) | Solo las suyas |
| Registrar/editar finca | ✅ | ❌ | ❌ | ❌ |
| Editar datos agronómicos de finca | ✅ | ✅ | ✅ (solo fincas de su zona) | ❌ |
| Agua de riego — registrar | ✅ | ✅ | ✅ (su zona) | ❌ lectura |
| Balance hídrico (ETo/Kc) | Lectura | Lectura | Lectura | Lectura |
| Monitoreo de plagas — registrar | ✅ | ✅ | ✅ (su zona) | ❌ lectura |
| Variedades — administrar catálogo | ✅ | ✅ | ❌ lectura | ❌ lectura |
| Rotación — ver sugerencia | ✅ | ✅ | ✅ | ✅ |
| Checklist BPA — diligenciar | ✅ | ✅ (su zona en revisión) | ❌ lectura | ❌ lectura |
| Notificaciones — configurar propias | ✅ | ✅ | ✅ | ✅ |
| Notificaciones — configurar de terceros | ✅ | ❌ | ❌ | ❌ |
| Dashboard consolidado de zona | ✅ (todas) | ❌ | ✅ (la suya) | ❌ |
| Reentrenar modelo ML | ✅ | ❌ | ❌ | ❌ |
| Alta de cultivo en catálogo | ✅ | ✅ (sujeto a revisión editorial existente) | ❌ | ❌ |
| Auditoría | ✅ | ❌ | ❌ | ❌ |

**Nota de implementación:** el Extensionista reutiliza `exigir_no_cliente()` (ya existe, permite escritura) pero necesita una nueva función `filtrar_por_zona(db, municipios_asignados)` en `services/acceso.py`, análoga a `fincas_permitidas_ids` pero por municipio en vez de por email.

---

## 5. Estructura de navegación resultante (menú/submenú)

```
🔐 P0 · Inicio de sesión
🏠 P1 · Inicio (Dashboard)
   └─ NUEVO: bloque "💧 Necesidad de riego (7 días)"
🗺️ NUEVA PESTAÑA · "Mi zona" (solo rol Extensionista, landing tras login)
🏡 P2 · Fincas
   └─ Panel de finca:
        └─ NUEVA PESTAÑA: "💧 Agua de riego"
        └─ 🗂️ Lotes
             └─ NUEVO SUBMENÚ: "🐛 Monitoreo de plagas"
             └─ 🔄 Ciclos (existente)
                 └─ NUEVO bloque: "🔄 Rotación sugerida" dentro del flujo de nuevo ciclo
📡 P3 · Sensores IoT
📁 P4 · Cargar archivo
🧪 P5 · Recomendaciones
📜 P6 · Historial
📄 P7 · Reportes
   └─ Sección N del reporte: agrega balance hídrico + rotación sugerida
   └─ Nueva sección de reporte: "Trazabilidad BPA" (bajo demanda)
💬 P8 · Chat asesor
🌾 P10 · Catálogo
   └─ Ficha de cultivo:
        └─ NUEVA PESTAÑA: "📈 Curva de extracción"
        └─ NUEVA PESTAÑA: "🌾 Variedades"
   └─ NUEVA SECCIÓN: "🏪 Proveedores" (directorio de insumos, autoregistro moderado)
⚙️ Administración (solo Admin)
   └─ 👥 Usuarios
   └─ 💰 Insumos
   └─ 🕵️ Auditoría
   └─ NUEVO: "📋 Trazabilidad / BPA" (checklist por finca)
   └─ NUEVO: "🤖 Reentrenar modelo"
🔔 NUEVO PANEL · "Notificaciones" (perfil de usuario / ficha de finca)
```

---

## 6. Resumen de migraciones propuestas (023 → 032)

| # | Migración | Tablas/campos |
|---|---|---|
| 023 | `analisis_agua_riego` | Tabla nueva |
| 024 | `curvas_extraccion` | Tabla nueva |
| 025 | `kc_cultivo` | Campos en `cultivos` |
| 026 | `monitoreo_plagas` | Tabla nueva |
| 027 | `variedades_cultivo` | Tabla nueva |
| 028 | `compatibilidad_rotacion` | Tabla nueva |
| 029 | `checklist_bpa` (+ `periodos_carencia`) | Tablas nuevas |
| 030 | `compactacion_lote` | Campo en `lotes` |
| 031 | `preferencias_notificacion` | Tabla nueva |
| 032 | `rol_extensionista` | Enum `rolusuario` + campo en `usuarios` |

**Todas siguen el patrón de auto-reparación ya existente** (`asegurar_enums()` / migraciones idempotentes en `lifespan`) para no romper el arranque en producción.

---

## 7. Priorización de implementación

| Prioridad | Módulos |
|---|---|
| **Bloqueante / alto impacto en adopción** | 1.I Notificaciones WhatsApp (canal real de uso rural) · 2 Ampliar catálogo (panela/caña panelera separada — corrige el gap más citado) |
| **Alto valor agronómico, esfuerzo medio** | 1.C Balance hídrico ETo/Kc (fuente ya integrada, solo falta Kc + endpoint) · 1.F Rotación de cultivos (reutiliza datos ya existentes) |
| **Alto valor, requiere curaduría de datos** | 1.A Agua de riego · 1.B Curvas de extracción · 1.E Variedades |
| **Estratégico institucional** | 1.J Rol Extensionista · 1.G Trazabilidad BPA |
| **Complementario** | 1.D Monitoreo de plagas · 1.H Compactación · 3 Reentrenamiento ML de cultivos nuevos (depende de que el catálogo y las fichas estén curadas primero) |

**Nota final de gobernanza:** igual que en la especificación v3, todas las tablas de referencia estática (FAO-29 agua, FAO-56 Kc, curvas de extracción, umbrales de plagas, checklist BPA) deben tratarse como **datos versionados**, no hardcode — permite corrección por un agrónomo sin necesidad de despliegue de código, y deja trazabilidad de quién y cuándo cambió cada valor.
