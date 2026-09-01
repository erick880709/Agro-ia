"""Restablecimiento de datos para demostración.

Limpia los datos operativos y siembra un set de demostración completo:

  - **2 ejemplos completos** (Café y Aguacate): lote, lectura de laboratorio
    de 18 variables, cuadrícula de muestreo 3×3 con posiciones (mapa de
    calor y plano del lote), labores de trabajo y ciclos cerrados — todo lo
    necesario para generar recomendaciones y el reporte completo.
  - **6 fincas en otras etapas fenológicas** (Café vegetativa, Café
    floración, Cacao fructificación, Tomate vegetativa, Maíz cosecha y
    Plátano) con datos parciales para explorar las vistas por etapa.
  - Precios de insumos y de cosecha para que el plan económico (ROI) y la
    inteligencia de mercado funcionen de inmediato.
  - Conserva las lecturas del sensor real (`esp32-npk-001`) reasociadas a la
    finca demo de café.

No toca: usuarios/roles, catálogo de cultivos, fichas técnicas ni reglas
agronómicas. Idempotente: puede ejecutarse varias veces.
"""

import uuid as uuid_mod
from datetime import date, datetime, timedelta, timezone

from agroia.logging import get_logger
from sqlalchemy import delete, or_, select, text, update

from agroia_backend.models.aceptacion_recomendacion import AceptacionRecomendacion
from agroia_backend.models.alerta_climatica import AlertaClimatica
from agroia_backend.models.chat_memoria import ChatMemoria
from agroia_backend.models.ciclo_lote import CicloLote
from agroia_backend.models.comision import Comision
from agroia_backend.models.cultivo import Cultivo
from agroia_backend.models.discordancia import Discordancia
from agroia_backend.models.dispositivo_iot import DispositivoIoT
from agroia_backend.models.finca import Finca, TipoRiego
from agroia_backend.models.finca_usuario import FincaUsuario
from agroia_backend.models.labor import Labor
from agroia_backend.models.lote import Lote, Pedregosidad
from agroia_backend.models.precio_cosecha import PrecioCosecha
from agroia_backend.models.precio_insumo import PrecioInsumo
from agroia_backend.models.recomendacion import Recomendacion
from agroia_backend.models.sensor_reading import SensorReading, TexturaSuelo
from agroia_backend.models.usuario import RolUsuario, Usuario
from agroia_backend.models.vision_diagnostico import VisionDiagnostico

logger = get_logger(__name__)

SENSOR_REAL = "esp32-npk-001"

# UUIDs fijos para los ejemplos completos (compatibles con semillas y tests).
UUID_VERGEL = uuid_mod.UUID("3a47d0c6-fb00-4106-91ba-0a707f612e86")
UUID_NARANJOS = uuid_mod.UUID("8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936")

# ── Lecturas de laboratorio completas (18 variables de suelo) ──

_LECTURA_CAFE = dict(
    ph=5.6, nitrogeno=42.0, fosforo=26.0, potasio=310.0,
    calcio=1250.0, magnesio=290.0, azufre=18.0,
    hierro=78.0, manganeso=34.0, zinc=7.2, cobre=2.1, boro=1.05,
    materia_organica=5.1, cic=13.2,
    textura=TexturaSuelo.FRANCO_ARCILLOSA,
    humedad=30.0, temperatura_suelo=21.5, conductividad_electrica=0.9,
    humedad_ambiental=76.0, temperatura_ambiental=24.0,
)

_LECTURA_AGUACATE = dict(
    ph=5.9, nitrogeno=38.0, fosforo=27.0, potasio=265.0,
    calcio=1380.0, magnesio=305.0, azufre=21.0,
    hierro=66.0, manganeso=29.0, zinc=5.4, cobre=2.3, boro=1.15,
    materia_organica=6.3, cic=14.1,
    textura=TexturaSuelo.FRANCO_LIMOSA,
    humedad=33.0, temperatura_suelo=16.8, conductividad_electrica=0.7,
    humedad_ambiental=70.0, temperatura_ambiental=18.0,
)

_LECTURA_PARCIAL = dict(
    ph=5.8, nitrogeno=35.0, fosforo=22.0, potasio=280.0,
    humedad=28.0, temperatura_suelo=20.0, calidad="OK",
)

