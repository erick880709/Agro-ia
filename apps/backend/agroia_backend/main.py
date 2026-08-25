"""AgroIA Backend — Servicio principal de negocio.

Expone la API REST para recomendaciones, catálogo de cultivos,
gestión de usuarios, dashboards, reportes e ingesta de datos externos.

Estrategia: Monolito modular con routers por dominio.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agroia.config import get_settings
from agroia.errors import register_error_handlers
from agroia.health import router as health_router
from agroia.logging import get_logger, setup_logging

# ── Registro de modelos en Base.metadata ──
# Estos imports garantizan que SQLAlchemy conozca todas las tablas al
# resolver claves foráneas entre modelos (ej. dispositivos_iot → fincas).
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

settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación."""
    logger.info("backend_starting", environment=settings.environment)
    yield
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

# ── Error handlers ──
register_error_handlers(app)


# ── Placeholder routers ──
# Estos serán poblados por builder al generar cada módulo de dominio:
from agroia_backend.api.recomendaciones import router as recomendaciones_router
from agroia_backend.api.catalogo import router as catalogo_router
from agroia_backend.api.iot import router as iot_router
from agroia_backend.api.dashboard import router as dashboard_router
from agroia_backend.api.usuarios import router as usuarios_router
from agroia_backend.api.location import router as location_router
from agroia_backend.api.fincas import router as fincas_router
from agroia_backend.api.auth import router as auth_router
from agroia_backend.api.reportes import router as reportes_router
from agroia_backend.api.sensor_api import router as sensor_api_router

app.include_router(recomendaciones_router)
app.include_router(catalogo_router)
app.include_router(iot_router)
app.include_router(dashboard_router)
app.include_router(usuarios_router)
app.include_router(location_router)
app.include_router(fincas_router)
app.include_router(auth_router)
app.include_router(reportes_router)
app.include_router(sensor_api_router)
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
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
else:
    logger.warning("frontend_dir_no_encontrado", path=_FRONTEND_DIR)
