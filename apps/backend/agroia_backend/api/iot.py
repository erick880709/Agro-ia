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
    """Registro de un dispositivo IoT asociado a una finca (E1, HU-01)."""
    device_id: str = Field(..., description="ID único del firmware")
    finca_id: str = Field(..., description="UUID de la finca asociada")
    nombre: str | None = None
    npk_calibrado: bool = Field(
        False, description="True si NPK fue calibrado contra laboratorio"
    )
    modelo: str | None = Field(None, description="Modelo (ej. JXBS-3001-NPK-RS)")
    variante: str | None = Field(None, description="Variante (confirmar con etiqueta física)")
    direccion_modbus: int | None = Field(
        None, ge=0, le=247, description="Dirección Modbus RTU (única por bus)"
    )
    baudios: int | None = Field(None, description="Baudios del bus RS485 (9600 por defecto)")
    bus_id: str | None = Field(None, description="Identificador del bus RS485")
    firmware: str | None = Field(None, description="Versión de firmware")
    fecha_instalacion: str | None = Field(None, description="Fecha de instalación (YYYY-MM-DD)")
    profundidad_cm: int | None = Field(None, ge=0, description="Profundidad de lectura/instalación (cm)")
    modo_instalacion: str | None = Field(
        None, description="Modo de instalación: superficial | enterrado"
    )
    lote_id: str | None = Field(None, description="UUID del lote asociado")
    ultimo_mantenimiento: str | None = Field(None, description="Fecha del último mantenimiento (YYYY-MM-DD)")
    estado_salud: str | None = Field(None, description="Estado de salud agregado")


class SensorRawRegistros(BaseModel, extra="allow"):
    """Trama cruda en registros Modbus (función 0x03) del JXBS-3001-NPK-RS."""
    device_id: str = Field(..., description="ID del dispositivo (ej. esp32-npk-001)")
    registros: dict[str, int] = Field(
        ..., description="Mapa registro (hex o decimal) → valor entero crudo de 16 bits"
    )
    timestamp: str | None = Field(None, description="ISO 8601 timestamp de la medición")


