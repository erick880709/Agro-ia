"""Restablecimiento de datos para demostración (finca demo + sensor real).

Conserva únicamente las lecturas capturadas con el sensor real
(`esp32-npk-001`), elimina el resto de datos operativos de prueba
(fincas, lotes, recomendaciones, chat, dispositivos de prueba) y crea
una finca demo completa asociada a esos datos reales.

No toca: usuarios/roles, catálogo de cultivos, fichas técnicas ni
reglas agronómicas.
"""

import uuid as uuid_mod
from datetime import datetime, timezone

from agroia.logging import get_logger
from sqlalchemy import delete, or_, select, text, update

from agroia_backend.models.aceptacion_recomendacion import AceptacionRecomendacion
from agroia_backend.models.chat_memoria import ChatMemoria
from agroia_backend.models.dispositivo_iot import DispositivoIoT
from agroia_backend.models.finca import Finca, TipoRiego
from agroia_backend.models.lote import Lote, Pedregosidad
from agroia_backend.models.recomendacion import Recomendacion
from agroia_backend.models.sensor_reading import SensorReading
from agroia_backend.models.usuario import RolUsuario, Usuario

logger = get_logger(__name__)

SENSOR_REAL = "esp32-npk-001"


async def restablecer_demo(db) -> dict:
    """Limpia los datos operativos y crea la finca demo completa."""
    await db.execute(text("SET LOCAL search_path TO public, agroia"))

    # 1) Conversación, feedback y recomendaciones previas
    await db.execute(delete(ChatMemoria))
    await db.execute(delete(AceptacionRecomendacion))
    await db.execute(delete(Recomendacion))

    # 2) Lecturas: solo las del sensor real (NULL = carga de archivo)
    await db.execute(
        delete(SensorReading).where(
            or_(
                SensorReading.sensor_id != SENSOR_REAL,
                SensorReading.sensor_id.is_(None),
            )
        )
    )

    # 3) Dispositivos: solo el sensor real
    await db.execute(
        delete(DispositivoIoT).where(DispositivoIoT.device_id != SENSOR_REAL)
    )

    # 4) Administrador para la finca demo (usuarios se conservan)
    admin = (
        await db.execute(
            select(Usuario)
            .where(Usuario.rol == RolUsuario.ADMIN)
            .order_by(Usuario.created_at)
            .limit(1)
        )
    ).scalars().first()
    if admin is not None:
        admin_id = admin.id
        tenant_id = admin.tenant_id
    else:
        primer_usuario = (
            await db.execute(select(Usuario).order_by(Usuario.created_at).limit(1))
        ).scalars().first()
        admin_id = primer_usuario.id
        tenant_id = primer_usuario.tenant_id

    # 5) Finca demo completa (se crea ANTES de borrar las fincas viejas,
    #    porque dispositivos/lecturas tienen finca_id NOT NULL)
    demo = Finca(
        id=uuid_mod.uuid4(),
        usuario_id=admin_id,
        tenant_id=tenant_id,
        nombre="Finca Demo — El Vergel",
        departamento="Quindío",
        municipio="Armenia",
        vereda="El Caimo",
        propietario="Productor Demo",
        contacto_telefono="3001234567",
        contacto_email="demo@agroia.com.co",
        latitud=4.5306,
        longitud=-75.6809,
        altitud_msnm=1480,
        area_hectareas=2.5,
        area_declarada_ha=2.5,
        tipo_area="finca_completa",
        tiene_multiples_lotes=False,
        largo_metros=125,
        ancho_metros=200,
        pendiente_pct=8,
        drenaje="Bueno",
        fuente_geolocalizacion="gps_navegador",
        precision_gps=3.0,
        fecha_georreferenciacion=datetime.now(timezone.utc),
        coordenadas_google="4.5306,-75.6809",
        validacion_laboratorio=True,
        cultivo_sembrado="Café",
        edad_anos=4,
        etapa_fenologica="Fructificación",
        tipo_riego=TipoRiego.GOTEO,
        historial_agronomico={
            "cultivo_anterior": "Plátano",
            "fertilizacion": "10-30-10 fraccionado, 2 aplicaciones/año",
            "encalado": "1 t/ha cal dolomítica (hace 2 años)",
            "notas": "Café variedad Castillo, sombrío con plátano",
        },
    )
    db.add(demo)
    await db.flush()

    lote = Lote(
        id=uuid_mod.uuid4(),
        finca_id=demo.id,
        nombre="Lote principal",
        area_ha=2.5,
        profundidad_suelo_cm=100,
        pedregosidad=Pedregosidad.NINGUNA,
        activo=True,
    )
    db.add(lote)

    # 6) Reasociar el sensor real y sus lecturas a la finca demo
    await db.execute(
        update(DispositivoIoT)
        .where(DispositivoIoT.device_id == SENSOR_REAL)
        .values(finca_id=demo.id)
    )
    await db.execute(
        update(SensorReading)
        .where(SensorReading.sensor_id == SENSOR_REAL)
        .values(finca_id=demo.id)
    )

    # 7) Borrar lotes y fincas viejas (conservando la demo)
    await db.execute(delete(Lote).where(Lote.finca_id != demo.id))
    await db.execute(delete(Finca).where(Finca.id != demo.id))

    await db.commit()

    n_lecturas = (
        await db.execute(
            select(SensorReading.id).where(SensorReading.sensor_id == SENSOR_REAL)
        )
    ).scalars().all()
    n_fincas = (await db.execute(select(Finca.id))).scalars().all()
    logger.info(
        "demo_restablecida",
        finca_demo=str(demo.id),
        lecturas_conservadas=len(n_lecturas),
        fincas_restantes=len(n_fincas),
    )
    return {
        "finca_demo_id": str(demo.id),
        "finca_demo": demo.nombre,
        "lecturas_conservadas": len(n_lecturas),
        "dispositivo_conservado": SENSOR_REAL,
        "fincas_restantes": len(n_fincas),
    }
