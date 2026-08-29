Especificación Técnica — AgroIA v3.4
Módulo Almanaque Bristol y Cierre de Brechas
Fecha: 29 de agosto de 2026
Versión del documento: 1.0
Equipo destino: Backend (Python/FastAPI), Frontend (Vanilla JS), Infraestructura (Render/Neon)

1. Estado actual del sistema (Baseline v3.3)
El sistema AgroIA se encuentra actualmente en su versión 3.3, completamente operativo y validado en entorno de demostración. Los siguientes módulos están implementados y funcionales:

✅ Autenticación JWT (access/refresh tokens, rotación y revocación).

✅ PWA offline-first (Service Worker, IndexedDB, sincronización idempotente).

✅ Motor de visión AgroVision (fallback OpenCV, diagnóstico preliminar, confirmación de etiquetas RQ-V6-01 para dataset DS09).

✅ Módulos agronómicos V4 (agua de riego, balance hídrico ETo/Kc, MIP con GBIF, variedades, rotación, BPA con visitas, Extensionista).

✅ Módulo operativo (equipo de trabajo, comisiones, lista de trabajos).

✅ Antagonismos nutricionales (4 reglas de interacción: K-Ca-Mg, P-Zn, N-maduración, pH-ácido+Mg).

✅ Inteligencia de mercado (precios de cosecha manuales, badge "Más rentable" en UC1).

✅ Laboratorios ICA (ingesta de análisis de suelo con prioridad sobre sensor).

✅ Enriquecimiento SIG (IGAC/UPRA con 13 puntos del país validados).

✅ Precios de insumos dinámicos (ROI actualizable por Admin).

✅ Reportes avanzados (12 mejoras de calidad, muestreo inteligente, ROI realista, simulación What-If).

Brecha identificada (prioridad alta):
El Almanaque Bristol (calendario lunar y tradición de siembra) no está implementado. Esta funcionalidad es estratégica para conectar culturalmente con el agricultor colombiano y enriquecer las alertas climáticas proactivas.

2. Especificación del Módulo Almanaque Bristol
2.1. Objetivo estratégico
Incorporar el Almanaque Bristol como una capa de recomendación cultural complementaria a las alertas climáticas. No reemplaza la decisión agronómica (suelo + clima), sino que la enriquece con un factor de confianza cultural para el agricultor.

2.2. Alcance funcional
Cálculo preciso de la fase lunar (iluminación, edad, emoji).

Recomendación de siembra según la fase (raíz, hoja, fruto, reposo).

Alerta climática proactiva: fase favorable + condiciones climáticas aptas (sin lluvias > 20 mm ni heladas < 5 °C en los próximos 7 días).

Visualización en el reporte (PDF/HTML) y en el panel de alertas climáticas (P1b).

Preferencia de usuario: toggle para activar/desactivar alertas de siembra.

3. Fuentes de datos astronómicos y contrato de API
3.1. Estrategia de implementación (Jerarquía de fuentes)
Skyfield (recomendada, local): Biblioteca Python con efemérides JPL de la NASA. No requiere API key, funciona offline (descarga única de ~50 MB).

US Navy Moon Phase API (respaldo): API pública sin autenticación.

Tabla estática (fallback extremo): Efemérides generadas para el año en curso al inicio del sistema.

3.2. Contrato de la API externa (US Navy)
Endpoint:

text
GET https://api.usno.navy.mil/moon/phase?date={YYYY-MM-DD}&timezone={UTC_OFFSET}
Ejemplo de solicitud:

http
GET https://api.usno.navy.mil/moon/phase?date=2026-08-29&timezone=-5
Ejemplo de respuesta (JSON):

json
{
  "phase": "Waxing Crescent",
  "illumination": 0.23,
  "age": 4.2,
  "next_full_moon": "2026-09-07",
  "next_new_moon": "2026-09-21"
}
Especificación OpenAPI:

yaml
openapi: 3.0.1
info:
  title: US Navy Moon Phase API
  version: 1.0.0
servers:
  - url: https://api.usno.navy.mil
paths:
  /moon/phase:
    get:
      summary: Obtener fase lunar
      parameters:
        - name: date
          in: query
          required: true
          schema:
            type: string
            format: date
            example: "2026-08-29"
        - name: timezone
          in: query
          required: false
          schema:
            type: integer
            default: 0
            example: -5
      responses:
        '200':
          description: Fase lunar calculada
          content:
            application/json:
              schema:
                type: object
                properties:
                  phase:
                    type: string
                    enum: [New Moon, Waxing Crescent, First Quarter, Waxing Gibbous, Full Moon, Waning Gibbous, Last Quarter, Waning Crescent]
                  illumination:
                    type: number
                    format: float
                  age:
                    type: number
                  next_full_moon:
                    type: string
                    format: date
                  next_new_moon:
                    type: string
                    format: date
