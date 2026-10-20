# RT-028: Infraestructura y costos de GPU para voz personalizada

**Tipo:** Requisito técnico
**Categoría:** Infraestructura
**Fuente:** RFP-AGROIA-002 — Secciones 9.2, 10, 16 y 19

## Descripción
Alojar el servicio de GPU para la voz personalizada en un **servicio de GPU en la nube** (RunPod, HuggingFace Spaces o similar), con estimación de costo mensual y plan de escalado. Los motores son GPT-SoVITS y Chatterbox (MIT).

## Criterio medible / restricción concreta
Estimación de infraestructura GPU en la nube y costo mensual, con justificación del proveedor elegido.

## Impacto en la arquitectura
La voz personalizada se autoaloja en GPU cloud; impacta costos, gobernanza y la integración con la cadena de síntesis (RT-021).

## Notas del analista
Riesgo alto de costo y operación (sección 14); el RFP exige prueba de concepto previa y permite diferir esta fase. Hosting decidido: GPU en la nube (no servidor propio, no diferido).
