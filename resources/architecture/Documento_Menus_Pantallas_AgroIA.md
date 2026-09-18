# AgroIA — Funcionalidades, menús por rol y pantallas

> Documento actualizado a **v3.5** (2026-09-18) · fuente: SPA `apps/frontend-web/` (index.html + app.js) y
> `Documento_Funcional_Tecnico_AgroIA.md`. Incluye la mejora de **clima actual + pronóstico semanal**
> en las alertas (commits 918f2a8 → cdf5228, desplegado en producción).

---

## 1. Qué es AgroIA

Plataforma de **diagnóstico agronómico para Colombia** que combina sensores IoT, análisis de suelo,
clima y un motor de reglas (UPRA / Cenicafé / AGROSAVIA) con ML en modo sombra. Funciona como un
**agrónomo virtual**: recomienda qué sembrar, qué fertilizar, dónde abonar, cuándo regar y proyecta
rendimiento y rentabilidad.

- **App web:** SPA (HTML + JavaScript vanilla) con PWA instalable y funcionamiento offline básico.
- **Backend:** FastAPI (`/api/v1`) con PostgreSQL, JWT, roles y trazabilidad total.
- **Roles:** Administrador, Agrónomo, Cliente y Extensionista (además de Técnico e Investigador,
  definidos como perfiles auxiliares sin menú propio).

---

## 2. Pantalla de autenticación

**Quién la ve:** todos (pantalla inicial sin sesión).

| Elemento | Qué hace |
|---|---|
| Formulario **Email / Contraseña** | Login JWT (access 8 h + refresh 30 días). |
| Botones **Cuentas de prueba** | Login de un clic con cuentas demo: Administrador, Agrónomo, Cliente (María), Cliente (Finca Demo) y Extensionista. |
| Cierre de sesión | Botón «Salir» en la barra superior. |

Tras iniciar sesión, el menú superior se adapta al rol: **cada usuario solo ve las pestañas de su rol**.

---

## 3. Barra superior (común a todos los roles)

- **Identidad:** nombre y rol del usuario activo.
- **Pills de estado:** API · BD · IoT (salud de los servicios).
- **Menú ❓ Ayuda:** manuales de usuario por rol (Administrador, Agrónomo, Cliente) y
  «🎓 Capacitación — flujo completo».
- **PWA:** instalable; banner «📡 N registro(s) pendientes de sincronizar» y sincronización
  automática de tramas y labores capturadas sin conexión.

---

## 4. Opciones de menú por rol

### 🟢 Cliente (agricultor — solo lectura)

| Pestaña | Qué puede hacer |
|---|---|
| 🏠 **Inicio** | Ver el semáforo de su finca, KPIs, alertas, lecturas, necesidad de riego y tareas. |
| 🌙 **Alertas clima y fases lunares** | Ver alertas activas de sus fincas (con clima actual y pronóstico de 7 días), calendario lunar y activar/desactivar alertas Bristol. |
| 📄 **Reportes** | Generar reportes de sus fincas (HTML/PDF) con el **chat asesor agronómico**. |

> No puede analizar suelo, cargar mediciones ni administrar. En los reportes, la vista en vivo
> usa automáticamente **lenguaje simple de agricultor**.

### 🧑‍🌾 Agrónomo (técnico de campo)

| Pestaña | Qué puede hacer |
|---|---|
| 🏠 **Inicio** | Dashboard completo de la finca seleccionada (semáforo, KPIs, alertas, riego, labores). |
| 🌙 **Alertas clima y fases lunares** | Ver alertas de todas las fincas (agrupadas por ubicación) y calendario lunar. |
| 📡 **Sensores IoT** | Monitorear lecturas, dispositivos, estado de conexión y **probar tramas con el simulador**. |
| 📂 **Cargar archivo** | Cargar mediciones (CSV/TXT/JSON) y obtener recomendación al instante; carga masiva de historial de ciclos. |
| 🧪 **Recomendaciones** | Elegir finca/cultivo y **«Analizar suelo»** (UC1 qué sembrar / UC2 diagnóstico), registrar nuevos ciclos y aceptar recomendaciones. |
| 📜 **Historial** | Historial de recomendaciones de las fincas. |
| 📄 **Reportes** | Generar reportes (siembra/cultivo/completo), vista previa, exportar por audiencia, **simular enmiendas** (what-if) y usar el chat asesor. |
| 🔬 **Visión plagas** | Subir foto de un síntoma y obtener diagnóstico visual preliminar con historial. |
| 🌾 **Catálogo** | Consultar el catálogo de cultivos (fichas, fisiología, variedades). |

