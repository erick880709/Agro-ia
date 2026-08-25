"""API endpoints para ingesta IoT y estado de sensores."""


from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/iot", tags=["iot"])


# ── Schemas ──

class SensorMessage(BaseModel):
    """Mensaje entrante de un sensor IoT LoRaWAN."""
    device_id: str = Field(..., description="ID único del dispositivo LoRaWAN")
    finca_id: str = Field(..., description="UUID de la finca asociada")
    timestamp: str | None = Field(None, description="ISO 8601 timestamp de la medición")
    payload: dict = Field(..., description="Variables de suelo medidas (JSON dinámico)")


class SensorStatus(BaseModel):
    finca_id: str
    device_id: str
    last_transmission: str | None = None
    hours_since_last: float | None = None
    status: str  # "online", "offline", "datos_desactualizados"


class Esp32SensorMessage(BaseModel, extra="allow"):
    """Trama cruda del firmware ESP32 (variables en la raíz, sin finca_id)."""
    device_id: str = Field(..., description="ID del dispositivo (ej. esp32-npk-001)")
    ph: float | None = None
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    conductivity: float | None = Field(None, description="µS/cm")
    humidity: float | None = Field(None, description="% HR ambiente")
    temperature: float | None = Field(None, description="°C ambiente")
    rssi: int | None = None
    uptime_s: int | None = None


class DispositivoRegistro(BaseModel):
    """Registro de un dispositivo IoT asociado a una finca."""
    device_id: str = Field(..., description="ID único del firmware")
    finca_id: str = Field(..., description="UUID de la finca asociada")
    nombre: str | None = None
    npk_calibrado: bool = Field(
        False, description="True si NPK fue calibrado contra laboratorio"
    )


# ── Endpoints ──

@router.post("/ingest", status_code=202)
async def ingest_sensor_data(message: SensorMessage):
    """Recibe datos de un sensor IoT y los encola para procesamiento.

    En producción, este endpoint lo llama el gateway LoRaWAN.
    En desarrollo, acepta POST directo desde simuladores.
    """
    from agroia_backend.services.data_adapters import ALL_SOIL_VARIABLES

    payload = message.payload
    vars_received = [v for v in ALL_SOIL_VARIABLES if v in payload and payload[v] is not None]

    logger.info(
        "sensor_data_received",
        device_id=message.device_id,
        finca_id=message.finca_id,
        vars_count=len(vars_received),
    )

    # Encolar en RabbitMQ (en producción) o procesar directamente (dev)
    from apps.iot.agroia_iot.consumer import process_sensor_message

    success = await process_sensor_message({
        "device_id": message.device_id,
        "finca_id": message.finca_id,
        "timestamp": message.timestamp,
        "payload": payload,
    })

    return {
        "status": "accepted" if success else "error",
        "device_id": message.device_id,
        "variables_recibidas": vars_received,
        "variables_faltantes": [v for v in ALL_SOIL_VARIABLES if v not in vars_received],
    }


@router.post("/sensor", status_code=202)
async def ingest_esp32_sensor(body: Esp32SensorMessage):
    """Endpoint de compatibilidad para tramas crudas del firmware ESP32 (brecha G1).

    Recibe el JSON tal como lo envía el ESP32 (variables en la raíz, sin
    `finca_id`) y lo normaliza al formato interno usando el registro de
    dispositivos (`device_id` → finca).
    """
    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.dispositivo_iot import DispositivoIoT
    from agroia_backend.services.normalizacion_iot import normalizar_trama

    async with async_session_factory() as session:
        dispositivo = (
            await session.execute(
                select(DispositivoIoT).where(
                    DispositivoIoT.device_id == body.device_id
                )
            )
        ).scalar_one_or_none()

    if dispositivo is None:
        raise HTTPException(status_code=404, detail={
            "code": "DEVICE_NOT_REGISTERED",
            "message": (
                f"Dispositivo '{body.device_id}' no registrado. Regístrelo en "
                "POST /api/v1/iot/dispositivos con su finca_id."
            ),
        })

    from apps.iot.agroia_iot.consumer import process_sensor_message

    payload, advertencias = normalizar_trama(body.model_dump())
    success = await process_sensor_message({
        "device_id": body.device_id,
        "finca_id": str(dispositivo.finca_id),
        "timestamp": None,
        "rssi": body.rssi,
        "uptime_s": body.uptime_s,
        "payload": payload,
    })

    if not success:
        raise HTTPException(status_code=422, detail={
            "code": "INGEST_ERROR",
            "message": "Error al procesar la trama del sensor. Revise los logs.",
        })

    return {
        "status": "accepted",
        "device_id": body.device_id,
        "finca_id": str(dispositivo.finca_id),
        "variables_recibidas": sorted(payload.keys()),
        "advertencias": advertencias,
    }


