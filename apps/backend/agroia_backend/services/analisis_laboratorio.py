"""Servicio de análisis de laboratorio ICA: normalización, validación y prioridad.

- `normalizar_resultados`: mapea etiquetas comunes (pH, N, P, K, MO, CIC…)
  a variables canónicas del sistema y valida rangos físicos.
- `lab_reciente`: análisis con `fecha_resultado` dentro de la ventana (90 días).
"""

from datetime import date, timedelta

from agroia.logging import get_logger
from sqlalchemy import select

from agroia_backend.models.analisis_laboratorio import AnalisisLaboratorio
from agroia_backend.services.data_adapters import SOIL_RANGES

logger = get_logger(__name__)

VENTANA_LAB_DIAS = 90

# Etiquetas comunes de laboratorios → variable canónica del sistema
ALIASES = {
    "ph": "ph", "acidez": "ph",
    "n": "nitrogeno", "nitrogeno": "nitrogeno", "nitrogeno_total": "nitrogeno",
    "p": "fosforo", "fosforo": "fosforo", "fosforo_disponible": "fosforo",
    "k": "potasio", "potasio": "potasio", "potasio_intercambiable": "potasio",
    "ca": "calcio", "calcio": "calcio",
    "mg": "magnesio", "magnesio": "magnesio",
    "s": "azufre", "azufre": "azufre",
    "fe": "hierro", "hierro": "hierro",
    "mn": "manganeso", "manganeso": "manganeso",
    "zn": "zinc", "zinc": "zinc",
    "cu": "cobre", "cobre": "cobre",
    "b": "boro", "boro": "boro",
    "mo": "materia_organica", "materia_organica": "materia_organica",
    "materiaorganica": "materia_organica",
    "cic": "cic", "capacidad_intercambio": "cic",
    "ce": "conductividad_electrica", "conductividad_electrica": "conductividad_electrica",
    "textura": "textura", "clase_textural": "textura",
}


def _num(v) -> float | None:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def normalizar_resultados(raw: dict) -> tuple[dict, list[str]]:
    """Devuelve (resultados canónicos validados, claves rechazadas)."""
    resultados: dict = {}
    rechazadas: list[str] = []
    for clave, valor in (raw or {}).items():
        canonica = ALIASES.get(str(clave).strip().lower().replace(" ", "_"))
        if canonica is None:
            rechazadas.append(str(clave))
            continue
        if canonica == "textura":
            if isinstance(valor, str) and valor.strip():
                resultados[canonica] = valor.strip()
            else:
                rechazadas.append(str(clave))
            continue
        num = _num(valor)
        if num is None:
            rechazadas.append(str(clave))
            continue
        lo, hi = SOIL_RANGES.get(canonica, (None, None))
        if lo is not None and not (lo <= num <= hi):
            logger.warning(
                "lab_valor_fuera_rango", variable=canonica, valor=num,
                rango=f"[{lo}, {hi}]",
            )
            rechazadas.append(str(clave))
            continue
        resultados[canonica] = num
    return resultados, rechazadas


async def lab_reciente(db, finca_id, dias: int = VENTANA_LAB_DIAS) -> AnalisisLaboratorio | None:
    """Análisis más reciente con fecha_resultado dentro de la ventana."""
    import uuid as uuid_mod

    try:
        finca_uuid = uuid_mod.UUID(str(finca_id))
    except ValueError:
        return None
    limite = date.today() - timedelta(days=dias)
    return (
        await db.execute(
            select(AnalisisLaboratorio)
            .where(
                AnalisisLaboratorio.finca_id == finca_uuid,
                AnalisisLaboratorio.fecha_resultado >= limite,
            )
            .order_by(AnalisisLaboratorio.fecha_resultado.desc())
            .limit(1)
        )
    ).scalars().first()
