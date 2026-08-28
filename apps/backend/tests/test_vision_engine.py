"""Pruebas unitarias del motor de visión (fallback OpenCV + abstención).

Sin base de datos: ejercita directamente diagnosticar_imagen y el fallback.
"""

import struct
import zlib

import numpy as np

from agroia_backend.services.vision_engine import diagnosticar_imagen
from agroia_backend.services.vision_fallback import (
    FUENTE_FALLBACK,
    MODELO_VERSION,
    decodificar,
    diagnosticar,
)


def _png_bytes(rgb: np.ndarray) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    alto, ancho = rgb.shape[:2]
    crudo = b"".join(b"\x00" + fila.tobytes() for fila in rgb)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(crudo, 6))
        + chunk(b"IEND", b"")
    )


def _hoja(crop: str | None = None) -> bytes:
    rng = np.random.default_rng(11)
    imagen = np.full((160, 200, 3), (60, 60, 60), dtype=np.uint8)
    imagen[20:140, 30:170] = (20, 140, 30)
    if crop != "cacao":
        imagen[40:70, 50:90] = (235, 215, 60)
    imagen[80:100, 60:90] = (120, 60, 20)
    ruido = rng.integers(-20, 20, size=imagen.shape, dtype=np.int16)
    return _png_bytes(np.clip(imagen.astype(np.int16) + ruido, 0, 255).astype(np.uint8))


def test_decodificar_png_sintetico():
    rgb = decodificar(_hoja())
    assert rgb is not None
    assert rgb.shape[0] == 160 and rgb.shape[2] == 3


def test_fallback_hoja_preliminary():
    resultado = diagnosticar(_hoja(), crop_hint="coffee")
    assert resultado["status"] == "preliminary"
    assert resultado["diagnosis"].endswith("_compatible") or resultado["diagnosis"] == "sin_sintomas_visibles"
    assert resultado["requires_review"] is True
    assert resultado["fuente"] == FUENTE_FALLBACK
    assert isinstance(resultado["evidence"], list) and resultado["evidence"]


def test_fallback_imagen_invalida_abstain():
    resultado = diagnosticar(b"\x00\x01\x02", crop_hint="coffee")
    assert resultado["status"] == "abstain"
    assert resultado["motivo"] == "imagen_no_decodificable"


def test_fallback_imagen_1x1_abstain():
    pixel = _png_bytes(np.array([[[255, 255, 255]]], dtype=np.uint8))
    resultado = diagnosticar(pixel)
    assert resultado["status"] == "abstain"
    assert "tamano_insuficiente" in resultado["motivo"]


def test_engine_contrato_publico():
    contrato = diagnosticar_imagen(_hoja(), crop_hint="coffee")
    assert contrato["estado"] in ("preliminary", "abstain")
    assert contrato["modelo_version"] == MODELO_VERSION
    assert contrato["fuente"] == FUENTE_FALLBACK
    assert "diagnosis" in contrato and "severity" in contrato
    if contrato["estado"] == "preliminary":
        assert contrato["plaga"].endswith("_compatible") or contrato["plaga"] == "sin_sintomas_visibles"
        assert contrato["confianza"] > 0.0
        assert contrato["requiere_revision"] is True


def test_engine_crop_cacao():
    contrato = diagnosticar_imagen(_hoja(crop="cacao"), crop_hint="cacao")
    assert contrato["estado"] in ("preliminary", "abstain")
    if contrato["estado"] == "preliminary":
        assert "compatible" in contrato["diagnosis"]["label"]