4. Detalles técnicos de implementación
4.1. Backend — Nuevo servicio lunar
Archivo: apps/backend/agroia_backend/services/calendario_lunar.py

Variables de entorno:

Variable	Default	Descripción
BRISTOL_MODO	skyfield	skyfield | usnavy | static
BRISTOL_ACTIVADO	true	Habilita/deshabilita el módulo globalmente
Función principal:

python
from datetime import date

def get_lunar_phase(fecha: date, lat: float, lon: float) -> dict:
    """
    Retorna:
    {
        "fase_nombre": "Luna Creciente",
        "fase_nombre_en": "Waxing Crescent",
        "iluminacion": 0.23,
        "edad_dias": 4.2,
        "emoji": "🌒"
    }
    """
    # Lógica de consulta según BRISTOL_MODO
Función de recomendación Bristol:

python
def mapear_recomendacion_bristol(fase: str) -> dict:
    """
    Retorna:
    {
        "tipo": "hojas",
        "descripcion": "Hortalizas de hoja y crecimiento aéreo...",
        "cultivos": ["Lechuga", "Espinaca"]
    }
    """
Tabla de mapeo:

Fase lunar	Recomendación	Cultivos sugeridos
Luna Nueva	Raíces y bulbos	Zanahoria, remolacha, papa, cebolla
Cuarto Creciente	Hojas y crecimiento aéreo	Lechuga, espinaca, repollo, coliflor
Luna Llena	Frutos y semillas	Tomate, pimiento, frijol, maíz
Cuarto Menguante	Mantenimiento, podas, raíces	(Trasplantes, abonos, preparación de suelo)
4.2. Base de datos — Migración 043
Archivo: alembic/versions/043_add_bristol_preferences.py

sql
-- 1. Extender el enum de tipo de alerta (si no existe)
ALTER TYPE agroia.tipoalerta ADD VALUE IF NOT EXISTS 'siembra_lunar';

