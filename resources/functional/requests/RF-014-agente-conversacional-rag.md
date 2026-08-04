# RF-014: Agente Conversacional IA (RAG)

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.13; RFP-inicial.md — Sección 3 (Agente IA)
**Prioridad:** Alta

## Descripción
El sistema debe incluir un asistente conversacional basado en IA generativa con arquitectura RAG (Retrieval-Augmented Generation). Características obligatorias:

**Dominio de conocimiento:**
- Entrenado únicamente sobre: agronomía, agricultura, fertilizantes, buenas prácticas agrícolas, manuales especializados y la base documental del proyecto.
- El conocimiento debe poder actualizarse sin reentrenar el modelo (actualización del índice vectorial).

**Restricciones:**
- No puede navegar libremente por Internet.
- Solo responde con: información del reporte generado, datos históricos del cliente y la base de conocimiento agrícola.
- Nunca debe inventar información; si no tiene datos suficientes, debe indicarlo.

**Capacidades requeridas:**
- Interpretar datos de sensores, mapas e imágenes satelitales.
- Explicar conceptos agrícolas en lenguaje sencillo (modo agricultor) y técnico (modo experto para agrónomos).
- Generar y priorizar recomendaciones agronómicas.
- Mostrar nivel de confianza en cada respuesta.
- Explicar el porqué de cada recomendación.

**Ejemplos de preguntas que debe responder:**
- "¿Qué puedo sembrar aquí?"
- "¿Por qué mi suelo tiene bajo rendimiento?"
- "¿Qué fertilizante debo aplicar y cuánto?"
- "¿Cuándo debo sembrar/cosechar/regar?"
- "¿Qué significa tener un pH de 5.2?"
- "¿Qué debo hacer primero?"

## Actores involucrados
- Cliente (Agricultor) — usuario principal del chat
- Técnico Agrónomo — modo experto

## Criterios de aceptación
- El chat responde en menos de 10 segundos.
- Las respuestas están fundamentadas en fuentes verificables.
- El sistema indica cuando no tiene información suficiente.
- El conocimiento se actualiza sin reentrenar el LLM.
- No especificados en el RFP — definir: modelo LLM concreto (comercial vs. open-source autoalojado), provedor de base de datos vectorial, estrategia de chunking para documentos.

## Dependencias / relacionados
- RF-013: Recomendaciones inteligentes
- RF-010: Motor de conocimiento agronómico
- RT-013: Base de datos vectorial para RAG
- RNF-010: No alucinación
- RNF-011: Actualización del RAG sin reentrenar

## Notas del analista
- La arquitectura RAG es adecuada para este caso de uso: permite mantener el conocimiento actualizado sin reentrenar el LLM, y reduce el riesgo de alucinaciones al anclar las respuestas en documentos verificables.
- Para el piloto de café, el corpus base del RAG debe incluir la biblioteca técnica de Cenicafé (guías de fertilidad, nutrición, manual del cafetero). La licencia CC BY-NC-ND de Cenicafé debe validarse para uso comercial.
- La elección del LLM (GPT-4, Claude, Llama 3, Mistral) tiene implicaciones de costo, latencia y privacidad de datos. Si se usa un modelo comercial (API), debe garantizarse que los datos de los agricultores no se envíen a servidores externos sin cifrado.
