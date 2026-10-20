# RT-023: Preprocesamiento del texto para lectura

**Tipo:** Requisito técnico
**Categoría:** Integración
**Fuente:** RFP-AGROIA-002 — Secciones 10 y 14

## Descripción
Preprocesar el texto antes de sintetizar: eliminar formato Markdown, expandir abreviaturas y unidades (ppm, meq/100 g, %, kg/ha), y dividir en frases para iniciar la reproducción antes de terminar la síntesis completa.

## Criterio medible / restricción concreta
Limpieza de formato, expansión de unidades/abreviaturas y división en frases. El RFP no define un diccionario de pronunciación concreto.

## Impacto en la arquitectura
Capa de normalización previa a la interfaz de síntesis (RT-020); debe incluir un diccionario de términos agronómicos para mitigar la mala pronunciación.

## Notas del analista
El riesgo "mala pronunciación de términos técnicos" (sección 14) se mitiga aquí. Debe definirse el alcance del diccionario (términos y unidades del catálogo).
