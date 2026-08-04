# RNF-010: Actualización del Conocimiento sin Reentrenamiento

**Tipo:** Requerimiento no funcional
**Categoría:** Mantenibilidad / Evolución del sistema
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 8

## Descripción
La base de conocimiento del sistema (motor de conocimiento agronómico y corpus del RAG) debe poder actualizarse sin necesidad de reentrenar los modelos de Machine Learning ni el modelo de lenguaje (LLM). Esto permite:

- Agregar nuevas reglas agronómicas, fichas técnicas de cultivos o manuales sin pasar por un ciclo completo de reentrenamiento.
- Corregir rápidamente información desactualizada o errónea detectada en producción.
- Incorporar nuevos hallazgos científicos o recomendaciones de fuentes oficiales (Cenicafé, AGROSAVIA, UPRA) de forma ágil.

La actualización debe realizarse mediante la modificación del índice vectorial del RAG (para el agente conversacional) y la edición de las reglas del sistema experto (para las recomendaciones).

## Criterio medible / restricción concreta
- Una nueva regla agronómica o documento agregado al RAG debe estar disponible para el sistema en menos de 1 hora tras su carga.
- El proceso de actualización no debe requerir tiempo de inactividad del sistema.
- No especificados en el RFP — definir: ¿quién tiene permisos para actualizar el conocimiento?, ¿flujo de aprobación de cambios?, ¿versionado del índice de conocimiento?

## Impacto en la arquitectura
- Ingesta de documentos desacoplada de la inferencia (pipeline de indexación independiente).
- API de administración para gestionar reglas agronómicas y documentos del RAG.
- Mecanismo de actualización en caliente del índice vectorial (reindexación incremental o por lotes).
- Separación clara entre modelos ML (reentrenamiento programado, lento) y conocimiento experto (actualización ágil, rápida).

## Notas del analista
- Esta separación entre "conocimiento actualizable sin reentrenar" y "modelos que requieren reentrenamiento" es una decisión arquitectónica clave. El conocimiento agronómico cambia poco (las leyes de la química de suelos no varían), pero se refina con nueva investigación.
- Para la actualización del índice vectorial, herramientas como Pinecone, Weaviate o Qdrant ofrecen operaciones de upsert que permiten agregar/actualizar documentos sin reconstruir todo el índice.
