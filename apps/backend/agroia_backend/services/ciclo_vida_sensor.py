"""Ciclo de vida del sensor (Épica E8: HU-14, TT-12, TT-13).

- TT-12: contrastes periódicos sensor–laboratorio y detección de deriva
  (alerta cuando el sesgo supera la meta).
- TT-13: telemetría de salud (voltaje de alimentación, errores CRC, tiempo
  sin reportar).
- HU-14: plan de mantenimiento (limpieza, revisión, reemplazo) por dispositivo.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

# Intervalo por defecto entre mantenimientos (días). Parametrizable.
INTERVALO_MANTENIMIENTO_DIAS = 180

# Tipos de mantenimiento aceptados (HU-14).
TIPOS_MANTENIMIENTO = ("limpieza", "revision", "reemplazo")


def detectar_deriva(sesgo: float | None, meta: float | None) -> dict:
    """TT-12: alerta de deriva cuando |sesgo| supera la meta."""
    if sesgo is None or meta is None:
        return {"deriva": False, "sesgo": sesgo, "meta": meta, "motivo": None}
    supera = abs(sesgo) > meta
    return {
        "deriva": supera,
        "sesgo": sesgo,
        "meta": meta,
        "motivo": "sesgo_supera_meta" if supera else None,
    }


def telemetria_salud(
    *,
    voltaje_alimentacion: float | None,
    errores_crc: int | None,
    ultima_transmision: datetime | str | None,
    voltaje_minimo: float = 10.5,
    voltaje_maximo: float = 14.5,
    ahora: datetime | None = None,
) -> dict:
    """TT-13: estado de salud desde la telemetría del dispositivo."""
    ahora = ahora or datetime.now(timezone.utc)
    if isinstance(ultima_transmision, str):
        try:
            ultima_transmision = datetime.fromisoformat(
                ultima_transmision.replace("Z", "+00:00")
            )
        except ValueError:
            ultima_transmision = None

    horas_sin_reportar = None
    if ultima_transmision is not None:
        if ultima_transmision.tzinfo is None:
            ultima_transmision = ultima_transmision.replace(tzinfo=timezone.utc)
        horas_sin_reportar = max(
            0.0, (ahora - ultima_transmision).total_seconds() / 3600
        )

    voltaje_ok = (
        voltaje_alimentacion is None
        or voltaje_minimo <= voltaje_alimentacion <= voltaje_maximo
    )

    alertas = []
    if not voltaje_ok:
        alertas.append("voltaje_fuera_de_rango")
    if errores_crc is not None and errores_crc > 0:
        alertas.append("errores_crc")
    if horas_sin_reportar is not None and horas_sin_reportar > 24:
        alertas.append("tiempo_sin_reportar")

    return {
        "voltaje_alimentacion": voltaje_alimentacion,
        "voltaje_ok": voltaje_ok,
        "errores_crc": errores_crc,
        "horas_sin_reportar": (
            round(horas_sin_reportar, 1) if horas_sin_reportar is not None else None
        ),
        "alertas": alertas,
        "estado": "alerta" if alertas else "ok",
    }


def proximo_mantenimiento(
    ultimo_mantenimiento: date | None,
    intervalo_dias: int = INTERVALO_MANTENIMIENTO_DIAS,
    hoy: date | None = None,
) -> dict:
    """HU-14: próximo mantenimiento programado y si está vencido."""
    hoy = hoy or date.today()
    if ultimo_mantenimiento is None:
        return {"proximo_mantenimiento": None, "vencido": False}
    proximo = ultimo_mantenimiento + timedelta(days=intervalo_dias)
    return {
        "proximo_mantenimiento": proximo.isoformat(),
        "vencido": proximo < hoy,
    }
