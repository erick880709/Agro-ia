"""AgroIA Auth Service — Autenticación JWT + OAuth2 + RBAC."""

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
    logger.info("auth_starting")
    yield
    logger.info("auth_stopping")

app = FastAPI(title="AgroIA Auth", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(health_router, prefix="/api/v1")
register_error_handlers(app)
