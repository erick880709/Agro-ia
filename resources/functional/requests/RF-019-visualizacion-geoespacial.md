# RF-019: Visualización Geoespacial y Mapas

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.6, 5.11, 5.14; Anexo-Datasets-Fuentes-Datos.md — Sección 5
**Prioridad:** Media

## Descripción
La plataforma debe integrar visualización geoespacial para que el usuario pueda ver sus fincas en un mapa interactivo. Las capacidades requeridas incluyen:

**Mapa de fincas:**
- Visualización de las fincas del cliente en un mapa interactivo con marcadores.
- Al hacer clic en una finca, mostrar información resumida (cultivo, estado, última medición).
- Navegación por zoom y desplazamiento.

**Capas de información geoespacial:**
- NDVI (índice de vegetación) superpuesto sobre el mapa, actualizado periódicamente (referencia: cada 5 días con Sentinel-2).
- Datos edafológicos del IGAC (tipo de suelo, capacidad de uso) como capa de referencia.
- Zonificación de aptitud de tierras de la UPRA para el cultivo de interés.

**Geolocalización:**
- Búsqueda de ubicación por dirección, municipio o coordenadas.
- Geocodificación inversa: obtener departamento/municipio/altitud desde coordenadas GPS.
- Delimitación del polígono de la finca en el mapa.

## Actores involucrados
- Cliente (Agricultor) — visualiza el mapa de sus fincas
- Técnico Agrónomo — analiza capas geoespaciales para validación

## Criterios de aceptación
- El mapa carga en menos de 3 segundos con caché de tiles.
- Los polígonos de las fincas se dibujan correctamente sobre el mapa base.
- El NDVI se actualiza y visualiza automáticamente.
- No especificados en el RFP — definir: ¿proveedor de tiles de mapa (Google Maps, OpenStreetMap, ESRI)?, ¿soporte offline para zonas sin conectividad?, ¿resolución espacial de las capas?

## Dependencias / relacionados
- RF-006: Gestión de fincas
- RF-008: Integración con Google Maps/GIS
- RF-015: Dashboard de usuario
- RT-005: PostgreSQL + PostGIS

## Notas del analista
- PostgreSQL + PostGIS es la elección correcta para almacenar y consultar datos geoespaciales (puntos GPS de fincas, polígonos, consultas de proximidad).
- OpenStreetMap es una alternativa gratuita a Google Maps que reduce costos de API. Leaflet es una biblioteca ligera compatible con Angular para la visualización.
- El cálculo de NDVI requiere procesamiento de imágenes satelitales. Google Earth Engine permite automatizarlo sin descargar imágenes manualmente — recomendado para producción.
