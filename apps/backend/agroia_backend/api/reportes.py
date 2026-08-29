"""Generación de reportes de análisis de suelo (HTML + PDF vía navegador).

Tipos:
  - siembra:  recomendación de siembra (UC1).
  - cultivo:  recomendación para el cultivo sembrado (UC2).
  - completo: UC1 + UC2 en un solo documento.
"""

import uuid as uuid_mod
from dataclasses import asdict

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.cultivo import Cultivo, EstadoFicha, FichaTecnica
from agroia_backend.models.checklist_bpa import ChecklistBpa
from agroia_backend.models.dispositivo_iot import DispositivoIoT
from agroia_backend.models.finca import Finca
from agroia_backend.models.labor import Labor
from agroia_backend.models.lote import Lote
from agroia_backend.models.sensor_reading import SensorReading
from agroia_backend.services.acceso import verificar_acceso_finca
from agroia_backend.services.aptitud import AptitudService
from agroia_backend.services.ml_oracle import MLOracleService
from agroia_backend.services.data_adapters import SueloAdapter
from agroia_backend.services.economia import calcular_plan_economico
from agroia_backend.services.orchestrator import (
    RecommendationOrchestrator,
    RecommendationRequest,
)
from agroia_backend.services.reportes_html import generar_reporte_html
from agroia_backend.services.rules_engine import RulesEngine

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/reportes", tags=["reportes"])

_PALABRAS_FOSFORO = {"dap", "fosfato", "fosforo", "fósforo", "p2o5", "superfosfato", "roca fosfórica"}


def _dosis_fosforo_ciclo(aplicaciones: list | None) -> float | None:
    """Máxima dosis (kg/ha) de productos fosforados en las aplicaciones del ciclo."""
    max_dosis = None
    for a in aplicaciones or []:
        if not isinstance(a, dict):
            continue
        nombre = str(a.get("producto", "")).lower()
        if any(p in nombre for p in _PALABRAS_FOSFORO):
            try:
                dosis = float(a.get("dosis_kg_ha") or 0)
            except (TypeError, ValueError):
                continue
            max_dosis = dosis if max_dosis is None else max(max_dosis, dosis)
    return max_dosis


async def _historial_ciclos_reporte(db, finca_uuid) -> dict:
    """Últimos 3 ciclos de la finca + predicción de rendimiento + alerta de P."""
    from agroia_backend.models.ciclo_lote import CicloLote
    from agroia_backend.models.lote import Lote

    lote = (
        await db.execute(
            select(Lote)
            .where(Lote.finca_id == finca_uuid, Lote.activo.is_(True))
            .order_by(Lote.created_at)
            .limit(1)
        )
    ).scalars().first()
    if lote is None:
        return {"ciclos": [], "prediccion": None, "advertencia_acumulacion": None}

    ciclos = (
        await db.execute(
            select(CicloLote)
            .where(CicloLote.lote_id == lote.id)
            .order_by(CicloLote.fecha_siembra.desc(), CicloLote.created_at.desc())
            .limit(3)
        )
    ).scalars().all()

    nombres: dict[str, str] = {}
    for c in ciclos:
        key = str(c.cultivo_id)
        if key not in nombres:
            cultivo = (
                await db.execute(
                    select(Cultivo).where(Cultivo.id == c.cultivo_id)
                )
            ).scalar_one_or_none()
            nombres[key] = cultivo.nombre if cultivo is not None else str(c.cultivo_id)

    historial = [
        {
            "cultivo": nombres.get(str(c.cultivo_id)),
            "fecha_siembra": c.fecha_siembra.isoformat() if c.fecha_siembra else None,
            "fecha_cosecha": c.fecha_cosecha.isoformat() if c.fecha_cosecha else None,
            "rendimiento_tn_ha": float(c.rendimiento_tn_ha) if c.rendimiento_tn_ha is not None else None,
            "aplicaciones": [
                {"producto": a.get("producto"), "dosis_kg_ha": a.get("dosis_kg_ha")}
                for a in (c.aplicaciones or [])
                if isinstance(a, dict) and a.get("producto")
            ],
        }
        for c in ciclos
    ]

    # ── Predicción de rendimiento (histórico + planes) ──
    con_rend = [h["rendimiento_tn_ha"] for h in historial if h["rendimiento_tn_ha"]]
    prediccion = None
    if con_rend:
        promedio = sum(con_rend) / len(con_rend)
        prediccion = {
            "promedio": round(promedio, 2),
            "optimizado": round(promedio * 1.15, 2),
            "ideal": round(promedio * 1.25, 2),
        }

    # ── Advertencia de acumulación de fósforo (últimos 2 ciclos cosechados) ──
    advertencia_acumulacion = None
    dosis_ultimos = [
        _dosis_fosforo_ciclo(c.aplicaciones)
        for c in ciclos
        if c.fecha_cosecha is not None
    ][:2]
    dosis_ultimos = [d for d in dosis_ultimos if d is not None]
    if len(dosis_ultimos) >= 2 and all(d > 120 for d in dosis_ultimos):
        advertencia_acumulacion = (
            "Histórico de P alto (últimos 2 ciclos > 120 kg/ha). Reduzca la dosis "
            "de fósforo en el plan actual para evitar fijación y ahorrar costos."
        )

    return {
        "ciclos": historial,
        "prediccion": prediccion,
        "advertencia_acumulacion": advertencia_acumulacion,
    }


