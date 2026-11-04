"""Salud de sensores (Épica E7, HU-12 / E8).

Por dispositivo: última lectura, tasa de lecturas válidas, deriva frente a
laboratorio, calibración vigente y próximo mantenimiento.
"""

from __future__ import annotations

from datetime import date, timedelta


def calcular_salud(
    *,
    ultima_lectura: str | None,
    total_lecturas: int,
    lecturas_validas: int,
    sesgo_calibracion: float | None = None,
    meta_sesgo: float | None = None,
    vigencia_calibracion: date | None = None,
    ultimo_mantenimiento: date | None = None,
    intervalo_mantenimiento_dias: int = 180,
    hoy: date | None = None,
) -> dict:
    """Estado de salud agregado de un dispositivo (HU-12)."""
    hoy = hoy or date.today()

    tasa_valida = round(lecturas_validas / total_lecturas, 4) if total_lecturas else None

    deriva = None
    if sesgo_calibracion is not None and meta_sesgo is not None:
        deriva = {
            "sesgo": sesgo_calibracion,
            "meta": meta_sesgo,
            "supera_meta": abs(sesgo_calibracion) > meta_sesgo,
        }

    calibracion_vigente = (
        vigencia_calibracion is None or vigencia_calibracion >= hoy
    )

    proximo_mantenimiento = None
    mantenimiento_vencido = False
    if ultimo_mantenimiento is not None:
        proximo = ultimo_mantenimiento + timedelta(days=intervalo_mantenimiento_dias)
        proximo_mantenimiento = proximo.isoformat()
        mantenimiento_vencido = proximo < hoy

    # Estado agregado.
    if not total_lecturas:
        estado_salud = "sin_datos"
    elif deriva and deriva["supera_meta"]:
        estado_salud = "deriva"
    elif mantenimiento_vencido:
        estado_salud = "mantenimiento_vencido"
    elif not calibracion_vigente:
        estado_salud = "calibracion_vencida"
    elif tasa_valida is not None and tasa_valida < 0.8:
        estado_salud = "baja_calidad"
    else:
        estado_salud = "saludable"

    return {
        "ultima_lectura": ultima_lectura,
        "tasa_lecturas_validas": tasa_valida,
        "deriva": deriva,
        "calibracion_vigente": calibracion_vigente,
        "vigencia_calibracion": vigencia_calibracion.isoformat() if vigencia_calibracion else None,
        "ultimo_mantenimiento": ultimo_mantenimiento.isoformat() if ultimo_mantenimiento else None,
        "proximo_mantenimiento": proximo_mantenimiento,
        "estado_salud": estado_salud,
    }