@router.post("/carga", status_code=200)
async def cargar_archivo_sensor(
    file: UploadFile = File(..., description="Archivo CSV, TXT o JSON con mediciones del sensor"),
    device_id: str | None = Form(None, description="ID del dispositivo (opcional si el archivo lo incluye)"),
    finca_id: str | None = Form(None, description="UUID de la finca a relacionar (opcional; permite cargar datos sin dispositivo)"),
    cultivo_id: str | None = Form(None, description="UUID del cultivo sembrado para diagnóstico UC2 (opcional)"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Carga manual de mediciones cuando se pierde la conexión con los sensores.

    Lee un archivo CSV, TXT o JSON, lo normaliza con las mismas reglas que
    una trama en vivo, persiste la lectura y ejecuta el motor de
    recomendaciones al instante (UC1 sin cultivo_id, UC2 con cultivo_id).

    Formatos aceptados:
      - CSV pares:        variable,valor (ej. `ph,7.1`)
      - CSV ancho:        cabecera de variables + fila de datos
      - TXT:              clave=valor o clave: valor (una por línea)
      - JSON:             trama cruda del firmware (variables en la raíz)
    """
    import uuid as uuid_mod
    from dataclasses import asdict

    from agroia.database import async_session_factory
    from agroia.errors import InsufficientDataError
    from sqlalchemy import select

    from agroia_backend.api.recomendaciones import (
        RecommendRequest,
        _persistir_recomendacion,
    )
    from agroia_backend.models.dispositivo_iot import DispositivoIoT
    from agroia_backend.models.finca import Finca
    from agroia_backend.services.acceso import exigir_no_cliente
    from agroia_backend.services.aptitud import AptitudService
    from agroia_backend.services.carga_archivo import (
        decodificar_contenido,
        parsear_archivo_sensor,
    )
    from agroia_backend.services.data_adapters import SueloAdapter
    from agroia_backend.services.normalizacion_iot import normalizar_trama
    from agroia_backend.services.orchestrator import (
        RecommendationOrchestrator,
        RecommendationRequest,
    )
    from agroia_backend.services.rules_engine import RulesEngine

    exigir_no_cliente(x_user_role)

    contenido = await file.read()
    texto = decodificar_contenido(contenido)
    try:
        frame, device_archivo, formato = parsear_archivo_sensor(texto)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={
            "code": "ARCHIVO_INVALIDO",
            "message": str(e),
        })

    def _a_entero(v):
        try:
            return int(float(v)) if v is not None else None
        except (TypeError, ValueError):
            return None

    dispositivo_id = device_id or device_archivo
    rssi = _a_entero(frame.get("rssi"))
    uptime_s = _a_entero(frame.get("uptime_s"))

    async with async_session_factory() as db:
        # ── Resolver finca (form > dispositivo) ──
        finca = None
        if finca_id:
            try:
                finca_uuid = uuid_mod.UUID(finca_id)
            except ValueError:
                raise HTTPException(status_code=422, detail={
                    "code": "FINCA_INVALIDA",
                    "message": "finca_id no es un UUID válido.",
                })
            finca = (
                await db.execute(select(Finca).where(Finca.id == finca_uuid))
            ).scalar_one_or_none()
            if finca is None:
                raise HTTPException(status_code=404, detail={
                    "code": "FINCA_NOT_FOUND",
                    "message": f"La finca '{finca_id}' no está registrada.",
                })

        # ── Resolver dispositivo (form > archivo > único registrado) ──
        dispositivo = None
        if dispositivo_id:
            dispositivo = (
                await db.execute(
                    select(DispositivoIoT).where(
                        DispositivoIoT.device_id == dispositivo_id
                    )
                )
            ).scalar_one_or_none()
            if dispositivo is None:
                raise HTTPException(status_code=404, detail={
                    "code": "DEVICE_NOT_REGISTERED",
                    "message": (
                        f"Dispositivo '{dispositivo_id}' no registrado. Regístrelo "
                        "en POST /api/v1/iot/dispositivos."
                    ),
                })
        elif finca is None:
            dispositivos = (
                await db.execute(
                    select(DispositivoIoT).where(DispositivoIoT.activo.is_(True))
                )
            ).scalars().all()
            if len(dispositivos) == 0:
                raise HTTPException(status_code=404, detail={
                    "code": "NO_DEVICES",
                    "message": "No hay dispositivos registrados.",
                })
            if len(dispositivos) > 1:
                raise HTTPException(status_code=422, detail={
                    "code": "MULTIPLE_DEVICES",
                    "message": "Hay varios dispositivos registrados; indique device_id.",
                })
            dispositivo = dispositivos[0]

        finca_final = str(finca.id) if finca else str(dispositivo.finca_id)
        device_final = dispositivo.device_id if dispositivo else None

        # ── Normalizar y persistir igual que una trama en vivo ──
        payload, advertencias = normalizar_trama(frame)
        from apps.iot.agroia_iot.consumer import process_sensor_message

        success = await process_sensor_message({
            "device_id": device_final,
            "finca_id": finca_final,
            "timestamp": None,
            "rssi": rssi,
            "uptime_s": uptime_s,
            "payload": payload,
        })
        if not success:
            raise HTTPException(status_code=422, detail={
                "code": "INGEST_ERROR",
                "message": "Error al procesar el archivo. Revise los logs.",
            })

        # ── Ejecutar el mismo motor de recomendaciones que /analyze ──
        rules_engine = RulesEngine(db)
        orch = RecommendationOrchestrator(
            db_session=db,
            soil_adapter=SueloAdapter(db),
            rules_engine=rules_engine,
            aptitud_service=AptitudService(db, rules_engine),
        )
        try:
            resultado = await orch.analyze(RecommendationRequest(
                finca_id=finca_final,
                cultivo_id=cultivo_id,
            ))
        except InsufficientDataError as e:
            raise HTTPException(status_code=422, detail={
                "code": "INSUFFICIENT_DATA",
                "message": (
                    "El archivo no trae datos suficientes para el análisis. "
                    "Variables faltantes: " + ", ".join(e.missing_vars)
                ),
                "missing_variables": e.missing_vars,
            })

        # ── Persistir en historial (mismo comportamiento que /analyze) ──
        await _persistir_recomendacion(
            db,
            RecommendRequest(
                finca_id=finca_final,
                cultivo_id=cultivo_id,
            ),
            resultado,
        )

    return {
        "status": "accepted",
        "origen": "archivo",
        "nombre_archivo": file.filename,
        "formato": formato,
        "device_id": device_final,
        "finca_id": finca_final,
        "variables_recibidas": sorted(payload.keys()),
        "advertencias_ingesta": advertencias,
        "analisis": asdict(resultado),
    }


@router.post("/dispositivos", status_code=201)
async def registrar_dispositivo(body: DispositivoRegistro):
    """Registra un dispositivo IoT y lo asocia a una finca (brecha G1)."""
    import uuid as uuid_mod

    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.dispositivo_iot import DispositivoIoT

    async with async_session_factory() as session:
        existente = (
            await session.execute(
                select(DispositivoIoT).where(
                    DispositivoIoT.device_id == body.device_id
                )
            )
        ).scalar_one_or_none()
        if existente is not None:
            raise HTTPException(status_code=409, detail={
                "code": "DEVICE_ALREADY_REGISTERED",
                "message": f"Dispositivo '{body.device_id}' ya está registrado.",
            })

        dispositivo = DispositivoIoT(
            id=uuid_mod.uuid4(),
            device_id=body.device_id,
            finca_id=uuid_mod.UUID(body.finca_id),
            nombre=body.nombre,
            activo=True,
            npk_calibrado=body.npk_calibrado,
        )
        session.add(dispositivo)
        await session.commit()

    return {
        "status": "registered",
        "device_id": body.device_id,
        "finca_id": body.finca_id,
        "npk_calibrado": body.npk_calibrado,
    }


@router.get("/dispositivos")
async def listar_dispositivos():
    """Lista los dispositivos IoT registrados con su telemetría."""
    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.dispositivo_iot import DispositivoIoT

    async with async_session_factory() as session:
        dispositivos = (await session.execute(select(DispositivoIoT))).scalars().all()

    return {
        "data": [
            {
                "device_id": d.device_id,
                "finca_id": str(d.finca_id),
                "nombre": d.nombre,
                "npk_calibrado": d.npk_calibrado,
                "ultima_transmision": (
                    d.ultima_transmision.isoformat() if d.ultima_transmision else None
                ),
                "rssi": d.rssi,
                "uptime_s": d.uptime_s,
                "activo": d.activo,
            }
            for d in dispositivos
        ],
        "total": len(dispositivos),
    }


@router.get("/lecturas/{finca_id}")
async def ultimas_lecturas(
    finca_id: str,
    limite: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Últimas lecturas de sensores de una finca (para monitoreo en pantalla)."""
    import uuid as uuid_mod

    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.sensor_reading import SensorReading
    from agroia_backend.services.acceso import verificar_acceso_finca

    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)

    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA",
            "message": "finca_id no es un UUID válido.",
        })

    async with async_session_factory() as session:
        lecturas = (
            await session.execute(
                select(SensorReading)
                .where(SensorReading.finca_id == finca_uuid)
                .order_by(SensorReading.ts.desc())
                .limit(limite)
            )
        ).scalars().all()

    return {
        "data": [
            {
                "id": str(r.id),
                "sensor_id": r.sensor_id,
                "ts": r.ts.isoformat() if r.ts else None,
                "ph": r.ph,
                "nitrogeno": r.nitrogeno,
                "fosforo": r.fosforo,
                "potasio": r.potasio,
                "conductividad_electrica": r.conductividad_electrica,
                "humedad_ambiental": r.humedad_ambiental,
                "temperatura_ambiental": r.temperatura_ambiental,
                "materia_organica": r.materia_organica,
                "cic": r.cic,
                "humedad": r.humedad,
                "temperatura_suelo": r.temperatura_suelo,
                "calidad": r.calidad,
            }
            for r in lecturas
        ],
        "total": len(lecturas),
    }


