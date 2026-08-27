"""Servicio de catálogo de cultivos y fichas técnicas.

Maneja el CRUD de Cultivo y FichaTecnica, el flujo de publicación
(Borrador → En Revisión → Publicado), el SLA de 5 días y la alerta
de revisión periódica cada 12 meses.
"""

import uuid
from datetime import datetime

from agroia.errors import NotFoundError, ValidationError
from agroia.logging import get_logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.cultivo import (
    Cultivo,
    EstadoFicha,
    FichaTecnica,
)

logger = get_logger(__name__)

# ── Cultivo CRUD ──

async def listar_cultivos(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    activo: bool | None = True,
) -> tuple[list[Cultivo], int]:
    """Lista cultivos paginados con búsqueda opcional."""
    stmt = select(Cultivo)
    count_stmt = select(func.count(Cultivo.id))

    if activo is not None:
        stmt = stmt.where(Cultivo.activo == activo)
        count_stmt = count_stmt.where(Cultivo.activo == activo)

    if search:
        filtro = Cultivo.nombre.ilike(f"%{search}%")
        stmt = stmt.where(filtro)
        count_stmt = count_stmt.where(filtro)

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.offset((page - 1) * page_size).limit(page_size).order_by(Cultivo.nombre)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def obtener_cultivo(db: AsyncSession, cultivo_id: str) -> Cultivo:
    """Obtiene un cultivo por ID."""
    stmt = select(Cultivo).where(Cultivo.id == cultivo_id)
    result = await db.execute(stmt)
    cultivo = result.scalar_one_or_none()
    if not cultivo:
        raise NotFoundError(f"Cultivo {cultivo_id} no encontrado")
    return cultivo


async def crear_cultivo(db: AsyncSession, nombre: str, **kwargs) -> Cultivo:
    """Crea un nuevo cultivo."""
    existing = await db.execute(
        select(Cultivo).where(Cultivo.nombre == nombre)
    )
    if existing.scalar_one_or_none():
        raise ValidationError(f"El cultivo '{nombre}' ya existe")

    cultivo = Cultivo(id=uuid.uuid4(), nombre=nombre, **kwargs)
    db.add(cultivo)
    await db.flush()
    logger.info("cultivo_creado", cultivo_id=str(cultivo.id), nombre=nombre)
    return cultivo


async def actualizar_cultivo(
    db: AsyncSession,
    cultivo_id: str,
    **campos,
) -> Cultivo:
    """Actualiza campos editables de un cultivo (fisiología, descripción…)."""
    cultivo = await obtener_cultivo(db, cultivo_id)
    for clave, valor in campos.items():
        if valor is not None and hasattr(cultivo, clave):
            setattr(cultivo, clave, valor)
    await db.flush()
    logger.info("cultivo_actualizado", cultivo_id=cultivo_id, campos=list(campos))
    return cultivo


# ── Ficha Técnica CRUD ──

