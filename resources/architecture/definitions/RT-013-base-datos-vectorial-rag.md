# RT-013: Base de Datos Vectorial para RAG

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / IA
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 7.2, 8; RFP-inicial.md — Sección 3 (Agente IA)

## Descripción
Para el agente conversacional basado en RAG (Retrieval-Augmented Generation), la plataforma debe contar con una base de datos vectorial que almacene los embeddings del corpus de conocimiento agronómico. Esta base de datos permite:

- Indexar documentos del dominio (manuales de Cenicafé, guías de AGROSAVIA, fichas técnicas de cultivos, publicaciones científicas) como vectores de alta dimensionalidad.
- Realizar búsqueda semántica: dado un embedding de la pregunta del usuario, recuperar los fragmentos de documento más relevantes.
- Actualizar el índice con nuevos documentos sin necesidad de reindexar todo el corpus.

## Criterio medible / restricción concreta
- Búsqueda semántica con latencia < 500ms para corpus de hasta 10,000 documentos.
- Soporte para operaciones de upsert (agregar/actualizar documentos individualmente).
- Distancia/similitud configurable (coseno, euclidiana, producto punto).
- No especificados en el RFP — definir: base de datos vectorial concreta (Pinecone, Weaviate, Qdrant, pgvector en PostgreSQL, Chroma), modelo de embeddings (text-embedding-3-small, all-MiniLM-L6-v2, modelo multilingüe), estrategia de chunking (tamaño de fragmento, solapamiento).

## Impacto en la arquitectura
- Servicio independiente o extensión de PostgreSQL (pgvector) para almacenar vectores.
- Pipeline de indexación: documento → chunking → embedding → upsert en BD vectorial.
- Pipeline de consulta: pregunta → embedding → búsqueda vectorial → contexto recuperado → prompt LLM → respuesta.
- Necesidad de un modelo de embeddings (puede ser el mismo LLM o un modelo especializado más ligero).

## Notas del analista
- **pgvector** (extensión de PostgreSQL) es una opción atractiva porque evita introducir un nuevo sistema de base de datos: los vectores se almacenan junto con los metadatos de documentos en PostgreSQL. Para el MVP, es probablemente suficiente.
- Si el corpus crece mucho, Pinecone o Qdrant ofrecen mejor rendimiento en búsqueda vectorial a escala.
- El modelo de embeddings debe manejar bien el español (los documentos de Cenicafé, AGROSAVIA están en español). `text-embedding-3-small` de OpenAI tiene buen soporte multilingüe. `paraphrase-multilingual-MiniLM-L12-v2` es una alternativa open-source.