@router.get("/sensores/{finca_id}/status")
async def sensor_status(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Consulta el estado de los sensores de una finca."""
    from datetime import datetime, timezone

    from sqlalchemy import func, select

    from agroia_backend.models.sensor_reading import SensorReading
    from agroia_backend.services.acceso import verificar_acceso_finca

    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)

    stmt = (
        select(SensorReading.sensor_id, func.max(SensorReading.ts).label("last_ts"))
        .where(SensorReading.finca_id == finca_id)
        .group_by(SensorReading.sensor_id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    now = datetime.now(timezone.utc)
    sensores = []
    for row in rows:
        last_ts = row.last_ts
        hours = (now - last_ts).total_seconds() / 3600 if last_ts else None
        status = "offline" if hours is None or hours > 24 else ("datos_desactualizados" if hours > 12 else "online")
        sensores.append({
            "device_id": row.sensor_id,
            "last_transmission": last_ts.isoformat() if last_ts else None,
            "hours_since_last": round(hours, 1) if hours else None,
            "status": status,
        })

    return {
        "finca_id": finca_id,
        "sensores": sensores,
        "total": len(sensores),
        "online": sum(1 for s in sensores if s["status"] == "online"),
        "offline": sum(1 for s in sensores if s["status"] != "online"),
    }


@router.get("/externas/enrich")
async def enrich_location(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    address: str | None = None,
):
    """Enriquece una ubicación con datos de APIs externas (IDEAM, GIS, IGAC, Copernicus)."""
    from agroia_backend.services.external_apis import enrich_location_data

    results = await enrich_location_data(lat, lon, address)
    return {"lat": lat, "lon": lon, "apis": results}
