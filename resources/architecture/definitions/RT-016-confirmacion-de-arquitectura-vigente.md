# RT-016: Confirmación de arquitectura vigente y alcance acotado

**Tipo:** Requisito técnico
**Categoría:** Arquitectura / Integración
**Fuente:** RFP-AGROIA-001 — Secciones 1, 9 y 15

## Descripción
Antes de proponer la implementación, el oferente debe confirmar la arquitectura vigente. El RFP identifica un backend basado en FastAPI y un frontend SPA en JavaScript sin framework, pero señala que la referencia funcional original menciona Flask. La solución debe constituir un cambio acotado del frontend, con cambios mínimos o nulos en backend.

## Criterio medible / restricción concreta
Confirmar la arquitectura vigente al inicio; limitar los cambios de backend al mínimo necesario. No se define una métrica para “cambio acotado”.

## Impacto en la arquitectura
La propuesta debe basarse en la inspección de la aplicación existente y evitar reescrituras del agente o del servicio de chat.

## Notas del analista
La mención contradictoria de FastAPI y Flask debe resolverse antes de cerrar el diseño técnico.
