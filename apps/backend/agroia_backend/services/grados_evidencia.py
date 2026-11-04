"""Grados de evidencia (Épica E6, RF-080/081/082/083).

Cada dato, clasificación y recomendación exhibe su grado:

- **A**: laboratorio vigente (< 90 días).
- **B**: sensor con calibración local vigente que cumple metas.
- **C**: sensor sin calibración local (indicativo).
- **D**: estimado SIG o modelo.

Reglas por grado (RF-081): la dosis de fertilización y la clasificación
definitiva solo proceden con A (o B en variables que cumplen metas); con C
solo tendencias, alertas y priorización de muestreo. Se mantiene el principio
de dominio: sin análisis de suelo no hay dosis.

Cobertura explícita (RF-082): las variables que el sensor no mide se declaran
"no medidas" con su fuente (laboratorio, SIG o ninguna).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

GRADO_A = "A"
GRADO_B = "B"
GRADO_C = "C"
GRADO_D = "D"

# Variables que el sensor JXBS-3001-NPK-RS mide directamente.
VARIABLES_SENSOR = {
    "ph", "humedad", "temperatura_suelo", "conductividad_electrica",
    "nitrogeno", "fosforo", "potasio",
}

# Variables de fertilidad que el sensor NO mide (solo laboratorio/SIG/modelo).
VARIABLES_NO_MEDIDAS = {
    "materia_organica": "MO (Walkley-Black) — no la mide el sensor",
    "cic": "CIC — no la mide el sensor",
    "textura": "Textura — no la mide el sensor",
    "calcio": "Ca intercambiable — no lo mide el sensor",
    "magnesio": "Mg intercambiable — no lo mide el sensor",
    "azufre": "S — no lo mide el sensor",
    "aluminio": "Al intercambiable — no lo mide el sensor",
    "hierro": "Fe — no lo mide el sensor",
    "manganeso": "Mn — no lo mide el sensor",
    "zinc": "Zn — no lo mide el sensor",
    "cobre": "Cu — no lo mide el sensor",
    "boro": "B — no lo mide el sensor",
}

# Fuentes canónicas para la cobertura explícita.
FUENTE_LABORATORIO = "laboratorio"
FUENTE_SIG = "SIG (IGAC/UPRA)"
FUENTE_NINGUNA = "ninguna"


def _antiguedad_dias(fecha: date | datetime | str | None) -> float | None:
    if fecha is None:
        return None
    hoy = datetime.now(timezone.utc).date()
    if isinstance(fecha, datetime):
        d = fecha.date()
    elif isinstance(fecha, date):
        d = fecha
    else:
        try:
            d = date.fromisoformat(str(fecha)[:10])
        except ValueError:
            return None
    return (hoy - d).days


def laboratorio_vigente(fecha_resultado) -> bool:
    """True si el resultado de laboratorio es vigente (< 90 días)."""
    dias = _antiguedad_dias(fecha_resultado)
    return dias is not None and 0 <= dias < 90


def grado_laboratorio(fecha_resultado) -> str | None:
    """Grado A si el laboratorio es vigente; None si no aplica."""
    return GRADO_A if laboratorio_vigente(fecha_resultado) else None


def grado_sensor(calibrada: bool, cumple_metas: bool = False) -> str:
    """Grado B (calibrada que cumple metas) o C (sin calibración, indicativa)."""
    return GRADO_B if (calibrada and cumple_metas) else GRADO_C


def puede_dosificar(*grados: str | None) -> bool:
    """RF-081: dosis solo con A o B. C y D no autorizan dosis ni clasificación definitiva."""
    return all(g in (GRADO_A, GRADO_B) for g in grados if g is not None)


def puede_clasificar_definitivamente(*grados: str | None) -> bool:
    """Clasificación definitiva solo con A (o B en variables que cumplen metas)."""
    return puede_dosificar(*grados)


def grados_por_variable(
    *,
    soil_vars: set[str],
    lab_variables: set[str] | None = None,
    estimaciones_sig: list[str] | None = None,
    npk_calibrado: bool = False,
    npk_cumple_metas: bool = False,
) -> dict[str, dict]:
    """Asigna grado (A/B/C/D) a cada variable presente en el análisis.

    - Laboratorio vigente que cubre la variable → A.
    - Variable medida por el sensor → B (si calibrada y cumple metas) o C.
    - Variable de SIG → D.
    """
    lab_variables = lab_variables or set()
    estimaciones_sig = estimaciones_sig or []
    grados: dict[str, dict] = {}

    for var in soil_vars:
        if var in lab_variables:
            grados[var] = {"grado": GRADO_A, "fuente": FUENTE_LABORATORIO}
        elif var in estimaciones_sig:
            grados[var] = {"grado": GRADO_D, "fuente": FUENTE_SIG}
        elif var in VARIABLES_SENSOR:
            grados[var] = {
                "grado": grado_sensor(npk_calibrado, npk_cumple_metas),
                "fuente": "sensor",
            }
        else:
            grados[var] = {"grado": GRADO_D, "fuente": "modelo"}
    return grados


def cobertura_variables(
    *,
    soil_vars: set[str],
    lab_variables: set[str] | None = None,
    estimaciones_sig: list[str] | None = None,
) -> dict:
    """Cobertura explícita (RF-082): variables que el sensor NO mide, con su fuente.

    El sensor cubre 7 de 18 variables. Para las que no mide (MO, CIC, textura,
    Ca, Mg, Al, S y micros) se indica de dónde viene el dato: laboratorio, SIG
    o ninguna. Si el sensor llegara a medirlas, no se listan como "no medidas".
    """
    lab_variables = lab_variables or set()
    estimaciones_sig = set(estimaciones_sig or [])

    no_medidas = []
    for var, desc in VARIABLES_NO_MEDIDAS.items():
        if var in soil_vars:  # el sensor la midió: ya no es "no medida"
            continue
        if var in lab_variables:
            fuente = FUENTE_LABORATORIO
        elif var in estimaciones_sig:
            fuente = FUENTE_SIG
        else:
            fuente = FUENTE_NINGUNA
        no_medidas.append({"variable": var, "descripcion": desc, "fuente": fuente})

    return {
        "variables_no_medidas": no_medidas,
        "total_no_medidas": len(no_medidas),
    }


def recomendar_muestreo(*, grados: dict[str, dict], hay_frontera: bool = False) -> dict:
    """RF-083: sugiere muestreo de laboratorio ante anomalías o frontera."""
    a_muestrear = [
        var for var, info in grados.items()
        if info["grado"] in (GRADO_C, GRADO_D)
    ]
    return {
        "recomienda_muestreo": bool(a_muestrear or hay_frontera),
        "motivo": "frontera" if hay_frontera else ("variables_en_grado_C_o_D" if a_muestrear else None),
        "variables_prioritarias": a_muestrear[:6],
    }
