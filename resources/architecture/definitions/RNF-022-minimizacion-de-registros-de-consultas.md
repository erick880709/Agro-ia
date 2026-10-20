# RNF-022: Minimización de registros de consultas

**Tipo:** Requerimiento no funcional
**Categoría:** Seguridad y privacidad
**Fuente:** RFP-AGROIA-001 — Secciones 7 (RF-14) y 10

## Descripción
La función no debe registrar el contenido de las consultas más allá de lo que ya registra el chat actual. Las métricas de voz deben limitarse a cantidad de consultas, errores y duración.

## Criterio medible / restricción concreta
No se deben añadir registros de contenido de consulta; las métricas enumeradas son cantidad, errores y duración.

## Impacto en la arquitectura
La instrumentación de métricas debe separar datos operativos de contenido conversacional y evitar recopilar información adicional innecesaria.

## Notas del analista
El RFP no concreta retención, nivel de agregación ni anonimización de las métricas.
