"""Migration 008 — Auto-reparación de tipos enum y columna `textura`.

En bases ya existentes (p. ej. Neon de producción) puede faltar el tipo
`texturasuelo` o la columna `sensor_readings.textura` puede no estar
tipada con él (por intervenciones manuales previas). Esta migración es
idempotente y repara:

1. Crea cualquier tipo enum que los modelos esperan y no exista.
2. Renombra labels viejos (valores Python) a los nombres que SQLAlchemy
   serializa (idempotente, igual que la migración 005).
3. Si `sensor_readings.textura` no es `agroia.texturasuelo`, lo convierte;
   los valores que no encajan en el enum quedan NULL.

Revision ID: 008_reparar_enums_sensor
Down revision: 007_chat_memoria
"""

import sqlalchemy as sa
from alembic import op

revision = "008_reparar_enums_sensor"
down_revision = "007_chat_memoria"
branch_labels = None
depends_on = None

# nombre: valores esperados por los modelos (nombres de los miembros)
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
}

# tipo: {label_viejo: label_nuevo}
RENOMBRES = {
    "rolusuario": {
        "Admin": "ADMIN",
        "Agronomo": "AGRONOMO",
        "Cliente": "CLIENTE",
        "Tecnico": "TECNICO",
        "Investigador": "INVESTIGADOR",
    },
    "planmembresia": {
        "Mensual": "MENSUAL",
        "Semestral": "SEMESTRAL",
        "Anual": "ANUAL",
    },
    "estadomembresia": {
        "Activa": "ACTIVA",
        "Vencida": "VENCIDA",
        "Cancelada": "CANCELADA",
    },
    "texturasuelo": {
        "Arena": "ARENA",
        "Limo": "LIMO",
        "Arcilla": "ARCILLA",
    },
}


def _tipo_existe(conn, nombre: str) -> bool:
    row = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_type t "
            "JOIN pg_namespace n ON n.oid = t.typnamespace "
            "WHERE n.nspname = 'agroia' AND t.typname = :n"
        ),
        {"n": nombre},
    ).first()
    return row is not None


def upgrade() -> None:
    conn = op.get_bind()

    # 1) Crear tipos enum faltantes
    for nombre, valores in ENUMS.items():
        if not _tipo_existe(conn, nombre):
            valores_sql = ", ".join(f"'{v}'" for v in valores)
            conn.execute(
                sa.text(f"CREATE TYPE agroia.{nombre} AS ENUM ({valores_sql})")
            )

    # 2) Renombrar labels viejos → nombres que serializa SQLAlchemy
    for tipo, mapa in RENOMBRES.items():
        if not _tipo_existe(conn, tipo):
            continue
        labels = {
            r[0]
            for r in conn.execute(
                sa.text(
                    "SELECT e.enumlabel FROM pg_enum e "
                    "JOIN pg_type t ON t.oid = e.enumtypid "
                    "JOIN pg_namespace n ON n.oid = t.typnamespace "
                    "WHERE n.nspname = 'agroia' AND t.typname = :t"
                ),
                {"t": tipo},
            ).all()
        }
        for viejo, nuevo in mapa.items():
            if viejo in labels and nuevo not in labels:
                conn.execute(
                    sa.text(
                        f"ALTER TYPE agroia.{tipo} RENAME VALUE '{viejo}' TO '{nuevo}'"
                    )
                )

    # 3) Columna textura de sensor_readings: forzar agroia.texturasuelo
    tipo_columna = conn.execute(
        sa.text(
            "SELECT format_type(a.atttypid, a.atttypmod) "
            "FROM pg_attribute a "
            "JOIN pg_class c ON c.oid = a.attrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'agroia' AND c.relname = 'sensor_readings' "
            "AND a.attname = 'textura'"
        )
    ).scalar()
    if tipo_columna is not None and tipo_columna.lower() not in (
        "texturasuelo",
        "agroia.texturasuelo",
    ):
        conn.execute(
            sa.text(
                "ALTER TABLE agroia.sensor_readings ALTER COLUMN textura "
                "TYPE agroia.texturasuelo "
                "USING CASE WHEN textura::text IN ('ARENA','LIMO','ARCILLA') "
                "THEN textura::text::agroia.texturasuelo ELSE NULL END"
            )
        )


def downgrade() -> None:
    """Sin cambios destructivos: la reparación no se revierte."""
