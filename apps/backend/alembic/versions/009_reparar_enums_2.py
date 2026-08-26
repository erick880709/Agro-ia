"""Migration 009 — Auto-reparación reforzada de tipos enum.

En BDs recreadas o restauradas puede faltar algún tipo enum que las
migraciones 004/008 ya no vuelven a crear (ej. `clasificacionupra`,
`estadorecomendacion`) mientras que otras sí existen (ej. `texturasuelo`
creado por la 003). Esta migración es idempotente:

1. Crea cualquier tipo enum de los modelos que no exista en `agroia`.
2. Convierte las columnas afectadas al tipo correcto si aún no lo tienen.

Revision ID: 009_reparar_enums_2
Down revision: 008_reparar_enums_sensor
"""

import sqlalchemy as sa
from alembic import op

revision = "009_reparar_enums_2"
down_revision = "008_reparar_enums_sensor"
branch_labels = None
depends_on = None

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

# columna → tipo enum esperado
COLUMNAS = [
    ("discordancias", "estado", "estadodiscordancia"),
    ("fichas_tecnicas", "estado", "estadoficha"),
    ("fichas_tecnicas", "tipo_fuente", "tipofuente"),
    ("recomendaciones", "clasificacion_upra", "clasificacionupra"),
    ("recomendaciones", "estado", "estadorecomendacion"),
    ("reglas_agronomicas", "variable", "variablesuelo"),
    ("reglas_agronomicas", "prioridad", "prioridadregla"),
    ("modelos_ml", "stage", "stagemodelo"),
]


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


def _tipo_columna(conn, tabla: str, columna: str) -> str | None:
    return conn.execute(
        sa.text(
            "SELECT format_type(a.atttypid, a.atttypmod) "
            "FROM pg_attribute a "
            "JOIN pg_class c ON c.oid = a.attrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'agroia' AND c.relname = :t AND a.attname = :c"
        ),
        {"t": tabla, "c": columna},
    ).scalar()


def upgrade() -> None:
    conn = op.get_bind()

    # 1) Crear tipos enum faltantes
    for nombre, valores in ENUMS.items():
        if not _tipo_existe(conn, nombre):
            valores_sql = ", ".join(f"'{v}'" for v in valores)
            conn.execute(
                sa.text(f"CREATE TYPE agroia.{nombre} AS ENUM ({valores_sql})")
            )

    # 2) Convertir columnas que no usan el tipo esperado
    for tabla, columna, tipo in COLUMNAS:
        actual = _tipo_columna(conn, tabla, columna)
        if actual is None:
            continue
        actual = actual.lower()
        if actual in (tipo, f"agroia.{tipo}"):
            continue
        conn.execute(
            sa.text(
                f"ALTER TABLE agroia.{tabla} ALTER COLUMN {columna} DROP DEFAULT"
            )
        )
        conn.execute(
            sa.text(
                f"ALTER TABLE agroia.{tabla} ALTER COLUMN {columna} "
                f"TYPE agroia.{tipo} USING {columna}::text::agroia.{tipo}"
            )
        )


def downgrade() -> None:
    """Sin cambios destructivos: la reparación no se revierte."""