class ReporteRequest(BaseModel):
    finca_id: str = Field(..., description="UUID de la finca a reportar")
    tipo: str = Field("completo", pattern="^(siembra|cultivo|completo)$")
    cultivo_id: str | None = Field(None, description="UUID del cultivo sembrado (obligatorio en tipo 'cultivo')")
    modelo_pronostico: str = Field(
        "ambos", pattern="^(auto|ecmwf|ambos)$",
        description=(
            "Modelo del pronóstico: ambos (Open-Meteo + ECMWF IFS 0.25°, por defecto), "
            "auto (mejor disponible) o ecmwf (solo ECMWF IFS 0.25°)"
        ),
    )
    presupuesto_cop: float | None = Field(
        None, ge=0, description="Presupuesto de fertilización ($/ha) para el plan económico (opcional)"
    )
    rendimiento_actual_t_ha: float | None = Field(
        None, ge=0, description="Rendimiento actual declarado (t/ha) para el ROI realista (opcional)"
    )


class SimularRequest(BaseModel):
    finca_id: str = Field(..., description="UUID de la finca")
    cultivo_id: str | None = Field(None, description="UUID del cultivo (opcional)")
    soil_modificado: dict = Field(..., description="Variables de suelo modificadas (claves canónicas: ph, nitrogeno, fosforo, potasio…)")

