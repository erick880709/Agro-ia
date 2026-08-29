"""Pruebas del módulo de visión por computadora (diagnóstico de plagas)."""

import base64
import struct
import uuid
import zlib

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from agroia_backend.main import app


@pytest.fixture()
async def cli():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _cabeceras(rol="Agronomo", email="agronomo@agroia.co"):
    return {"X-User-Role": rol, "X-User-Email": email}


def _png_bytes(rgb: np.ndarray) -> bytes:
    """Codifica un arreglo RGB uint8 como PNG (sin PIL)."""

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


@pytest.fixture()
def png_minimo():
    # PNG de 1x1 válido: falla el quality gate → abstención explicada.
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )


@pytest.fixture()
def hoja_sintomatica():
    """Hoja sintética: fondo neutro, hoja verde con clorosis y necrosis."""
    rng = np.random.default_rng(7)
    imagen = np.full((160, 200, 3), (60, 60, 60), dtype=np.uint8)
    ruido = rng.integers(-20, 20, size=imagen.shape, dtype=np.int16)
    # Hoja: rectángulo verde (60% del área aprox.).
    imagen[20:140, 30:170] = (20, 140, 30)
    # Clorosis: parches amarillos.
    imagen[40:70, 50:90] = (235, 215, 60)
    imagen[110:130, 120:160] = (230, 210, 70)
    # Necrosis: manchas marrón/oscuro.
    imagen[80:100, 60:90] = (120, 60, 20)
    imagen[70:85, 140:165] = (60, 30, 10)
    imagen = np.clip(imagen.astype(np.int16) + ruido, 0, 255).astype(np.uint8)
    return _png_bytes(imagen)


