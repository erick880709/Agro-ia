# RF-046: Limpieza del texto para lectura natural

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 4.1, 7 (RF-09) y 10
**Prioridad:** Mandatoria (M)

## Descripción
Antes de leer una respuesta, el sistema debe preparar el texto: omitir símbolos, marcas de formato, enlaces y tablas, y leer de forma natural números y unidades agronómicas (ppm, meq/100 g, %, kg/ha).

## Actores involucrados
- Asistente agronómico (origen del texto)
- Productor / agricultor y técnico (receptores del audio)

## Criterios de aceptación
- El texto se lee sin pronunciar símbolos ni formato.
- Las unidades agronómicas se pronuncian de forma natural (ej. "kg/ha" como "kilos por hectárea").

## Dependencias / relacionados
- RT-023: Preprocesamiento del texto

## Notas del analista
El RFP menciona además "diccionario de pronunciación" en riesgos (sección 14); no especifica si se usa reglas, un diccionario estático o ambos.
