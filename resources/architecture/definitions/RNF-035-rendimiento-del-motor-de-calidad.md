# RNF-035: Rendimiento del motor de calidad

**Tipo:** Requerimiento no funcional
**Categoría:** Rendimiento
**Fuente:** RFP-AGROIA-003 §7 (Requerimientos no funcionales)

## Descripción
La evaluación de calidad no agrega más de 100 ms por trama; el reproceso histórico se ejecuta por lotes.

## Criterio medible / restricción concreta
≤ 100 ms adicionales por trama en la evaluación de calidad.

## Impacto en la arquitectura
El reproceso histórico por lotes evita bloquear la ingesta en tiempo real.

## Notas del analista
No aplican — el RFP define el requisito de forma concreta.
