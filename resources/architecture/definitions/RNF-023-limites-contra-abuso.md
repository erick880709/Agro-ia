# RNF-023: Límites contra abuso de la función de voz

**Tipo:** Requerimiento no funcional
**Categoría:** Seguridad
**Fuente:** RFP-AGROIA-001 — Secciones 9.2 y 10

## Descripción
La solución debe prevenir el abuso mediante límites de duración, tamaño y frecuencia de solicitudes.

## Criterio medible / restricción concreta
Se requieren límites para duración, tamaño y frecuencia; los valores máximos no están especificados en el RFP.

## Impacto en la arquitectura
Si se recibe audio en servidor, el endpoint debe aplicar límites de tamaño y duración y tasa de peticiones; los valores deben ser configurables o acordados.

## Notas del analista
Los umbrales deben definirse considerando costos, experiencia de usuario y capacidad del servicio de transcripción.
