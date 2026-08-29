"""Alertas climáticas proactivas (pronóstico cruzado con fenología y labores).

El servicio programado (cada 6 h, tarea en el lifespan) consulta el
pronóstico de 7 días para cada finca activa con coordenadas y cruza:

  1. Lluvia > 20 mm/24h + labores de Fertilización programadas
     → «Aplace la aplicación…, riesgo de lixiviación».
  2. Temperatura mínima < 5 °C + etapa Floración (Café/frutales)
     → «Riesgo de helada, active sistema de riego por aspersión».

Las alertas se persisten en `alertas_climaticas` (solo las activas se
muestran en el Dashboard y el pronóstico va al reporte, sección N).
"""

import uuid
from datetime import datetime, timedelta, timezone

from agroia.logging import get_logger
from sqlalchemy import select

from agroia_backend.models.alerta_climatica import AlertaClimatica
from agroia_backend.models.finca import Finca
from agroia_backend.models.labor import Labor

logger = get_logger(__name__)

UMBRAL_LLUVIA_MM = 20.0
UMBRAL_HELADA_C = 5.0
CULTIVOS_SENSIBLES_HELADA = {
    "café", "aguacate", "cacao", "limón", "naranja", "mandarina", "mango",
    "papaya", "uva", "mora", "lulo", "frutales",
}


async def _labores_fertilizacion_proximas(db, finca_uuid, dias_ventana: int = 3):
    """Labores de Fertilización pendientes programadas dentro de la ventana."""
    hoy = datetime.now(timezone.utc).date()
    from agroia_backend.models.lote import Lote

    lotes = (
        await db.execute(select(Lote.id).where(Lote.finca_id == finca_uuid))
    ).scalars().all()
    if not lotes:
        return []
    labores = (
        await db.execute(
            select(Labor)
            .where(
                Labor.lote_id.in_(lotes),
                Labor.tipo == "Fertilización",
                Labor.estado.in_(["Pendiente", "En Progreso"]),
                Labor.fecha_programada.is_not(None),
            )
        )
    ).scalars().all()
    return [
        labor for labor in labores
        if labor.fecha_programada and labor.fecha_programada <= hoy + timedelta(days=dias_ventana)
    ]


def _dia_lluvia_fuerte(pronostico: list[dict], dias: int = 3) -> dict | None:
    for d in pronostico[:dias]:
        if float(d.get("precipitacion_mm") or 0) > UMBRAL_LLUVIA_MM:
            return d
    return None


def _dia_helada(pronostico: list[dict], dias: int = 3) -> dict | None:
    for d in pronostico[:dias]:
        if float(d.get("temp_min_c") or 99) < UMBRAL_HELADA_C:
            return d
    return None


async def _usuarios_permiten_siembra_lunar(db, finca_uuid) -> bool:
    """True si ningún usuario vinculado a la finca desactivó las alertas Bristol.

    Sin preferencias registradas → se permite (default activado).
    """
    from agroia_backend.models.finca_usuario import FincaUsuario
    from agroia_backend.models.preferencia_bristol import PreferenciaBristol

    vinculados = (
        await db.execute(
            select(FincaUsuario.usuario_id).where(FincaUsuario.finca_id == finca_uuid)
        )
    ).scalars().all()
    if not vinculados:
        return True
    prefs = (
        await db.execute(
            select(PreferenciaBristol).where(
                PreferenciaBristol.usuario_id.in_(list(vinculados))
            )
        )
    ).scalars().all()
    if not prefs:
        return True
    return any(p.generar_alertas_siembra for p in prefs)


async def _evaluar_siembra_bristol(
    db, finca: Finca, pronostico: list[dict], _registrar, _desactivar_tipo
) -> None:
    """Regla 3 (v3.4): alerta 'siembra_lunar' cuando fase + clima favorecen.

    Fase favorable (Bristol) + pronóstico 7 días sin lluvias > 20 mm ni
    heladas < 5 °C → alerta. Si ya existe una activa del tipo para la
    finca se desactiva (no se duplica).
    """
    from agroia_backend.services.calendario_lunar import (
        BRISTOL_ACTIVADO,
        clima_favorable_siembra,
        resumen_bristol,
    )

    if not BRISTOL_ACTIVADO:
        return

    hoy = datetime.now(timezone.utc).date()
    try:
        lunar = resumen_bristol(hoy, float(finca.latitud), float(finca.longitud))
    except Exception as exc:  # noqa: BLE001 — nunca tumbar el lote
        logger.error("bristol_evaluacion_fallo", error=str(exc))
        return

    recomendacion = lunar["recomendacion_bristol"]
    if not recomendacion["favorable"] or not clima_favorable_siembra(pronostico):
        await _desactivar_tipo("siembra_lunar")
        return

    if not await _usuarios_permiten_siembra_lunar(db, finca.id):
        await _desactivar_tipo("siembra_lunar")
        return

    cultivo = recomendacion["cultivos"][0] if recomendacion["cultivos"] else "su cultivo"
    fase = lunar["fase"]
    await _registrar(
        "siembra_lunar",
        "Media",
        f"📅 El Almanaque Bristol indica días propicios para siembra "
        f"({fase['nombre']} {fase['emoji']}). El clima (temp y lluvia) es "
        "favorable en los próximos días. Considere programar siembra de "
        f"{cultivo}.",
        {"fecha": hoy.isoformat(), "fase": fase["nombre_en"]},
    )