> No puede registrar fincas ni acceder a Administración.

### 👑 Administrador (todo el poder)

Ve **todas las pestañas del Agrónomo** más «🏡 Fincas» y el submenú **⚙️ Administración**:

| Pestaña | Qué hace |
|---|---|
| 🏡 **Registrar finca** | Wizard de 3 pasos (datos básicos → ubicación con mapa/GPS/enlace → características del predio) con validación automática. |
| 🗂️ **Fincas** | Listado de fincas con administración de **lotes** (crear/editar/eliminar, características de suelo) y **ciclos productivos** (registrar, cosechar, histórico). |
| 👥 **Administrar usuarios** | Crear/editar/desactivar usuarios, cambiar rol y asignar fincas visibles. |
| 💰 **Administrar insumos** | Precios por kg de los 14 insumos del plan económico (urea, DAP, KCl, cal…). |
| 🌾 **Precios de cosecha** | Precio por cultivo + departamento para la utilidad estimada del ranking. |
| 🕵️ **Auditoría** | Bitácora de acciones (fincas, lotes, usuarios, inicios de sesión, demo). |
| 📋 **Trazabilidad / BPA** | Checklist ICA 30021/2017, períodos de carencia y visitas de verificación. |
| 🧑‍🤝‍🧑 **Equipo de trabajo** | Empleados de campo, tarifas por rol y novedades (incapacidades con reemplazo). |
| 🗂️ **Comisiones** | Comisiones de toma de medidas por finca: equipo, fechas, estados y valores. |
| 📊 **Lista de trabajos** | Cada finca como orden de trabajo con semáforo de etapa y gráfico por etapa. |
| 🤖 **Reentrenar modelo** | Encolar reentrenamiento del ML (active learning o completo). |
| 🔄 **Evaluar ahora** (en Alertas clima) | Disparar manualmente la evaluación de alertas climáticas de todas las fincas. |

### 🗺️ Extensionista

| Pestaña | Qué hace |
|---|---|
| 🗺️ **Mi zona** | Landing tras login: fincas de sus municipios asignados (datos y alertas de su territorio). |
| 🌙 **Alertas clima y fases lunares** | Alertas de las fincas de su zona. |
| 📡 **Sensores IoT** · 📜 **Historial** | Consulta de datos de las fincas de su zona. |
| 📄 **Reportes** | Generar reportes de las fincas de su zona. |
| 🔬 **Visión plagas** · 🌾 **Catálogo** | Diagnóstico visual y consulta del catálogo. |

---

## 5. Descripción de cada pantalla

### 5.1 🏠 Inicio (Dashboard) — todos los roles

- **Alertas activas de la finca** (banner) con el clima completo: temperatura actual, sensación
  térmica, humedad, viento, presión, UV y pronóstico de la semana.
- **Semáforo de aptitud** (🟢🟡🟠🔴) y KPIs de la última recomendación (pH, N, P, K, CE…).
- **Finca de análisis** (selector de finca) y **acciones rápidas** (cargar mediciones, generar
  recomendación, ver sensores).
- **💧 Necesidad de riego** de los próximos 7 días (ETo × Kc − lluvia; selector de modelo
  Auto / ECMWF IFS 0.25°).
- **📋 Tareas pendientes de hoy** (órdenes de trabajo) y **últimas lecturas** del sensor.
- Bloque **🔄 Ciclo activo** con «✏️ Cosechar ciclo» cuando hay un ciclo sin cerrar.

### 5.2 🌙 Alertas clima y fases lunares — todos los roles

- **Calendario lunar (Almanaque Bristol):** fase actual, iluminación, recomendación cultural de
  siembra, próximas lunas llena/nueva y calendario navegable por meses.
- **Preferencia personal:** «📅 Activar alertas de siembra según Almanaque Bristol».
- **Listado de alertas activas** agrupadas por tipo + ubicación (departamento/municipio).
  Cada tarjeta incluye:
  - **Clima del día en transcurso:** 🌡 temperatura, 🤚 sensación térmica, 💧 humedad, 🌬 viento,
    ráfagas, nubosidad, presión, UV y estado del cielo (WMO traducido al español).
  - **Pronóstico de la semana:** tabla de 7 días con mínima/máxima, lluvia (mm), probabilidad,
    viento, humedad y horas de sol; con refresco en vivo (endpoint `/fincas/{id}/clima`).
- Tipos de alerta: **⛅ lluvia/lixiviación** (aplazar fertilización), **🥶 helada en floración**
  y **📅 siembra lunar favorable**.
