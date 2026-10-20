"""Cliente HTTP del servicio de clonación de voz (TT-06).

El motor de clonación (Chatterbox Multilingual V3 / GPT-SoVITS, MIT) se autoaloja
en GPU cloud (RunPod Serverless / HF Spaces) y se expone como un servicio HTTP
con un contrato mínimo. Este adaptador es la única pieza del backend que conoce
ese contrato; si el servicio no está configurado (`clonacion_voz_url` vacío), los
métodos lanzan `ClonacionError` con código `CLONACION_NO_CONFIGURADA` y la
cadena de síntesis degrada a la voz del navegador.

Contrato esperado en el servicio de GPU (documentado en resources/architecture/):
    POST {base}/clonar         {"usuario_email", "audio_base64"} → {"voice_id", "estado"}
    GET  {base}/voces/{id}     → {"voice_id", "estado"}
    POST {base}/sintetizar     {"voice_id", "texto", "velocidad"} → audio (body)
"""

import base64

import httpx

from agroia.config import get_settings
from agroia.logging import get_logger

logger = get_logger(__name__)


class ClonacionError(Exception):
    """Fallo del servicio de clonación de voz."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class ClonacionVozProvider:
    """Adaptador HTTP del motor de clonación autoalojado."""

    def __init__(self, base_url: str | None = None, token: str | None = None,
                 transport: httpx.AsyncBaseTransport | None = None):
        settings = get_settings()
        self.base_url = (base_url if base_url is not None else settings.clonacion_voz_url or "").rstrip("/")
        self.token = token if token is not None else settings.clonacion_voz_token or ""
        self._transport = transport

    @property
    def configurado(self) -> bool:
        return bool(self.base_url)

    def _client(self) -> httpx.AsyncClient:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        return httpx.AsyncClient(base_url=self.base_url, headers=headers,
                                 transport=self._transport, timeout=httpx.Timeout(300.0))

    def _exigir_configurado(self) -> None:
        if not self.configurado:
            raise ClonacionError(
                "CLONACION_NO_CONFIGURADA",
                "El motor de clonación de voz no está configurado (CLONACION_VOZ_URL).",
            )

    async def clonar(self, usuario_email: str, audio: bytes) -> str:
        """Envía la muestra de voz y devuelve el identificador de la voz clonada."""
        self._exigir_configurado()
        payload = {
            "usuario_email": usuario_email,
            "audio_base64": base64.b64encode(audio).decode("ascii"),
        }
        async with self._client() as client:
            try:
                resp = await client.post("/clonar", json=payload)
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPError as e:
                logger.error("clonacion_envio_error", error=str(e))
                raise ClonacionError("CLONACION_NO_DISPONIBLE", "No se pudo enviar la muestra al motor de clonación.") from e
        voice_id = (data or {}).get("voice_id")
        if not voice_id:
            raise ClonacionError("CLONACION_RESPUESTA_INVALIDA", "El motor no devolvió un identificador de voz.")
        return voice_id

    async def estado(self, voice_id: str) -> str:
        """Consulta el estado de la clonación (procesando | activa | error)."""
        self._exigir_configurado()
        async with self._client() as client:
            try:
                resp = await client.get(f"/voces/{voice_id}")
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPError as e:
                logger.error("clonacion_estado_error", voice_id=voice_id, error=str(e))
                raise ClonacionError("CLONACION_NO_DISPONIBLE", "No se pudo consultar el estado de la clonación.") from e
        return str((data or {}).get("estado") or "procesando")

    async def sintetizar(self, voice_id: str, texto: str, velocidad: str = "1") -> bytes:
        """Sintetiza texto con la voz clonada; devuelve el audio crudo."""
        self._exigir_configurado()
        payload = {"voice_id": voice_id, "texto": texto, "velocidad": velocidad}
        async with self._client() as client:
            try:
                resp = await client.post("/sintetizar", json=payload)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                logger.error("clonacion_sintesis_error", voice_id=voice_id, error=str(e))
                raise ClonacionError("CLONACION_NO_DISPONIBLE", "No se pudo sintetizar con la voz clonada.") from e
        audio = resp.content
        if not audio:
            raise ClonacionError("CLONACION_AUDIO_VACIO", "El motor devolvió un audio vacío.")
        return audio