class VerificacionVariante(BaseModel):
    """Registros leídos del equipo para la prueba de aceptación de variante."""
    registros: dict[str, int] = Field(
        ..., description="Mapa registro (hex o decimal) → valor entero crudo de 16 bits"
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
    from agroia_backend.services.puente_iot import process_sensor_message

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

    from agroia_backend.services.puente_iot import process_sensor_message

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


@router.post("/sensor/raw", status_code=202)
async def ingest_esp32_registros(body: SensorRawRegistros):
    """Decodifica una trama Modbus cruda (TT-01) y la persiste.

    Recibe los registros leídos por el firmware (mapa registro→entero de 16
    bits) y los decodifica con las escalas y el signo correctos, conservando
    el valor crudo.
    """
    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.dispositivo_iot import DispositivoIoT
    from agroia_backend.services.decodificacion_modbus import decodificar_para_sensor
    from agroia_backend.services.puente_iot import process_sensor_message

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

    payload = decodificar_para_sensor(body.registros)
    if not any(k in payload for k in ("ph", "humedad", "conductividad_electrica",
                                      "nitrogeno", "fosforo", "potasio",
                                      "temperatura_suelo")):
        raise HTTPException(status_code=422, detail={
            "code": "REGISTROS_NO_RECONOCIDOS",
            "message": "Ningún registro coincide con los del JXBS-3001-NPK-RS.",
        })

    success = await process_sensor_message({
        "device_id": body.device_id,
        "finca_id": str(dispositivo.finca_id),
        "timestamp": body.timestamp,
        "payload": payload,
        "valor_crudo": payload.get("valor_crudo"),
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
    }


@router.post("/dispositivos/{device_id}/verificar-variante")
async def verificar_variante_dispositivo(device_id: str, body: VerificacionVariante):
    """Prueba de aceptación de variante (TT-03): confirma pH, CE, N, P y K."""
    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.dispositivo_iot import DispositivoIoT
    from agroia_backend.services.decodificacion_modbus import verificar_variante

    async with async_session_factory() as session:
        dispositivo = (
            await session.execute(
                select(DispositivoIoT).where(DispositivoIoT.device_id == device_id)
            )
        ).scalar_one_or_none()

    if dispositivo is None:
        raise HTTPException(status_code=404, detail={
            "code": "DEVICE_NOT_REGISTERED",
            "message": f"Dispositivo '{device_id}' no registrado.",
        })

    resultado = verificar_variante(body.registros)
    return {
        "device_id": device_id,
        "aceptado": resultado["aceptado"],
        "variables_presentes": resultado["variables_presentes"],
        "variables_faltantes": resultado["variables_faltantes"],
        "decodificadas": resultado["decodificadas"],
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
        frames, device_archivo, formato = parsear_archivo_sensor(texto)
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

    def _a_flotante(v):
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _posicion(frame: dict, eje: str):
        # Prioridad: coordenadas locales en metros (pos_x/pos_y) sobre GPS absoluto
        claves = {
            "x": ("pos_x", "x", "coordenada_x", "punto_x", "columna", "latitude"),
            "y": ("pos_y", "y", "coordenada_y", "punto_y", "fila", "longitude"),
        }[eje]
        for clave in claves:
            if clave in frame and frame[clave] not in (None, ""):
                return _a_flotante(frame[clave])
        return None

    frame_primero = frames[0]
    dispositivo_id = device_id or device_archivo or frame_primero.get("device_id")
    rssi = _a_entero(frame_primero.get("rssi"))
    uptime_s = _a_entero(frame_primero.get("uptime_s"))

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

        # ── Regla de negocio: sin comisión asignada no se genera recomendación ──
        from agroia_backend.services.comision_etapas import (
            exigir_comision_para_recomendacion,
            marcar_en_recomendacion,
        )

        comision = await exigir_comision_para_recomendacion(db, finca_final)

        # ── Normalizar y persistir cada muestra (cuadrícula) ──
        from agroia_backend.services.geo_utils import centroide_finca, haversine_relativa
        from agroia_backend.services.puente_iot import process_sensor_message

        variables_recibidas: set[str] = set()
        numero_muestras = 0
        for frame in frames:
            payload, advertencias = normalizar_trama(frame)
            pos_x = _posicion(frame, "x")
            pos_y = _posicion(frame, "y")
            lat_abs = _a_flotante(frame.get("latitude"))
            lng_abs = _a_flotante(frame.get("longitude"))
            gps_convertido = False
            if lat_abs is not None and lng_abs is not None and pos_x is None and pos_y is None and finca is not None:
                centro = centroide_finca(finca)
                if centro is not None:
                    pos_x, pos_y = haversine_relativa(centro[0], centro[1], lat_abs, lng_abs)
                    gps_convertido = True
                    advertencias.append("gps_convertido_a_relativo")
            mensaje = {
                "device_id": device_final,
                "finca_id": finca_final,
                "timestamp": None,
                "rssi": rssi,
                "uptime_s": uptime_s,
                "payload": payload,
            }
            if gps_convertido:
                mensaje["pos_x"] = pos_x
                mensaje["pos_y"] = pos_y
            else:
                mensaje["latitude"] = pos_x if pos_x is not None else lat_abs
                mensaje["longitude"] = pos_y if pos_y is not None else lng_abs
            success = await process_sensor_message(mensaje)
            if not success:
                raise HTTPException(status_code=422, detail={
                    "code": "INGEST_ERROR",
                    "message": "Error al procesar el archivo. Revise los logs.",
                })
            variables_recibidas.update(payload.keys())
            numero_muestras += 1

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
        # La recomendación generada mueve la comisión a `en_recomendacion`.
        await marcar_en_recomendacion(db, comision)
        await db.commit()

    return {
        "status": "accepted",
        "origen": "archivo",
        "nombre_archivo": file.filename,
        "formato": formato,
        "device_id": device_final,
        "finca_id": finca_final,
        "numero_muestras": numero_muestras,
        "variables_recibidas": sorted(variables_recibidas),
        "advertencias_ingesta": advertencias,
        "analisis": asdict(resultado),
        "comision_estado": comision.estado,
    }


@router.post("/dispositivos", status_code=201)
async def registrar_dispositivo(body: DispositivoRegistro):
    """Registra un dispositivo IoT y lo asocia a una finca (brecha G1, HU-01)."""
    import uuid as uuid_mod
    from datetime import date

    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.dispositivo_iot import DispositivoIoT

    def _a_fecha(texto: str | None) -> date | None:
        if not texto:
            return None
        try:
            return date.fromisoformat(texto)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "FECHA_INVALIDA",
                "message": f"'{texto}' no es una fecha ISO válida (YYYY-MM-DD).",
            })

    try:
        finca_uuid = uuid_mod.UUID(body.finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA",
            "message": "finca_id no es un UUID válido.",
        })

    lote_uuid = None
    if body.lote_id:
        try:
            lote_uuid = uuid_mod.UUID(body.lote_id)
        except ValueError:
            raise HTTPException(status_code=422, detail={
                "code": "LOTE_INVALIDO",
                "message": "lote_id no es un UUID válido.",
            })

    if body.modo_instalacion and body.modo_instalacion not in ("superficial", "enterrado"):
        raise HTTPException(status_code=422, detail={
            "code": "MODO_INSTALACION_INVALIDO",
            "message": "modo_instalacion debe ser 'superficial' o 'enterrado'.",
        })

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

        # Unicidad dirección ↔ bus: no puede haber dos sensores con la misma
        # dirección Modbus en el mismo bus (CA2 de HU-01).
        if body.direccion_modbus is not None:
            clave_nueva = body.bus_id or f"finca:{body.finca_id}"
            mismo_dir = (
                await session.execute(
                    select(DispositivoIoT).where(
                        DispositivoIoT.direccion_modbus == body.direccion_modbus
                    )
                )
            ).scalars().all()
            for d in mismo_dir:
                clave_existente = d.bus_id or f"finca:{d.finca_id}"
                if clave_existente == clave_nueva:
                    raise HTTPException(status_code=409, detail={
                        "code": "DIRECCION_MODBUS_DUPLICADA",
                        "message": (
                            f"La dirección Modbus {body.direccion_modbus} ya está "
                            f"asignada a otro sensor del bus '{clave_nueva}'."
                        ),
                    })

        dispositivo = DispositivoIoT(
            id=uuid_mod.uuid4(),
            device_id=body.device_id,
            finca_id=finca_uuid,
            nombre=body.nombre,
            activo=True,
            npk_calibrado=body.npk_calibrado,
            modelo=body.modelo,
            variante=body.variante,
            direccion_modbus=body.direccion_modbus,
            baudios=body.baudios,
            bus_id=body.bus_id,
            firmware=body.firmware,
            fecha_instalacion=_a_fecha(body.fecha_instalacion),
            profundidad_cm=body.profundidad_cm,
            modo_instalacion=body.modo_instalacion,
            lote_id=lote_uuid,
            ultimo_mantenimiento=_a_fecha(body.ultimo_mantenimiento),
            estado_salud=body.estado_salud,
        )
        session.add(dispositivo)
        await session.commit()

    return {
        "status": "registered",
        "device_id": body.device_id,
        "finca_id": body.finca_id,
        "npk_calibrado": body.npk_calibrado,
        "modelo": body.modelo,
        "direccion_modbus": body.direccion_modbus,
        "bus_id": body.bus_id,
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
                "modelo": d.modelo,
                "variante": d.variante,
                "direccion_modbus": d.direccion_modbus,
                "baudios": d.baudios,
                "bus_id": d.bus_id,
                "firmware": d.firmware,
                "fecha_instalacion": (
                    d.fecha_instalacion.isoformat() if d.fecha_instalacion else None
                ),
                "profundidad_cm": d.profundidad_cm,
                "modo_instalacion": d.modo_instalacion,
                "lote_id": str(d.lote_id) if d.lote_id else None,
                "ultimo_mantenimiento": (
                    d.ultimo_mantenimiento.isoformat() if d.ultimo_mantenimiento else None
                ),
                "estado_salud": d.estado_salud,
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
                "finca_id": str(r.finca_id),
                "sensor_id": r.sensor_id,
                "ts": r.ts.isoformat() if r.ts else None,
                "pos_x": r.pos_x,
                "pos_y": r.pos_y,
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
                "motivos_calidad": r.motivos_calidad,
                "version_regla": r.version_regla,
                "incertidumbre": r.incertidumbre,
            }
            for r in lecturas
        ],
        "total": len(lecturas),
    }


