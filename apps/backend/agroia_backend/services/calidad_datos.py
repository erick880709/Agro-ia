"""Regla de calidad del sensor de suelo (JXBS-3001-NPK-RS, 7 en 1).

Define el **rango objetivo** de cada variable y decide si una lectura es válida
para análisis y reportes. Una lectura fuera de este rango (o con la coordenada
por defecto del firmware) se marca con `calidad = 'invalidada'` y se excluye del
motor de recomendación y de los reportes.

Rangos del fabricante:
    - pH: 3–9 (exactitud ±0,3). El límite superior 9,0 satura el sensor.
    - CE: 0–10.000 µS/cm → en dS/m: 0,01–10 (resolución 10 µS/cm).
    - N/P/K: 0–1.999 mg/kg (resolución 1 mg/kg; 0 = sin captura).

La coordenada (pos_x=-1698.64, pos_y=6614.3) es el valor por defecto del
firmware (GPS 4.578333, -75.666944), fuera del predio.
"""

COORD_DEFECTO = (-1698.64, 6614.3)

RANGO_PH = (3.0, 9.0)      # [3, 9): excluye la saturación en 9,0
RANGO_CE = (0.01, 10.0)    # dS/m (0–10.000 µS/cm)
RANGO_NPK = (1.0, 1999.0)  # mg/kg; 0 = sin captura

CALIDAD_INVALIDADA = "invalidada"


def _a_flotante(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


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
    """True si la lectura está dentro del rango objetivo del sensor."""
    px = _a_flotante(pos_x)
    py = _a_flotante(pos_y)
    if px is not None and py is not None:
        if round(px, 2) == COORD_DEFECTO[0] and round(py, 2) == COORD_DEFECTO[1]:
            return False

    ph = _a_flotante(ph)
    ce = _a_flotante(conductividad_electrica)
    n = _a_flotante(nitrogeno)
    p = _a_flotante(fosforo)
    k = _a_flotante(potasio)

    if ph is not None and not (RANGO_PH[0] <= ph < RANGO_PH[1]):
        return False
    if ce is not None and not (RANGO_CE[0] <= ce <= RANGO_CE[1]):
        return False
    for v in (n, p, k):
        if v is not None and not (RANGO_NPK[0] <= v <= RANGO_NPK[1]):
            return False
    return True


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
