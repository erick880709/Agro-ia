"""Motor de calidad del dato del sensor (Épica E2, RFP-AGROIA-003).

Sustituye la regla binaria "válida/inválida" por un motor de **10 estados**
(RF-006) que clasifica cada lectura con una lista de motivos y la versión de
regla aplicada. El valor crudo se conserva siempre (principio 1 del RFP); lo
que cambia es la clasificación, no el dato.

Estados (RF-006):
  valida · valida_con_advertencia · bajo_limite_deteccion · saturada ·
  fuera_de_rango · sonda_fuera_de_suelo · humedad_insuficiente ·
  no_calibrada · estimado_sig · invalidada

Reglas (RF-007..RF-009, Anexo A):
  - Saturación simétrica: pH ≤3,0 o ≥9,0; CE ≥10 dS/m; N/P/K ≥1999 mg/kg.
  - 0 en CE o NPK = "bajo límite de detección" (se conserva, no es error).
  - Validez por humedad: VWC < 15 % → pH/CE/NPK "humedad_insuficiente".
  - Humedad ≈ 0 y CE ≈ 0 → "sonda_fuera_de_suelo".
  - Plausibilidad cruzada: temperatura >45 °C (sol directo), NPK alto con
    CE ≈ 0 → "valida_con_advertencia".
  - Coordenada por defecto del firmware → "invalidada".
"""

from __future__ import annotations

# ── Estados de calidad ──
CALIDAD_VALIDA = "valida"
CALIDAD_VALIDA_CON_ADVERTENCIA = "valida_con_advertencia"
CALIDAD_BAJO_LIMITE = "bajo_limite_deteccion"
CALIDAD_SATURADA = "saturada"
CALIDAD_FUERA_RANGO = "fuera_de_rango"
CALIDAD_SONDA_FUERA = "sonda_fuera_de_suelo"
CALIDAD_HUMEDAD_INSUFICIENTE = "humedad_insuficiente"
CALIDAD_NO_CALIBRADA = "no_calibrada"
CALIDAD_ESTIMADO_SIG = "estimado_sig"
CALIDAD_INVALIDADA = "invalidada"

ESTADOS_CALIDAD = (
    CALIDAD_VALIDA,
    CALIDAD_VALIDA_CON_ADVERTENCIA,
    CALIDAD_BAJO_LIMITE,
    CALIDAD_SATURADA,
    CALIDAD_FUERA_RANGO,
    CALIDAD_SONDA_FUERA,
    CALIDAD_HUMEDAD_INSUFICIENTE,
    CALIDAD_NO_CALIBRADA,
    CALIDAD_ESTIMADO_SIG,
    CALIDAD_INVALIDADA,
)

# Estados que NO alimentan análisis ni reportes (RF-010 / §9): cero lecturas
# invalidada/saturada/humedad_insuficiente en reportes. `bajo_limite_deteccion`
# y `no_calibrada` sí se conservan para análisis (indicativo / con incertidumbre).
CALIDADES_EXCLUIDAS_ANALISIS = (
    CALIDAD_ESTIMADO_SIG,
    CALIDAD_SATURADA,
    CALIDAD_FUERA_RANGO,
    CALIDAD_SONDA_FUERA,
    CALIDAD_HUMEDAD_INSUFICIENTE,
    CALIDAD_INVALIDADA,
)

# Severidad relativa: el estado final es el más severo entre los motivos.
_SEVERIDAD = {
    CALIDAD_VALIDA: 0,
    CALIDAD_VALIDA_CON_ADVERTENCIA: 1,
    CALIDAD_NO_CALIBRADA: 2,
    CALIDAD_BAJO_LIMITE: 3,
    CALIDAD_HUMEDAD_INSUFICIENTE: 4,
    CALIDAD_FUERA_RANGO: 5,
    CALIDAD_SATURADA: 6,
    CALIDAD_SONDA_FUERA: 7,
    CALIDAD_INVALIDADA: 8,
}

# Versión de la regla de calidad (parametrizable/versionada en RF-087).
VERSION_REGLA_CALIDAD = "2.0"

