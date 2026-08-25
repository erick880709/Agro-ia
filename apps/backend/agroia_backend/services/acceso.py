"""Control de acceso a fincas por rol (MVP sin Auth Service).

Reglas:
  - Admin y Agrónomo: acceso a todas las fincas.
  - Cliente: solo las fincas asociadas en `fincas_usuarios` (o de las que
    es propietario vía `fincas.usuario_id`).
  - Sin email registrado, un cliente no ve ninguna finca.

El rol viaja en `X-User-Role` y el email en `X-User-Email` (sesión demo).
"""

import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select

from agroia_backend.models.finca import Finca
from agroia_backend.models.finca_usuario import FincaUsuario
from agroia_backend.models.usuario import Usuario

ROLES_TOTALES = {"admin", "agronomo", "investigador", "tecnico"}


def _normalizar(rol: Optional[str]) -> str:
    return (rol or "").strip().lower()


async def get_usuario(db, email: Optional[str]) -> Optional[Usuario]:
    """Busca el usuario por email (sesión demo)."""
    email = (email or "").strip().lower()
    if not email:
        return None
    return (
        await db.execute(select(Usuario).where(Usuario.email == email))
    ).scalar_one_or_none()


async def fincas_permitidas_ids(
    db, rol: Optional[str], email: Optional[str]
) -> Optional[list[uuid.UUID]]:
    """Devuelve los IDs de fincas visibles o None si tiene acceso total."""
    r = _normalizar(rol)
    if r in ROLES_TOTALES:
        return None

    # Cliente (u otro rol restringido): requiere email registrado
    usuario = await get_usuario(db, email)
    if usuario is None:
        return []

    ids: set[uuid.UUID] = set()
    links = (
        await db.execute(
            select(FincaUsuario.finca_id).where(FincaUsuario.usuario_id == usuario.id)
        )
    ).scalars().all()
    ids.update(links)

    propias = (
        await db.execute(
            select(Finca.id).where(Finca.usuario_id == usuario.id)
        )
    ).scalars().all()
    ids.update(propias)

    return list(ids)


async def verificar_acceso_finca(
    db, rol: Optional[str], email: Optional[str], finca_id: str
) -> None:
    """Lanza 403 si el usuario actual no puede ver la finca indicada."""
    r = _normalizar(rol)
    if r in ROLES_TOTALES:
        return
    try:
        fid = uuid.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA",
            "message": "finca_id no es un UUID válido.",
        })
    permitidas = await fincas_permitidas_ids(db, rol, email) or []
    if fid not in permitidas:
        raise HTTPException(status_code=403, detail={
            "code": "FINCA_NO_AUTORIZADA",
            "message": "No tiene acceso a los reportes de esta finca.",
        })


def exigir_no_cliente(rol: Optional[str]) -> None:
    """Bloquea acciones de escritura para el rol cliente."""
    if _normalizar(rol) == "cliente":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "El rol Cliente es de solo lectura: no puede ejecutar esta acción.",
        })
