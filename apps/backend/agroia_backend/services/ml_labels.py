"""Etiquetas doradas (Ground Truth) para aprendizaje activo del ML.

Fuentes de verdad humana:
  1. `aceptaciones_recomendacion` — diagnósticos por variable validados
     por un Admin/Agrónomo (resumen.recomendaciones[] con variable/estado).
  2. `historial_ciclos_lote` — ciclos cerrados con rendimiento real,
     comparado contra el rendimiento esperado de la ficha técnica para
     derivar una etiqueta de aptitud verificada en campo.

Estas etiquetas alimentan `train_colombia.py --active-learning` y el
tablero de transparencia `GET /api/v1/ml/etiquetas-doradas`.
"""

from datetime import datetime

from agroia.logging import get_logger
from sqlalchemy import select

logger = get_logger(__name__)

# Display (reglas/UI) → columna canónica del sensor
MAPA_VARIABLE = {
    "ph": "ph", "n": "nitrogeno", "p": "fosforo", "k": "potasio",
    "ca": "calcio", "mg": "magnesio", "s": "azufre", "fe": "hierro",
    "mn": "manganeso", "zn": "zinc", "cu": "cobre", "b": "boro",
    "mo": "materia_organica", "cic": "cic", "humedad": "humedad",
    "temperatura_suelo": "temperatura_suelo", "ce": "conductividad_electrica",
}
MAPA_DISPLAY = {v: k for k, v in MAPA_VARIABLE.items()}
VARIABLES_CANONICAS = list(dict.fromkeys(MAPA_VARIABLE.values()))

ESTADOS_VALIDOS = {"DEFICIT", "OK", "EXCESO"}


def _features_desde_lectura(lectura) -> dict:
    """Extrae el perfil de suelo canónico desde una lectura de sensor."""
    features: dict[str, float] = {}
    for var in VARIABLES_CANONICAS:
        v = getattr(lectura, var, None)
        if v is not None:
            features[var] = float(v)
    return features


def _estados_desde_resumen(resumen: dict | None) -> dict[str, str]:
    """Convierte resumen.recomendaciones[] en {variable_canonica: estado}."""
    etiquetas: dict[str, str] = {}
    if not isinstance(resumen, dict):
        return etiquetas
    for fila in resumen.get("recomendaciones") or []:
        if not isinstance(fila, dict):
            continue
        var = str(fila.get("variable") or "").strip().lower()
        estado = str(fila.get("estado") or "").strip().upper()
        clave = MAPA_VARIABLE.get(var)
        if clave is None or estado not in ESTADOS_VALIDOS:
            continue
        etiquetas[clave] = estado
    return etiquetas


async def _ultima_lectura_finca(db, finca_id, hasta: datetime | None = None) -> object | None:
    from agroia_backend.models.sensor_reading import SensorReading

    stmt = select(SensorReading).where(SensorReading.finca_id == finca_id)
    if hasta is not None:
        stmt = stmt.where(SensorReading.ts <= hasta)
    stmt = stmt.order_by(SensorReading.ts.desc()).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none()


async def etiquetas_aceptaciones(db) -> list[dict]:
    """Aceptaciones humanas como etiquetas por variable (con perfil de suelo)."""
    from agroia_backend.models.aceptacion_recomendacion import AceptacionRecomendacion

    aceptaciones = (
        await db.execute(
            select(AceptacionRecomendacion).order_by(AceptacionRecomendacion.created_at)
        )
    ).scalars().all()
    filas: list[dict] = []
    for a in aceptaciones:
        etiquetas = _estados_desde_resumen(a.resumen)
        if not etiquetas:
            continue
        lectura = await _ultima_lectura_finca(db, a.finca_id, hasta=a.created_at)
        if lectura is None:
            continue
        features = _features_desde_lectura(lectura)
        if not features:
            continue
        # Solo etiquetas cuya variable está presente en el perfil
        etiquetas_validas = {v: e for v, e in etiquetas.items() if v in features}
        if not etiquetas_validas:
            continue
        filas.append({
            "origen": "aceptacion",
            "finca_id": str(a.finca_id),
            "cultivo_id": str(a.cultivo_id) if a.cultivo_id else None,
            "rol": a.rol,
            "features": features,
            "etiquetas": etiquetas_validas,
            "created_at": a.created_at,
        })
    return filas


def _aptitud_desde_rendimiento(rendimiento: float, esperado: float) -> str:
    ratio = rendimiento / esperado if esperado and esperado > 0 else 0.0
    if ratio >= 0.95:
        return "Apta"
    if ratio >= 0.75:
        return "Moderadamente apta"
    if ratio >= 0.5:
        return "Marginalmente apta"
    return "No apta"


