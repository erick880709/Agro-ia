"""Servicio de síntesis de voz — interfaz común y preprocesamiento (TT-01/TT-03).

Decisión técnica (TT-01/TT-02): la lectura usa `speechSynthesis` en el navegador
como motor por defecto (sin costo, funciona sin servidor). Este servicio expone
la interfaz común de síntesis en servidor como respaldo; el proveedor es
intercambiable (Google/Azure/Piper como adaptadores futuros). Sin proveedor
configurado, el endpoint responde 503 y la respuesta se muestra en texto
(degradación elegante).

El preprocesamiento (`limpiar_texto_lectura`) se aplica antes de sintetizar:
quita formato Markdown y expande unidades agronómicas para lectura natural.
"""

import re

from agroia.logging import get_logger

logger = get_logger(__name__)

_UNIDADES_LECTURA = {
    "kg/ha": "kilos por hectárea",
    "g/ha": "gramos por hectárea",
    "t/ha": "toneladas por hectárea",
    "meq/100 g": "miliequivalentes por cien gramos",
    "meq/100g": "miliequivalentes por cien gramos",
    "cmol/kg": "centimoles por kilo",
    "dS/m": "decisiemens por metro",
    "ppm": "partes por millón",
    "%": "por ciento",
    "°C": "grados centígrados",
    "pH": "pe hache",
}


def limpiar_texto_lectura(texto: str | None) -> str:
    """Normaliza el texto para lectura en voz alta (sin formato ni símbolos)."""
    if not texto:
        return ""
    t = str(texto)
    # Enlaces e imágenes Markdown
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " imagen ", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
    # Negrita / cursiva / código
    t = re.sub(r"(\*\*|__)(.*?)\1", r"\2", t)
    t = re.sub(r"(\*|_)(.*?)\1", r"\2", t)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    # Encabezados y listas
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.MULTILINE)
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"^\s*\d+[.)]\s+", "", t, flags=re.MULTILINE)
    # Separadores de tabla y símbolos sueltos
    t = t.replace("|", " ")
    t = re.sub(r"[*#_>~]", " ", t)
    # Unidades agronómicas → lectura natural
    for clave, lectura in _UNIDADES_LECTURA.items():
        t = t.replace(clave, f" {lectura} ")
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


class SintesisError(Exception):
    """Fallo del servicio de síntesis."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class SintesisProvider:
    """Contrato de síntesis (intercambiable): texto → audio."""

    nombre = "base"

    async def sintetizar(self, texto: str, voz: str = "femenina", velocidad: str = "1") -> bytes:
        raise NotImplementedError


class OpenAITTSProvider(SintesisProvider):
    """Síntesis con OpenAI (requiere OPENAI_API_KEY). Voces: nova (femenina) / onyx (masculina)."""

    nombre = "openai-tts"

    async def sintetizar(self, texto: str, voz: str = "femenina", velocidad: str = "1") -> bytes:
        from openai import AsyncOpenAI

        from agroia.config import get_settings

        settings = get_settings()
        key = settings.openai_api_key or ""
        if not key:
            raise SintesisError(
                "SINTESIS_NO_CONFIGURADA",
                "El motor de síntesis en servidor no está configurado.",
            )
        voz_openai = "nova" if voz != "masculina" else "onyx"
        speed = {"0.75": 0.75, "1": 1.0, "1.25": 1.25, "1.5": 1.5}.get(velocidad, 1.0)
        client = AsyncOpenAI(api_key=key)
        try:
            resultado = await client.audio.speech.create(
                model="tts-1",
                voice=voz_openai,
                input=texto,
                speed=speed,
            )
        except Exception as e:  # noqa: BLE001 — se traduce a error de dominio
            logger.error("sintesis_proveedor_error", error=str(e))
            raise SintesisError(
                "SINTESIS_NO_DISPONIBLE", "El motor de síntesis no está disponible."
            ) from e
        return resultado.content


class VozClonadaProvider(SintesisProvider):
    """Síntesis con la voz clonada del usuario (motor autoalojado, TT-06)."""

    nombre = "voz-clonada"

    def __init__(self, voice_id: str):
        self.voice_id = voice_id

    async def sintetizar(self, texto: str, voz: str = "mi-voz", velocidad: str = "1") -> bytes:
        from agroia_backend.services.clonacion_voz import ClonacionVozProvider

        proveedor = ClonacionVozProvider()
        return await proveedor.sintetizar(self.voice_id, texto, velocidad)


_PROVEEDORES: list[SintesisProvider] = [OpenAITTSProvider()]


async def sintetizar(
    texto: str,
    voz: str = "femenina",
    velocidad: str = "1",
    voz_clonada_id: str | None = None,
) -> bytes:
    """Sintetiza texto a audio con la cadena de proveedores.

    Para `voz="mi-voz"` se usa la voz clonada del usuario; si no hay
    identificador de voz clonada activa se devuelve un error de dominio.
    """
    texto_limpio = limpiar_texto_lectura(texto)
    if not texto_limpio:
        raise SintesisError("TEXTO_VACIO", "No hay texto para leer.")
    proveedores = list(_PROVEEDORES)
    if voz == "mi-voz":
        if not voz_clonada_id:
            raise SintesisError(
                "VOZ_CLONADA_NO_DISPONIBLE",
                "Aún no se ha generado la voz clonada; la lectura usa la voz del navegador.",
            )
        proveedores.insert(0, VozClonadaProvider(voz_clonada_id))
    for proveedor in proveedores:
        try:
            return await proveedor.sintetizar(texto_limpio, voz, velocidad)
        except SintesisError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error("sintesis_proveedor_error", proveedor=proveedor.nombre, error=str(e))
    raise SintesisError(
        "SINTESIS_NO_DISPONIBLE", "El motor de síntesis no está disponible."
    )
