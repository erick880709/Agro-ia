"""Mantenimiento de datos: limpieza programada de imágenes en BD.

`chat_memoria.imagen_base64` guarda fotos en Base64 dentro de PostgreSQL;
para no inflar la BD (Neon Free), un job diario borra las imágenes de más
de 90 días. Las fotos de labores ya no van a la BD (solo `imagen_url`).
"""

from agroia.logging import get_logger
from sqlalchemy import text

logger = get_logger(__name__)


async def limpiar_imagenes_chat(db, dias: int = 90) -> int:
    """Elimina `imagen_base64` de chat_memoria con más de `dias` días.

    Devuelve el número de filas liberadas. Idempotente.
    """
    resultado = await db.execute(
        text(
            "UPDATE agroia.chat_memoria SET imagen_base64 = NULL "
            "WHERE imagen_base64 IS NOT NULL "
            "AND ts < NOW() - make_interval(days => :dias)"
        ),
        {"dias": int(dias)},
    )
    await db.commit()
    filas = int(resultado.rowcount or 0)
    logger.info("chat_imagenes_limpiadas", liberadas=filas, dias=dias)
    return filas