@router.post("/generar")
async def generar_reporte(
    body: ReporteRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Genera el HTML del reporte según el tipo solicitado."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, body.finca_id)

    try:
        finca_uuid = uuid_mod.UUID(body.finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })

    finca = (
        await db.execute(select(Finca).where(Finca.id == finca_uuid))
    ).scalar_one_or_none()
    if finca is None:
        raise HTTPException(status_code=404, detail={
            "code": "FINCA_NOT_FOUND", "message": "La finca no está registrada.",
        })

    lectura = (
        await db.execute(
            select(SensorReading)
            .where(SensorReading.finca_id == finca_uuid)
            .order_by(SensorReading.ts.desc())
            .limit(1)
        )
    ).scalars().first()

    dispositivo = (
        await db.execute(
            select(DispositivoIoT)
            .where(DispositivoIoT.finca_id == finca_uuid)
            .order_by(DispositivoIoT.created_at)
            .limit(1)
        )
    ).scalars().first()

    # Sin lecturas: el reporte se genera igual, de forma preliminar, y se
    # informa qué parámetros harían falta para un mayor detalle.

    # ── Ejecutar el motor según el tipo de reporte ──
    rules_engine = RulesEngine(db)
    orch = RecommendationOrchestrator(
        db_session=db,
        soil_adapter=SueloAdapter(db),
        ml_service=MLOracleService(),
        rules_engine=rules_engine,
        aptitud_service=AptitudService(db, rules_engine),
    )

    def _analizar(cultivo_id):
        return orch.analyze(RecommendationRequest(
            finca_id=body.finca_id, cultivo_id=cultivo_id,
            presupuesto_cop=body.presupuesto_cop,
            rendimiento_actual_t_ha=body.rendimiento_actual_t_ha,
        ))

    uc1 = uc2 = None
    cultivo_analizado = None
    if body.tipo in ("siembra", "completo"):
        uc1 = await _analizar(None)
    if body.tipo in ("cultivo", "completo"):
        cultivo = body.cultivo_id
        if not cultivo and body.tipo == "completo" and uc1 and uc1.sugerencias_cultivos:
            cultivo = uc1.sugerencias_cultivos[0].get("cultivo_id")
        if body.tipo == "cultivo" and not cultivo:
            raise HTTPException(status_code=422, detail={
                "code": "CULTIVO_REQUERIDO",
                "message": "El tipo 'cultivo' requiere cultivo_id.",
            })
        if cultivo:
            uc2 = await _analizar(cultivo)
            cultivo_analizado = cultivo

    # ── Parámetros esenciales faltantes (aviso de detalle en el reporte) ──
    if lectura is None:
        parametros_faltantes = ["ph", "nitrogeno", "fosforo", "potasio"]
    else:
        parametros_faltantes = (
            (uc2.variables_faltantes_esenciales if uc2 else [])
            or (uc1.variables_faltantes_esenciales if uc1 else [])
        )

    # ── Plan económico para el ROI (ideal si no se declaró presupuesto) ──
    recs = (
        uc2.recomendaciones if (uc2 and uc2.recomendaciones)
        else (uc1.recomendaciones if uc1 else [])
    )
    plan_economico = (uc2.plan_economico if uc2 else None) or (
        uc1.plan_economico if uc1 else None
    )
    if plan_economico is None and recs:
        from agroia_backend.services.economia import cargar_precios_insumos

        plan_economico = calcular_plan_economico(
            recs, None, precios_insumos=await cargar_precios_insumos(db)
        )

    # ── Ficha técnica del cultivo analizado (precios de referencia) ──
    ficha_economicos = None
    cultivo_ref = cultivo_analizado
    if not cultivo_ref and body.tipo == "siembra" and uc1 and uc1.sugerencias_cultivos:
        cultivo_ref = uc1.sugerencias_cultivos[0].get("cultivo_id")
    if cultivo_ref:
        try:
            cultivo_ref_uuid = uuid_mod.UUID(str(cultivo_ref))
        except ValueError:
            cultivo_ref_uuid = None
        if cultivo_ref_uuid:
            # Nota (Neon): no se filtra por `estado` en SQL — los casts de enum
            # dependen del search_path de la conexión y fallan intermitentemente.
            # Se traen las últimas fichas y se elige en Python (prefiere Publicado).
            fichas = (
                await db.execute(
                    select(FichaTecnica)
                    .where(FichaTecnica.cultivo_id == cultivo_ref_uuid)
                    .order_by(FichaTecnica.updated_at.desc())
                    .limit(3)
                )
            ).scalars().all()
            ficha = next(
                (f for f in fichas if getattr(f.estado, "value", f.estado) == EstadoFicha.PUBLICADO.value),
                fichas[0] if fichas else None,
            )
            if ficha is not None and ficha.datos_economicos:
                ficha_economicos = dict(ficha.datos_economicos)

    muestras_geo = await _muestras_geo(db, finca_uuid)

    # ── Órdenes de trabajo / labores de la finca (para la sección Q) ──
    filas_lotes = (
        await db.execute(select(Lote.id, Lote.nombre).where(Lote.finca_id == finca_uuid))
    ).all()
    lote_nombres = {str(lid): nombre for lid, nombre in filas_lotes}
    labores_report = []
    if filas_lotes:
        labores_rows = (
            await db.execute(
                select(Labor)
                .where(Labor.lote_id.in_([lid for lid, _ in filas_lotes]))
                .order_by(Labor.fecha_programada.desc(), Labor.created_at.desc())
                .limit(50)
            )
        ).scalars().all()
        labores_report = [
            {
                "titulo": labor.titulo,
                "tipo": labor.tipo,
                "producto": labor.producto,
                "dosis_kg_ha": labor.dosis_kg_ha,
                "fecha_programada": labor.fecha_programada.isoformat() if labor.fecha_programada else None,
                "fecha_ejecucion": labor.fecha_ejecucion.isoformat() if labor.fecha_ejecucion else None,
                "estado": labor.estado,
                "finca_nombre": finca.nombre,
                "lote_nombre": lote_nombres.get(str(labor.lote_id)),
                "observaciones_ejecucion": labor.observaciones_ejecucion,
            }
            for labor in labores_rows
        ]

    # ── Historial de ciclos (últimos 3) + predicción de rendimiento ──
    historial = await _historial_ciclos_reporte(db, finca_uuid)
    historial_ciclos = historial["ciclos"]
    prediccion_rendimiento = historial["prediccion"]
    advertencia_acumulacion = historial["advertencia_acumulacion"]

    # ── Muestreo inteligente: dónde tomar la muestra de laboratorio ──
    puntos_sugeridos = []
    confianza_actual = (uc2.confianza if uc2 else (uc1.confianza if uc1 else None))
    if parametros_faltantes:
        from agroia_backend.services.optimizador_muestreo import puntos_muestreo_optimos

        puntos_sugeridos = puntos_muestreo_optimos(muestras_geo, 3)

    # ── Clima del día de la muestra (IDEAM) ──
    # Solo si la finca tiene coordenadas útiles (enlace de Google, 'lat,lng'
    # o latitud/longitud registradas); si no, la sección se omite.
    clima = None
    if finca.coordenadas_google or (finca.latitud is not None and finca.longitud is not None):
        from agroia_backend.api.fincas import _extraer_coordenadas
        from agroia_backend.services.external_apis import (
            fetch_ideam_clima_fecha,
            resolver_enlace_google,
        )

        lat = lng = None
        if finca.coordenadas_google:
            lat, lng = _extraer_coordenadas(finca.coordenadas_google)
        if (lat is None or lng is None) and finca.latitud is not None and finca.longitud is not None:
            lat, lng = float(finca.latitud), float(finca.longitud)
        if (lat is None or lng is None) and finca.coordenadas_google and str(finca.coordenadas_google).startswith("http"):
            try:
                enlace_final = await resolver_enlace_google(finca.coordenadas_google)
                lat, lng = _extraer_coordenadas(enlace_final)
            except Exception as e:  # noqa: BLE001
                logger.warning("enlace_google_no_resuelto", error=str(e))
        if lat is not None and lng is not None:
            fecha_muestreo = None
            if muestras_geo:
                con_fecha = [m["ts"] for m in muestras_geo if m.get("ts")]
                if con_fecha:
                    fecha_muestreo = max(con_fecha)[:10]
            fecha_muestreo = fecha_muestreo or (
                lectura.ts.date().isoformat()
                if lectura is not None and lectura.ts else None
            )
            if fecha_muestreo:
                try:
                    clima = await fetch_ideam_clima_fecha(lat, lng, fecha_muestreo)
                except Exception as e:  # noqa: BLE001
                    logger.warning("clima_ideam_no_disponible", error=str(e))

    # ── Pronóstico extendido (7 días) para la sección N ──
    # Por defecto (ambos) se consultan las dos fuentes y se muestran las dos
    # tablas en el reporte; con auto/ecmwf se muestra una sola.
    pronostico_extendido = None
    pronostico_ecmwf = None
    if finca.latitud is not None and finca.longitud is not None:
        from agroia_backend.services.external_apis import fetch_pronostico_open_meteo

        modelo = body.modelo_pronostico or "ambos"
        lat_f, lng_f = float(finca.latitud), float(finca.longitud)
        if modelo in ("auto", "ambos"):
            pronostico_extendido = await fetch_pronostico_open_meteo(lat_f, lng_f, dias=7, modelo="auto")
        if modelo in ("ecmwf", "ambos"):
            pronostico_ecmwf = await fetch_pronostico_open_meteo(lat_f, lng_f, dias=7, modelo="ecmwf")

    # ── v4: balance hídrico, rotación y avance BPA para el reporte ──
    from agroia_backend.api.rotacion import calcular_rotacion
    from agroia_backend.services.balance_hidrico import calcular_balance_hidrico

    balance_hidrico = await calcular_balance_hidrico(
        db, finca, dias=7,
        modelo=body.modelo_pronostico if body.modelo_pronostico in ("auto", "ecmwf") else "auto",
    )
    rotacion = await calcular_rotacion(db, finca_uuid)
    checklist = (
        await db.execute(select(ChecklistBpa).where(ChecklistBpa.finca_id == finca_uuid))
    ).scalars().all()
    bpa_resumen = {
        "total": len(checklist),
        "cumplidos": sum(1 for c in checklist if c.cumple),
        "pct": (
            round(sum(1 for c in checklist if c.cumple) * 100 / len(checklist), 1)
            if checklist else None
        ),
    }

    # ── v3.4: calendario lunar (Almanaque Bristol) ──
    # Solo si la finca tiene coordenadas y el usuario no desactivó la sección.
    lunar = None
    try:
        from agroia_backend.services.calendario_lunar import (
            BRISTOL_ACTIVADO,
            resumen_bristol,
        )

        if BRISTOL_ACTIVADO and finca.latitud is not None and finca.longitud is not None:
            mostrar = True
            if x_user_email:
                from agroia_backend.models.preferencia_bristol import PreferenciaBristol
                from agroia_backend.models.usuario import Usuario

                usuario = (
                    await db.execute(
                        select(Usuario).where(Usuario.email == x_user_email.lower())
                    )
                ).scalar_one_or_none()
                if usuario is not None:
                    pref = (
                        await db.execute(
                            select(PreferenciaBristol).where(
                                PreferenciaBristol.usuario_id == usuario.id
                            )
                        )
                    ).scalar_one_or_none()
                    mostrar = pref.mostrar_en_reportes if pref else True
            if mostrar:
                lunar = resumen_bristol(
                    None, float(finca.latitud), float(finca.longitud)
                )
    except Exception as e:  # noqa: BLE001 — el reporte nunca falla por Bristol
        logger.warning("bristol_reporte_no_disponible", error=str(e))

    html = generar_reporte_html(
        finca={
            "nombre": finca.nombre,
            "departamento": finca.departamento,
            "municipio": finca.municipio,
            "propietario": finca.propietario,
            "contacto_telefono": finca.contacto_telefono,
            "area_hectareas": finca.area_hectareas,
            "latitud": finca.latitud,
            "longitud": finca.longitud,
            "largo_metros": finca.largo_metros,
            "ancho_metros": finca.ancho_metros,
            "coordenadas_google": finca.coordenadas_google,
            "pendiente_pct": finca.pendiente_pct,
            "drenaje": finca.drenaje,
            "historial_agronomico": finca.historial_agronomico,
            "validacion_laboratorio": finca.validacion_laboratorio,
            "cultivo_sembrado": finca.cultivo_sembrado,
            "edad_anos": finca.edad_anos,
            "etapa_fenologica": finca.etapa_fenologica,
            "tipo_riego": finca.tipo_riego.value if finca.tipo_riego else None,
        },
        lectura={
            "ts": lectura.ts.isoformat() if lectura is not None and lectura.ts else None,
            "sensor_id": lectura.sensor_id if lectura is not None else None,
            "ph": lectura.ph if lectura is not None else None,
            "nitrogeno": lectura.nitrogeno if lectura is not None else None,
            "fosforo": lectura.fosforo if lectura is not None else None,
            "potasio": lectura.potasio if lectura is not None else None,
            "conductividad_electrica": lectura.conductividad_electrica if lectura is not None else None,
            "humedad_ambiental": lectura.humedad_ambiental if lectura is not None else None,
            "temperatura_ambiental": lectura.temperatura_ambiental if lectura is not None else None,
            "materia_organica": lectura.materia_organica if lectura is not None else None,
            "calidad": lectura.calidad if lectura is not None else None,
        },
        dispositivo={
            "device_id": dispositivo.device_id,
            "rssi": dispositivo.rssi,
            "uptime_s": dispositivo.uptime_s,
            "npk_calibrado": dispositivo.npk_calibrado,
        } if dispositivo else None,
        tipo=body.tipo,
        uc1=asdict(uc1) if uc1 else None,
        uc2=asdict(uc2) if uc2 else None,
        muestras=muestras_geo,
        umbrales=_umbrales_de_analisis(uc1, uc2),
        clima=clima,
        plan_economico=plan_economico,
        ficha_economicos=ficha_economicos,
        parametros_faltantes=parametros_faltantes,
        puntos_sugeridos=puntos_sugeridos,
        confianza_actual=confianza_actual,
        rendimiento_actual_t_ha=body.rendimiento_actual_t_ha,
        historial_ciclos=historial_ciclos,
        prediccion_rendimiento=prediccion_rendimiento,
        advertencia_acumulacion=advertencia_acumulacion,
        pronostico_extendido=pronostico_extendido,
        pronostico_ecmwf=pronostico_ecmwf,
        modelo_pronostico=body.modelo_pronostico,
        labores=labores_report,
        balance_hidrico=balance_hidrico,
        rotacion=rotacion,
        bpa_resumen=bpa_resumen,
        lunar=lunar,
    )

    titulo = {
        "siembra": "Reporte de recomendación de siembra",
        "cultivo": "Reporte de recomendación para el cultivo sembrado",
        "completo": "Reporte completo de análisis",
    }.get(body.tipo, "Reporte AgroIA")

    logger.info("reporte_generado", finca_id=body.finca_id, tipo=body.tipo, rol=(x_user_role or "?"))
    # Traza de la orden de trabajo: el reporte generado marca el fin de actividad
    # de la finca en la lista de trabajos (Admin).
    try:
        from agroia_backend.services.auditoria import registrar_auditoria

        await registrar_auditoria(
            db,
            usuario_email=(x_user_email or "desconocido@agroia.co").strip().lower(),
            usuario_nombre=x_user_nombre,
            rol=x_user_role,
            accion="reporte.generar",
            entidad="reporte",
            entidad_id=body.finca_id,
            detalle={"tipo": body.tipo, "modelo_pronostico": body.modelo_pronostico},
        )
        await db.commit()
    except Exception as e:  # noqa: BLE001 — la traza no debe romper el reporte
        logger.warning("reporte_auditoria_fallo", error=str(e))
    return {
        "titulo": titulo,
        "tipo": body.tipo,
        "html": html,
        "parametros_faltantes": parametros_faltantes,
        "preliminar": bool(parametros_faltantes),
    }


