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

from agroia_backend.models.cultivo import EstadoFicha, FichaTecnica
from agroia_backend.models.dispositivo_iot import DispositivoIoT
from agroia_backend.models.finca import Finca
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


class ReporteRequest(BaseModel):
    finca_id: str = Field(..., description="UUID de la finca a reportar")
    tipo: str = Field("completo", pattern="^(siembra|cultivo|completo)$")
    cultivo_id: str | None = Field(None, description="UUID del cultivo sembrado (obligatorio en tipo 'cultivo')")
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
        plan_economico = calcular_plan_economico(recs, None)

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
    )

    titulo = {
        "siembra": "Reporte de recomendación de siembra",
        "cultivo": "Reporte de recomendación para el cultivo sembrado",
        "completo": "Reporte completo de análisis",
    }.get(body.tipo, "Reporte AgroIA")

    logger.info("reporte_generado", finca_id=body.finca_id, tipo=body.tipo, rol=(x_user_role or "?"))
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
