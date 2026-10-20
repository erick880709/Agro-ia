"""API de interacción por voz — transcripción, parámetros y métricas.

- POST /voz/transcripcion : respaldo en servidor de la transcripción (TT-02).
  Requiere JWT (middleware), limita tamaño y tasa de peticiones y descarta el
  audio al terminar (sin persistencia).
- GET/PUT /voz/parametros : parámetros administrables (TT-03). La lectura está
  disponible para cualquier usuario autenticado (el frontend la usa para saber
  si la función está activa); la escritura es solo de administrador.
- POST /voz/metricas : registro de uso (TT-04) — consultas, errores y duración.
- GET /voz/metricas : panel del administrador con los agregados mensuales.
"""

import time
from datetime import datetime, timezone

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.metrica_voz import MetricaVoz
from agroia_backend.models.parametro_voz import ParametroVoz
from agroia_backend.services.transcripcion import TranscripcionError, transcribir_audio

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/voz", tags=["voz"])

ROL_ADMIN = {"admin", "administrador"}

# Límites contra abuso (RNF-023): máx. solicitudes de transcripción por usuario/minuto.
_TASA_MAX_POR_MINUTO = 10
_tasa: dict[str, list[float]] = {}


def _exigir_admin(rol: str | None) -> str:
    rol = (rol or "").strip().lower()
    if rol not in ROL_ADMIN:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el administrador puede gestionar parámetros y métricas de voz.",
        })
    return rol


def _limitar_tasa(email: str | None) -> None:
    clave = email or "anon"
    ahora = time.monotonic()
    eventos = [t for t in _tasa.get(clave, []) if ahora - t < 60]
    if len(eventos) >= _TASA_MAX_POR_MINUTO:
        raise HTTPException(status_code=429, detail={
            "code": "TASA_EXCEDIDA",
            "message": "Demasiadas solicitudes de transcripción. Intente en un momento.",
        })
    eventos.append(ahora)
    _tasa[clave] = eventos


async def _parametros(db: AsyncSession) -> ParametroVoz:
    """Devuelve la fila única de parámetros; la crea con valores por defecto si falta."""
    fila = (await db.execute(select(ParametroVoz).limit(1))).scalars().first()
    if fila is None:
        fila = ParametroVoz(activado=True, duracion_maxima_segundos=60, idioma="es")
        db.add(fila)
        await db.commit()
        await db.refresh(fila)
    return fila


class ParametrosVozIn(BaseModel):
    activado: bool | None = Field(None)
    duracion_maxima_segundos: int | None = Field(None, ge=5, le=300)
    idioma: str | None = Field(None, min_length=2, max_length=10)


class MetricaVozIn(BaseModel):
    tipo: str = Field(..., pattern="^(consulta|error)$")
    duracion_ms: int | None = Field(None, ge=0, le=3_600_000)


@router.post("/transcripcion")
async def transcribir(
    audio: UploadFile = File(...),
    idioma: str = Form("es"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Convierte audio a texto en español. El audio se descarta al terminar."""
    _limitar_tasa(x_user_email)
    datos = await audio.read()
    try:
        resultado = await transcribir_audio(datos, idioma or "es")
    except TranscripcionError as e:
        raise HTTPException(status_code=503, detail={"code": e.code, "message": e.message})
    return {"texto": resultado.texto, "proveedor": resultado.proveedor}


@router.get("/parametros")
async def obtener_parametros(db: AsyncSession = Depends(get_db)):
    """Parámetros vigentes de la función de voz (cualquier usuario autenticado)."""
    p = await _parametros(db)
    return {
        "activado": p.activado,
        "duracion_maxima_segundos": p.duracion_maxima_segundos,
        "idioma": p.idioma,
    }


@router.put("/parametros")
async def actualizar_parametros(
    body: ParametrosVozIn,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Actualiza los parámetros de voz (solo administrador)."""
    _exigir_admin(x_user_role)
    p = await _parametros(db)
    if body.activado is not None:
        p.activado = body.activado
    if body.duracion_maxima_segundos is not None:
        p.duracion_maxima_segundos = body.duracion_maxima_segundos
    if body.idioma is not None:
        p.idioma = body.idioma.strip().lower()
    await db.commit()
    await db.refresh(p)
    return {
        "activado": p.activado,
        "duracion_maxima_segundos": p.duracion_maxima_segundos,
        "idioma": p.idioma,
    }


@router.post("/metricas")
async def registrar_metrica(
    body: MetricaVozIn,
    db: AsyncSession = Depends(get_db),
):
    """Registra un evento de uso (consulta o error) sin audio ni contenido."""
    periodo = datetime.now(timezone.utc).strftime("%Y-%m")
    fila = (
        await db.execute(select(MetricaVoz).where(MetricaVoz.periodo == periodo))
    ).scalars().first()
    if fila is None:
        fila = MetricaVoz(periodo=periodo, consultas=0, errores=0, duracion_total_ms=0)
        db.add(fila)
    if body.tipo == "consulta":
        fila.consultas += 1
        fila.duracion_total_ms += body.duracion_ms or 0
    else:
        fila.errores += 1
    await db.commit()
    return {"ok": True}


@router.get("/metricas")
async def listar_metricas(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Agregados mensuales de uso de voz (solo administrador)."""
    _exigir_admin(x_user_role)
    filas = (
        await db.execute(select(MetricaVoz).order_by(MetricaVoz.periodo.desc()))
    ).scalars().all()
    data = []
    for f in filas:
        data.append({
            "periodo": f.periodo,
            "consultas": f.consultas,
            "errores": f.errores,
            "duracion_media_ms": (
                round(f.duracion_total_ms / f.consultas) if f.consultas else 0
            ),
        })
    return {"data": data}
