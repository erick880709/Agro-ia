"""Servicio de transcripción de voz — respaldo en servidor del enfoque híbrido.

Decisión técnica (TT-01 / RT-017): la captura de voz usa Web Speech API en el
navegador por defecto; este servicio provee el respaldo en servidor cuando el
navegador no soporta captura o la transcripción del navegador falla (enfoque
híbrido C). El proveedor es intercambiable detrás de `TranscripcionProvider`.

Seguridad y privacidad (RNF-019/021): el audio se procesa en memoria y se
descarta al terminar la transcripción — nunca se persiste. Sin proveedor
configurado el endpoint responde 503 para degradar con elegancia (la escritura
del chat sigue disponible).
"""

import io
from dataclasses import dataclass

from agroia.config import get_settings
from agroia.logging import get_logger

logger = get_logger(__name__)

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_AUDIO_SEGUNDOS = 60  # duración máxima por consulta (RF-034); se aplica en el cliente


class TranscripcionError(Exception):
    """Fallo del servicio de transcripción."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass
class TranscripcionResultado:
    texto: str
    proveedor: str


class TranscripcionProvider:
    """Contrato del proveedor de transcripción (intercambiable)."""

    nombre = "base"

    async def transcribir(self, audio: bytes, idioma: str = "es") -> str:
        raise NotImplementedError


class OpenAIWhisperProvider(TranscripcionProvider):
    """Transcripción con OpenAI Whisper (requiere OPENAI_API_KEY)."""

    nombre = "openai-whisper"

    async def transcribir(self, audio: bytes, idioma: str = "es") -> str:
        from openai import AsyncOpenAI

        settings = get_settings()
        key = settings.openai_api_key or ""
        if not key:
            raise TranscripcionError(
                "TRANSCRIPCION_NO_CONFIGURADA",
                "La transcripción en servidor no está configurada.",
            )
        client = AsyncOpenAI(api_key=key)
        archivo = io.BytesIO(audio)
        archivo.name = "consulta.webm"
        try:
            resultado = await client.audio.transcriptions.create(
                model="whisper-1",
                file=archivo,
                language=idioma or "es",
            )
        except Exception as e:  # noqa: BLE001 — se convierte a error de dominio
            logger.error("transcripcion_proveedor_error", error=str(e))
            raise TranscripcionError(
                "TRANSCRIPCION_NO_DISPONIBLE",
                "El servicio de transcripción no está disponible.",
            ) from e
        finally:
            archivo.close()

        texto = (getattr(resultado, "text", "") or "").strip()
        if not texto:
            raise TranscripcionError(
                "TRANSCRIPCION_VACIA", "No se pudo transcribir el audio."
            )
        return texto


_PROVEEDORES: list[TranscripcionProvider] = [OpenAIWhisperProvider()]


async def transcribir_audio(audio: bytes, idioma: str = "es") -> TranscripcionResultado:
    """Transcribe audio usando el primer proveedor disponible. No persiste audio."""
    if not audio:
        raise TranscripcionError("AUDIO_VACIO", "El audio está vacío.")
    if len(audio) > MAX_AUDIO_BYTES:
        raise TranscripcionError(
            "AUDIO_DEMASIADO_GRANDE",
            "El audio supera el tamaño máximo permitido (10 MB).",
        )
    for proveedor in _PROVEEDORES:
        try:
            texto = await proveedor.transcribir(audio, idioma or "es")
            return TranscripcionResultado(texto=texto, proveedor=proveedor.nombre)
        except TranscripcionError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(
                "transcripcion_proveedor_error",
                proveedor=proveedor.nombre,
                error=str(e),
            )
    raise TranscripcionError(
        "TRANSCRIPCION_NO_DISPONIBLE",
        "El servicio de transcripción no está disponible.",
    )
