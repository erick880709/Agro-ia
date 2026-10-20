# RT-021: Cadena de respaldo de motores de voz (híbrido)

**Tipo:** Requisito técnico
**Categoría:** Integración
**Fuente:** RFP-AGROIA-002 — Secciones 9.1, 9.3 y 10

## Descripción
Implementar una cadena de respaldo: voz del navegador (`speechSynthesis`, lista curada de voces femeninas/masculinas) como **motor por defecto**; una API en la nube con capa gratuita recurrente (Google TTS o Azure Speech) como motor consistente; Piper (autoalojado) como contingencia; y, para la voz personalizada, los motores de clonación autoalojados en GPU cloud (GPT-SoVITS/Chatterbox) cuando el usuario crea y activa "Mi voz".

## Criterio medible / restricción concreta
Cadena ordenada de motores con conmutación automática ante fallo o cuota agotada. El RFP no define tiempos de conmutación.

## Impacto en la arquitectura
La interfaz común (RT-020) es la precondición; la cadena ordena proveedores según costo, calidad y disponibilidad.

## Notas del analista
El solicitante recomienda el enfoque híbrido (sección 9.3). La voz del navegador no expone género; se necesita una lista curada de voces por plataforma.
