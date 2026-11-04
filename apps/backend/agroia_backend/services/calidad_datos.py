"""Compatibilidad con la antigua regla binaria de calidad (pre-E2).

El motor real vive en `motor_calidad.py` (10 estados). Este módulo conserva la
API anterior (`es_lectura_objetivo`, `lectura_a_invalidar`, `CALIDAD_INVALIDADA`)
para no romper importadores externos; internamente delega en el motor nuevo.
"""

from agroia_backend.services.motor_calidad import (  # noqa: F401
    CALIDADES_EXCLUIDAS_ANALISIS,
    CALIDAD_INVALIDADA,
    COORD_DEFECTO,
    clasificar_lectura,
    es_lectura_valida_para_analisis,
)

# Rangos históricos (se conservan por compatibilidad de la API antigua).
RANGO_PH = (3.0, 9.0)
RANGO_CE = (0.01, 10.0)
RANGO_NPK = (1.0, 1999.0)


def es_lectura_objetivo(
    *,
    ph=None,
    conductividad_electrica=None,
    nitrogeno=None,
    fosforo=None,
    potasio=None,
    pos_x=None,
    pos_y=None,
) -> bool:
    """True si la lectura alimenta análisis/reportes (equivalente histórico)."""
    estado, _ = clasificar_lectura(
        ph=ph,
        conductividad_electrica=conductividad_electrica,
        nitrogeno=nitrogeno,
        fosforo=fosforo,
        potasio=potasio,
        pos_x=pos_x,
        pos_y=pos_y,
    )
    return es_lectura_valida_para_analisis(estado)


def lectura_a_invalidar(reading) -> bool:
    """Atajo para un objeto SensorReading (o dict-like) ya persistido."""
    if hasattr(reading, "get"):
        return not es_lectura_objetivo(
            ph=reading.get("ph"),
            conductividad_electrica=reading.get("conductividad_electrica"),
            nitrogeno=reading.get("nitrogeno"),
            fosforo=reading.get("fosforo"),
            potasio=reading.get("potasio"),
            pos_x=reading.get("pos_x"),
            pos_y=reading.get("pos_y"),
        )
    return not es_lectura_objetivo(
        ph=getattr(reading, "ph", None),
        conductividad_electrica=getattr(reading, "conductividad_electrica", None),
        nitrogeno=getattr(reading, "nitrogeno", None),
        fosforo=getattr(reading, "fosforo", None),
        potasio=getattr(reading, "potasio", None),
        pos_x=getattr(reading, "pos_x", None),
        pos_y=getattr(reading, "pos_y", None),
    )
