"""API de lectura en voz alta — preferencias, síntesis, métricas y voz personalizada.

- GET|PUT /lectura/preferencias : preferencia por usuario (activado, voz, velocidad).
- POST /lectura/sintetizar : síntesis en servidor (respaldo); devuelve audio o 503.
- GET|POST /lectura/metricas : agregados mensuales (admin) y registro de eventos.
- CRUD /lectura/voz-personalizada : ciclo de vida de la voz clonada (Fase 2).
"""

import os
import re
from datetime import datetime, timezone

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, File, Header, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.metrica_lectura_voz import MetricaLecturaVoz
from agroia_backend.models.preferencia_lectura_voz import PreferenciaLecturaVoz
from agroia_backend.models.voz_personalizada import VozPersonalizada
from agroia_backend.services.clonacion_voz import ClonacionError, ClonacionVozProvider
from agroia_backend.services.sintesis_voz import SintesisError, sintetizar

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/lectura", tags=["lectura"])

ROL_ADMIN = {"admin", "administrador"}


def _exigir_admin(rol: str | None) -> str:
    rol = (rol or "").strip().lower()
    if rol not in ROL_ADMIN:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el administrador puede gestionar métricas de lectura.",
        })
    return rol


def _email(x_user_email: str | None) -> str:
    return (x_user_email or "").strip().lower() or "anon"


async def _preferencia(db: AsyncSession, email: str) -> PreferenciaLecturaVoz:
    fila = (
        await db.execute(select(PreferenciaLecturaVoz).where(PreferenciaLecturaVoz.usuario_email == email))
    ).scalars().first()
    if fila is None:
        fila = PreferenciaLecturaVoz(usuario_email=email, activado=False, voz="femenina", velocidad="1")
        db.add(fila)
        await db.commit()
        await db.refresh(fila)
    return fila


class PreferenciaIn(BaseModel):
    activado: bool | None = Field(None)
    voz: str | None = Field(None, pattern="^(femenina|masculina|mi-voz)$")
    velocidad: str | None = Field(None, pattern="^(0.75|1|1.25|1.5)$")


class SintetizarIn(BaseModel):
    texto: str = Field(..., min_length=1, max_length=6000)
    voz: str = Field("femenina", pattern="^(femenina|masculina|mi-voz)$")
    velocidad: str = Field("1", pattern="^(0.75|1|1.25|1.5)$")


class MetricaLecturaIn(BaseModel):
    tipo: str = Field(..., pattern="^(activacion|error)$")
    caracteres_leidos: int | None = Field(None, ge=0, le=100_000)
    voz_elegida: str | None = Field(None, max_length=20)


