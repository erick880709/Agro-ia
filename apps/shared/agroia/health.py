"""Health check endpoint estándar para todos los servicios de AgroIA.

Verifica que el servicio esté vivo y que sus dependencias críticas
(base de datos) respondan.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check del servicio. Verifica conexión a BD."""
    from agroia.database import check_database_health

    db_ok = await check_database_health()

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version="0.1.0",
        database="connected" if db_ok else "unreachable",
    )
