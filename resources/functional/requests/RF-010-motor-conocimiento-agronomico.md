# RF-010: Motor de Conocimiento Agronómico

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.8
**Prioridad:** Alta

## Descripción
La plataforma debe modelar y almacenar conocimiento agronómico estructurado que sirva como base para el sistema experto de recomendaciones. El motor de conocimiento debe abarcar:

- **Relación e interacción entre nutrientes:** cómo la presencia o ausencia de un nutriente afecta la absorción de otros (ej. exceso de potasio puede bloquear la absorción de magnesio).
- **Bloqueo de nutrientes:** condiciones bajo las cuales un nutriente se vuelve no disponible para la planta a pesar de estar presente en el suelo (ej. pH inadecuado).
- **Compatibilidad entre fertilizantes:** qué fertilizantes pueden mezclarse y cuáles no.
- **Compatibilidad y rotación/asociación de cultivos:** qué cultivos son compatibles para sembrarse juntos o en rotación.
- **Enfermedades, plagas, hongos y malezas:** condiciones que las favorecen, cultivos afectados y medidas de control.
- **Buenas prácticas agrícolas (BPA):** recomendaciones generales de manejo sostenible.

Este motor funciona como la base de reglas del **sistema híbrido de recomendación** (reglas agronómicas + modelos de ML), asegurando que las recomendaciones nunca dependan únicamente de reglas simples sino que integren múltiples variables simultáneamente.

## Actores involucrados
- Técnico Agrónomo — valida y actualiza las reglas agronómicas
- Investigador IES — puede proponer nuevas reglas basadas en evidencia científica
- Administrador — gestiona la configuración del motor

## Criterios de aceptación
- Las reglas agronómicas son configurables sin necesidad de re-desplegar el sistema.
- Cada regla tiene una fuente verificable (estudio científico, manual técnico, norma oficial).
- El motor puede evaluar múltiples variables simultáneamente para generar una recomendación.
- No especificados en el RFP — definir: formato de representación de reglas (JSON, DSL propio, Drools-like), ¿versionado de reglas?, ¿proceso de revisión/aprobación de reglas nuevas?

## Dependencias / relacionados
- RF-009: Catálogo de cultivos
- RF-012: Motor predictivo
- RF-013: Recomendaciones inteligentes
- RD-003: Sistema híbrido de recomendación

## Notas del analista
- La combinación de reglas explícitas (sistema experto) + modelos de ML es una buena práctica en dominios donde la explicabilidad es crítica. Las reglas proporcionan transparencia y los modelos capturan patrones no lineales.
- Para el piloto de café, las reglas base pueden extraerse de las guías técnicas de Cenicafé (ej. tablas de fertilización nitrogenada según nivel de materia orgánica).