_CUADRICULA_3X3 = [
    (20.0, 30.0), (20.0, 100.0), (20.0, 170.0),
    (62.0, 30.0), (62.0, 100.0), (62.0, 170.0),
    (105.0, 30.0), (105.0, 100.0), (105.0, 170.0),
]

# Variación determinística por punto (el mapa de calor muestra gradiente).
_FACTOR_PUNTO = [0.94, 0.97, 1.0, 0.96, 1.02, 1.05, 0.98, 1.0, 1.03]

# ── Insumos con precio vigente (COP/kg) ──

_INSUMOS = [
    ("Urea 46%", 3200.0),
    ("DAP 18-46-0", 4200.0),
    ("KCl 0-0-60", 3800.0),
    ("10-30-10", 3900.0),
    ("Cal dolomítica", 600.0),
    ("Kieserita (Mg/S)", 1800.0),
    ("Nitrato de calcio", 2800.0),
    ("Nitrato de potasio", 4500.0),
    ("Sulfato de magnesio", 2200.0),
    ("Sulfato de zinc", 6500.0),
    ("Boro (Borax)", 5200.0),
    ("Sulfato de cobre", 14000.0),
]

# ── Precios de cosecha por cultivo/departamento ──

_PRECIOS_COSECHA = [
    ("Café", "Quindío", 7800.0, 4.2),
    ("Café", "Huila", 8200.0, 4.5),
    ("Café", "Caldas", 7950.0, 4.1),
    ("Aguacate", "Antioquia", 5200.0, 8.0),
    ("Cacao", "Santander", 11500.0, 0.9),
    ("Tomate", "Cundinamarca", 2800.0, 45.0),
    ("Maíz", "Tolima", 1900.0, 6.5),
    ("Plátano", "Quindío", 1400.0, 14.0),
]


async def _cultivo_por_nombre(db, nombre: str) -> Cultivo | None:
    return (
        await db.execute(select(Cultivo).where(Cultivo.nombre == nombre))
    ).scalar_one_or_none()


def _lectura(finca_id, sensor_id, ts, valores: dict, pos_x=None, pos_y=None) -> SensorReading:
    return SensorReading(
        finca_id=finca_id,
        ts=ts,
        sensor_id=sensor_id,
        pos_x=pos_x,
        pos_y=pos_y,
        **valores,
    )


async def _upsert_finca(db, cfg: dict) -> Finca:
    """Crea o actualiza la finca (los ids fijos se reutilizan)."""
    finca_id = cfg.get("id")
    finca = None
    if finca_id is not None:
        finca = (
            await db.execute(select(Finca).where(Finca.id == finca_id))
        ).scalar_one_or_none()
    if finca is None:
        finca = Finca(id=finca_id)
        db.add(finca)
    finca.usuario_id = cfg["usuario_id"]
    finca.tenant_id = cfg["tenant_id"]
    finca.nombre = cfg["nombre"]
    finca.departamento = cfg["departamento"]
    finca.municipio = cfg["municipio"]
    finca.vereda = cfg["vereda"]
    finca.propietario = cfg["propietario"]
    finca.contacto_telefono = cfg["contacto_telefono"]
    finca.contacto_email = cfg["contacto_email"]
    finca.latitud = cfg["latitud"]
    finca.longitud = cfg["longitud"]
    finca.altitud_msnm = cfg["altitud_msnm"]
    finca.area_hectareas = cfg["area_hectareas"]
    finca.area_declarada_ha = cfg["area_hectareas"]
    finca.tipo_area = "finca_completa"
    finca.tiene_multiples_lotes = False
    finca.largo_metros = cfg["largo_metros"]
    finca.ancho_metros = cfg["ancho_metros"]
    finca.pendiente_pct = cfg.get("pendiente_pct", 8)
    finca.drenaje = cfg.get("drenaje", "Bueno")
    finca.fuente_geolocalizacion = "gps_navegador"
    finca.precision_gps = cfg.get("precision_gps", 3.0)
    finca.fecha_georreferenciacion = datetime.now(timezone.utc)
    finca.coordenadas_google = f"{cfg['latitud']},{cfg['longitud']}"
    finca.validacion_laboratorio = cfg.get("validacion_laboratorio", True)
    finca.cultivo_sembrado = cfg["cultivo"]
    finca.edad_anos = cfg["edad_anos"]
    finca.etapa_fenologica = cfg["etapa"]
    finca.tipo_riego = cfg["tipo_riego"]
    finca.historial_agronomico = cfg.get("historial") or {}
    await db.flush()
    return finca