-- 2. Crear tabla de preferencias de usuario para el Bristol
CREATE TABLE IF NOT EXISTS agroia.preferencias_bristol (
    usuario_id UUID PRIMARY KEY REFERENCES agroia.usuarios(id) ON DELETE CASCADE,
    mostrar_en_reportes BOOLEAN DEFAULT TRUE,
    generar_alertas_siembra BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
4.3. Endpoints internos de AgroIA
Método	Endpoint	Descripción	Rol
GET	/api/v1/calendario-lunar/actual?lat=&lon=	Fase actual y recomendación	Todos
GET	/api/v1/calendario-lunar/pronostico?dias=7&lat=&lon=	Fases de los próximos 7 días	Todos
GET	/api/v1/calendario-lunar/estado	Fuente activa (skyfield/usnavy/static)	Admin
PUT	/api/v1/usuarios/preferencias-bristol	Toggle de alertas y visibilidad	Todos (perfil)
Contrato de respuesta (formato unificado):

json
{
  "fecha": "2026-08-29",
  "fase": {
    "nombre": "Luna Creciente",
    "nombre_en": "Waxing Crescent",
    "iluminacion": 0.23,
    "edad_dias": 4.2,
    "emoji": "🌒"
  },
  "recomendacion_bristol": {
    "tipo": "hojas",
    "descripcion": "Hortalizas de hoja y crecimiento aéreo (lechuga, espinaca, repollo)",
    "cultivos_sugeridos": ["Lechuga", "Espinaca", "Repollo", "Coliflor"]
  },
  "fuente": "skyfield",
  "proximos_eventos": {
    "proxima_luna_llena": "2026-09-07",
    "proxima_luna_nueva": "2026-09-21"
  }
}
4.4. Integración con Alertas Climáticas (Servicio Programado)
Archivo: apps/backend/agroia_backend/services/clima_alertas.py
Ubicación: Tarea asyncio en el lifespan de main.py (cada 6 horas).

Nueva lógica:

python
# Iterar sobre fincas con coordenadas y cultivo activo (fincas con ciclo activo)
if BRISTOL_ACTIVADO:
    lunar_data = get_lunar_phase(hoy, lat, lon)
    es_favorable = lunar_data["fase"] in ["Luna Nueva", "Luna Llena", "Cuarto Creciente"]
    if es_favorable:
        pronostico = fetch_pronostico_open_meteo(lat, lon)
        clima_favorable = pronostico["lluvia_max"] < 20 and pronostico["temp_min"] > 5
        if clima_favorable:
            # Crear alerta tipo 'siembra_lunar' en tabla alertas_climaticas
            mensaje = f"📅 El Almanaque Bristol indica días propicios para siembra. El clima (temp y lluvia) es favorable en los próximos días. Considere programar siembra de {lunar_data['recomendacion']['cultivos_sugeridos'][0]}."
Nota: La alerta no se duplica si ya existe una activa del mismo tipo para la finca (se desactiva la anterior).

4.5. Reportes HTML (P7)
Archivo: apps/backend/agroia_backend/services/reportes_html.py

Nueva sección (justo después de la sección N — Plano del lote):

html
<div class="seccion-lunar">
  <h3>📅 Calendario Lunar (Almanaque Bristol)</h3>
  <p><span class="fase-emoji">🌕</span> Fase actual: <strong>Luna Llena</strong></p>
  <p>Recomendación de siembra: <strong>Frutos (tomate, pimiento, frijol, maíz)</strong></p>
  <p class="nota-cultural">* Esta recomendación es cultural y complementa el diagnóstico agronómico. 
  La decisión final debe basarse en el análisis de suelo, clima y manejo validado por un agrónomo.</p>
</div>
4.6. Frontend — UI
1. Tarjeta de fase actual (P1b — Alertas clima):

Ubicación: apps/frontend-web/index.html (dentro de la vista #vista-alertas).

Contenido: Ícono de la fase lunar actual + texto de recomendación.

Estilo: Tarjeta estática fija al inicio del panel.

2. Preferencias de usuario:

Ubicación: Modal de perfil (o nueva sección de configuración).

Toggle: "Activar alertas de siembra según Almanaque Bristol".

Llamada: PUT /api/v1/usuarios/preferencias-bristol con {generar_alertas_siembra: true/false}.

3. Listado de alertas:

Las alertas de tipo siembra_lunar aparecerán automáticamente en el listado de P1b, con el ícono 📅 y color verde/azul claro.

5. Ajustes adicionales (Diferidos a v3.5)
Durante la validación del sistema no se detectaron otras funcionalidades críticas faltantes. Los siguientes módulos son mejoras de siguiente nivel que no bloquean el lanzamiento del piloto:

Módulo	Prioridad	Motivo del diferimiento
Sostenibilidad / Huella de Carbono	Media	Requiere consultoría ambiental y definición de factores de emisión locales.
Automatización de precios de cosecha (API DANE)	Baja	El panel Admin manual es suficiente para el piloto; se puede automatizar después.
Ampliación de reglas de antagonismo	Baja	Las 4 reglas actuales cubren el 80% de los casos; se ampliarán con feedback de agrónomos.
6. Plan de implementación y estimación de esfuerzo
#	Tarea	Archivos	Esfuerzo
1	Agregar dependencia skyfield (o instalar fallback)	pyproject.toml	0.1 días
2	Crear services/calendario_lunar.py	Backend	0.8 días
3	Migración BD (043) y actualización de enums	Alembic, models/	0.4 días
4	Crear endpoints API (api/calendario.py)	Backend	0.5 días
5	Integrar con job de alertas climáticas	clima_alertas.py, main.py	0.6 días
6	Agregar sección Lunar en Reportes	reportes_html.py	0.4 días
7	UI: Tarjeta en P1b + Toggle en preferencias	index.html, app.js, styles.css	1.0 días
8	Pruebas unitarias y de integración	tests/	0.5 días
9	Documentación y actualización de manuales	Documento_Pantallas_AgroIA.md	0.3 días
Total			~4.5 días (1 desarrollador)
7. Criterios de aceptación
□ La fase lunar calculada coincide con la de la API de la US Navy (margen de error < 1%).
□ La recomendación de siembra se mapea correctamente según la tabla Bristol.
□ Las alertas de siembra solo se generan cuando fase favorable + clima favorable (sin lluvias > 20 mm y sin heladas).
□ La sección lunar aparece en el reporte con el disclaimer cultural.
□ El usuario puede activar/desactivar las alertas de siembra desde su perfil.
□ El sistema degrada elegantemente a static si skyfield falla y la API US Navy no responde.