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
import agroia_backend.models.auditoria  # noqa: F401
import agroia_backend.models.chat_memoria  # noqa: F401
import agroia_backend.models.ciclo_lote  # noqa: F401
import agroia_backend.models.labor  # noqa: F401
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
from agroia_backend.api.alertas import router as alertas_router
from agroia_backend.api.auditoria import router as auditoria_router
from agroia_backend.api.catalogo import router as catalogo_router
from agroia_backend.api.chat import router as chat_router
from agroia_backend.api.ciclos import router as ciclos_router
from agroia_backend.api.dashboard import router as dashboard_router
from agroia_backend.api.demo import router as demo_router
from agroia_backend.api.fincas import router as fincas_router
from agroia_backend.api.iot import router as iot_router
from agroia_backend.api.labores import router as labores_router
from agroia_backend.api.location import router as location_router
from agroia_backend.api.ml import router as ml_router
from agroia_backend.api.recomendaciones import router as recomendaciones_router
from agroia_backend.api.reportes import router as reportes_router
from agroia_backend.api.sensor_api import router as sensor_api_router
from agroia_backend.api.sig import router as sig_router
from agroia_backend.api.usuarios import router as usuarios_router

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
    yield
    clima_task.cancel()
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
app.include_router(demo_router)
# app.include_router(catalogo_router, prefix="/api/v1")
# app.include_router(usuarios_router, prefix="/api/v1")
# app.include_router(dashboards_router, prefix="/api/v1")


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
                and not path.startswith("/openapi") and not path.startswith("/redoc"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response

    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
else:
    logger.warning("frontend_dir_no_encontrado", path=_FRONTEND_DIR)
