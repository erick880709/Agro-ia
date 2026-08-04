---
id: 006
slug: agente-conversacional-rag
ia_cierre: 13/100
rondas: 2
estado: lista-para-diseno
fecha: 2026-08-03
---

# NECESIDAD DE NEGOCIO REFINADA

Asistente conversacional con arquitectura RAG que responde preguntas agronómicas usando exclusivamente el corpus documental indexado (Cenicafé, AGROSAVIA, fichas técnicas, manuales). Sin navegación a Internet. Opera en dos modos: agricultor (lenguaje coloquial) y experto (técnico). Respuesta <10s, búsqueda vectorial <500ms. Stack: LLM OpenAI GPT-4, embeddings open-source autogestionado `paraphrase-multilingual-MiniLM-L12-v2`, pgvector en PostgreSQL, chunking de 1024 tokens con 10% overlap. Calidad medida con banco de 50 preguntas de prueba evaluadas por agrónomo (meta: ≥85% respuestas correctas). El conocimiento se actualiza sin reentrenar el LLM (upsert en índice vectorial). Nunca inventa información: si no hay datos suficientes, lo indica explícitamente.

**Fuente(s) de origen**
- `RF-014-agente-conversacional-rag.md`, `RT-013-base-datos-vectorial-rag.md`

**Stack RAG definido**
| Componente | Elección | Justificación |
|-----------|----------|---------------|
| LLM | OpenAI GPT-4 | Consistente con refinamiento #1 |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (open-source, autogestionado) | Documentos en español, sin enviar corpus a OpenAI |
| Vector DB | pgvector en PostgreSQL | Sin nuevo sistema, integrado con datos transaccionales |
| Chunking | 1024 tokens, 10% overlap | Contexto profundo para documentos técnicos densos |

**Actores**

| Rol | Tipo | Responsabilidad |
|-----|------|-----------------|
| Agricultor | Beneficiario | Usa el chat en modo simple; recibe respuestas en lenguaje coloquial |
| Técnico Agrónomo | Beneficiario avanzado | Usa el chat en modo experto; recibe respuestas técnicas con fuentes |
| Administrador | Ejecutor | Actualiza el índice vectorial con nuevos documentos |

**Alcance**

- ✅ IN SCOPE (MVP):
  - RAG sobre corpus: biblioteca Cenicafé, manuales AGROSAVIA, fichas técnicas, guías UPRA
  - Modo agricultor: lenguaje coloquial, respuestas paso a paso
  - Modo experto: lenguaje técnico, cita de fuentes, datos numéricos
  - No alucinación: "No tengo información suficiente para responder..." cuando no hay datos
  - Actualización sin reentrenar: upsert en índice vectorial
  - Latencia: chat <10s, búsqueda vectorial <500ms
  - Calidad: ≥85% respuestas correctas en banco de 50 preguntas evaluadas por agrónomo
  - Ejemplos: "¿Qué puedo sembrar?", "¿Qué fertilizante aplicar?", "¿Qué significa pH 5.2?"

- ❌ OUT OF SCOPE (MVP):
  - Navegación a Internet
  - Respuestas fuera del dominio agronómico
  - Corpus de Cenicafé en producción comercial sin validación de licencia (brecha compartida con #1 y #2)

**Criterios de Aceptación** (Gherkin — 4 escenarios: respuesta con fuentes, "no sé" sin datos, modo dual, actualización sin reentrenar)

**Métricas de Éxito**

| Métrica | Meta | Plazo |
|---------|------|-------|
| Latencia chat | <10s (p95) | Producción |
| Búsqueda vectorial | <500ms | Producción |
| Calidad respuestas | ≥85% en banco de 50 preguntas | Fin de piloto |
| Tasa de "no sé" apropiado | 100% (sin alucinar cuando no hay datos) | Continuo |

**Prioridad (MoSCoW)**
- Must: RAG sin Internet, pgvector, no alucinación, actualización sin reentrenar, <10s, modo agricultor
- Should: Modo experto, banco de 50 preguntas, embeddings open-source, chunking 1024 tokens
- Could: Dashboard de uso del chat, feedback del agricultor
- Won't: Internet, modelo de embeddings comercial, Pinecone/Qdrant externo

**Dependencias:** Motor de recomendaciones (#1), Catálogo de cultivos (#2), Licencia Cenicafé (brecha legal compartida)

**Brechas:** Licencia CC BY-NC-ND de Cenicafé para uso comercial del corpus en el RAG

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 37/100
 Ronda 1:           24/100
 Ronda 2:           13/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Lista para diseño/estimación**
