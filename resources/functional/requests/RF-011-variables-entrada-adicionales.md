# RF-011: Variables de Entrada Adicionales

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.6; contextAgro.md (Variables de entrada)
**Prioridad:** Media

## Descripción
Además de los datos de sensores IoT, el sistema debe permitir el ingreso y procesamiento de variables adicionales que enriquecen el análisis agronómico. Estas se agrupan en:

**Variables de ubicación:** latitud, longitud, altitud, departamento, municipio, país, tipo de terreno, pendiente, orientación solar.

**Variables ambientales (fuente IDEAM):** temperatura ambiente, humedad relativa, radiación solar, velocidad del viento, precipitación, evapotranspiración, presión atmosférica, índice UV. Con históricos de al menos 5 años.

**Variables históricas de la finca:** últimos cultivos sembrados, fecha de siembra, fecha de cosecha, producción obtenida, fertilizaciones aplicadas (tipo, cantidad, fecha), plaguicidas aplicados, riego (frecuencia y volumen), enfermedades y plagas registradas.

**Variables económicas:** precio del cultivo en mercado, costo de fertilizantes, costo de transporte, costo de mano de obra, rentabilidad estimada, demanda del mercado.

**Imágenes satelitales:** NDVI (índice de vegetación) con resolución temporal de referencia cada 5 días.

## Actores involucrados
- Cliente — ingresa variables históricas y económicas de sus fincas
- Sistema — obtiene automáticamente variables ambientales (IDEAM), de ubicación (GIS) y satelitales (Copernicus)

## Criterios de aceptación
- Las variables históricas pueden ser ingresadas manualmente por el agricultor o cargadas desde un archivo (CSV/Excel).
- Las variables ambientales se actualizan automáticamente desde IDEAM.
- El NDVI se calcula y actualiza automáticamente para cada finca registrada con coordenadas GPS.
- No especificados en el RFP — definir: ¿formatos de importación de datos históricos?, ¿frecuencia de actualización del NDVI?, ¿fuente de datos económicos en tiempo real (DANE-SIPSA)?

## Dependencias / relacionados
- RF-006: Gestión de fincas
- RF-008: Integración con APIs externas
- RF-012: Motor predictivo (consume estas variables)
- RF-027: Visualización geoespacial

## Notas del analista
- Las variables económicas dependen de fuentes externas como el DANE-SIPSA (precios mayoristas) y EVA (rendimientos por municipio). Se recomienda automatizar su obtención en fases posteriores al MVP.
- El NDVI requiere procesamiento de imágenes satelitales. Google Earth Engine es la opción más escalable para automatizar este cálculo sin descargar/procesar imágenes manualmente.