async def _sembrar_lecturas(db, finca_id, base: dict, sensor_grid: str) -> None:
    """Cuadrícula 3×3 con variación determinística + lectura central exacta."""
    hoy = datetime.now(timezone.utc)
    for (x, y), factor in zip(_CUADRICULA_3X3, _FACTOR_PUNTO):
        valores = dict(base)
        for clave in ("nitrogeno", "fosforo", "potasio", "calcio", "magnesio", "ph"):
            if clave in valores and isinstance(valores[clave], (int, float)):
                valores[clave] = round(valores[clave] * factor, 2)
        db.add(_lectura(finca_id, sensor_grid, hoy - timedelta(days=2), valores, x, y))
    db.add(_lectura(finca_id, sensor_grid, hoy, base, 62.0, 100.0))


async def _sembrar_labores(db, lote_id, labores: list[dict]) -> None:
    hoy = datetime.now(timezone.utc).date()
    for lab in labores:
        db.add(Labor(
            lote_id=lote_id,
            titulo=lab["titulo"],
            tipo=lab.get("tipo", "Fertilización"),
            producto=lab.get("producto"),
            dosis_kg_ha=lab.get("dosis_kg_ha"),
            fecha_programada=lab.get("fecha_programada") or (hoy + timedelta(days=lab.get("en_dias", 2))),
            fecha_ejecucion=lab.get("fecha_ejecucion"),
            estado=lab.get("estado", "Pendiente"),
            observaciones_ejecucion=lab.get("observaciones"),
        ))


async def _sembrar_ciclos(db, lote_id, nombre_cultivo: str, ciclos: list[dict]) -> None:
    cultivo = await _cultivo_por_nombre(db, nombre_cultivo)
    if cultivo is None:
        return
    for ciclo in ciclos:
        db.add(CicloLote(
            lote_id=lote_id,
            cultivo_id=cultivo.id,
            fecha_siembra=ciclo["fecha_siembra"],
            fecha_cosecha=ciclo.get("fecha_cosecha"),
            variedad=ciclo.get("variedad"),
            densidad_siembra_plantas_ha=ciclo.get("densidad_siembra_plantas_ha"),
            rendimiento_tn_ha=ciclo.get("rendimiento_tn_ha"),
            calidad_cosecha=ciclo.get("calidad_cosecha"),
            aplicaciones=ciclo.get("aplicaciones"),
            practicas_riego=ciclo.get("practicas_riego"),
            observaciones=ciclo.get("observaciones"),
        ))


async def _lote_para(db, finca_id, cfg: dict, completo: bool) -> Lote:
    lote = Lote(
        id=uuid_mod.uuid4(),
        finca_id=finca_id,
        nombre="Lote principal",
        area_ha=cfg["area_hectareas"],
        profundidad_suelo_cm=100 if completo else 60,
        pedregosidad=Pedregosidad.NINGUNA if completo else Pedregosidad.MODERADA,
        activo=True,
    )
    db.add(lote)
    await db.flush()
    return lote


async def _crear_ejemplo_completo(db, cfg: dict) -> str:
    finca = await _upsert_finca(db, cfg)
    lote = await _lote_para(db, finca.id, cfg, completo=True)
    await _sembrar_lecturas(db, finca.id, cfg["lectura_base"], cfg["sensor_grid"])
    await _sembrar_labores(db, lote.id, cfg["labores"])
    await _sembrar_ciclos(db, lote.id, cfg["cultivo"], cfg["ciclos"])
    db.add(Comision(
        finca_id=finca.id,
        servicio=f"Toma de muestras — {cfg['cultivo']} (demo)",
        fecha_asignacion=date.today() - timedelta(days=12),
        fecha_inicio_tomas=date.today() - timedelta(days=10),
        fecha_fin_tomas=date.today() - timedelta(days=8),
        estado=cfg.get("estado_comision", "en_recomendacion"),
        valor_comision_cop=450000.0,
        observaciones="Comisión demo: muestreo 3×3 + lectura de laboratorio.",
    ))
    return str(finca.id)