async def rendimiento_esperado_cultivo(db, cultivo_id) -> float | None:
    """Rendimiento esperado (t/ha) de la ficha técnica del cultivo."""
    from agroia_backend.models.cultivo import FichaTecnica

    fichas = (
        await db.execute(
            select(FichaTecnica)
            .where(FichaTecnica.cultivo_id == cultivo_id)
            .order_by(FichaTecnica.created_at.desc())
            .limit(1)
        )
    ).scalars().all()
    for f in fichas:
        esperado = (f.datos_economicos or {}).get("rendimiento_esperado")
        if esperado is not None:
            try:
                return float(esperado)
            except (TypeError, ValueError):
                continue
    return None


def es_rendimiento_atipico(declarado_tn_ha: float, esperado_tn_ha: float) -> bool:
    """Outlier humano: rendimiento > 2× el esperado o < 0.3× el esperado."""
    return (
        declarado_tn_ha > esperado_tn_ha * 2.0
        or declarado_tn_ha < esperado_tn_ha * 0.3
    )


async def etiquetas_ciclos(db) -> list[dict]:
    """Ciclos cerrados (rendimiento real) como etiquetas de aptitud."""
    from agroia_backend.models.ciclo_lote import CicloLote
    from agroia_backend.models.lote import Lote

    ciclos = (
        await db.execute(
            select(CicloLote).where(CicloLote.rendimiento_tn_ha.is_not(None))
        )
    ).scalars().all()
    lotes_ids = [c.lote_id for c in ciclos]
    lotes: dict = {}
    if lotes_ids:
        lotes = {
            lote.id: lote
            for lote in (
                await db.execute(select(Lote).where(Lote.id.in_(lotes_ids)))
            ).scalars().all()
        }
    filas: list[dict] = []
    for c in ciclos:
        # ── Protección anti-envenenamiento: los rendimientos atípicos ──
        #    (outliers humanos marcados al cosechar) NO son Ground Truth. ──
        if c.rendimiento_atipico:
            logger.info(
                "ciclo_atipico_excluido_ground_truth",
                ciclo_id=str(c.id), rendimiento=float(c.rendimiento_tn_ha),
            )
            continue
        lote = lotes.get(c.lote_id)
        if lote is None:
            continue
        esperado = await rendimiento_esperado_cultivo(db, c.cultivo_id)
        if esperado is None:
            continue
        rendimiento = float(c.rendimiento_tn_ha)
        # Defensa en profundidad: recalcular la regla aunque falte la marca
        if es_rendimiento_atipico(rendimiento, esperado):
            continue
        lectura = await _ultima_lectura_finca(db, lote.finca_id)
        if lectura is None:
            continue
        features = _features_desde_lectura(lectura)
        if not features:
            continue
        filas.append({
            "origen": "ciclo",
            "finca_id": str(lote.finca_id),
            "cultivo_id": str(c.cultivo_id),
            "features": features,
            "etiqueta_aptitud": _aptitud_desde_rendimiento(rendimiento, esperado),
            "rendimiento_tn_ha": rendimiento,
            "rendimiento_esperado": esperado,
            "fecha_cosecha": c.fecha_cosecha,
        })
    return filas


async def resumen_etiquetas_doradas(db) -> dict:
    """Resumen de disponibilidad de Ground Truth (para API/CLI)."""
    aceptaciones = await etiquetas_aceptaciones(db)
    ciclos = await etiquetas_ciclos(db)
    cobertura: dict[str, int] = {}
    for fila in aceptaciones:
        for var in fila["etiquetas"]:
            cobertura[var] = cobertura.get(var, 0) + 1
    return {
        "aceptaciones_utiles": len(aceptaciones),
        "ciclos_cerrados_utiles": len(ciclos),
        "total_etiquetas_variable": sum(cobertura.values()),
        "cobertura_por_variable": cobertura,
        "umbral_promocion_precision": 0.85,
        "min_muestras_promocion": 5,
    }


async def cargar_etiquetas_doradas(db) -> tuple[list[dict], list[dict]]:
    """Carga las dos fuentes de Ground Truth para el pipeline de entrenamiento."""
    aceptaciones = await etiquetas_aceptaciones(db)
    ciclos = await etiquetas_ciclos(db)
    logger.info(
        "etiquetas_doradas_cargadas",
        aceptaciones=len(aceptaciones), ciclos=len(ciclos),
    )
    return aceptaciones, ciclos
