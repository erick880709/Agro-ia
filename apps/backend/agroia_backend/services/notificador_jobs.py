"""Disparadores de notificaciones (1.I) — labores próximas a vencer.

Se invoca desde la tarea de mantenimiento existente (cada 24 h). Reutiliza
`services/notificaciones.py::enviar_whatsapp`, que degrada a no-op sin
credenciales de WhatsApp Cloud API.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from agroia.logging import get_logger
from agroia_backend.models.labor import Labor
from agroia_backend.models.lote import Lote
from agroia_backend.models.preferencia_notificacion import PreferenciaNotificacion

logger = get_logger(__name__)


async def notificar_labores_proximas(db) -> dict:
    """Avisa por canal configurado las labores que vencen en ≤ 2 días."""
    from agroia_backend.services.notificaciones import enviar_whatsapp

    enviadas = 0
    omitidas = 0
    prefs = (
        await db.execute(
            select(PreferenciaNotificacion).where(
                PreferenciaNotificacion.activo.is_(True),
                PreferenciaNotificacion.canal == "whatsapp",
                PreferenciaNotificacion.telefono.isnot(None),
            )
        )
    ).scalars().all()
    if not prefs:
        return {"enviadas": 0, "omitidas": 0, "motivo": "sin_preferencias"}

    hoy = datetime.now(timezone.utc).date()
    limite = hoy + timedelta(days=2)

    for pref in prefs:
        if not pref.finca_id:
            continue
        lotes = (
            await db.execute(select(Lote.id).where(Lote.finca_id == pref.finca_id))
        ).scalars().all()
        if not lotes:
            continue
        labores = (
            await db.execute(
                select(Labor).where(
                    Labor.lote_id.in_(lotes),
                    Labor.estado.in_(["Pendiente", "En Progreso"]),
                    Labor.fecha_programada <= limite,
                ).order_by(Labor.fecha_programada).limit(5)
            )
        ).scalars().all()
        if not labores:
            continue
        nombres = "; ".join(labor.titulo or labor.tipo for labor in labores[:3])
        resultado = enviar_whatsapp(
            pref.telefono,
            "alerta_lluvia_aplicacion",  # plantilla registrada en Meta
            [nombres[:180], limite.isoformat()],
        )
        if resultado.get("estado") == "enviado":
            enviadas += 1
        else:
            omitidas += 1

    logger.info("notificaciones_labores", enviadas=enviadas, omitidas=omitidas)
    return {"enviadas": enviadas, "omitidas": omitidas}