async def test_analizar_plaga_flujo_completo(cli, hoja_sintomatica):
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"  # Finca Demo
    r = await cli.post(
        f"/api/v1/vision/analizar-plaga?finca_id={finca_id}",
        headers=_cabeceras(),
        files={"file": ("hoja.png", hoja_sintomatica, "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["estado"] == "preliminary"
    assert body["fuente"] == "agrovision_opencv_v1"
    assert body["imagen_url"].startswith("/media/vision/")
    assert body["requiere_revision"] is True
    assert isinstance(body["evidencia"], list) and body["evidencia"]
    assert 0.0 < body["confianza"] <= 1.0
    # Historial
    r2 = await cli.get(f"/api/v1/vision/diagnosticos/{finca_id}", headers=_cabeceras())
    assert r2.status_code == 200
    diags = r2.json()["diagnosticos"]
    assert any(d["id"] == body["diagnostico_id"] for d in diags)


async def test_analizar_plaga_foto_invalida_abstencion(cli, png_minimo):
    """Una foto inválida NO termina en 'No determinada' sin explicación:
    devuelve abstención explicada (sección 24)."""
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
    r = await cli.post(
        f"/api/v1/vision/analizar-plaga?finca_id={finca_id}",
        headers=_cabeceras(),
        files={"file": ("pixel.png", png_minimo, "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["estado"] == "abstain"
    assert body["confianza"] == 0.0
    assert "recomendacion" in body and body["recomendacion"]


async def test_diagnose_contrato_seccion18(cli, hoja_sintomatica):
    """POST /api/v1/vision/diagnose devuelve el contrato de la sección 18."""
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
    r = await cli.post(
        f"/api/v1/vision/analizar-plaga?finca_id={finca_id}",
        headers=_cabeceras(),
        files={"file": ("hoja.png", hoja_sintomatica, "image/png")},
    )
    imagen_uri = r.json()["imagen_url"]
    r2 = await cli.post(
        "/api/v1/vision/diagnose",
        headers=_cabeceras(),
        json={"image_uri": imagen_uri, "crop_hint": "coffee"},
    )
    assert r2.status_code == 200, r2.text
    cuerpo = r2.json()
    assert cuerpo["model_version"].startswith("agrovision")
    assert cuerpo["status"] in ("preliminary", "abstain")
    assert cuerpo["recommend_review"] is True
    assert set(cuerpo) >= {"model_version", "status", "crop", "diagnosis", "severity", "evidence", "recommend_review", "dataset_lineage"}


async def test_diagnose_uri_invalida(cli):
    r = await cli.post(
        "/api/v1/vision/diagnose",
        headers=_cabeceras(),
        json={"image_uri": "http://externo.ejemplo/hoja.png"},
    )
    assert r.status_code == 422


async def test_confirmar_diagnostico_rq_v6_01(cli, hoja_sintomatica):
    """RQ-V6-01: el agrónomo confirma la etiqueta y queda en el historial."""
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
    r = await cli.post(
        f"/api/v1/vision/analizar-plaga?finca_id={finca_id}",
        headers=_cabeceras(),
        files={"file": ("hoja.png", hoja_sintomatica, "image/png")},
    )
    diag_id = r.json()["diagnostico_id"]
    r2 = await cli.post(
        f"/api/v1/vision/diagnosticos/{diag_id}/confirmar",
        headers=_cabeceras(),
        json={"etiqueta": "coffee_rust"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["etiqueta_confirmada"] == "coffee_rust"
    # Etiqueta no válida → 422
    r3 = await cli.post(
        f"/api/v1/vision/diagnosticos/{diag_id}/confirmar",
        headers=_cabeceras(),
        json={"etiqueta": "x"},
    )
    assert r3.status_code == 422
    # Cliente no puede confirmar
    r4 = await cli.post(
        f"/api/v1/vision/diagnosticos/{diag_id}/confirmar",
        headers=_cabeceras(rol="Cliente", email="maria.cliente@agroia.co"),
        json={"etiqueta": "coffee_rust"},
    )
    assert r4.status_code in (401, 403)
    # Aparece en el historial
    r5 = await cli.get(f"/api/v1/vision/diagnosticos/{finca_id}", headers=_cabeceras())
    diags = r5.json()["diagnosticos"]
    assert any(d["id"] == diag_id and d["etiqueta_confirmada"] == "coffee_rust" for d in diags)


async def test_dataset_estado_solo_admin(cli):
    r = await cli.get("/api/v1/vision/admin/dataset-estado", headers=_cabeceras())
    assert r.status_code == 403
    r2 = await cli.get(
        "/api/v1/vision/admin/dataset-estado",
        headers=_cabeceras(rol="Admin", email="admin@agroia.co"),
    )
    assert r2.status_code == 200
    cuerpo = r2.json()
    assert set(cuerpo) >= {"disponible", "manifest", "metadata", "fuentes", "curacion", "modelos"}


async def test_analizar_plaga_formato_rechazado(cli):
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
    r = await cli.post(
        f"/api/v1/vision/analizar-plaga?finca_id={finca_id}",
        headers=_cabeceras(),
        files={"file": ("nota.txt", b"hola", "text/plain")},
    )
    assert r.status_code == 415


async def test_analizar_plaga_cliente_prohibido(cli, png_minimo):
    finca_id = "3a47d0c6-fb00-4106-91ba-0a707f612e86"
    r = await cli.post(
        f"/api/v1/vision/analizar-plaga?finca_id={finca_id}",
        headers=_cabeceras(rol="Cliente", email="maria.cliente@agroia.co"),
        files={"file": ("hoja.png", png_minimo, "image/png")},
    )
    assert r.status_code in (401, 403)


async def test_reentrenar_solo_admin(cli):
    r = await cli.post("/api/v1/vision/admin/reentrenar", headers=_cabeceras())
    assert r.status_code == 403
    r = await cli.post(
        "/api/v1/vision/admin/reentrenar",
        headers=_cabeceras(rol="Admin", email="admin@agroia.co"),
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "programado"


async def test_diagnosticos_finca_inexistente(cli):
    r = await cli.get(
        f"/api/v1/vision/diagnosticos/{uuid.uuid4()}",
        headers=_cabeceras(),
    )
    assert r.status_code in (200, 403, 404)