- Botón **🔄 Evaluar ahora** (solo Admin).

### 5.3 🗺️ Mi zona — Extensionista

Resumen de las fincas de los municipios asignados al extensionista (conteos y alertas activas de
su territorio).

### 5.4 📡 Sensores IoT — Admin / Agrónomo / Extensionista

- **🔗 Simulador de trama:** textarea con el formato real del firmware y botón «📡 Enviar trama»
  contra `POST /api/sensor` (muestra dispositivo, finca, variables recibidas y advertencias).
- **Dispositivos registrados** y **estado de conexión** por sensor
  (🟢 online < 12 h · 🟡 datos desactualizados < 24 h · 🔴 offline).
- **Historial de lecturas** con auto-refresco (10 s) y variables de suelo + ambientales.

### 5.5 📂 Cargar archivo — Admin / Agrónomo

- **Carga manual de mediciones** (CSV/TXT/JSON) cuando el sensor perdió conexión: normaliza
  unidades, persiste la lectura y **genera la recomendación al instante** (UC1 o UC2 según
  cultivo seleccionado). Archivos de ejemplo descargables.
- **🗂️ Carga masiva — historial de ciclos (CSV):** importa los últimos 5 años de ciclos
  (`lote, cultivo, fecha_siembra, fecha_cosecha, rendimiento, aplicaciones_texto`).

### 5.6 🧪 Recomendaciones — Admin / Agrónomo

La pantalla central del sistema:

- Formulario: **finca** (solo fincas con comisión), **cultivo** (vacío = UC1 «¿qué me conviene
  sembrar?»), **presupuesto $/ha** y **rendimiento actual t/ha** (ROI realista).
- Botones: **🌱 Registrar nuevo ciclo** y **🧪 Analizar suelo**.
- Resultado del análisis:
  - Badge de clasificación UPRA + estado de validación + barra de confianza.
  - Tabla de diagnóstico: variable, DÉFICIT/EXCESO/SIN DATO, lectura, rango ideal, acción,
    prioridad, confiabilidad y plan sugerido.
  - Fenología y GDD (cuánto falta para cosecha).
  - **💰 Plan económico vs. plan ideal** (incluidas/aplazadas según presupuesto).
  - **🌾 Ranking de cultivos sugeridos** (top 5 con score, confianza y reglas aplicadas),
    con badge «Más rentable» según precios de cosecha.
  - Bloque «📝 Complete los parámetros esenciales» con «💾 Guardar y reanalizar» cuando faltan
    pH/N/P/K.
  - Panel de aceptación (Admin/Agrónomo): «✅ Aceptar recomendación» con comentario.

### 5.7 📜 Historial — Admin / Agrónomo / Extensionista

Historial paginado de recomendaciones de la finca (fecha, cultivo, clasificación, confianza,
estado) y el bloque de ciclo activo con «Cosechar ciclo».

### 5.8 📄 Reportes — todos los roles

- **Generación:** finca (solo fincas con recomendación previa), tipo
  (**siembra / cultivo / completo**), modelo del pronóstico (Ambos / Auto / ECMWF), presupuesto
  y rendimiento actual.
- **Vista previa** con:
  - **Audiencia al exportar:** 👨‍🌾 Agricultor (lenguaje simple, siglas traducidas, telemetría
    colapsada, orden simple-primero) o 🧑‍🔬 Agrónomo (versión técnica completa).
  - **Abrir / Descargar HTML** e imprimir a PDF.
  - **🧪 Simular enmienda (what-if):** sliders de pH/N/P/K que re-evalúan el motor de reglas sin
    tocar la base de datos.
- **💬 Asesor agronómico (chat):** conversación sobre el reporte (cómo abonar, qué significa cada
  medición, qué sembrar) con memoria por finca y opción de adjuntar foto.
- El reporte HTML contiene: telemetría, escala de pH, diagnóstico, ranking de siembra, mapa de
  calor, plano del lote, análisis económico (ROI), advertencias, próximos pasos, pronóstico
  extendido 7 días, riego (R), rotación (S), BPA (B) y órdenes de trabajo (Q).

### 5.9 🏡 Registrar finca — Admin

Wizard de 3 secciones con validación automática (departamento/municipio reales, coordenadas
válidas, área razonable, precisión GPS):

1. **Información básica:** nombre, propietario, contacto, departamento (33) y municipio.
2. **Ubicación:** 📍 geolocalización del navegador · 🗺️ selección en mapa (polígono del lindero
   con cálculo de área/perímetro) · 🔗 pegar enlace de Google Maps. Muestra latitud, longitud,
   altitud y precisión.
