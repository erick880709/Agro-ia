"""Contexto agronómico de muestreo (Épica E5, RF-077) y guía de campo (RF-078).

RF-077: lecturas dentro de una ventana parametrizable posterior a
fertilización o riego se marcan `valida_con_advertencia` y no se usan para
clasificar fertilidad.

RF-078: guía de campo con réplicas mínimas, inserción vertical, profundidad
por cultivo, pozo >20 cm para instalación enterrada y horario recomendado.
"""

from __future__ import annotations

from datetime import date, datetime

# Ventana (días) posterior a fertilización/riego en la que la lectura se
# degrada a valida_con_advertencia. Parametrizable (RF-087).
VENTANA_CONTEXTO_DIAS = 3

# Mínimo de réplicas por punto (RF-078).
REPLICAS_MINIMAS_POR_PUNTO = 3

# Profundidad por cultivo (capa por defecto 0–20 cm; perennes 20–40 cm).
PROFUNDIDAD_POR_CULTIVO = {
    "cafe": 20,        # plato del árbol (Cenicafé)
    "cacao": 20,       # 0–20 cm
    "platano": 20,     # 0–20 y 20–40 cm
    "banano": 20,
    "frutales": 40,    # 20–60 cm
    "pastos": 15,
    "arroz": 20,
    "default": 20,
}


def _a_fecha(valor) -> date | None:
    if isinstance(valor, date):
        return valor
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor[:10])
        except ValueError:
            return None
    return None


def dentro_ventana_contexto(
    ts: datetime | None,
    fecha_ultima_fertilizacion=None,
    fecha_ultimo_riego=None,
    ventana_dias: int = VENTANA_CONTEXTO_DIAS,
) -> bool:
    """True si la lectura está dentro de la ventana post-fertilización/riego."""
    if ts is None:
        return False
    fecha_ts = ts.date() if isinstance(ts, datetime) else ts
    for fecha in (fecha_ultima_fertilizacion, fecha_ultimo_riego):
        f = _a_fecha(fecha)
        if f is None:
            continue
        dias = (fecha_ts - f).days
        if 0 <= dias <= ventana_dias:
            return True
    return False


def aplicar_contexto(
    *,
    estado: str | None,
    motivos: list[str],
    ts: datetime | None,
    fecha_ultima_fertilizacion=None,
    fecha_ultimo_riego=None,
    ventana_dias: int = VENTANA_CONTEXTO_DIAS,
) -> tuple[str, list[str]]:
    """Degrada una lectura a `valida_con_advertencia` si hay contexto reciente.

    No se usa para clasificar fertilidad (RF-077). Devuelve (estado, motivos).
    """
    if estado in (None, "valida") and dentro_ventana_contexto(
        ts, fecha_ultima_fertilizacion, fecha_ultimo_riego, ventana_dias
    ):
        estado = "valida_con_advertencia"
        if "contexto_reciente" not in motivos:
            motivos = list(motivos) + ["contexto_reciente"]
    return estado, motivos


def profundidad_por_cultivo(cultivo: str | None) -> int:
    """Profundidad de lectura recomendada (cm) para un cultivo."""
    clave = (cultivo or "default").strip().lower()
    return PROFUNDIDAD_POR_CULTIVO.get(clave, PROFUNDIDAD_POR_CULTIVO["default"])


def guia_campo(cultivo: str | None = None) -> dict:
    """Guía de campo (RF-078): réplicas, inserción, profundidad, instalación."""
    return {
        "replicas_minimas_por_punto": REPLICAS_MINIMAS_POR_PUNTO,
        "profundidad_recomendada_cm": profundidad_por_cultivo(cultivo),
        "cultivo": cultivo or "default",
        "insercion": "Vertical, sin balanceo, retirando la capa superficial hasta la profundidad de lectura.",
        "evitar": "Evitar piedras y contacto con raíces gruesas.",
        "instalacion_enterrada": "Pozo de más de 20 cm de diámetro; no energizar el sensor al aire.",
        "horario_recomendado": "Evitar sol directo sobre la sonda (temperatura > 45 °C).",
        "humedad_minima": "Suelo húmedo (VWC ≥ 15 %) para lecturas de pH/CE/NPK confiables.",
    }
