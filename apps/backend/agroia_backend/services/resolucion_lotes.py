"""Resolución del campo `lote` de la trama del sensor al UUID del lote.

El sensor envía un identificador corto de lote (UUID o nombre); aquí se
valida que pertenezca a la finca indicada y se devuelve el `lote_id` para
persistir la lectura diferenciada por lote (multi-lote).
"""

import uuid as uuid_mod

from fastapi import HTTPException
from sqlalchemy import select

from agroia.database import async_session_factory


async def resolver_lote_id(finca_id: str, lote_ref: str) -> str:
    """Resuelve `lote_ref` al UUID del lote de la finca.

    Acepta el UUID del lote o su nombre (sin distinguir mayúsculas). Lanza
    HTTPException 422 si el lote no existe, no pertenece a la finca o el
    nombre es ambiguo.
    """
    from agroia_backend.models.lote import Lote

    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA",
            "message": "finca_id no es un UUID válido.",
        })

    async with async_session_factory() as session:
        lotes = (
            await session.execute(
                select(Lote).where(Lote.finca_id == finca_uuid, Lote.activo.is_(True))
            )
        ).scalars().all()

    ref = str(lote_ref).strip()

    # 1) UUID exacto del lote
    try:
        lote_uuid = uuid_mod.UUID(ref)
    except ValueError:
        lote_uuid = None
    if lote_uuid is not None:
        for lote in lotes:
            if lote.id == lote_uuid:
                return str(lote.id)
        raise HTTPException(status_code=422, detail={
            "code": "LOTE_NO_PERTENECE",
            "message": f"El lote '{ref}' no pertenece a la finca '{finca_id}'.",
        })

    # 2) Nombre del lote (sin distinguir mayúsculas)
    nombre = ref.lower()
    coincidencias = [
        lote for lote in lotes if (lote.nombre or "").strip().lower() == nombre
    ]
    if len(coincidencias) == 1:
        return str(coincidencias[0].id)
    if len(coincidencias) > 1:
        raise HTTPException(status_code=422, detail={
            "code": "LOTE_AMBIGUO",
            "message": f"Varios lotes se llaman '{ref}' en esta finca; use el ID del lote.",
        })

    disponibles = [f"{lote.nombre} ({lote.id})" for lote in lotes]
    raise HTTPException(status_code=422, detail={
        "code": "LOTE_NOT_FOUND",
        "message": (
            f"Lote '{ref}' no encontrado en la finca. Lotes disponibles: "
            + (", ".join(disponibles) if disponibles else "ninguno")
        ),
    })