async def listar_fichas(
    db: AsyncSession,
    cultivo_id: str | None = None,
    estado: EstadoFicha | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[FichaTecnica], int]:
    """Lista fichas técnicas paginadas con filtros opcionales."""
    stmt = select(FichaTecnica)
    count_stmt = select(func.count(FichaTecnica.id))

    if cultivo_id:
        stmt = stmt.where(FichaTecnica.cultivo_id == cultivo_id)
        count_stmt = count_stmt.where(FichaTecnica.cultivo_id == cultivo_id)
    if estado:
        stmt = stmt.where(FichaTecnica.estado == estado)
        count_stmt = count_stmt.where(FichaTecnica.estado == estado)

    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.offset((page - 1) * page_size).limit(page_size).order_by(FichaTecnica.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def obtener_ficha(db: AsyncSession, ficha_id: str) -> FichaTecnica:
    """Obtiene una ficha técnica por ID."""
    stmt = select(FichaTecnica).where(FichaTecnica.id == ficha_id)
    result = await db.execute(stmt)
    ficha = result.scalar_one_or_none()
    if not ficha:
        raise NotFoundError(f"Ficha técnica {ficha_id} no encontrada")
    return ficha


async def crear_ficha(db: AsyncSession, cultivo_id: str, **kwargs) -> FichaTecnica:
    """Crea una nueva ficha técnica en estado Borrador."""
    cultivo = await obtener_cultivo(db, cultivo_id)

    # Validar que no exista otra ficha publicada para este cultivo
    existing = await db.execute(
        select(FichaTecnica).where(
            FichaTecnica.cultivo_id == cultivo_id,
            FichaTecnica.estado == EstadoFicha.PUBLICADO,
        )
    )
    if existing.scalar_one_or_none():
        raise ValidationError(f"Ya existe una ficha publicada para el cultivo '{cultivo.nombre}'")

    ficha = FichaTecnica(
        id=uuid.uuid4(),
        cultivo_id=uuid.UUID(cultivo_id) if isinstance(cultivo_id, str) else cultivo_id,
        estado=EstadoFicha.BORRADOR,
        **kwargs,
    )
    db.add(ficha)
    await db.flush()
    logger.info("ficha_creada", ficha_id=str(ficha.id), cultivo=cultivo.nombre)
    return ficha


async def actualizar_ficha(db: AsyncSession, ficha_id: str, **kwargs) -> FichaTecnica:
    """Actualiza campos de una ficha (solo en estado Borrador)."""
    ficha = await obtener_ficha(db, ficha_id)

    if ficha.estado != EstadoFicha.BORRADOR:
        raise ValidationError(
            f"Solo se pueden editar fichas en estado 'Borrador'. Estado actual: {ficha.estado.value}"
        )

    for key, value in kwargs.items():
        if hasattr(ficha, key) and value is not None:
            setattr(ficha, key, value)

    await db.flush()
    logger.info("ficha_actualizada", ficha_id=ficha_id)
    return ficha


# ── Flujo de publicación ──

async def enviar_a_revision(db: AsyncSession, ficha_id: str) -> FichaTecnica:
    """Envía una ficha a revisión (Borrador → En Revisión)."""
    ficha = await obtener_ficha(db, ficha_id)

    if ficha.estado != EstadoFicha.BORRADOR:
        raise ValidationError(f"Estado inválido para envío: {ficha.estado.value}")

    ficha.estado = EstadoFicha.EN_REVISION
    ficha.fecha_envio_revision = datetime.utcnow()
    await db.flush()
    logger.info("ficha_enviada_revision", ficha_id=ficha_id)
    return ficha


async def aprobar_ficha(db: AsyncSession, ficha_id: str) -> FichaTecnica:
    """Aprueba una ficha (En Revisión → Publicado)."""
    ficha = await obtener_ficha(db, ficha_id)

    if ficha.estado != EstadoFicha.EN_REVISION:
        raise ValidationError(f"Estado inválido para aprobación: {ficha.estado.value}")

    now = datetime.utcnow()
    ficha.estado = EstadoFicha.PUBLICADO
    ficha.fecha_revision = now
    ficha.fecha_ultima_revision = now
    await db.flush()
    logger.info("ficha_aprobada", ficha_id=ficha_id)
    return ficha


async def rechazar_ficha(
    db: AsyncSession, ficha_id: str, notas: str | None = None
) -> FichaTecnica:
    """Rechaza una ficha (En Revisión → Borrador) con notas de corrección."""
    ficha = await obtener_ficha(db, ficha_id)

    if ficha.estado != EstadoFicha.EN_REVISION:
        raise ValidationError(f"Estado inválido para rechazo: {ficha.estado.value}")

    now = datetime.utcnow()
    ficha.estado = EstadoFicha.BORRADOR
    ficha.fecha_revision = now
    ficha.notas_revision = notas
    await db.flush()
    logger.info("ficha_rechazada", ficha_id=ficha_id)
    return ficha


# ── Consultas específicas ──

async def obtener_fichas_para_recomendaciones(db: AsyncSession) -> list[FichaTecnica]:
    """Obtiene fichas publicadas que pueden usarse en recomendaciones
    (fuente nacional, estado Publicado, sin etiqueta internacional)."""
    stmt = select(FichaTecnica).where(
        FichaTecnica.estado == EstadoFicha.PUBLICADO,
        FichaTecnica.etiqueta_internacional.is_(False),
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def obtener_fichas_pendientes_revision(
    db: AsyncSession, tecnico_id: str | None = None
) -> list[FichaTecnica]:
    """Obtiene fichas en revisión, ordenadas por antigüedad (SLA)."""
    stmt = select(FichaTecnica).where(
        FichaTecnica.estado == EstadoFicha.EN_REVISION
    ).order_by(FichaTecnica.fecha_envio_revision.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def obtener_fichas_vencidas_revision_periodica(db: AsyncSession) -> list[FichaTecnica]:
    """Obtiene fichas publicadas que no han sido revisadas en >12 meses."""
    cutoff = datetime.utcnow().replace(year=datetime.utcnow().year - 1)
    stmt = select(FichaTecnica).where(
        FichaTecnica.estado == EstadoFicha.PUBLICADO,
        or_(
            FichaTecnica.fecha_ultima_revision.is_(None),
            FichaTecnica.fecha_ultima_revision < cutoff,
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()
