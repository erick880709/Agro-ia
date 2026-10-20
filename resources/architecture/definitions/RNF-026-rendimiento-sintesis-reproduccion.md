# RNF-026: Rendimiento de la síntesis y reproducción

**Tipo:** Requerimiento no funcional
**Categoría:** Rendimiento
**Fuente:** RFP-AGROIA-002 — Sección 8

## Descripción
La reproducción debe iniciar en pocos segundos tras recibir la respuesta (valor a acordar). Las respuestas largas deben leerse por fragmentos.

## Criterio medible / restricción concreta
"Inicio en pocos segundos" sin umbral concreto; el valor debe acordarse en la propuesta. Lectura por fragmentos para respuestas largas.

## Impacto en la arquitectura
El preprocesamiento debe dividir el texto en frases/fragmentos para iniciar la reproducción antes de terminar la síntesis completa (streaming o fragmentos).

## Notas del analista
El RFP no define percentil, condiciones de red ni umbral de "respuesta larga" para activar la fragmentación.
