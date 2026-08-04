"""AgroIA Backend — Servicio principal de negocio.

Expone la API REST para recomendaciones, catálogo de cultivos,
gestión de usuarios, dashboards, reportes e ingesta de datos externos.

Estrategia: Monolito modular con routers por dominio.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agroia.config import get_settings
from agroia.errors import register_error_handlers
from agroia.health import router as health_router
from agroia.logging import get_logger, setup_logging

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

app.include_router(recomendaciones_router)
app.include_router(catalogo_router)
app.include_router(iot_router)
app.include_router(dashboard_router)
app.include_router(usuarios_router)
# app.include_router(catalogo_router, prefix="/api/v1")
# app.include_router(usuarios_router, prefix="/api/v1")
# app.include_router(dashboards_router, prefix="/api/v1")