@router.post("/simular")
async def simular_enmienda(
    body: SimularRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Modo simulación (what-if): re-ejecuta el motor con valores modificados.

    NO toca la base de datos: toma la última lectura, le aplica
    `soil_modificado` y re-ejecuta solo el RulesEngine para devolver la
    nueva clasificación y confianza en < 200 ms.
    """
    await verificar_acceso_finca(db, x_user_role, x_user_email, body.finca_id)
    try:
        finca_uuid = uuid_mod.UUID(body.finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })

    adapter = SueloAdapter(db)
    soil_data = await adapter.get_latest(str(finca_uuid))
    base = soil_data.to_dict() if soil_data is not None else {}
    suelo = dict(base)
    for clave, valor in (body.soil_modificado or {}).items():
        try:
            suelo[clave] = float(valor)
        except (TypeError, ValueError):
            continue

    rules = RulesEngine(db)
    resultado = await rules.evaluate(suelo, body.cultivo_id)
    if resultado.is_blocked:
        clasificacion = "No apta"
    elif resultado.has_violations:
        clasificacion = "Moderadamente apta"
    else:
        clasificacion = "Apta"

    n_viol = len(resultado.violations)
    n_warn = len(resultado.warnings)
    confianza = round(
        max(0.05, min(0.99, 1.0 - (n_viol * 0.20 + n_warn * 0.05))), 3
    )
    violaciones = [{
        "variable": v.variable,
        "estado": "DEFICIT" if (v.umbral_min is not None and v.valor_actual < v.umbral_min)
        else "EXCESO",
        "valor_actual": v.valor_actual,
        "rango_ideal": (
            f"[{v.umbral_min} - {v.umbral_max}]"
            if v.umbral_min is not None and v.umbral_max is not None else "—"
        ),
        "accion": v.accion,
        "prioridad": v.prioridad,
        "fuente": v.fuente,
    } for v in resultado.violations + resultado.warnings]

    return {
        "clasificacion": clasificacion,
        "confianza": confianza,
        "violaciones": n_viol,
        "advertencias": n_warn,
        "detalle": violaciones,
        "soil_usado": suelo,
    }


# ── Helpers del mapa de calor (muestreo en cuadrícula) ──

_VAR_ATRIBUTOS = [
    "ph", "nitrogeno", "fosforo", "potasio", "calcio", "magnesio", "azufre",
    "hierro", "manganeso", "zinc", "cobre", "boro", "materia_organica", "cic",
    "humedad", "temperatura_suelo", "conductividad_electrica",
]


async def _muestras_geo(db: AsyncSession, finca_uuid) -> list[dict]:
    """Lecturas recientes con posición (x, y) para pintar el mapa de calor."""
    lecturas = (
        await db.execute(
            select(SensorReading)
            .where(
                SensorReading.finca_id == finca_uuid,
                SensorReading.pos_x.isnot(None),
                SensorReading.pos_y.isnot(None),
            )
            .order_by(SensorReading.ts.desc())
            .limit(400)
        )
    ).scalars().all()
    muestras = []
    for r in lecturas:
        muestra = {"pos_x": r.pos_x, "pos_y": r.pos_y}
        if r.ts:
            muestra["ts"] = r.ts.isoformat()
        for attr in _VAR_ATRIBUTOS:
            valor = getattr(r, attr, None)
            if valor is not None:
                muestra[attr] = float(valor)
        muestras.append(muestra)
    return muestras


def _umbrales_de_analisis(uc1, uc2) -> dict:
    """Rangos ideales por variable (símbolo → (min, max)) desde el análisis."""
    umbrales: dict[str, tuple[float, float]] = {}
    fuente = (uc2.recomendaciones if uc2 else []) or (uc1.recomendaciones if uc1 else [])
    for rec in fuente:
        variable = str(rec.get("variable") or "").strip()
        rango = str(rec.get("rango_ideal") or "")
        nums = [n for n in rango.replace("[", "").replace("]", "").split("-") if n.strip()]
        try:
            minimo = float(nums[0]) if nums else None
            maximo = float(nums[1]) if len(nums) > 1 else None
        except ValueError:
            continue
        if minimo is not None or maximo is not None:
            umbrales[variable] = (minimo, maximo)
    return umbrales
