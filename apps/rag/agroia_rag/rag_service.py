"""Servicio RAG — Agente conversacional agronómico.

Arquitectura: Retrieval-Augmented Generation.
1. Embedding de la pregunta con MiniLM (local, open-source, español)
2. Búsqueda vectorial en pgvector (top-K chunks relevantes)
3. Prompt engineering con contexto recuperado
4. LLM (OpenAI GPT-4) genera respuesta SIN alucinar

Modo dual: agricultor (coloquial) / experto (técnico con fuentes).
"""

import json
from typing import Optional

from agroia.config import get_settings
from agroia.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ── Config RAG ──
CHUNK_SIZE = 1024   # tokens por chunk
CHUNK_OVERLAP = 0.10  # 10% overlap
TOP_K = 5            # chunks a recuperar
MAX_RESPONSE_TOKENS = 500

# ── System prompts por modo ──
SYSTEM_PROMPTS = {
    "agricultor": (
        "Eres un asistente agronómico virtual de AgroIA que ayuda a agricultores colombianos. "
        "Reglas ESTRICTAS:\n"
        "1. Usa lenguaje coloquial, sencillo, SIN tecnicismos.\n"
        "2. Responde SOLO con la información del contexto proporcionado.\n"
        "3. Si el contexto no tiene suficiente información, di EXACTAMENTE: "
        "'No tengo información suficiente para responder a esta pregunta. Consulte a su técnico agrónomo.'\n"
        "4. NO inventes datos, recomendaciones ni umbrales.\n"
        "5. Sé alentador y práctico. Da respuestas paso a paso.\n"
        "6. Responde en español colombiano."
    ),
    "experto": (
        "Eres un asistente agronómico técnico de AgroIA para agrónomos e investigadores. "
        "Reglas ESTRICTAS:\n"
        "1. Usa lenguaje técnico preciso.\n"
        "2. Responde SOLO con la información del contexto proporcionado, citando la fuente.\n"
        "3. Si el contexto no tiene suficiente información, di EXACTAMENTE: "
        "'No hay datos suficientes en el corpus para responder. Fuente requerida.'\n"
        "4. Incluye datos numéricos, umbrales y referencias cuando estén disponibles.\n"
        "5. NO inventes información.\n"
        "6. Responde en español."
    ),
}

# ── Prompt template ──
PROMPT_TEMPLATE = """{system_prompt}

CONTEXTO (documentos relevantes):
{context}

PREGUNTA DEL USUARIO:
{question}

RESPUESTA:"""


async def generate_embedding(text: str) -> list[float]:
    """Genera embedding de texto usando MiniLM (local).

    En producción, carga el modelo una vez al iniciar la app.
    Modelo: paraphrase-multilingual-MiniLM-L12-v2 (español, open-source).
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except ImportError:
        logger.warning("sentence_transformers_not_installed", fallback="dummy_embedding")
        # Dummy embedding para desarrollo sin el modelo
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in h[:384]]  # 384-dim dummy


async def search_similar_chunks(
    embedding: list[float],
    top_k: int = TOP_K,
) -> list[dict]:
    """Busca los chunks más similares en pgvector."""
    from agroia.database import async_session_factory
    from sqlalchemy import text

    async with async_session_factory() as session:
        # pgvector cosine similarity search
        query = text("""
            SELECT chunk_text, source, similarity
            FROM agroia.rag_chunks
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """)
        result = await session.execute(query, {
            "embedding": str(embedding),
            "top_k": top_k,
        })
        return [
            {"text": row.chunk_text, "source": row.source, "similarity": float(row.similarity)}
            for row in result
        ]


async def build_context(chunks: list[dict]) -> str:
    """Construye el contexto para el prompt."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[Documento {i}] (Fuente: {chunk['source']}, Similitud: {chunk['similarity']:.2f})\n{chunk['text']}")
    return "\n\n".join(parts)


async def query_llm(system_prompt: str, context: str, question: str) -> str:
    """Consulta a OpenAI GPT-4 con el contexto recuperado."""
    if not settings.openai_api_key or settings.openai_api_key == "sk-your-key-here":
        # Modo sin API key: respuesta de fallback
        return (
            "⚠️ Modo sin conexión a OpenAI.\n\n"
            f"Pregunta recibida: {question}\n\n"
            f"Contexto recuperado: {len(context)} caracteres de {TOP_K} fuentes.\n\n"
            "Para activar el agente RAG, configure OPENAI_API_KEY en .env"
        )

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        prompt = PROMPT_TEMPLATE.format(
            system_prompt=system_prompt,
            context=context,
            question=question,
        )

        response = await client.chat.completions.create(
            model=settings.openai_model or "gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=MAX_RESPONSE_TOKENS,
            temperature=0.3,  # baja temperatura = menos alucinación
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("openai_api_error", error=str(e))
        return "Lo siento, no puedo procesar su consulta en este momento. Intente de nuevo más tarde."


# ═══════════════════════════════════════════════
# Servicio RAG principal
# ═══════════════════════════════════════════════

async def rag_query(
    question: str,
    mode: str = "agricultor",
) -> dict:
    """Ejecuta el pipeline RAG completo.

    Args:
        question: Pregunta del usuario en español
        mode: 'agricultor' (coloquial) o 'experto' (técnico con fuentes)

    Returns:
        Dict con respuesta, fuentes, confianza
    """
    # Paso 1: Embedding
    embedding = await generate_embedding(question)

    # Paso 2: Búsqueda vectorial
    chunks = await search_similar_chunks(embedding)

    if not chunks:
        return {
            "respuesta": "No tengo información suficiente para responder a esta pregunta. Consulte a su técnico agrónomo.",
            "fuentes": [],
            "modo": mode,
        }

    # Paso 3: Construir contexto
    context = await build_context(chunks)

    # Paso 4: Prompt + LLM
    system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["agricultor"])
    respuesta = await query_llm(system_prompt, context, question)

    return {
        "respuesta": respuesta,
        "fuentes": [{"source": c["source"], "similarity": round(c["similarity"], 3)} for c in chunks],
        "modo": mode,
        "confianza": round(sum(c["similarity"] for c in chunks[:3]) / min(3, len(chunks)), 3),
    }


async def index_document(text: str, source: str, doc_id: str = None):
    """Indexa un documento en el índice vectorial (pgvector).

    Divide el texto en chunks de CHUNK_SIZE tokens con overlap,
    genera embeddings y los inserta en la tabla rag_chunks.
    """
    from agroia.database import async_session_factory
    from sqlalchemy import text

    # Chunking simple (por párrafos, ~1024 tokens)
    words = text.split()
    chunk_words = int(CHUNK_SIZE * 0.75)  # ~768 words ≈ 1024 tokens
    overlap_words = int(chunk_words * CHUNK_OVERLAP)

    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_words])
        if len(chunk) < 50:  # ignorar chunks muy pequeños
            break
        chunks.append(chunk)
        i += chunk_words - overlap_words

    logger.info("indexing_document", source=source, chunks=len(chunks))

    for chunk in chunks:
        embedding = await generate_embedding(chunk)
        async with async_session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO agroia.rag_chunks (doc_id, chunk_text, embedding, source)
                    VALUES (:doc_id, :chunk, :embedding::vector, :source)
                    ON CONFLICT (doc_id, chunk_idx) DO UPDATE
                    SET embedding = :embedding::vector, chunk_text = :chunk
                """),
                {
                    "doc_id": doc_id or source,
                    "chunk": chunk,
                    "embedding": str(embedding),
                    "source": source,
                },
            )
            await session.commit()
