"""Contexto de usuario para las APIs AGC-COST (F2-F7).

Lee la identidad del request: JWT validado por el middleware
(`request.state.usuario`) con respaldo en las cabeceras X-User-* (demo).
Valida rol y devuelve {uid, email, nombre, rol} normalizado.
"""

import uuid

from fastapi import HTTPException, Request


def _uuid_o_none(valor) -> uuid.UUID | None:
    if not valor:
        return None
    try:
        return uuid.UUID(str(valor))
    except ValueError:
        return None


def contexto_usuario(request: Request, exigir_roles: set[str] | None = None) -> dict:
    """Identidad del usuario actual; lanza 401/403 si falta o el rol no aplica."""
    usuario = getattr(request.state, "usuario", None) or {}
    email = usuario.get("email") or request.headers.get("x-user-email")
    uid = usuario.get("uid") or request.headers.get("x-user-id")
    nombre = usuario.get("nombre") or request.headers.get("x-user-nombre")
    rol = (usuario.get("rol") or request.headers.get("x-user-role") or "").strip().lower()

    if not email and not uid and not rol:
        raise HTTPException(status_code=401, detail={
            "code": "UNAUTHORIZED",
            "message": "Autenticación requerida (Authorization: Bearer).",
        })
    if exigir_roles and rol not in exigir_roles:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": (
                f"El rol «{rol or 'sin rol'}» no tiene permiso para esta operación. "
                f"Se requiere: {', '.join(sorted(exigir_roles))}."
            ),
        })
    return {
        "uid": _uuid_o_none(uid),
        "email": email or "desconocido@agroia.co",
        "nombre": nombre,
        "rol": rol,
    }


ROLES_ADMIN = {"admin", "administrador"}
ROLES_ADMIN_AGRONOMO = {"admin", "administrador", "agronomo", "agrónomo"}
