"""Tests del campo `lote` en la trama del sensor (diferenciación multi-lote)."""

import pytest
from fastapi import HTTPException

from agroia_backend.api.iot import Esp32SensorMessage, SensorRawRegistros
from agroia_backend.api.sensor_api import SensorFrame
from agroia_backend.services.normalizacion_iot import normalizar_trama
from agroia_backend.services.resolucion_lotes import resolver_lote_id


def test_trama_esp32_acepta_lote():
    msg = Esp32SensorMessage(
        device_id="esp32-npk-001",
        finca_id="a0562767-13a8-4a49-bd98-e8097d5b2674",
        lote="1",
        ph=7.0,
    )
    assert msg.lote == "1"
    assert msg.ph == 7.0


def test_trama_firmware_acepta_lote():
    frame = SensorFrame(
        device_id="esp32-npk-001",
        finca_id="a0562767-13a8-4a49-bd98-e8097d5b2674",
        lote="042217d5-0c84-40be-aa5f-080429fbfcba",
        ph=7.0,
    )
    assert frame.lote == "042217d5-0c84-40be-aa5f-080429fbfcba"


def test_trama_raw_acepta_lote():
    msg = SensorRawRegistros(
        device_id="esp32-npk-001",
        registros={"0x0006": 70},
        lote="Lote frijol",
    )
    assert msg.lote == "Lote frijol"


def test_normalizar_trama_ignora_lote():
    """El campo `lote` no debe filtrarse al payload canónico de suelo."""
    payload, _ = normalizar_trama({
        "device_id": "esp32-npk-001",
        "lote": "1",
        "ph": 7.0,
        "nitrogen": 5.0,
    })
    assert payload == {"ph": 7.0, "nitrogeno": 5.0}
    assert "lote" not in payload


@pytest.mark.asyncio
async def test_resolver_lote_id_finca_invalida():
    """finca_id no UUID → 422 sin tocar la BD."""
    with pytest.raises(HTTPException) as exc:
        await resolver_lote_id("no-es-uuid", "1")
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "FINCA_INVALIDA"
