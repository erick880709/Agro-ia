"""AgroIA Backend — Servicio principal de negocio.

Expone la API REST para recomendaciones, catálogo de cultivos,
gestión de usuarios, dashboards, reportes e ingesta de datos externos.

Estrategia: Monolito modular con routers por dominio.
"""

import os
from contextlib import asynccontextmanager

from agroia.config import get_settings
from agroia.errors import register_error_handlers
from agroia.health import router as health_router
from agroia.logging import get_logger, setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ── Registro de modelos en Base.metadata ──
# Estos imports garantizan que SQLAlchemy conozca todas las tablas al
# resolver claves foráneas entre modelos (ej. dispositivos_iot → fincas).
import agroia_backend.models.aceptacion_recomendacion  # noqa: F401
import agroia_backend.models.alerta_climatica  # noqa: F401
import agroia_backend.models.analisis_agua_riego  # noqa: F401
import agroia_backend.models.auditoria  # noqa: F401
import agroia_backend.models.precio_insumo  # noqa: F401
import agroia_backend.models.checklist_bpa  # noqa: F401
import agroia_backend.models.chat_memoria  # noqa: F401
import agroia_backend.models.ciclo_lote  # noqa: F401
import agroia_backend.models.compatibilidad_rotacion  # noqa: F401
import agroia_backend.models.curva_extraccion  # noqa: F401
import agroia_backend.models.labor  # noqa: F401
import agroia_backend.models.monitoreo_plaga  # noqa: F401
import agroia_backend.models.preferencia_notificacion  # noqa: F401
import agroia_backend.models.variedad_cultivo  # noqa: F401
import agroia_backend.models.cultivo  # noqa: F401
import agroia_backend.models.discordancia  # noqa: F401
import agroia_backend.models.dispositivo_iot  # noqa: F401
import agroia_backend.models.finca  # noqa: F401
import agroia_backend.models.finca_usuario  # noqa: F401
import agroia_backend.models.metrica_modelo  # noqa: F401
import agroia_backend.models.modelo_ml  # noqa: F401
import agroia_backend.models.recomendacion  # noqa: F401
import agroia_backend.models.regla_agronomica  # noqa: F401
import agroia_backend.models.sensor_reading  # noqa: F401
import agroia_backend.models.usuario  # noqa: F401

from agroia_backend.api.auth import router as auth_router
from agroia_backend.api.admin_precios import router as admin_precios_router
from agroia_backend.api.agua_riego import router as agua_riego_router
from agroia_backend.api.alertas import router as alertas_router
from agroia_backend.api.auditoria import router as auditoria_router
from agroia_backend.api.balance_hidrico import router as balance_hidrico_router
from agroia_backend.api.bpa import router as bpa_router
from agroia_backend.api.catalogo import router as catalogo_router
from agroia_backend.api.chat import router as chat_router
from agroia_backend.api.ciclos import router as ciclos_router
from agroia_backend.api.curvas import router as curvas_router
from agroia_backend.api.dashboard import router as dashboard_router
from agroia_backend.api.demo import router as demo_router
from agroia_backend.api.extensionista import router as extensionista_router
from agroia_backend.api.fincas import router as fincas_router
from agroia_backend.api.iot import router as iot_router
from agroia_backend.api.labores import router as labores_router
from agroia_backend.api.location import router as location_router
from agroia_backend.api.mantenimiento import router as mantenimiento_router
from agroia_backend.api.ml import admin_router as ml_admin_router
from agroia_backend.api.ml import router as ml_router
from agroia_backend.api.notificaciones import router as notificaciones_router
from agroia_backend.api.plagas import router as plagas_router
from agroia_backend.api.recomendaciones import router as recomendaciones_router
from agroia_backend.api.reportes import router as reportes_router
from agroia_backend.api.rotacion import router as rotacion_router
from agroia_backend.api.sensor_api import router as sensor_api_router
from agroia_backend.api.sig import router as sig_router
from agroia_backend.api.usuarios import router as usuarios_router
from agroia_backend.api.variedades import router as variedades_router

settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación."""
    logger.info("backend_starting", environment=settings.environment)
    # Auto-reparación de tipos enum (BDs externas reiniciadas/restauradas)
    from agroia_backend.services.asegurar_enums import asegurar_enums

    try:
        await asegurar_enums()
    except Exception as e:  # noqa: BLE001 — no bloquear el arranque
        logger.error("asegurar_enums_fallo", error=str(e))

    # Reglas agronómicas ampliadas (cobertura completa de variables/cultivos)
    from agroia_backend.services.asegurar_reglas import asegurar_reglas

    try:
        await asegurar_reglas()
    except Exception as e:  # noqa: BLE001 — no bloquear el arranque
        logger.error("asegurar_reglas_fallo", error=str(e))

    # Lecturas históricas con GPS en grados → metros relativos (idempotente)
    from agroia_backend.services.reparacion_geo import reparar_gps_legado

    try:
        await reparar_gps_legado()
    except Exception as e:  # noqa: BLE001 — no bloquear el arranque
        logger.error("reparar_gps_legado_fallo", error=str(e))

    # ── Servicio programado: alertas climáticas proactivas (cada 6 h) ──
    import asyncio

    from agroia.database import async_session_factory

    async def _tarea_clima_periodica():
        await asyncio.sleep(45)  # primer ciclo poco después del arranque
        while True:
            try:
                from agroia_backend.services.clima_alertas import evaluar_todas_fincas

                async with async_session_factory() as db:
                    await evaluar_todas_fincas(db)
            except Exception as e:  # noqa: BLE001 — el ciclo sigue vivo
                logger.error("tarea_clima_error", error=str(e))
            await asyncio.sleep(6 * 3600)  # cada 6 horas

    clima_task = asyncio.create_task(_tarea_clima_periodica())

    # ── Mantenimiento: limpiar imágenes Base64 del chat (cada 24 h) ──
    async def _tarea_mantenimiento():
        await asyncio.sleep(120)  # primer ciclo 2 min después del arranque
        while True:
            try:
                from agroia_backend.services.mantenimiento import limpiar_imagenes_chat
                from agroia_backend.services.notificador_jobs import notificar_labores_proximas

                async with async_session_factory() as db:
                    await limpiar_imagenes_chat(db, dias=90)
                async with async_session_factory() as db:
                    await notificar_labores_proximas(db)
            except Exception as e:  # noqa: BLE001 — el ciclo sigue vivo
                logger.error("tarea_mantenimiento_error", error=str(e))
            await asyncio.sleep(24 * 3600)  # cada 24 horas

    mantenimiento_task = asyncio.create_task(_tarea_mantenimiento())
    yield
    clima_task.cancel()
    mantenimiento_task.cancel()
    logger.info("backend_stopping")


app = FastAPI(
    title="AgroIA Backend API",
    description="Servicio principal de AgroInteligente Colombia",
    version="0.1.0",
    docs_url="/docs" if settings.environment == "development" else None,
    lifespan=lifespan,
)

# ── Middlewares ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health check ──
app.include_router(health_router, prefix="/api/v1")

# ── Estado de modelos ML ──
app.include_router(ml_router, prefix="/api/v1")

# ── Estado de modelos ML ──
app.include_router(ml_router, prefix="/api/v1")

# ── Error handlers ──
register_error_handlers(app)


# ── Routers por dominio ──
app.include_router(recomendaciones_router)
app.include_router(catalogo_router)
app.include_router(chat_router)
app.include_router(iot_router)
app.include_router(dashboard_router)
app.include_router(usuarios_router)
app.include_router(location_router)
app.include_router(fincas_router)
app.include_router(auth_router)
app.include_router(alertas_router)
app.include_router(auditoria_router)
app.include_router(ciclos_router)
app.include_router(labores_router)
app.include_router(reportes_router)
app.include_router(sensor_api_router)
app.include_router(sig_router)
app.include_router(admin_precios_router)
app.include_router(mantenimiento_router)
app.include_router(demo_router)
# ── Módulos v4 (especificación técnica v4) ──
app.include_router(agua_riego_router)
app.include_router(balance_hidrico_router)
app.include_router(bpa_router)
app.include_router(extensionista_router)
app.include_router(notificaciones_router)
app.include_router(plagas_router)
app.include_router(rotacion_router)
app.include_router(ml_admin_router)
# curvas/variedades: expuestas también bajo /api/v1/catalogo (catálogo)
app.include_router(curvas_router, prefix="/api/v1")
app.include_router(curvas_router, prefix="/api/v1/catalogo")
app.include_router(variedades_router, prefix="/api/v1")
app.include_router(variedades_router, prefix="/api/v1/catalogo")
# app.include_router(catalogo_router, prefix="/api/v1")
# app.include_router(usuarios_router, prefix="/api/v1")
# app.include_router(dashboards_router, prefix="/api/v1")


# ── Media (fotos de labores en disco; la BD solo guarda imagen_url) ──
_MEDIA_DIR = os.environ.get("AGROIA_MEDIA_DIR") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "media",
)
os.makedirs(_MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=_MEDIA_DIR), name="media")


# ── Frontend web integrado (SPA estática servida en la raíz) ──
# Debe registrarse al final para que /api/* y /docs tengan prioridad.
_FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "apps",
    "frontend-web",
)
if os.path.isdir(_FRONTEND_DIR):

    @app.middleware("http")
    async def _no_cache_frontend(request, call_next):
        """Fuerza revalidación de los estáticos del frontend.

        Sin esto, tras un deploy el navegador puede combinar HTML nuevo con
        CSS/JS viejos en caché (wizard sin estilos y sin paginación).
        """
        response = await call_next(request)
        path = request.url.path
        if not path.startswith("/api") and not path.startswith("/docs") \
                and not path.startswith("/openapi") and not path.startswith("/redoc") \
                and not path.startswith("/media"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response

    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
else:
    logger.warning("frontend_dir_no_encontrado", path=_FRONTEND_DIR)