async def evaluar_alertas_finca(db, finca: Finca, pronostico: list[dict] | None = None) -> list[dict]:
    """Evalúa las reglas y persiste/desactiva alertas para una finca.

    Devuelve las alertas creadas (dict) para respuesta de API/logs.
    """
    if finca.latitud is None or finca.longitud is None:
        return []

    if pronostico is None:
        from agroia_backend.services.external_apis import fetch_pronostico_open_meteo

        pronostico = await fetch_pronostico_open_meteo(
            float(finca.latitud), float(finca.longitud), dias=7
        )
    if not pronostico:
        return []

    hoy = datetime.now(timezone.utc).date()
    creadas: list[dict] = []
    cambios = 0

    async def _desactivar_tipo(tipo: str) -> int:
        anteriores = (
            await db.execute(
                select(AlertaClimatica).where(
                    AlertaClimatica.finca_id == finca.id,
                    AlertaClimatica.tipo == tipo,
                    AlertaClimatica.activa.is_(True),
                )
            )
        ).scalars().all()
        for a in anteriores:
            a.activa = False
        return len(anteriores)

    async def _registrar(tipo: str, severidad: str, mensaje: str, dia: dict) -> None:
        nonlocal cambios
        cambios += await _desactivar_tipo(tipo)
        alerta = AlertaClimatica(
            id=uuid.uuid4(),
            finca_id=finca.id,
            tipo=tipo,
            severidad=severidad,
            mensaje=mensaje,
            fecha_alerta=hoy,
            pronostico={"dia": dia, "pronostico": pronostico[:3]},
            activa=True,
        )
        db.add(alerta)
        await db.flush()
        creadas.append({
            "finca_id": str(finca.id),
            "tipo": tipo,
            "severidad": severidad,
            "mensaje": mensaje,
        })

    # ── Regla 1: lluvia fuerte + fertilización programada ──
    dia_lluvia = _dia_lluvia_fuerte(pronostico)
    labores = await _labores_fertilizacion_proximas(db, finca.id) if dia_lluvia else []
    if dia_lluvia and labores:
        productos = " y ".join(
            labor.producto or labor.titulo[:60] for labor in labores[:2]
        )
        await _registrar(
            "lluvia_aplicacion",
            "Alta",
            f"Aplace la aplicación de {productos}: se pronostican "
            f"{float(dia_lluvia['precipitacion_mm']):.0f} mm en 24h "
            f"({dia_lluvia['fecha']}), riesgo de lixiviación.",
            dia_lluvia,
        )
    else:
        # Sin riesgo: desactivar alertas previas de este tipo (ya no vigentes)
        cambios += await _desactivar_tipo("lluvia_aplicacion")

    # ── Regla 2: helada + etapa de Floración en cultivos sensibles ──
    dia_helada = _dia_helada(pronostico)
    etapa = (finca.etapa_fenologica or "").strip().lower()
    cultivo = (finca.cultivo_sembrado or "").strip().lower()
    if dia_helada and etapa == "floración" and cultivo in CULTIVOS_SENSIBLES_HELADA:
        await _registrar(
            "helada_floracion",
            "Alta",
            f"Riesgo de helada: temperatura mínima de "
            f"{float(dia_helada['temp_min_c']):.1f} °C el {dia_helada['fecha']} "
            "durante la floración. Active el sistema de riego por aspersión.",
            dia_helada,
        )
    else:
        cambios += await _desactivar_tipo("helada_floracion")

    # ── Regla 3: siembra según Almanaque Bristol (fase lunar + clima) ──
    await _evaluar_siembra_bristol(db, finca, pronostico, _registrar, _desactivar_tipo)

    if creadas or cambios:
        await db.commit()
        logger.info(
            "alertas_climaticas_evaluadas",
            finca_id=str(finca.id), alertas=len(creadas), desactivadas=cambios,
        )
    return creadas


async def evaluar_todas_fincas(db) -> dict:
    """Evalúa todas las fincas con coordenadas (para el servicio programado)."""
    fincas = (
        await db.execute(
            select(Finca)
            .where(Finca.latitud.is_not(None), Finca.longitud.is_not(None))
            .limit(200)
        )
    ).scalars().all()
    total = 0
    for finca in fincas:
        try:
            total += len(await evaluar_alertas_finca(db, finca))
        except Exception as e:  # noqa: BLE001
            logger.error("alerta_finca_error", finca_id=str(finca.id), error=str(e))
            await db.rollback()
    logger.info("alertas_climaticas_batch", fincas=len(fincas), alertas=total)
    return {"fincas_evaluadas": len(fincas), "alertas_creadas": total}
