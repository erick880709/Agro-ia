"""Asegura que los tipos enum existan en la BD al arrancar la aplicación.

Las migraciones crean los tipos, pero una BD externa (Neon) puede ser
reiniciada o restaurada después del arranque del contenedor, dejando la
aplicación conectada a una base sin los tipos. Esta rutina es idempotente
y se ejecuta en el arranque de la API: crea cualquier tipo enum faltante
en el schema `agroia`.
"""

import sqlalchemy as sa

from agroia.database import async_session_factory
from agroia.logging import get_logger

logger = get_logger(__name__)

ENUMS = {
    "clasificacionupra": ["ALTA", "MEDIA", "BAJA", "NO_APTA"],
    "estadodiscordancia": ["PENDIENTE", "REVISADA", "BLOQUEADA"],
    "estadoficha": ["BORRADOR", "EN_REVISION", "PUBLICADO"],
    "estadomembresia": ["ACTIVA", "VENCIDA", "CANCELADA"],
    "estadorecomendacion": ["PUBLICADA", "ADVERTENCIA", "BLOQUEADA"],
    "planmembresia": ["MENSUAL", "SEMESTRAL", "ANUAL"],
    "prioridadregla": ["CRITICA", "ALTA", "MEDIA", "BAJA"],
    "rolusuario": ["ADMIN", "CLIENTE", "TECNICO", "INVESTIGADOR", "AGRONOMO"],
    "stagemodelo": ["STAGING", "PRODUCTION", "ARCHIVED"],
    "texturasuelo": ["ARENA", "LIMO", "ARCILLA"],
    "tipofuente": ["NACIONAL", "INTERNACIONAL"],
    "variablesuelo": [
        "PH", "N", "P", "K", "Ca", "Mg", "S", "Fe", "Mn", "Zn", "Cu",
        "B", "MO", "CIC", "TEXTURA", "HUMEDAD", "TEMPERATURA_SUELO", "CE",
    ],
    "pedregosidad": ["NINGUNA", "MODERADA", "ALTA"],
    "tiporiego": ["GOTEO", "ASPERSION", "GRAVEDAD", "SECANO"],
}


async def asegurar_enums() -> list[str]:
    """Crea los tipos enum faltantes. Retorna los nombres creados."""
    creados: list[str] = []
    async with async_session_factory() as db:
        for nombre, valores in ENUMS.items():
            existe = (
                await db.execute(
                    sa.text(
                        "SELECT 1 FROM pg_type t "
                        "JOIN pg_namespace n ON n.oid = t.typnamespace "
                        "WHERE n.nspname = 'agroia' AND t.typname = :n"
                    ),
                    {"n": nombre},
                )
            ).first()
            if existe is not None:
                continue
            valores_sql = ", ".join(f"'{v}'" for v in valores)
            await db.execute(
                sa.text(f"CREATE TYPE agroia.{nombre} AS ENUM ({valores_sql})")
            )
            creados.append(nombre)
        await db.commit()
    if creados:
        logger.info("enums_creados_en_arranque", creados=creados)
    return creados
