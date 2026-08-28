"""Servicio de balance hídrico (ETo/Kc) — necesidad real de riego (1.C).

ETo desde Open-Meteo (FAO-56 Penman-Monteith) × Kc del cultivo por etapa.
"""

import asyncio

from agroia.logging import get_logger
from sqlalchemy import select

logger = get_logger(__name__)

# Kc genérico por categoría cuando el cultivo no tiene kc_* cargado
KC_GENERICO = {
    "frutal": 0.75,
    "cereal": 0.90,
    "hortaliza": 0.95,
    "tuberculo": 0.85,
    "leguminosa": 0.80,
    "cafe": 0.85,
    "generico": 0.80,
}

_PALABRAS_CATEGORIA = {
    "leguminosa": ("fríjol", "frijol", "arveja", "habichuela", "soya", "lenteja"),
    "cereal": ("maíz", "maiz", "arroz", "trigo", "cebada", "avena", "sorgo", "quinua"),
    "tuberculo": ("papa", "yuca", "ñame", "batata", "arracacha"),
    "hortaliza": ("tomate", "lechuga", "cebolla", "zanahoria", "repollo", "ahuyama", "lulo"),
    "frutal": ("aguacate", "cítrico", "mango", "banano", "plátano", "mora", "fresa",
               "guayaba", "granadilla", "curuba", "chontaduro", "coco"),
    "cafe": ("café", "cafe", "cacao"),
}


def _categoria_cultivo(nombre: str) -> str:
    n = (nombre or "").lower()
    for categoria, palabras in _PALABRAS_CATEGORIA.items():
        if any(p in n for p in palabras):
            return categoria
    return "generico"


def _kc_por_etapa(cultivo, etapa: str | None) -> tuple[float | None, bool]:
    """Devuelve (kc, generico). Usa kc_medio/kc_final según etapa; fallback categoría."""
    if cultivo is None:
        return KC_GENERICO["generico"], True
    if cultivo.kc_medio is not None:
        kc = float(cultivo.kc_medio)
        etapa_n = (etapa or "").lower()
        if etapa_n and "cosecha" in etapa_n and cultivo.kc_final is not None:
            kc = float(cultivo.kc_final)
        elif etapa_n and "veget" in etapa_n and cultivo.kc_inicial is not None:
            kc = float(cultivo.kc_inicial)
        return kc, False
    return KC_GENERICO.get(_categoria_cultivo(cultivo.nombre), KC_GENERICO["generico"]), True


def _fetch_et0(lat: float, lng: float, dias: int = 7) -> dict | None:
    """ETo + precipitación diaria desde Open-Meteo (sin API key)."""
    import json
    import urllib.parse
    import urllib.request

    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lng,
        "daily": "et0_fao_evapotranspiration,precipitation_sum",
        "timezone": "America/Bogota",
        "forecast_days": dias,
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgroIA/0.1"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        daily = data.get("daily") or {}
        return daily
    except Exception as e:  # noqa: BLE001 — degradación silenciosa
        logger.warning("et0_no_disponible", error=str(e))
        return None


async def calcular_balance_hidrico(db, finca, lote_id=None, dias=7) -> dict | None:
    """Calcula el balance hídrico de la finca. None si no hay coordenadas."""
    if finca.latitud is None or finca.longitud is None:
        return None

    from agroia_backend.models.cultivo import Cultivo

    cultivo = None
    if finca.cultivo_sembrado:
        cultivo = (
            await db.execute(
                select(Cultivo).where(Cultivo.nombre == finca.cultivo_sembrado).limit(1)
            )
        ).scalar_one_or_none()
    etapa = getattr(finca, "etapa_fenologica", None)
    etapa_txt = str(getattr(etapa, "value", etapa)) if etapa else None

    kc, generico = _kc_por_etapa(cultivo, etapa_txt)
    daily = await asyncio.to_thread(_fetch_et0, float(finca.latitud), float(finca.longitud), dias)
    if not daily:
        return None

    fechas = daily.get("time") or []
    et0 = daily.get("et0_fao_evapotranspiration") or []
    lluvia = daily.get("precipitation_sum") or []
    filas = []
    deficit_acumulado = 0.0
    for i, fecha in enumerate(fechas):
        e0 = float(et0[i]) if i < len(et0) and et0[i] is not None else 0.0
        pre = float(lluvia[i]) if i < len(lluvia) and lluvia[i] is not None else 0.0
        etc = round(e0 * kc, 2)
        deficit = round(max(0.0, etc - pre), 2)
        deficit_acumulado += deficit
        filas.append({
            "fecha": fecha,
            "et0_mm": round(e0, 2),
            "etc_mm": etc,
            "precipitacion_mm": round(pre, 1),
            "deficit_mm": deficit,
        })

    if deficit_acumulado <= 0:
        recomendacion = "La lluvia pronosticada cubre la demanda hídrica del cultivo esta semana."
    elif deficit_acumulado < 10:
        recomendacion = f"Riego suplementario de ~{deficit_acumulado:.1f} mm en los próximos días; el resto de la semana la lluvia cubre la demanda."
    else:
        recomendacion = f"Su cultivo necesita ~{deficit_acumulado:.1f} mm esta semana por encima de la lluvia pronosticada. Programe riego fraccionado."

    return {
        "finca_id": str(finca.id),
        "cultivo": str(cultivo.nombre) if cultivo else (finca.cultivo_sembrado or None),
        "etapa_fenologica": etapa_txt,
        "kc_aplicado": kc,
        "kc_aplicado_generico": generico,
        "dias": filas,
        "deficit_acumulado_7d_mm": round(deficit_acumulado, 2),
        "recomendacion": recomendacion,
    }
