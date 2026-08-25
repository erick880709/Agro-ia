"""Migration 004 — Crear tipos enum faltantes y alinear nombres de columnas.

Las migraciones 001/002 crearon tablas con columnas de tipo enum usando
nombres snake_case (`estado_ficha_enum`, ...) con `create_type=False`, pero
nunca crearon los tipos, y los modelos SQLAlchemy generan los tipos con el
nombre de la clase Python (`estadoficha`, ...). En bases nuevas (CI, Neon)
esto rompe los INSERT.

Esta migración:
  1. Crea en el schema `agroia` todos los tipos enum (los que esperan los
     modelos y también los legacy, para que las tablas sean legibles).
  2. Convierte las columnas afectadas al tipo correcto.
  3. Elimina los tipos legacy con nombres snake_case que quedaron huérfanos.
"""

import sqlalchemy as sa
from alembic import op

revision = "004_crear_enums"
down_revision = "003_dispositivos_iot"
branch_labels = None
depends_on = None

# nombre_nuevo: (nombre_legacy, valores_en_orden)
ENUMS = {
    "clasificacionupra": ("clasificacion_upra_enum", ["ALTA", "MEDIA", "BAJA", "NO_APTA"]),
    "estadodiscordancia": ("estado_discordancia_enum", ["PENDIENTE", "REVISADA", "BLOQUEADA"]),
    "estadoficha": ("estado_ficha_enum", ["BORRADOR", "EN_REVISION", "PUBLICADO"]),
    "estadomembresia": (None, ["ACTIVA", "VENCIDA", "CANCELADA"]),
    "estadorecomendacion": ("estado_recomendacion_enum", ["PUBLICADA", "ADVERTENCIA", "BLOQUEADA"]),
    "planmembresia": (None, ["MENSUAL", "SEMESTRAL", "ANUAL"]),
    "prioridadregla": ("prioridad_regla_enum", ["CRITICA", "ALTA", "MEDIA", "BAJA"]),
    "rolusuario": (None, ["ADMIN", "CLIENTE", "TECNICO", "INVESTIGADOR", "AGRONOMO"]),
    "stagemodelo": ("stage_modelo_enum", ["STAGING", "PRODUCTION", "ARCHIVED"]),
    "texturasuelo": (None, ["ARENA", "LIMO", "ARCILLA"]),
    "tipofuente": ("tipo_fuente_enum", ["NACIONAL", "INTERNACIONAL"]),
    "variablesuelo": (
        "variable_suelo_enum",
        [
            "PH", "N", "P", "K", "Ca", "Mg", "S", "Fe", "Mn", "Zn", "Cu",
            "B", "MO", "CIC", "TEXTURA", "HUMEDAD", "TEMPERATURA_SUELO", "CE",
        ],
    ),
}

# columna → tipo nuevo (solo las que hoy usan nombres legacy)
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


def _tipo_existe(nombre: str) -> bool:
    conn = op.get_bind()
    row = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_type t "
            "JOIN pg_namespace n ON n.oid = t.typnamespace "
            "WHERE n.nspname = 'agroia' AND t.typname = :nombre"
        ),
        {"nombre": nombre},
    ).first()
    return row is not None


def _crear_enum_si_falta(nombre: str, valores: list[str]) -> None:
    if _tipo_existe(nombre):
        return
    conn = op.get_bind()
    valores_sql = ", ".join(f"'{v}'" for v in valores)
    conn.execute(sa.text(f"CREATE TYPE agroia.{nombre} AS ENUM ({valores_sql})"))


def upgrade() -> None:
    conn = op.get_bind()
    # 1) Crear los tipos que esperan los modelos
    for nombre, (_legacy, valores) in ENUMS.items():
        _crear_enum_si_falta(nombre, valores)
    # 2) Crear también los legacy (las columnas existentes los referencian
    #    y sin ellos la tabla es ilegible para el ALTER)
    for nombre, (legacy, valores) in ENUMS.items():
        if legacy:
            _crear_enum_si_falta(legacy, valores)
    # 3) Convertir columnas con tipos legacy al tipo correcto.
    #    Se quita el DEFAULT (tipado al enum legacy) y no se recrea: los
    #    modelos aplican sus defaults en Python al insertar vía ORM.
    for tabla, columna, tipo in COLUMNAS:
        conn.execute(
            sa.text(f"ALTER TABLE agroia.{tabla} ALTER COLUMN {columna} DROP DEFAULT")
        )
        conn.execute(
            sa.text(
                f"ALTER TABLE agroia.{tabla} ALTER COLUMN {columna} "
                f"TYPE agroia.{tipo} USING {columna}::text::agroia.{tipo}"
            )
        )
    # 4) Eliminar tipos legacy huérfanos
    for nombre, (legacy, _valores) in ENUMS.items():
        if legacy:
            conn.execute(sa.text(f"DROP TYPE IF EXISTS agroia.{legacy}"))


def downgrade() -> None:
    conn = op.get_bind()
    # 1) Recrear tipos legacy y revertir columnas
    for tabla, columna, tipo in COLUMNAS:
        legacy = ENUMS[tipo][0]
        valores = ENUMS[tipo][1]
        _crear_enum_si_falta(legacy, valores)
        conn.execute(
            sa.text(
                f"ALTER TABLE agroia.{tabla} ALTER COLUMN {columna} "
                f"TYPE agroia.{legacy} USING {columna}::text::agroia.{legacy}"
            )
        )
    # 2) Eliminar los tipos renombrados que quedaron sin referencias
    for _tabla, _columna, tipo in COLUMNAS:
        conn.execute(sa.text(f"DROP TYPE IF EXISTS agroia.{tipo}"))
