# RNF-031: Calidad de audio — voces naturales en español

**Tipo:** Requerimiento no funcional
**Categoría:** Otro — Calidad de audio
**Fuente:** RFP-AGROIA-002 — Sección 8

## Descripción
Las voces deben ser naturales y comprensibles, con acento neutro o latinoamericano.

## Criterio medible / restricción concreta
"Naturales y comprensibles" sin métrica objetiva (MOS, WER, etc.). El RFP exige acento neutro o latinoamericano.

## Impacto en la arquitectura
La selección de motores debe priorizar voces es-CO/es-MX/es-ES de calidad (Azure/Google neuronales) sobre la voz del navegador, cuya calidad varía.

## Notas del analista
La mala pronunciación de términos técnicos es un riesgo explícito (sección 14); se mitiga con diccionario de pronunciación y preprocesamiento (RT-023).