@router.get("/preferencias")
async def obtener_preferencia(
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    p = await _preferencia(db, _email(x_user_email))
    return {"activado": p.activado, "voz": p.voz, "velocidad": p.velocidad}


@router.put("/preferencias")
async def actualizar_preferencia(
    body: PreferenciaIn,
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    p = await _preferencia(db, _email(x_user_email))
    if body.activado is not None:
        p.activado = body.activado
    if body.voz is not None:
        p.voz = body.voz
    if body.velocidad is not None:
        p.velocidad = body.velocidad
    await db.commit()
    await db.refresh(p)
    return {"activado": p.activado, "voz": p.voz, "velocidad": p.velocidad}


@router.post("/sintetizar")
async def sintetizar_audio(
    body: SintetizarIn,
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Síntesis en servidor (respaldo). Devuelve audio MP3 o 503 si no hay motor.

    Para `voz="mi-voz"` se resuelve la voz clonada activa del usuario; si no
    existe o el motor de clonación no está configurado, se devuelve 503 y el
    frontend degrada a la voz del navegador.
    """
    voz_clonada_id = None
    if body.voz == "mi-voz":
        email = _email(x_user_email)
        fila = (
            await db.execute(select(VozPersonalizada).where(VozPersonalizada.usuario_email == email))
        ).scalars().first()
        if fila is not None and fila.estado == "activa" and fila.referencia:
            voz_clonada_id = fila.referencia
    try:
        audio = await sintetizar(body.texto, body.voz, body.velocidad, voz_clonada_id)
    except SintesisError as e:
        raise HTTPException(status_code=503, detail={"code": e.code, "message": e.message})
    media_type = "audio/wav" if body.voz == "mi-voz" else "audio/mpeg"
    return Response(content=audio, media_type=media_type)


@router.post("/metricas")
async def registrar_metrica(
    body: MetricaLecturaIn,
    db: AsyncSession = Depends(get_db),
):
    """Registra un evento de uso (activación o error) sin audio ni contenido."""
    periodo = datetime.now(timezone.utc).strftime("%Y-%m")
    fila = (
        await db.execute(select(MetricaLecturaVoz).where(MetricaLecturaVoz.periodo == periodo))
    ).scalars().first()
    if fila is None:
        fila = MetricaLecturaVoz(periodo=periodo, activaciones=0, errores=0, caracteres_leidos=0)
        db.add(fila)
    if body.tipo == "activacion":
        fila.activaciones += 1
    else:
        fila.errores += 1
    if body.voz_elegida:
        fila.voz_elegida = body.voz_elegida
    fila.caracteres_leidos += body.caracteres_leidos or 0
    await db.commit()
    return {"ok": True}


@router.get("/metricas")
async def listar_metricas(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Agregados mensuales de la lectura (solo administrador)."""
    _exigir_admin(x_user_role)
    filas = (
        await db.execute(select(MetricaLecturaVoz).order_by(MetricaLecturaVoz.periodo.desc()))
    ).scalars().all()
    data = [
        {
            "periodo": f.periodo,
            "activaciones": f.activaciones,
            "voz_elegida": f.voz_elegida,
            "errores": f.errores,
            "caracteres_leidos": f.caracteres_leidos,
        }
        for f in filas
    ]
    return {"data": data}


# ── Voz personalizada (Fase 2) ──

# Directorio donde se guardan las muestras de voz (fuera de la BD, cifrado en tránsito).
_VOCES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "media", "voces",
)
_MAX_AUDIO_BYTES = 8 * 1024 * 1024  # 8 MB


def _ruta_voz(email: str) -> str:
    segura = re.sub(r"[^a-z0-9@._-]", "_", email)
    return os.path.join(_VOCES_DIR, f"{segura}.webm")


@router.get("/voz-personalizada")
async def obtener_voz_personalizada(
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    fila = (
        await db.execute(select(VozPersonalizada).where(VozPersonalizada.usuario_email == _email(x_user_email)))
    ).scalars().first()
    if fila is None:
        return {"existe": False}
    if fila.estado == "eliminada":
        return {"existe": False}
    return {"existe": True, "estado": fila.estado, "creada_en": fila.creada_en.isoformat() if fila.creada_en else None}


@router.get("/voz-personalizada/audio")
async def obtener_audio_voz_personalizada(
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Devuelve la muestra grabada para previsualización (si existe)."""
    ruta = _ruta_voz(_email(x_user_email))
    if not os.path.isfile(ruta):
        raise HTTPException(status_code=404, detail={"code": "VOZ_SIN_MUESTRA", "message": "No hay muestra de voz."})
    with open(ruta, "rb") as f:
        contenido = f.read()
    return Response(content=contenido, media_type="audio/webm")


@router.post("/voz-personalizada")
async def crear_voz_personalizada(
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Guarda la muestra de la propia voz y habilita 'Mi voz' como opción.

    El motor de clonación (GPT-SoVITS/Chatterbox en GPU cloud) se integrará en
    TT-06; mientras tanto la muestra queda guardada y la voz se marca 'activa'
    para que aparezca en el selector (la síntesis de lectura seguirá usando la
    voz del navegador hasta integrar el motor).
    """
    email = _email(x_user_email)
    datos = await audio.read()
    if not datos:
        raise HTTPException(status_code=422, detail={"code": "AUDIO_VACIO", "message": "La muestra está vacía."})
    if len(datos) > _MAX_AUDIO_BYTES:
        raise HTTPException(status_code=422, detail={"code": "AUDIO_GRANDE", "message": "La muestra supera 8 MB."})

    os.makedirs(_VOCES_DIR, exist_ok=True)
    with open(_ruta_voz(email), "wb") as f:
        f.write(datos)

    fila = (
        await db.execute(select(VozPersonalizada).where(VozPersonalizada.usuario_email == email))
    ).scalars().first()
    if fila is None:
        fila = VozPersonalizada(usuario_email=email, estado="procesando", referencia=None)
        db.add(fila)
    else:
        fila.referencia = None

    # Si el motor de clonación está configurado, se envía la muestra de inmediato
    # (estado "procesando" hasta que el GPU confirme "activa"). Sin motor, la voz
    # queda "activa" en modo muestra (la lectura usa la voz del navegador).
    clonador = ClonacionVozProvider()
    if clonador.configurado:
        try:
            voice_id = await clonador.clonar(email, datos)
            fila.referencia = voice_id
            fila.estado = "procesando"
            nota = "Muestra enviada al motor de clonación."
        except ClonacionError as e:
            fila.estado = "error"
            nota = e.message
    else:
        fila.estado = "activa"
        nota = (
            "Voz guardada. El motor de clonación (TT-06) generará la voz sintética; "
            "hasta entonces la lectura usa la voz del navegador."
        )
    await db.commit()
    await db.refresh(fila)
    return {"existe": True, "estado": fila.estado, "referencia": fila.referencia, "nota": nota}


@router.post("/voz-personalizada/clonar")
async def clonar_voz_personalizada(
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Envía la muestra guardada al motor de clonación y registra el job."""
    email = _email(x_user_email)
    ruta = _ruta_voz(email)
    if not os.path.isfile(ruta):
        raise HTTPException(status_code=404, detail={"code": "VOZ_SIN_MUESTRA", "message": "Grabe una muestra antes de clonar."})
    with open(ruta, "rb") as f:
        datos = f.read()
    clonador = ClonacionVozProvider()
    if not clonador.configurado:
        raise HTTPException(status_code=503, detail={
            "code": "CLONACION_NO_CONFIGURADA",
            "message": "El motor de clonación no está configurado (CLONACION_VOZ_URL).",
        })
    fila = (
        await db.execute(select(VozPersonalizada).where(VozPersonalizada.usuario_email == email))
    ).scalars().first()
    try:
        voice_id = await clonador.clonar(email, datos)
    except ClonacionError as e:
        raise HTTPException(status_code=503, detail={"code": e.code, "message": e.message})
    if fila is None:
        fila = VozPersonalizada(usuario_email=email, estado="procesando", referencia=voice_id)
        db.add(fila)
    else:
        fila.referencia = voice_id
        fila.estado = "procesando"
    await db.commit()
    await db.refresh(fila)
    return {"existe": True, "estado": fila.estado, "referencia": voice_id}


@router.get("/voz-personalizada/estado")
async def estado_voz_personalizada(
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Consulta el estado de clonación en el motor GPU y sincroniza la BD."""
    email = _email(x_user_email)
    fila = (
        await db.execute(select(VozPersonalizada).where(VozPersonalizada.usuario_email == email))
    ).scalars().first()
    if fila is None or not fila.referencia:
        return {"existe": bool(fila), "estado": (fila.estado if fila else "sin-registro")}
    clonador = ClonacionVozProvider()
    if not clonador.configurado:
        return {"existe": True, "estado": fila.estado}
    try:
        estado = await clonador.estado(fila.referencia)
    except ClonacionError as e:
        raise HTTPException(status_code=503, detail={"code": e.code, "message": e.message})
    if estado != fila.estado:
        fila.estado = estado
        await db.commit()
        await db.refresh(fila)
    return {"existe": True, "estado": fila.estado, "referencia": fila.referencia}


@router.put("/voz-personalizada")
async def actualizar_voz_personalizada(
    body: dict,
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Activa o desactiva la voz personalizada."""
    email = _email(x_user_email)
    fila = (
        await db.execute(select(VozPersonalizada).where(VozPersonalizada.usuario_email == email))
    ).scalars().first()
    if fila is None:
        raise HTTPException(status_code=404, detail={"code": "VOZ_NO_EXISTE", "message": "No hay voz personalizada."})
    estado = str(body.get("estado") or "")
    if estado in ("activa", "desactivada"):
        fila.estado = estado
        await db.commit()
        await db.refresh(fila)
    return {"existe": True, "estado": fila.estado}


@router.delete("/voz-personalizada")
async def eliminar_voz_personalizada(
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Elimina la voz personalizada (registro y archivo de muestra)."""
    email = _email(x_user_email)
    fila = (
        await db.execute(select(VozPersonalizada).where(VozPersonalizada.usuario_email == email))
    ).scalars().first()
    if fila is not None:
        fila.estado = "eliminada"
        fila.referencia = None
        await db.commit()
    ruta = _ruta_voz(email)
    if os.path.isfile(ruta):
        os.remove(ruta)
    return {"ok": True}