@router.get("/lecturas/{finca_id}/calidad-resumen")
async def resumen_calidad_lecturas(
    finca_id: str,
    dias: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Transparencia de calidad (HU-02): 'N de M lecturas válidas' por motivo."""
    import uuid as uuid_mod
    from datetime import datetime, timedelta, timezone

    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.sensor_reading import SensorReading
    from agroia_backend.services.acceso import verificar_acceso_finca
    from agroia_backend.services.motor_calidad import resumir_calidad

    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)

    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA",
            "message": "finca_id no es un UUID válido.",
        })

    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    async with async_session_factory() as session:
        lecturas = (
            await session.execute(
                select(SensorReading)
                .where(SensorReading.finca_id == finca_uuid, SensorReading.ts >= desde)
                .order_by(SensorReading.ts.desc())
                .limit(1000)
            )
        ).scalars().all()

    resumen = resumir_calidad(lecturas)
    resumen["finca_id"] = finca_id
    resumen["dias"] = dias
    return resumen


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


class ParCalibracionRegistro(BaseModel):
    """Par sensor–laboratorio (RF-017): misma muestra, mismo día y profundidad."""
    device_id: str = Field(..., description="ID del dispositivo (ej. esp32-npk-001)")
    variable: str = Field(..., description="ph | humedad | conductividad_electrica | nitrogeno | fosforo | potasio")
    valor_sensor: float
    valor_laboratorio: float
    metodo: str | None = Field(None, description="Método de laboratorio (pH 1:1, Bray II…)")
    laboratorio: str | None = Field(None, description="Laboratorio acreditado")
    fecha: str = Field(..., description="Fecha del par (YYYY-MM-DD)")
    profundidad_cm: int | None = Field(None, ge=0)
    punto_id: str | None = None


@router.post("/calibracion/pares", status_code=201)
async def registrar_par_calibracion(body: ParCalibracionRegistro):
    """Registra un par sensor–laboratorio (HU-04) y recalcula la calibración."""
    import uuid as uuid_mod
    from datetime import date

    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.calibracion import CalibracionSensor, ParCalibracion
    from agroia_backend.models.dispositivo_iot import DispositivoIoT
    from agroia_backend.services.calibracion import regresion_lineal

    try:
        fecha = date.fromisoformat(body.fecha)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FECHA_INVALIDA",
            "message": "fecha debe ser YYYY-MM-DD.",
        })

    async with async_session_factory() as session:
        dispositivo = (
            await session.execute(
                select(DispositivoIoT).where(DispositivoIoT.device_id == body.device_id)
            )
        ).scalar_one_or_none()
        if dispositivo is None:
            raise HTTPException(status_code=404, detail={
                "code": "DEVICE_NOT_REGISTERED",
                "message": f"Dispositivo '{body.device_id}' no registrado.",
            })

        par = ParCalibracion(
            id=uuid_mod.uuid4(),
            dispositivo_id=dispositivo.id,
            variable=body.variable,
            valor_sensor=body.valor_sensor,
            valor_laboratorio=body.valor_laboratorio,
            metodo=body.metodo,
            laboratorio=body.laboratorio,
            fecha=fecha,
            profundidad_cm=body.profundidad_cm,
            punto_id=body.punto_id,
        )
        session.add(par)
        await session.flush()

        # Recalcular la calibración de esta variable con todos los pares.
        pares = (
            await session.execute(
                select(ParCalibracion).where(
                    ParCalibracion.dispositivo_id == dispositivo.id,
                    ParCalibracion.variable == body.variable,
                )
            )
        ).scalars().all()
        reg = regresion_lineal(
            [p.valor_sensor for p in pares], [p.valor_laboratorio for p in pares]
        )

        calibracion = None
        if reg is not None:
            # La nueva calibración reemplaza a la anterior (la deja inactiva).
            anteriores = (
                await session.execute(
                    select(CalibracionSensor).where(
                        CalibracionSensor.dispositivo_id == dispositivo.id,
                        CalibracionSensor.variable == body.variable,
                        CalibracionSensor.activa.is_(True),
                    )
                )
            ).scalars().all()
            for c in anteriores:
                c.activa = False
            calibracion = CalibracionSensor(
                id=uuid_mod.uuid4(),
                dispositivo_id=dispositivo.id,
                variable=body.variable,
                pendiente=reg["pendiente"],
                intercepto=reg["intercepto"],
                n=reg["n"],
                r2=reg["r2"],
                rmse=reg["rmse"],
                sesgo=reg["sesgo"],
                responsable=body.laboratorio,
            )
            session.add(calibracion)
            await session.flush()
            par.calibracion_id = calibracion.id

        await session.commit()

    return {
        "status": "registered",
        "par_id": str(par.id),
        "device_id": body.device_id,
        "variable": body.variable,
        "calibracion": reg,
    }


@router.get("/calibracion/{device_id}")
async def listar_calibraciones(device_id: str):
    """Lista las calibraciones (vigentes y métricas) de un dispositivo."""
    from agroia.database import async_session_factory
    from sqlalchemy import select

    from agroia_backend.models.calibracion import CalibracionSensor
    from agroia_backend.models.dispositivo_iot import DispositivoIoT

    async with async_session_factory() as session:
        dispositivo = (
            await session.execute(
                select(DispositivoIoT).where(DispositivoIoT.device_id == device_id)
            )
        ).scalar_one_or_none()
        if dispositivo is None:
            raise HTTPException(status_code=404, detail={
                "code": "DEVICE_NOT_REGISTERED",
                "message": f"Dispositivo '{device_id}' no registrado.",
            })

        calibraciones = (
            await session.execute(
                select(CalibracionSensor).where(
                    CalibracionSensor.dispositivo_id == dispositivo.id
                ).order_by(CalibracionSensor.created_at.desc())
            )
        ).scalars().all()

    return {
        "device_id": device_id,
        "data": [
            {
                "id": str(c.id),
                "variable": c.variable,
                "unidad_suelo": c.unidad_suelo,
                "pendiente": c.pendiente,
                "intercepto": c.intercepto,
                "n": c.n,
                "r2": c.r2,
                "rmse": c.rmse,
                "sesgo": c.sesgo,
                "vigencia": c.vigencia.isoformat() if c.vigencia else None,
                "activa": c.activa,
                "responsable": c.responsable,
            }
            for c in calibraciones
        ],
        "total": len(calibraciones),
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
