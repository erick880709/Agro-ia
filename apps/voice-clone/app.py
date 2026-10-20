"""Servicio de clonación de voz — wrapper HTTP de Chatterbox Multilingual V3.

Implementa el contrato consumido por `agroia_backend.services.clonacion_voz`:

    POST /clonar        {"usuario_email", "audio_base64"} → {"voice_id", "estado"}
    GET  /voces/{id}    → {"voice_id", "estado"}
    POST /sintetizar    {"voice_id", "texto", "velocidad"} → audio/wav
    GET  /health        → {"status": "ok"}

Chatterbox es zero-shot: la "clonación" consiste en guardar la muestra de
referencia y usarla como `audio_prompt_path` en la síntesis. No requiere
entrenamiento. Modelo por defecto: V3 multilingüe con `language_id="es"`.

Variables de entorno:
    CHATTERBOX_T3_MODEL    "v3" (por defecto) — ver tarjeta del modelo para packs
                           de idioma único (p. ej. Latam Spanish).
    CHATTERBOX_LANGUAGE_ID "es" (por defecto).
"""
import base64
import io
import os
import subprocess
import tempfile
import uuid

import torch
import torchaudio as ta
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
T3_MODEL = os.getenv("CHATTERBOX_T3_MODEL", "v3")
LANGUAGE_ID = os.getenv("CHATTERBOX_LANGUAGE_ID", "es")

app = FastAPI(title="AgroIA Voice Clone (Chatterbox)")

# El modelo se carga al arrancar (tarda en descargar pesos la primera vez).
from chatterbox.mtl_tts import ChatterboxMultilingualTTS  # noqa: E402

MODEL = ChatterboxMultilingualTTS.from_pretrained(device=DEVICE, t3_model=T3_MODEL)

VOCES: dict[str, dict] = {}


class ClonarIn(BaseModel):
    usuario_email: str
    audio_base64: str


class SintetizarIn(BaseModel):
    voice_id: str
    texto: str
    velocidad: str = "1"


def _convertir_a_wav(base64_audio: str) -> str:
    """Decodifica la muestra (webm/opus del navegador) y la convierte a wav 24 kHz mono."""
    raw = base64.b64decode(base64_audio)
    if not raw:
        raise HTTPException(status_code=422, detail="Muestra de audio vacía.")
    src = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(raw)
            src = f.name
        dst = src + ".wav"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "24000", "-ac", "1", dst],
            check=True,
        )
        return dst
    finally:
        if src and os.path.isfile(src):
            os.remove(src)


@app.get("/health")
async def health():
    return {"status": "ok", "device": DEVICE, "t3_model": T3_MODEL, "language_id": LANGUAGE_ID}


@app.post("/clonar")
async def clonar(body: ClonarIn):
    wav_path = _convertir_a_wav(body.audio_base64)
    voice_id = uuid.uuid4().hex
    VOCES[voice_id] = {"wav_path": wav_path, "email": body.usuario_email, "estado": "activa"}
    return JSONResponse({"voice_id": voice_id, "estado": "activa"})


@app.get("/voces/{voice_id}")
async def estado(voice_id: str):
    voz = VOCES.get(voice_id)
    if voz is None:
        raise HTTPException(status_code=404, detail="Voz no encontrada.")
    return JSONResponse({"voice_id": voice_id, "estado": voz["estado"]})


@app.post("/sintetizar")
async def sintetizar(body: SintetizarIn):
    voz = VOCES.get(body.voice_id)
    if voz is None:
        raise HTTPException(status_code=404, detail="Voz no encontrada.")
    texto = (body.texto or "").strip()
    if not texto:
        raise HTTPException(status_code=422, detail="Texto vacío.")
    wav = MODEL.generate(texto, language_id=LANGUAGE_ID, audio_prompt_path=voz["wav_path"])
    buf = io.BytesIO()
    ta.save(buf, wav, MODEL.sr, format="wav")
    return Response(content=buf.getvalue(), media_type="audio/wav")
