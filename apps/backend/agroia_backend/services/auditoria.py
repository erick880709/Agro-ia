"""Registro de auditoría: quién hizo qué, sobre qué y cuándo.

Uso desde los endpoints:

    await registrar_auditoria(db, email="a@b.co", nombre="Admin", rol="Admin",
        accion="finca.eliminar", entidad="finca", entidad_id="<uuid>",
        detalle={"nombre": "El Vergel", "lotes": 2})

La función hace `db.add` + `db.flush()` y delega el `commit` al endpoint
(que de todas formas commitea su operación). Para acciones sin commit
propio (login, reset de demo) usar `auditar_y_commit(...)`.
"""

from agroia_backend.models.auditoria import Auditoria


async def registrar_auditoria(
    db,
    *,
    usuario_email: str,
    accion: str,
    entidad: str,
    entidad_id: str | None = None,
    usuario_nombre: str | None = None,
    rol: str | None = None,
    detalle: dict | None = None,
    ip: str | None = None,
) -> None:
    """Registra un evento de auditoría (add + flush; el endpoint commitea)."""
    db.add(Auditoria(
        usuario_email=(usuario_email or "desconocido@agroia.co").lower(),
        usuario_nombre=usuario_nombre,
        rol=rol,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle,
        ip=ip,
    ))
    await db.flush()


async def auditar_y_commit(db, **kwargs) -> None:
    """Registra el evento y commitea (para acciones sin commit propio)."""
    await registrar_auditoria(db, **kwargs)
    await db.commit()
