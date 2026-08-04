"""API endpoints del agente conversacional RAG."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agroia.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


class ChatRequest(BaseModel):
    pregunta: str = Field(..., min_length=3, max_length=1000)
    modo: str = Field("agricultor", pattern="^(agricultor|experto)$")


class ChatResponse(BaseModel):
    respuesta: str
    fuentes: list[dict] = []
    modo: str
    confianza: float


class IndexRequest(BaseModel):
    texto: str = Field(..., min_length=50)
    fuente: str = Field(..., min_length=3, max_length=255)
    doc_id: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Consulta al agente conversacional RAG.

    Ejemplos:
    - "¿Qué puedo sembrar en mi finca?"
    - "¿Qué fertilizante debo aplicar si tengo pH 5.2?"
    - "¿Cuáles son los umbrales ideales para café?"
    """
    from agroia_rag.rag_service import rag_query

    try:
        result = await rag_query(request.pregunta, request.modo)
        return ChatResponse(**result)
    except Exception as e:
        logger.error("rag_chat_error", error=str(e))
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": "Error en el agente RAG"})


@router.post("/index", status_code=202)
async def index_document(request: IndexRequest):
    """Indexa un documento en el corpus RAG (pgvector)."""
    from agroia_rag.rag_service import index_document

    try:
        await index_document(request.texto, request.fuente, request.doc_id)
        return {"status": "indexed", "fuente": request.fuente}
    except Exception as e:
        logger.error("rag_index_error", error=str(e))
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": "Error al indexar documento"})


@router.get("/health")
async def rag_health():
    """Verifica el estado del servicio RAG."""
    from agroia.config import get_settings

    s = get_settings()
    return {
        "status": "ok",
        "llm": "OpenAI GPT-4" if s.openai_api_key and s.openai_api_key != "sk-your-key-here" else "no configurado",
        "embeddings": "MiniLM (local)",
        "vector_db": "pgvector",
        "chunk_size": 1024,
        "top_k": 5,
    }
