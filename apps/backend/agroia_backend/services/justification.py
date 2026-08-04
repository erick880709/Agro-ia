"""Servicio de justificación de recomendaciones.

Genera explicaciones en lenguaje natural (modo agricultor y modo técnico)
para cada recomendación del motor.
"""

from agroia.logging import get_logger

logger = get_logger(__name__)


# ── Plantillas de justificación ──
TEMPLATES = {
    "fertilizacion": {
        "agricultor": (
            "Su suelo tiene {deficiencia} de {variable}. "
            "Se recomienda aplicar {accion}. "
            "Esto puede mejorar su cultivo en aproximadamente {impacto}."
        ),
        "tecnico": (
            "Deficiencia de {variable}: valor actual {valor_actual}, "
            "rango ideal [{umbral_min} - {umbral_max}]. "
            "Acción recomendada: {accion}. "
            "Fuente: {fuente}. "
            "Costo estimado: COP {costo_estimado}/ha."
        ),
    },
    "correccion_ph": {
        "agricultor": (
            "Su suelo está {condicion} (pH {valor_actual}). "
            "Se recomienda {accion} para ajustarlo al rango ideal de {umbral_min} a {umbral_max}. "
            "Impacto esperado: {impacto}."
        ),
        "tecnico": (
            "pH del suelo: {valor_actual} ({condicion}). "
            "Rango ideal para {cultivo}: [{umbral_min} - {umbral_max}]. "
            "Acción: {accion}. Fuente: {fuente}. "
            "Costo estimado: COP {costo_estimado}/ha."
        ),
    },
    "cultivo_ideal": {
        "agricultor": (
            "Basado en las condiciones de su suelo, el cultivo más recomendable es {cultivo} "
            "(confianza: {confianza}%). {justificacion_breve}"
        ),
        "tecnico": (
            "Cultivo recomendado: {cultivo} (score: {score:.2f}, confianza: {confianza:.0%}). "
            "Variables determinantes: {variables_clave}. "
            "Rendimiento estimado: {rendimiento_est} ton/ha."
        ),
    },
    "insufficient_data": {
        "agricultor": (
            "No hay datos suficientes para generar una recomendación completa. "
            "Hacen falta las siguientes mediciones de su suelo: {variables_faltantes}. "
            "Por favor, verifique que los sensores estén funcionando correctamente."
        ),
        "tecnico": (
            "Datos insuficientes. Variables bloqueantes faltantes: {variables_faltantes}. "
            "Sensor offline o datos no recibidos en las últimas 24 horas."
        ),
    },
}


def generate_justification(
    template_key: str,
    mode: str = "agricultor",
    **kwargs,
) -> str:
    """Genera una justificación en lenguaje natural.

    Args:
        template_key: Clave de la plantilla ('fertilizacion', 'correccion_ph', 'cultivo_ideal', 'insufficient_data')
        mode: 'agricultor' (lenguaje coloquial) o 'tecnico' (técnico con fuentes)
        **kwargs: Variables para interpolar en la plantilla

    Returns:
        Texto de justificación en español
    """
    template = TEMPLATES.get(template_key, {}).get(mode)
    if not template:
        logger.warning("unknown_justification_template", key=template_key, mode=mode)
        return "Recomendación generada por el sistema AgroIA."

    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.error("justification_template_missing_key", key=str(e), template=template_key)
        return "Error al generar la justificación. Contacte al administrador."


def translate_soil_condition(variable: str, value: float, umbral_min: float, umbral_max: float) -> str:
    """Traduce un valor técnico a lenguaje coloquial."""
    if variable == "ph":
        if value < umbral_min:
            return "demasiado ácido"
        elif value > umbral_max:
            return "demasiado alcalino"
        return "en rango ideal"
    elif variable in ("nitrogeno", "fosforo", "potasio"):
        if value < umbral_min:
            return "bajo en nutrientes"
        elif value > umbral_max:
            return "con exceso de nutrientes"
        return "bien nutrido"
    return "fuera del rango recomendado"


def estimate_cost(accion: str, area_ha: float = 1.0) -> float:
    """Estima el costo de una recomendación en COP/ha.

    Valores de referencia (2026, Colombia):
        - Cal dolomita: ~$120,000 COP/ton
        - Urea (46% N): ~$180,000 COP/ton
        - DAP (18-46-0): ~$220,000 COP/ton
        - KCl (60% K₂O): ~$160,000 COP/ton
    """
    cost_map = {
        "encalado": 120_000,
        "cal": 120_000,
        "dolomita": 120_000,
        "nitrógeno": 180_000,
        "urea": 180_000,
        "fósforo": 220_000,
        "dap": 220_000,
        "potasio": 160_000,
        "kcl": 160_000,
    }
    for key, unit_cost in cost_map.items():
        if key in accion.lower():
            return unit_cost * area_ha
    return 100_000 * area_ha  # default: $100,000 COP/ha
