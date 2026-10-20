# RT-022: Control de cuota y costos de síntesis

**Tipo:** Requisito técnico
**Categoría:** Integración
**Fuente:** RFP-AGROIA-002 — Secciones 10, 12 y 15

## Descripción
Controlar el consumo de cuota: caché del audio de respuestas repetidas (por voz y fragmento, sin datos personales), límite de longitud leída (resumir o leer solo las primeras secciones con opción "seguir leyendo") y límites por usuario.

## Criterio medible / restricción concreta
Caché, límites de longitud y límites por usuario. El RFP no fija valores máximos; deben acordarse y monitorearse.

## Impacto en la arquitectura
Requiere una capa de caché de audio, una política de truncado/resumen y contadores de consumo por usuario.

## Notas del analista
Es la mitigación principal contra el agotamiento de la cuota gratuita (riesgo alto, sección 14). Complementa RF-056 (métricas de caracteres leídos).
