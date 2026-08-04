# RF-008: Integración con APIs Externas de Datos

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.6, 5.14; RFP-inicial.md — Sección 3 (Integración con APIs externas)
**Prioridad:** Alta

## Descripción
La plataforma debe integrarse con múltiples APIs y fuentes de datos externas para enriquecer el análisis agronómico con información que no proviene de los sensores IoT. Las integraciones requeridas son:

**Fuentes obligatorias (MVP):**
1. **IDEAM** — Datos climáticos históricos y pronósticos: temperatura, humedad relativa, radiación solar, velocidad del viento, precipitación, evapotranspiración, presión atmosférica, índice UV. Se debe consumir la API Socrata Open Data (SODA) y/o el portal DHIME.
2. **Google Maps / Proveedor GIS** — Geolocalización, latitud, longitud, altitud, geocodificación inversa para obtener departamento/municipio.

**Fuentes recomendadas (MVP extendido o Fase 2):**
3. **IGAC** — Datos edafológicos: levantamientos de suelos, clasificación por capacidad de uso de tierras (shapefiles, CC-BY-SA 4.0).
4. **Copernicus/Sentinel-2** — Imágenes satelitales multiespectrales, índice NDVI (resolución 10m, revisita cada 5 días). Se recomienda usar Google Earth Engine para procesamiento automatizado.
5. **WhatsApp / SMS** — Canal de envío de notificaciones y alertas al agricultor.

## Actores involucrados
- Sistema (consumo automático de APIs)
- Administrador (configuración de conectores y claves de API)
- Cliente (recibe notificaciones por WhatsApp/SMS)

## Criterios de aceptación
- Los conectores a APIs externas están implementados como módulos independientes y reemplazables.
- Los datos climáticos del IDEAM se actualizan periódicamente (frecuencia diaria como mínimo).
- La geolocalización por GIS devuelve coordenadas y altitud correctas para cualquier punto de Colombia.
- El sistema maneja graceful degradation cuando una API externa no está disponible (sin bloquear la funcionalidad core).
- No especificados en el RFP — definir: frecuencias de actualización por fuente, estrategia de caché de datos externos, proveedor concreto de WhatsApp Business API vs. Twilio para SMS.

## Dependencias / relacionados
- RF-012: Motor predictivo (consume estos datos)
- RF-014: Agente IA
- RT-010: MLOps
- Anexo-Datasets-Fuentes-Datos.md: detalla fuentes, endpoints y licencias

## Notas del analista
- El Anexo de Datasets proporciona información detallada sobre cómo consumir cada fuente (SODA API para IDEAM, shapefiles para IGAC, Google Earth Engine para Sentinel). Se recomienda seguir esas guías durante la implementación.
- La integración con WhatsApp/SMS es crítica para la adopción por agricultores, ya que muchos en zonas rurales colombianas no usan correo electrónico pero sí WhatsApp.
- Las fuentes de datos abiertos del Estado colombiano (AGROSAVIA, IDEAM, IGAC, DANE, UPRA) son de uso libre, pero debe verificarse la licencia específica de cada dataset antes de su uso en un producto comercial.