# ── Límites iniciales (Anexo A). Parametrizables; aquí los valores por defecto.
UMBRALES = {
    "ph_min": 3.0,               # ≤ 3,0 → saturada
    "ph_max": 9.0,               # ≥ 9,0 → saturada
    "ce_max_dsm": 10.0,          # ≥ 10 dS/m → saturada
    "npk_max_mgkg": 1999.0,      # ≥ 1999 mg/kg → saturada
    "humedad_minima_pct": 15.0,  # VWC por debajo → humedad_insuficiente
    "humedad_sonda_max_pct": 1.0,  # ≈ 0
    "ce_sonda_max_dsm": 0.01,    # ≈ 0 (10 µS/cm, resolución del sensor)
    "temp_min_c": -40.0,
    "temp_max_sensor_c": 80.0,   # rango físico del sensor
    "temp_sol_directo_c": 45.0,  # alerta por sol directo (RF-009)
}

# Coordenada por defecto del firmware (GPS 4.578333, -75.666944), fuera del
# predio: la lectura no es atribuible a la finca.
COORD_DEFECTO = (-1698.64, 6614.3)

# Variables NPK (clave → valor) para motivos legibles.
_NPK_VALORES = ("nitrogeno", "fosforo", "potasio")


def _a_flotante(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _marcar(estado: str, nuevo: str, motivos: list[str], motivo: str | None) -> str:
    """Actualiza el estado si el nuevo es más severo y acumula el motivo."""
    if _SEVERIDAD.get(nuevo, 0) > _SEVERIDAD.get(estado, 0):
        estado = nuevo
    if motivo and motivo not in motivos:
        motivos.append(motivo)
    return estado


def clasificar_lectura(
    *,
    ph=None,
    conductividad_electrica=None,
    nitrogeno=None,
    fosforo=None,
    potasio=None,
    humedad=None,
    temperatura_suelo=None,
    pos_x=None,
    pos_y=None,
    npk_calibrado: bool = False,
    fuente_sig: bool = False,
) -> tuple[str, list[str]]:
    """Clasifica una lectura de sensor y devuelve (estado, motivos).

    Todas las variables son opcionales; el motor evalúa solo las presentes.
    """
    motivos: list[str] = []
    estado = CALIDAD_VALIDA

    # Fuente SIG (no sensor): IGAC/UPRA precargado.
    if fuente_sig:
        return CALIDAD_ESTIMADO_SIG, ["origen_sig"]

    # Coordenada por defecto del firmware → lectura no atribuible al predio.
    px = _a_flotante(pos_x)
    py = _a_flotante(pos_y)
    if (
        px is not None and py is not None
        and round(px, 2) == COORD_DEFECTO[0] and round(py, 2) == COORD_DEFECTO[1]
    ):
        return CALIDAD_INVALIDADA, ["coordenada_defecto"]

    ph = _a_flotante(ph)
    ce = _a_flotante(conductividad_electrica)
    npk = {nombre: _a_flotante(v) for nombre, v in (
        ("nitrogeno", nitrogeno), ("fosforo", fosforo), ("potasio", potasio),
    )}
    hum = _a_flotante(humedad)
    temp = _a_flotante(temperatura_suelo)

    # Sonda fuera del suelo: humedad ≈ 0 y CE ≈ 0 (RF-008).
    if (
        hum is not None and ce is not None
        and hum <= UMBRALES["humedad_sonda_max_pct"]
        and ce <= UMBRALES["ce_sonda_max_dsm"]
    ):
        estado = _marcar(estado, CALIDAD_SONDA_FUERA, motivos, "sonda_fuera_de_suelo")
        return estado, motivos

    # Saturación simétrica (RF-007).
    if ph is not None and (ph <= UMBRALES["ph_min"] or ph >= UMBRALES["ph_max"]):
        estado = _marcar(estado, CALIDAD_SATURADA, motivos, "ph_saturado")
    if ce is not None and ce >= UMBRALES["ce_max_dsm"]:
        estado = _marcar(estado, CALIDAD_SATURADA, motivos, "ce_saturada")
    for nombre in _NPK_VALORES:
        if npk[nombre] is not None and npk[nombre] >= UMBRALES["npk_max_mgkg"]:
            estado = _marcar(estado, CALIDAD_SATURADA, motivos, f"{nombre}_saturado")

    # Fuera de rango físico.
    if temp is not None and (temp < UMBRALES["temp_min_c"] or temp > UMBRALES["temp_max_sensor_c"]):
        estado = _marcar(estado, CALIDAD_FUERA_RANGO, motivos, "temperatura_fuera_rango")
    if ce is not None and ce < 0:
        estado = _marcar(estado, CALIDAD_FUERA_RANGO, motivos, "ce_negativa")
    if ph is not None and (ph < 0 or ph > 14):
        estado = _marcar(estado, CALIDAD_FUERA_RANGO, motivos, "ph_fuera_rango")

    # Bajo límite de detección: 0 en CE o NPK se conserva (RF-007).
    if ce is not None and ce == 0:
        estado = _marcar(estado, CALIDAD_BAJO_LIMITE, motivos, "ce_bajo_limite")
    for nombre in _NPK_VALORES:
        if npk[nombre] is not None and npk[nombre] == 0:
            estado = _marcar(estado, CALIDAD_BAJO_LIMITE, motivos, f"{nombre}_bajo_limite")

    # Validez por humedad: pH/CE/NPK no son confiables con suelo seco (RF-008).
    if hum is not None and hum < UMBRALES["humedad_minima_pct"]:
        estado = _marcar(estado, CALIDAD_HUMEDAD_INSUFICIENTE, motivos, "humedad_insuficiente")

    # Plausibilidad cruzada (RF-009): advertencias, no invalidan.
    if temp is not None and temp > UMBRALES["temp_sol_directo_c"]:
        estado = _marcar(estado, CALIDAD_VALIDA_CON_ADVERTENCIA, motivos, "temperatura_sol_directo")
    if ce is not None and ce <= UMBRALES["ce_sonda_max_dsm"]:
        npk_alto = any(npk[nombre] is not None and npk[nombre] > 0 for nombre in _NPK_VALORES)
        if npk_alto:
            estado = _marcar(estado, CALIDAD_VALIDA_CON_ADVERTENCIA, motivos, "npk_alto_con_ce_baja")

    # NPK sin calibrar → indicativo (no_calibrada).
    if any(npk[nombre] is not None for nombre in _NPK_VALORES) and not npk_calibrado:
        estado = _marcar(estado, CALIDAD_NO_CALIBRADA, motivos, "npk_sin_calibrar")

    return estado, motivos


def es_lectura_valida_para_analisis(estado: str | None) -> bool:
    """True si la lectura debe alimentar análisis y reportes."""
    if estado is None:
        return True  # lecturas previas a la regla de calidad
    return estado not in CALIDADES_EXCLUIDAS_ANALISIS


def resumir_calidad(lecturas: list) -> dict:
    """Resumen de transparencia (HU-02): 'N de M válidas' + desglose por motivo.

    Acepta objetos SensorReading o dicts con `calidad` y `motivos_calidad`.
    """
    total = len(lecturas)
    validas = 0
    por_estado: dict[str, int] = {}
    por_motivo: dict[str, int] = {}
    excluidas: list[dict] = []

    for r in lecturas:
        estado = r.get("calidad") if isinstance(r, dict) else getattr(r, "calidad", None)
        motivos = r.get("motivos_calidad") if isinstance(r, dict) else getattr(r, "motivos_calidad", None)
        estado = estado or CALIDAD_VALIDA
        por_estado[estado] = por_estado.get(estado, 0) + 1
        if es_lectura_valida_para_analisis(estado):
            validas += 1
        else:
            excluidas.append({
                "id": str(r.get("id")) if isinstance(r, dict) else str(getattr(r, "id", "")),
                "estado": estado,
                "motivos": list(motivos) if motivos else [],
            })
        for m in (motivos or []):
            por_motivo[m] = por_motivo.get(m, 0) + 1

    return {
        "total": total,
        "validas": validas,
        "excluidas": total - validas,
        "por_estado": por_estado,
        "por_motivo": por_motivo,
        "detalle_excluidas": excluidas,
    }
