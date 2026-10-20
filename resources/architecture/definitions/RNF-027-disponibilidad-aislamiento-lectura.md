# RNF-027: Disponibilidad — aislamiento de fallos de la lectura

**Tipo:** Requerimiento no funcional
**Categoría:** Disponibilidad
**Fuente:** RFP-AGROIA-002 — Secciones 8, 12 y 14

## Descripción
La falla de la lectura en voz alta no debe afectar el chat de texto: la respuesta escrita se muestra normalmente y la lectura se degrada con un aviso.

## Criterio medible / restricción concreta
El RFP exige que el chat de texto no se vea afectado, pero no define SLA ni métricas de disponibilidad.

## Impacto en la arquitectura
La síntesis y reproducción deben fallar de forma aislada, sin bloquear el flujo de texto del chat; cadena de respaldo de motores.

## Notas del analista
Complementa RNF-014 (aislamiento de fallos de la entrada por voz); ambas funciones comparten el principio de no degradar el chat.
