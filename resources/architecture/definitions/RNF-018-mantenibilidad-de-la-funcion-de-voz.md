# RNF-018: Mantenibilidad de la función de voz

**Tipo:** Requerimiento no funcional
**Categoría:** Mantenibilidad
**Fuente:** RFP-AGROIA-001 — Secciones 8 y 9.2

## Descripción
El código de la función debe ser modular y sus parámetros de negocio no deben estar fijados directamente en el código.

## Criterio medible / restricción concreta
El RFP no define métricas de modularidad ni un mecanismo de configuración concreto.

## Impacto en la arquitectura
Los parámetros de voz deben configurarse mediante un mecanismo administrable, conservando el alcance acotado de la evolución.

## Notas del analista
El conjunto de parámetros configurables y quién puede modificarlos requiere definición; duración, activación e idioma se mencionan como ejemplos en el lineamiento técnico.
