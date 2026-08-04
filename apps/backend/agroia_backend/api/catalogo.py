"""API endpoints del catálogo de cultivos y fichas técnicas."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from agroia.errors import NotFoundError, ValidationError
from agroia.logging import get_logger
from agroia_backend.models.cultivo import EstadoFicha, TipoFuente
from agroia_backend.services import catalogo_service as svc

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/catalogo", tags=["catálogo"])

# ── Schemas ──

class CultivoCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    nombre_cientifico: Optional[str] = None
    descripcion: Optional[str] = None
    icono: Optional[str] = None


class CultivoResponse(BaseModel):
    id: str
    nombre: str
    nombre_cientifico: Optional[str] = None
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    activo: bool
    model_config = {"from_attributes": True}


class FichaCreate(BaseModel):
    cultivo_id: str
    tipo_fuente: TipoFuente = TipoFuente.NACIONAL
    fuente: str = Field(..., min_length=5, max_length=255)
    etiqueta_internacional: bool = False
    umbrales: dict = Field(default_factory=dict)
    datos_economicos: dict = Field(default_factory=dict)


class FichaUpdate(BaseModel):
    fuente: Optional[str] = None
    umbrales: Optional[dict] = None
    datos_economicos: Optional[dict] = None


class FichaResponse(BaseModel):
    id: str
    cultivo_id: str
    estado: str
    tipo_fuente: str
    fuente: str
    etiqueta_internacional: bool
    umbrales: dict
    datos_economicos: dict
    fecha_envio_revision: Optional[str] = None
    fecha_ultima_revision: Optional[str] = None
    notas_revision: Optional[str] = None
    model_config = {"from_attributes": True}


# ── Cultivos ──

@router.get("/cultivos")
async def listar_cultivos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
):
    """Lista cultivos paginados con búsqueda."""
    items, total = await svc.listar_cultivos(None, page, page_size, search)
    return {
        "data": [CultivoResponse.model_validate(c).model_dump() for c in items],
        "meta": {"page": page, "page_size": page_size, "total": total, "total_pages": max(1, (total + page_size - 1) // page_size)},
    }


@router.get("/cultivos/{cultivo_id}", response_model=CultivoResponse)
async def obtener_cultivo(cultivo_id: str):
    """Obtiene un cultivo por ID."""
    try:
        return await svc.obtener_cultivo(None, cultivo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": str(e)})


@router.post("/cultivos", response_model=CultivoResponse, status_code=201)
async def crear_cultivo(body: CultivoCreate):
    """Crea un nuevo cultivo."""
    try:
        return await svc.crear_cultivo(None, **body.model_dump())
    except ValidationError as e:
        raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR", "message": str(e)})


# ── Fichas Técnicas ──

@router.get("/fichas")
async def listar_fichas(
    cultivo_id: Optional[str] = None,
    estado: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lista fichas técnicas paginadas."""
    estado_enum = EstadoFicha(estado) if estado else None
    items, total = await svc.listar_fichas(None, cultivo_id, estado_enum, page, page_size)
    return {
        "data": [FichaResponse.model_validate(f).model_dump() for f in items],
        "meta": {"page": page, "page_size": page_size, "total": total, "total_pages": max(1, (total + page_size - 1) // page_size)},
    }


@router.get("/fichas/{ficha_id}", response_model=FichaResponse)
async def obtener_ficha(ficha_id: str):
    """Obtiene una ficha técnica por ID."""
    try:
        return await svc.obtener_ficha(None, ficha_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": str(e)})


@router.post("/fichas", response_model=FichaResponse, status_code=201)
async def crear_ficha(body: FichaCreate):
    """Crea una nueva ficha técnica (estado: Borrador)."""
    try:
        return await svc.crear_ficha(None, **body.model_dump())
    except (NotFoundError, ValidationError) as e:
        status = 404 if isinstance(e, NotFoundError) else 422
        raise HTTPException(status_code=status, detail={"code": "NOT_FOUND" if status == 404 else "VALIDATION_ERROR", "message": str(e)})


@router.put("/fichas/{ficha_id}", response_model=FichaResponse)
async def actualizar_ficha(ficha_id: str, body: FichaUpdate):
    """Actualiza una ficha (solo en estado Borrador)."""
    try:
        return await svc.actualizar_ficha(None, ficha_id, **body.model_dump(exclude_none=True))
    except (NotFoundError, ValidationError) as e:
        status = 404 if isinstance(e, NotFoundError) else 422
        raise HTTPException(status_code=status, detail={"code": "NOT_FOUND" if status == 404 else "VALIDATION_ERROR", "message": str(e)})


@router.post("/fichas/{ficha_id}/enviar-revision", response_model=FichaResponse)
async def enviar_a_revision(ficha_id: str):
    """Envía una ficha a revisión (Borrador → En Revisión)."""
    try:
        return await svc.enviar_a_revision(None, ficha_id, "admin")
    except (NotFoundError, ValidationError) as e:
        status = 404 if isinstance(e, NotFoundError) else 422
        raise HTTPException(status_code=status, detail={"code": "NOT_FOUND" if status == 404 else "VALIDATION_ERROR", "message": str(e)})


@router.post("/fichas/{ficha_id}/aprobar", response_model=FichaResponse)
async def aprobar_ficha(ficha_id: str):
    """Aprueba una ficha (En Revisión → Publicado)."""
    try:
        return await svc.aprobar_ficha(None, ficha_id, "tecnico")
    except (NotFoundError, ValidationError) as e:
        status = 404 if isinstance(e, NotFoundError) else 422
        raise HTTPException(status_code=status, detail={"code": "NOT_FOUND" if status == 404 else "VALIDATION_ERROR", "message": str(e)})


@router.post("/fichas/{ficha_id}/rechazar", response_model=FichaResponse)
async def rechazar_ficha(ficha_id: str, notas: str = Query(..., min_length=10)):
    """Rechaza una ficha (En Revisión → Borrador) con notas."""
    try:
        return await svc.rechazar_ficha(None, ficha_id, "tecnico", notas)
    except (NotFoundError, ValidationError) as e:
        status = 404 if isinstance(e, NotFoundError) else 422
        raise HTTPException(status_code=status, detail={"code": "NOT_FOUND" if status == 404 else "VALIDATION_ERROR", "message": str(e)})
