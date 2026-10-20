# RNF-029: Conectividad — lectura con señal limitada

**Tipo:** Requerimiento no funcional
**Categoría:** Disponibilidad
**Fuente:** RFP-AGROIA-002 — Sección 8

## Descripción
La función debe tolerar señal limitada en zonas rurales, prefiriendo motores que funcionen sin conexión o con poco ancho de banda.

## Criterio medible / restricción concreta
El RFP no define condiciones de red ni exige modo offline; pide preferir motores ligeros (navegador/Piper) como base y respaldo.

## Impacto en la arquitectura
Favorece `speechSynthesis` (sin servidor) y un contingente autoalojado (Piper) antes que motores en la nube dependientes de red.

## Notas del analista
La cadena de respaldo debe priorizar motores que degraden bien sin conexión; el RFP no define comportamiento de reintento ni caché offline de audio.
