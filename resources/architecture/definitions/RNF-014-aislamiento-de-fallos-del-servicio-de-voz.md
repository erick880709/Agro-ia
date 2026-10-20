# RNF-014: Aislamiento de fallos del servicio de voz

**Tipo:** Requerimiento no funcional
**Categoría:** Disponibilidad
**Fuente:** RFP-AGROIA-001 — Secciones 8, 11 y 13

## Descripción
La indisponibilidad o fallo del servicio de voz no debe afectar el funcionamiento del chat de texto.

## Criterio medible / restricción concreta
El RFP exige mantener disponible la escritura ante fallos de voz, pero no define SLA ni métricas de disponibilidad.

## Impacto en la arquitectura
La captura y transcripción deben poder fallar de forma aislada, sin bloquear ni alterar el envío de texto al servicio de chat existente.

## Notas del analista
No se define comportamiento de reintentos ni persistencia temporal de audio o transcripciones ante errores.