async def _crear_finca_etapa(db, cfg: dict) -> str:
    cfg["validacion_laboratorio"] = False
    finca = await _upsert_finca(db, cfg)
    lote = await _lote_para(db, finca.id, cfg, completo=False)
    db.add(_lectura(
        finca.id, f"{cfg['slug']}-sensor",
        datetime.now(timezone.utc) - timedelta(days=1),
        dict(_LECTURA_PARCIAL), 50.0, 50.0,
    ))
    if cfg.get("labores"):
        await _sembrar_labores(db, lote.id, cfg["labores"])
    db.add(Comision(
        finca_id=finca.id,
        servicio=f"Toma de muestras — {cfg['cultivo']} (demo)",
        fecha_asignacion=date.today() - timedelta(days=3),
        estado=cfg.get("estado_comision", "asignada"),
        valor_comision_cop=380000.0,
        observaciones="Comisión demo: pendiente de toma de muestras.",
    ))
    return str(finca.id)


async def restablecer_demo(db) -> dict:
    """Limpia los datos operativos y crea el set de demostración completo."""
    await db.execute(text("SET LOCAL search_path TO public, agroia"))
    hoy = datetime.now(timezone.utc)

    # ── 1) Limpieza de datos operativos (respetando claves foráneas) ──
    await db.execute(delete(ChatMemoria))
    await db.execute(delete(Discordancia))
    await db.execute(delete(AceptacionRecomendacion))
    await db.execute(delete(Recomendacion))
    await db.execute(delete(Labor))
    await db.execute(delete(CicloLote))
    await db.execute(delete(AlertaClimatica))
    await db.execute(delete(VisionDiagnostico))
    await db.execute(delete(PrecioCosecha))
    await db.execute(delete(FincaUsuario))
    await db.execute(delete(Comision))
    await db.execute(delete(Lote))
    await db.execute(
        delete(SensorReading).where(
            or_(
                SensorReading.sensor_id != SENSOR_REAL,
                SensorReading.sensor_id.is_(None),
            )
        )
    )
    await db.execute(
        delete(DispositivoIoT).where(DispositivoIoT.device_id != SENSOR_REAL)
    )

    # ── 2) Actores ──
    admin = (
        await db.execute(
            select(Usuario).where(Usuario.rol == RolUsuario.ADMIN)
            .order_by(Usuario.id).limit(1)
        )
    ).scalars().first()
    if admin is None:
        admin = (
            await db.execute(select(Usuario).order_by(Usuario.id).limit(1))
        ).scalars().first()
    agronomo = (
        await db.execute(select(Usuario).where(Usuario.rol == RolUsuario.AGRONOMO))
    ).scalars().first()
    juan = (
        await db.execute(select(Usuario).where(Usuario.email == "cliente@agroia.co"))
    ).scalars().first()
    maria = (
        await db.execute(select(Usuario).where(Usuario.email == "maria.cliente@agroia.co"))
    ).scalars().first()

    tenant_id = admin.tenant_id if admin else uuid_mod.UUID("11111111-1111-1111-1111-111111111111")
    admin_id = admin.id if admin else None

    # ── 3) Precios de insumos (asegurar; no se borran) ──
    for producto, precio in _INSUMOS:
        existe = (
            await db.execute(select(PrecioInsumo).where(PrecioInsumo.producto == producto))
        ).scalar_one_or_none()
        if existe is None:
            db.add(PrecioInsumo(
                producto=producto, precio_kg_cop=precio,
                fecha_actualizacion=hoy.date(), fuente="Cotización AgroIA demo",
            ))

    # ── 4) Precios de cosecha ──
    for nombre_cultivo, departamento, precio, rendimiento in _PRECIOS_COSECHA:
        cultivo = await _cultivo_por_nombre(db, nombre_cultivo)
        if cultivo is None:
            continue
        db.add(PrecioCosecha(
            cultivo_id=cultivo.id,
            departamento=departamento,
            precio_promedio_cop_kg=precio,
            rendimiento_promedio_t_ha=rendimiento,
            fecha_actualizacion=hoy.date(),
            fuente="Ingreso manual (demo)",
        ))

    # ── 5) Ejemplo completo 1: Café (El Vergel, Quindío) ──
    await _crear_ejemplo_completo(db, {
        "id": UUID_VERGEL,
        "usuario_id": admin_id, "tenant_id": tenant_id,
        "nombre": "Finca Demo — El Vergel",
        "departamento": "Quindío", "municipio": "Armenia", "vereda": "El Caimo",
        "propietario": "Productor Demo", "contacto_telefono": "3001234567",
        "contacto_email": "demo@agroia.com.co",
        "latitud": 4.5306, "longitud": -75.6809, "altitud_msnm": 1480,
        "area_hectareas": 2.5, "largo_metros": 125.0, "ancho_metros": 200.0,
        "pendiente_pct": 8, "drenaje": "Bueno",
        "cultivo": "Café", "edad_anos": 4, "etapa": "Fructificación",
        "tipo_riego": TipoRiego.GOTEO,
        "lectura_base": _LECTURA_CAFE, "sensor_grid": "demo-vergel-grid",
        "historial": {
            "cultivo_anterior": "Plátano",
            "fertilizacion": "10-30-10 fraccionado, 2 aplicaciones/año",
            "encalado": "1 t/ha cal dolomítica (hace 2 años)",
            "notas": "Café variedad Castillo, sombrío con plátano",
        },
        "labores": [
            {"titulo": "Fertilización edáfica café", "tipo": "Fertilización",
             "producto": "10-30-10", "dosis_kg_ha": 120.0, "en_dias": 2, "estado": "Pendiente"},
            {"titulo": "Control preventivo de roya", "tipo": "Control Fitosanitario",
             "producto": "Oxicloruro de cobre", "dosis_kg_ha": 2.0, "en_dias": 5, "estado": "Pendiente"},
            {"titulo": "Mantenimiento de goteo", "tipo": "Riego",
             "producto": None, "dosis_kg_ha": None,
             "fecha_ejecucion": hoy.date() - timedelta(days=2), "estado": "Completada",
             "observaciones": "Líneas revisadas, sin fugas."},
        ],
        "ciclos": [
            {"fecha_siembra": date(2022, 5, 15), "fecha_cosecha": date(2023, 6, 30),
             "variedad": "Castillo", "densidad_siembra_plantas_ha": 5000,
             "rendimiento_tn_ha": 4.2, "calidad_cosecha": "Premium",
             "aplicaciones": [{"producto": "Urea", "dosis_kg_ha": 80, "tipo": "Fertilización"}],
             "practicas_riego": "Goteo", "observaciones": "Ciclo estable."},
            {"fecha_siembra": date(2023, 7, 20), "fecha_cosecha": date(2024, 8, 10),
             "variedad": "Castillo", "densidad_siembra_plantas_ha": 5000,
             "rendimiento_tn_ha": 4.8, "calidad_cosecha": "Premium",
             "aplicaciones": [{"producto": "10-30-10", "dosis_kg_ha": 120, "tipo": "Fertilización"}],
             "practicas_riego": "Goteo", "observaciones": "Mejor manejo de sombrío."},
        ],
    })

    # ── 6) Ejemplo completo 2: Aguacate (Los Naranjos, Antioquia) ──
    await _crear_ejemplo_completo(db, {
        "id": UUID_NARANJOS,
        "usuario_id": admin_id, "tenant_id": tenant_id,
        "nombre": "Los Naranjos",
        "departamento": "Antioquia", "municipio": "Rionegro", "vereda": "San Antonio",
        "propietario": "Familia Gómez", "contacto_telefono": "3102223344",
        "contacto_email": "naranjos@agroia.com.co",
        "latitud": 6.1536, "longitud": -75.3740, "altitud_msnm": 2120,
        "area_hectareas": 3.5, "largo_metros": 175.0, "ancho_metros": 200.0,
        "pendiente_pct": 12, "drenaje": "Regular",
        "cultivo": "Aguacate", "edad_anos": 5, "etapa": "Floración",
        "tipo_riego": TipoRiego.ASPERSION,
        "lectura_base": _LECTURA_AGUACATE, "sensor_grid": "demo-naranjos-grid",
        "historial": {
            "cultivo_anterior": "Papa",
            "fertilizacion": "Nitrato de calcio + KCl, 3 aplicaciones/año",
            "encalado": "500 kg/ha cal dolomítica (hace 1 año)",
            "notas": "Aguacate Hass injertado, riego por aspersión",
        },
        "labores": [
            {"titulo": "Fertilización de floración", "tipo": "Fertilización",
             "producto": "Nitrato de calcio", "dosis_kg_ha": 90.0, "en_dias": 1, "estado": "Pendiente"},
            {"titulo": "Monitoreo de trips", "tipo": "Control Fitosanitario",
             "producto": None, "dosis_kg_ha": None, "en_dias": 3, "estado": "En Progreso",
             "observaciones": "Trampas instaladas en 4 puntos del lote."},
            {"titulo": "Riego por aspersión", "tipo": "Riego",
             "producto": None, "dosis_kg_ha": None,
             "fecha_ejecucion": hoy.date() - timedelta(days=1), "estado": "Completada"},
        ],
        "ciclos": [
            {"fecha_siembra": date(2021, 3, 1), "fecha_cosecha": date(2025, 11, 30),
             "variedad": "Hass", "densidad_siembra_plantas_ha": 625,
             "rendimiento_tn_ha": 12.5, "calidad_cosecha": "Premium",
             "aplicaciones": [{"producto": "Nitrato de potasio", "dosis_kg_ha": 60, "tipo": "Fertilización"}],
             "practicas_riego": "Aspersión", "observaciones": "Ciclo de 5 años."},
        ],
    })

    # ── 7) Fincas en otras etapas fenológicas ──
    etapa_cfg = [
        {"slug": "villa-cafe", "nombre": "Villa Café", "cultivo": "Café",
         "departamento": "Huila", "municipio": "Garzón", "vereda": "La Jagua",
         "propietario": "Cooperativa Huila Verde", "contacto_telefono": "3207654321",
         "contacto_email": "cooperativa@example.com",
         "latitud": 2.1960, "longitud": -75.6270, "altitud_msnm": 1500,
         "area_hectareas": 3.2, "largo_metros": 200.0, "ancho_metros": 160.0,
         "edad_anos": 1, "etapa": "Vegetativa", "tipo_riego": TipoRiego.GOTEO,
         "labores": [{"titulo": "Fertilización de levante", "tipo": "Fertilización",
                      "producto": "Urea 46%", "dosis_kg_ha": 70.0, "en_dias": 4, "estado": "Pendiente"}]},
        {"slug": "el-cafetal", "nombre": "El Cafetal", "cultivo": "Café",
         "departamento": "Caldas", "municipio": "Chinchiná", "vereda": "La Floresta",
         "propietario": "Hacienda Caldas", "contacto_telefono": "3115556677",
         "contacto_email": "cafetal@agroia.com.co",
         "latitud": 4.9828, "longitud": -75.6036, "altitud_msnm": 1378,
         "area_hectareas": 5.0, "largo_metros": 250.0, "ancho_metros": 200.0,
         "edad_anos": 3, "etapa": "Floración", "tipo_riego": TipoRiego.SECANO},
        {"slug": "cacao-valle", "nombre": "Cacao del Valle", "cultivo": "Cacao",
         "departamento": "Santander", "municipio": "San Vicente de Chucurí", "vereda": "Guamales",
         "propietario": "Asociación Cacaotera", "contacto_telefono": "3168889900",
         "contacto_email": "cacao@agroia.com.co",
         "latitud": 6.8810, "longitud": -73.4090, "altitud_msnm": 700,
         "area_hectareas": 4.0, "largo_metros": 200.0, "ancho_metros": 200.0,
         "edad_anos": 6, "etapa": "Fructificación", "tipo_riego": TipoRiego.GRAVEDAD,
         "labores": [{"titulo": "Control de monilia", "tipo": "Control Fitosanitario",
                      "producto": "Fungicida cúprico", "dosis_kg_ha": 1.5, "en_dias": 2, "estado": "Pendiente"}]},
        {"slug": "huerta-primavera", "nombre": "Huerta La Primavera", "cultivo": "Tomate",
         "departamento": "Cundinamarca", "municipio": "Fusagasugá", "vereda": "La Venta",
         "propietario": "María Cliente", "contacto_telefono": "3131112233",
         "contacto_email": "maria.cliente@agroia.co",
         "latitud": 4.3438, "longitud": -74.3678, "altitud_msnm": 1720,
         "area_hectareas": 1.0, "largo_metros": 100.0, "ancho_metros": 100.0,
         "edad_anos": 0.2, "etapa": "Vegetativa", "tipo_riego": TipoRiego.GOTEO,
         "labores": [{"titulo": "Tutorado de plantas", "tipo": "Riego",
                      "producto": None, "dosis_kg_ha": None, "en_dias": 1, "estado": "En Progreso"}]},
        {"slug": "los-cereales", "nombre": "Los Cereales", "cultivo": "Maíz",
         "departamento": "Tolima", "municipio": "Espinal", "vereda": "La Chamba",
         "propietario": "AgroTolima SAS", "contacto_telefono": "3154445566",
         "contacto_email": "cereales@agroia.com.co",
         "latitud": 4.1495, "longitud": -74.8899, "altitud_msnm": 320,
         "area_hectareas": 8.0, "largo_metros": 400.0, "ancho_metros": 200.0,
         "edad_anos": 0.4, "etapa": "Cosecha", "tipo_riego": TipoRiego.SECANO},
        {"slug": "la-platanera", "nombre": "La Platanera", "cultivo": "Plátano",
         "departamento": "Quindío", "municipio": "Montenegro", "vereda": "Pueblo Tapao",
         "propietario": "Finca Tradicional", "contacto_telefono": "3177778899",
         "contacto_email": "platano@agroia.com.co",
         "latitud": 4.5666, "longitud": -75.7507, "altitud_msnm": 1294,
         "area_hectareas": 2.0, "largo_metros": 140.0, "ancho_metros": 140.0,
         "edad_anos": 2, "etapa": "Vegetativa", "tipo_riego": TipoRiego.GRAVEDAD},
    ]
    ids_etapas: list[str] = []
    for cfg in etapa_cfg:
        cfg_completo = {"usuario_id": admin_id, "tenant_id": tenant_id, **cfg}
        ids_etapas.append(await _crear_finca_etapa(db, cfg_completo))

    # ── 8) Reasociar sensor real a El Vergel y borrar fincas viejas ──
    await db.execute(
        update(DispositivoIoT).where(DispositivoIoT.device_id == SENSOR_REAL)
        .values(finca_id=UUID_VERGEL)
    )
    await db.execute(
        update(SensorReading).where(SensorReading.sensor_id == SENSOR_REAL)
        .values(finca_id=UUID_VERGEL)
    )
    nuevos_ids = [UUID_VERGEL, UUID_NARANJOS, *[uuid_mod.UUID(i) for i in ids_etapas]]
    await db.execute(delete(Finca).where(Finca.id.not_in(nuevos_ids)))

    # ── 9) Asociaciones finca ↔ usuario ──
    asociaciones: list[tuple[uuid_mod.UUID, uuid_mod.UUID]] = []
    if agronomo is not None:
        asociaciones.extend((agronomo.id, fid) for fid in nuevos_ids)
    if juan is not None:
        for fid in (UUID_VERGEL, UUID_NARANJOS, uuid_mod.UUID(ids_etapas[1])):
            asociaciones.append((juan.id, fid))
    if maria is not None:
        for fid in (UUID_VERGEL, uuid_mod.UUID(ids_etapas[3])):
            asociaciones.append((maria.id, fid))
    for uid, fid in asociaciones:
        db.add(FincaUsuario(finca_id=fid, usuario_id=uid))

    await db.commit()

    resumen = {
        "fincas_restantes": len(nuevos_ids),
        "ejemplos_completos": [
            {"id": str(UUID_VERGEL), "nombre": "Finca Demo — El Vergel", "cultivo": "Café", "etapa": "Fructificación"},
            {"id": str(UUID_NARANJOS), "nombre": "Los Naranjos", "cultivo": "Aguacate", "etapa": "Floración"},
        ],
        "fincas_por_etapa": [
            {"id": id_, "nombre": cfg["nombre"], "cultivo": cfg["cultivo"], "etapa": cfg["etapa"]}
            for id_, cfg in zip(ids_etapas, etapa_cfg)
        ],
        "dispositivo_conservado": SENSOR_REAL,
        "precios_insumos": len(_INSUMOS),
        "precios_cosecha": len(_PRECIOS_COSECHA),
        "comisiones": len(nuevos_ids),
        "comisiones_en_recomendacion": 2,
    }
    logger.info("demo_restablecida", fincas=resumen["fincas_restantes"])
    return resumen
