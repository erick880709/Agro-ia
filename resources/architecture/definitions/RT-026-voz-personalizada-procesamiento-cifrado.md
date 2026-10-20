# RT-026: Voz personalizada — procesamiento asíncrono, cifrado y eliminación

**Tipo:** Requisito técnico
**Categoría:** Integración
**Fuente:** RFP-AGROIA-002 — Secciones 10, 11 y 12

## Descripción
Para la voz personalizada: procesamiento asíncrono con estado visible ("procesando tu voz"), almacenamiento cifrado de la muestra o de la representación de voz, y eliminación efectiva al borrar.

## Criterio medible / restricción concreta
Estado visible del procesamiento, cifrado en reposo y tránsito, y borrado completo de muestra y representación al eliminarla.

## Impacto en la arquitectura
Trabajo asíncrono (cola) para la síntesis de voz; almacenamiento cifrado de datos biométricos; flujo de eliminación que purga todos los artefactos.

## Notas del analista
La eliminación efectiva es criterio de aceptación (sección 12) y requisito normativo (Ley 1581). El RFP no define el mecanismo de verificación del borrado.
