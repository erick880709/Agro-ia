"""Migration 005 — Alinear valores de 4 tipos enum con los nombres del modelo.

La migración 003 creó `rolusuario`, `planmembresia`, `estadomembresia` y
`texturasuelo` con los VALORES de los enums Python ("Admin", "Mensual", ...),
pero SQLAlchemy serializa los NOMBRES de los miembros ("ADMIN", "MENSUAL",
...). Esta migración renombra los labels a los nombres que esperan los
modelos (idempotente: solo renombra si el label viejo existe y el nuevo no).
"""

import sqlalchemy as sa
from alembic import op

revision = "005_fix_enum_values"
down_revision = "004_crear_enums"
branch_labels = None
depends_on = None

# tipo: {valor_viejo: nombre_nuevo}
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


def _labels(tipo: str) -> set[str]:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT e.enumlabel FROM pg_enum e "
            "JOIN pg_type t ON t.oid = e.enumtypid "
            "JOIN pg_namespace n ON n.oid = t.typnamespace "
            "WHERE n.nspname = 'agroia' AND t.typname = :tipo"
        ),
        {"tipo": tipo},
    ).all()
    return {r[0] for r in rows}


def _aplicar(tipo: str, mapa: dict[str, str]) -> None:
    conn = op.get_bind()
    labels = _labels(tipo)
    for viejo, nuevo in mapa.items():
        if viejo in labels and nuevo not in labels:
            conn.execute(
                sa.text(
                    f"ALTER TYPE agroia.{tipo} RENAME VALUE '{viejo}' TO '{nuevo}'"
                )
            )


def upgrade() -> None:
    for tipo, mapa in RENOMBRES.items():
        _aplicar(tipo, mapa)


def downgrade() -> None:
    for tipo, mapa in RENOMBRES.items():
        _aplicar(tipo, {nuevo: viejo for viejo, nuevo in mapa.items()})
