"""Pruebas del adaptador de clonación de voz (TT-06).

Validan el contrato HTTP del servicio GPU y la integración con la cadena de
síntesis sin requerir el motor real (se usa un transporte HTTP simulado).
"""
import pytest
from httpx import MockTransport, Request, Response

from agroia_backend.services.clonacion_voz import ClonacionError, ClonacionVozProvider
from agroia_backend.services.sintesis_voz import SintesisError, sintetizar


def _proveedor(handler):
    return ClonacionVozProvider(
        base_url="https://gpu.mock",
        token="secreto",
        transport=MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_clonar_devuelve_voice_id():
    def handler(request: Request) -> Response:
        assert request.url.path == "/clonar"
        assert request.headers["authorization"] == "Bearer secreto"
        import json

        payload = json.loads(request.content)
        assert payload["usuario_email"] == "user@agroia.co"
        assert payload["audio_base64"]
        return Response(200, json={"voice_id": "voz-123", "estado": "procesando"})

    provider = _proveedor(handler)
    voice_id = await provider.clonar("user@agroia.co", b"\x00\x01\x02")
    assert voice_id == "voz-123"


@pytest.mark.asyncio
async def test_sintetizar_devuelve_audio():
    def handler(request: Request) -> Response:
        assert request.url.path == "/sintetizar"
        import json

        payload = json.loads(request.content)
        assert payload["voice_id"] == "voz-123"
        assert payload["texto"].startswith("Buenos días")
        return Response(200, content=b"RIFF....audio")

    provider = _proveedor(handler)
    audio = await provider.sintetizar("voz-123", "Buenos días, **su suelo** está bien")
    assert audio == b"RIFF....audio"


@pytest.mark.asyncio
async def test_estado_sincroniza():
    def handler(request: Request) -> Response:
        assert request.url.path == "/voces/voz-123"
        return Response(200, json={"voice_id": "voz-123", "estado": "activa"})

    provider = _proveedor(handler)
    assert await provider.estado("voz-123") == "activa"


@pytest.mark.asyncio
async def test_sin_configurar_lanza_error():
    provider = ClonacionVozProvider(base_url="", token="")
    with pytest.raises(ClonacionError) as err:
        await provider.clonar("user@agroia.co", b"x")
    assert err.value.code == "CLONACION_NO_CONFIGURADA"


@pytest.mark.asyncio
async def test_sintesis_mi_voz_sin_referencia_error():
    with pytest.raises(SintesisError) as err:
        await sintetizar("Hola", voz="mi-voz")
    assert err.value.code == "VOZ_CLONADA_NO_DISPONIBLE"
