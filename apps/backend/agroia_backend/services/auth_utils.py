"""Utilidades de hash de contraseñas (MVP; el Auth Service usará bcrypt/argon2)."""

import hashlib
import hmac

_SALT = "agroia:"


def hash_password(password: str) -> str:
    return hashlib.sha256(f"{_SALT}{password}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Comparación en tiempo constante contra el hash almacenado."""
    return hmac.compare_digest(hash_password(password), password_hash or "")