3. **Características del predio:** tipo de área, área registrada y georreferenciada, varios lotes,
   profundidad efectiva del suelo, pedregosidad, tipo de riego y dimensiones.

Al guardar se crea la finca + **lote principal** y se enriquece con **SIG IGAC/UPRA**
(textura, materia orgánica y CIC estimados por zona de suelos).

### 5.10 🗂️ Fincas — Admin

Tarjetas por finca con ID (botón copiar para configurar el firmware) y acciones:
**🗂️ Lotes** (características propias: profundidad, pedregosidad; **🔄 Ciclos** productivos con
registro/edición/eliminación), **✏️ Editar** y **🗑️ Eliminar** (cascada con auditoría).

### 5.11 🌾 Catálogo de cultivos — todos los roles (gestión Admin/Agrónomo)

45 cultivos activos con búsqueda; cada tarjeta muestra ícono, ficha técnica y fisiología
(🌱 profundidad radicular, GDD, días del ciclo). Variedades compatibles por altitud y curvas de
extracción por cultivo (consulta).

### 5.12 🔬 Visión plagas — Admin / Agrónomo / Extensionista

Sube una foto del síntoma (JPEG/PNG/WebP, máx 5 MB). El **motor AgroVision** entrega un
diagnóstico **preliminar no confirmatorio** (modelo empaquetado → fallback OpenCV → abstención
explicada) con severidad, evidencia (clorosis/necrosis/área afectada) y explicación en lenguaje
humano; historial de diagnósticos por finca con confirmación de etiqueta por el agrónomo.

### 5.13 Administración (submenú solo Admin)

| Pantalla | Qué hace |
|---|---|
| 👥 **Usuarios** | Alta/edición/desactivación, cambio de rol y multi-select de fincas visibles. |
| 💰 **Insumos** | Precio por kg de los insumos del plan económico (alimenta el ROI). |
| 🌾 **Precios de cosecha** | Precio y rendimiento por cultivo + departamento (badge «Más rentable»). |
| 🕵️ **Auditoría** | Bitácora filtrable por entidad y búsqueda, paginada. |
| 📋 **BPA** | Checklist ICA 30021/2017 por finca + visitas de verificación (línea de tiempo). |
| 🧑‍🤝‍🧑 **Equipo** | CRUD de empleados, tarifas por rol/día y novedades con reemplazo. |
| 🗂️ **Comisiones** | CRUD de comisiones por finca con equipo, fechas, estados y valores. |
| 📊 **Lista de trabajos** | Órdenes por etapa (registro → comisión → muestras → recomendación → reporte → fin). |
| 🤖 **Reentrenar modelo** | Encola `train_colombia.py` (active learning / completo). |

---

## 6. Reglas de acceso destacadas (backend)

- **Cliente:** solo lectura de sus fincas; puede generar reportes y usar el chat asesor; no puede
  analizar ni administrar (403 en escritura).
- **Reportes:** requieren que la finca tenga una **comisión** en etapa `en_recomendacion` o
  posterior (409 `FINCA_SIN_COMISION` / `REPORTE_SIN_RECOMENDACION`).
- **Recomendaciones:** solo se listan fincas con comisión activa; cada análisis la avanza a
  `en_recomendacion`.
- **Visión plagas:** escritura/confirmación para roles no-cliente; el Cliente puede consultar por API.
- **Sensores:** `POST /api/sensor` es público (firmware); el simulador y la carga de archivos
  exigen rol no-cliente.
- **Alertas climáticas:** visibles para todos los roles según las fincas permitidas
  (Cliente → suyas, Extensionista → su zona, Admin/Agrónomo → todas).

---

## 7. Novedades recientes (v3.5 + clima en alertas)

- **Alertas con clima completo:** cada alerta muestra el estado actual (temperatura, sensación
  térmica, humedad, viento, presión, UV, descripción del cielo) y el pronóstico de 7 días
  (mín/máx, lluvia, probabilidad, viento, humedad, horas de sol), con refresco en vivo vía
  `GET /api/v1/fincas/{finca_id}/clima`.
- **Comisiones por etapas y accesibilidad del reporte (v8):** reporte con lenguaje simple para
  agricultores, semáforo de confianza explicado y exportación por audiencia.
- **Almanaque Bristol:** calendario lunar navegable + preferencias por usuario.

---

*Documento informativo — el detalle técnico completo vive en
`resources/architecture/Documento_Funcional_Tecnico_AgroIA.md` (v3.5).*
