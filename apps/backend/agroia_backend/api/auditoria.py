"""API de auditoría: consulta de la bitácora de acciones (solo Admin)."""

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia.database import get_db
from agroia_backend.models.auditoria import Auditoria

router = APIRouter(prefix="/api/v1", tags=["auditoria"])


def _exigir_admin(x_user_role: str | None) -> str:
    rol = (x_user_role or "").strip().lower()
    if rol not in {"admin", "administrador"}:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol administrador puede consultar la auditoría.",
        })
    return rol


@router.get("/auditoria")
async def listar_auditoria(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    entidad: str | None = Query(None, description="finca | lote | usuario | auth | demo…"),
    accion: str | None = Query(None, description="Código de acción, ej. usuario.eliminar"),
    search: str | None = Query(None, description="Busca en email, nombre o entidad_id"),
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Lista paginada de eventos de auditoría (solo Admin)."""
    _exigir_admin(x_user_role)

    filtros = []
    if entidad:
        filtros.append(Auditoria.entidad == entidad.strip().lower())
    if accion:
        filtros.append(Auditoria.accion == accion.strip().lower())
    if search:
        s = f"%{search.strip().lower()}%"
        filtros.append(or_(
            Auditoria.usuario_email.ilike(s),
            Auditoria.usuario_nombre.ilike(s),
            Auditoria.entidad_id.ilike(s),
        ))

    stmt_total = select(func.count()).select_from(Auditoria)
    stmt = select(Auditoria)
    if filtros:
        stmt_total = stmt_total.where(*filtros)
        stmt = stmt.where(*filtros)

    total = (await db.execute(stmt_total)).scalar_one()
    filas = (
        await db.execute(
            stmt.order_by(Auditoria.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    total_pages = (total + page_size - 1) // page_size if total else 0
    return {
        "data": [
            {
                "id": str(a.id),
                "usuario_email": a.usuario_email,
                "usuario_nombre": a.usuario_nombre,
                "rol": a.rol,
                "accion": a.accion,
                "entidad": a.entidad,
                "entidad_id": a.entidad_id,
                "detalle": a.detalle,
                "ip": a.ip,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in filas
        ],
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }
