"""Pruebas de la API AGC-COST (F2-F7): casos de aceptación CA-05 a CA-15.

Requiere base de datos con migraciones aplicadas (corre en CI contra
PostgreSQL). El conjunto semilla se asegura de forma idempotente.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from agroia.database import async_session_factory
from agroia_backend.main import app
from agroia_backend.models.estimaciones import Estimacion
from agroia_backend.models.finca import Finca
from agroia_backend.services.costeo_seed import asegurar_conjunto_semilla

EDITOR = str(uuid.uuid4())
APROBADOR = str(uuid.uuid4())


@pytest.fixture()
async def cli():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _cab(rol="Admin", email="admin@agroia.co", uid=None):
    h = {"X-User-Role": rol, "X-User-Email": email}
    if uid:
        h["X-User-Id"] = uid
    return h


async def _semilla() -> None:
    async with async_session_factory() as db:
        await asegurar_conjunto_semilla(db)


async def _finca_id() -> str:
    async with async_session_factory() as db:
        finca = (await db.execute(select(Finca).limit(1))).scalars().first()
        assert finca is not None, "Se requiere al menos una finca en la BD de pruebas"
        return str(finca.id)


async def _crear_y_publicar(cli, *, nombre=None, uid_editor=EDITOR, uid_aprobador=APROBADOR,
                            clon_de: str | None = None, editar: callable | None = None) -> str:
    """Helper: crea (o clona) un conjunto, opcionalmente lo edita, simula y publica."""
    if clon_de:
        r = await cli.post(f"/api/v1/costeo/conjuntos/{clon_de}/clonar",
                           headers=_cab(uid=uid_editor),
                           json={"nombre": nombre or "Clon de prueba"})
        assert r.status_code == 201, r.text
        conjunto_id = r.json()["id"]
    else:
        r = await cli.post("/api/v1/costeo/conjuntos", headers=_cab(uid=uid_editor),
                           json={"nombre": nombre or "Conjunto de prueba"})
        assert r.status_code == 201, r.text
        conjunto_id = r.json()["id"]
    if editar is not None:
        await editar(cli, conjunto_id)
    # Simulación obligatoria sobre el borrador (RF-16).
    r = await cli.post("/api/v1/costeo/simular", headers=_cab(uid=uid_editor), json={
        "conjunto_id": conjunto_id, "area_ha": 1, "puntos": 10,
        "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": 10}],
    })
    assert r.status_code == 200, r.text
    r = await cli.post(f"/api/v1/costeo/conjuntos/{conjunto_id}/publicar",
                       headers=_cab(uid=uid_aprobador))
    assert r.status_code == 200, r.text
    return conjunto_id


async def _conjunto_dict(cli, conjunto_id) -> dict:
    r = await cli.get(f"/api/v1/costeo/conjuntos/{conjunto_id}", headers=_cab())
    assert r.status_code == 200, r.text
    return r.json()["conjunto"]


async def _componente(cli, conjunto_id, codigo) -> dict:
    c = await _conjunto_dict(cli, conjunto_id)
    for s in c["servicios"]:
        for comp in s["componentes"]:
            if comp["codigo"] == codigo:
                return comp
    raise AssertionError(f"Componente {codigo} no encontrado")


async def _poner_componente(cli, componente: dict, config: dict) -> None:
    r = await cli.put(f"/api/v1/costeo/componentes/{componente['id']}", headers=_cab(), json={
        "codigo": componente["codigo"],
        "nombre": componente["nombre"],
        "tipo": componente["tipo"],
        "orden": componente["orden"],
        "afectable_por_factores": componente["afectable_por_factores"],
        "config": config,
    })
    assert r.status_code == 200, r.text


# ─────────────────────────── F2 · parámetros ───────────────────────────

async def test_ca05_cambiar_tarifa_base_sin_despliegue(cli):
    """CA-05: tarifa base 100k → 120k en un conjunto nuevo → CA-01 = 270k."""
    await _semilla()
    async with async_session_factory() as db:
        from agroia_backend.models.costeo import CosteoConjunto
        semilla = (await db.execute(
            select(CosteoConjunto).where(CosteoConjunto.estado == "publicado")
            .order_by(CosteoConjunto.version.desc())
        )).scalars().first()
        semilla_id = str(semilla.id)

    r = await cli.post(f"/api/v1/costeo/conjuntos/{semilla_id}/clonar",
                       headers=_cab(uid=EDITOR), json={"nombre": "CA-05 tarifa nueva"})
    assert r.status_code == 201, r.text
    nuevo_id = r.json()["id"]

    base = await _componente(cli, nuevo_id, "tarifa_base")
    await _poner_componente(cli, base, {"valor": 120000})

    r = await cli.post("/api/v1/costeo/simular", headers=_cab(), json={
        "conjunto_id": nuevo_id, "area_ha": 1, "puntos": 10, "dificultad": "plano",
        "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": 10}],
    })
    assert r.status_code == 200, r.text
    assert r.json()["total_final"] == 270000.0


async def test_ca08_rechaza_traslape_de_tramos(cli):
    """CA-08: publicar/validar con tramos 1-15 y 14-30 se rechaza con el rango."""
    await _semilla()
    async with async_session_factory() as db:
        from agroia_backend.models.costeo import CosteoConjunto
        semilla = (await db.execute(
            select(CosteoConjunto).where(CosteoConjunto.estado == "publicado")
            .order_by(CosteoConjunto.version.desc())
        )).scalars().first()
        semilla_id = str(semilla.id)
    r = await cli.post(f"/api/v1/costeo/conjuntos/{semilla_id}/clonar",
                       headers=_cab(uid=EDITOR), json={"nombre": "CA-08 traslape"})
    assert r.status_code == 201, r.text
    nuevo_id = r.json()["id"]
    puntos = await _componente(cli, nuevo_id, "puntos_muestreo")
    r = await cli.post(f"/api/v1/costeo/componentes/{puntos['id']}/tramos",
                       headers=_cab(), json={"desde": 14, "hasta": 30, "valor": 15000, "modo": "marginal"})
    assert r.status_code == 201, r.text
    r = await cli.post(f"/api/v1/costeo/conjuntos/{nuevo_id}/validar", headers=_cab())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["valido"] is False
    assert any(e["codigo"] == "TRAMOS_INCONSISTENTES" for e in body["errores"])


async def test_doble_control_aprobador_es_editor(cli):
    """RF-15: el editor no puede publicar su propio conjunto."""
    await _semilla()
    async with async_session_factory() as db:
        from agroia_backend.models.costeo import CosteoConjunto
        semilla = (await db.execute(
            select(CosteoConjunto).where(CosteoConjunto.estado == "publicado")
            .order_by(CosteoConjunto.version.desc())
        )).scalars().first()
        semilla_id = str(semilla.id)
    r = await cli.post(f"/api/v1/costeo/conjuntos/{semilla_id}/clonar",
                       headers=_cab(uid=EDITOR), json={"nombre": "Doble control"})
    assert r.status_code == 201, r.text
    conjunto_id = r.json()["id"]
    # El clon queda atribuido al editor (simula que EDITOR lo creó/editó).
    async with async_session_factory() as db:
        from agroia_backend.models.costeo import CosteoConjunto
        c = (await db.execute(select(CosteoConjunto).where(
            CosteoConjunto.id == uuid.UUID(conjunto_id)))).scalars().one()
        c.creado_por = uuid.UUID(EDITOR)
        await db.commit()
    # Simulación previa para aislar la validación del doble control.
    r = await cli.post("/api/v1/costeo/simular", headers=_cab(uid=EDITOR), json={
        "conjunto_id": conjunto_id, "area_ha": 1,
        "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": 10}],
    })
    assert r.status_code == 200, r.text
    r = await cli.post(f"/api/v1/costeo/conjuntos/{conjunto_id}/publicar",
                       headers=_cab(uid=EDITOR))
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "APROBADOR_ES_EDITOR"


async def test_publicar_exige_simulacion_previa(cli):
    """§13: sin simulación registrada la publicación se rechaza."""
    r = await cli.post("/api/v1/costeo/conjuntos", headers=_cab(uid=EDITOR),
                       json={"nombre": "Sin simular"})
    assert r.status_code == 201, r.text
    conjunto_id = r.json()["id"]
    r = await cli.post(f"/api/v1/costeo/conjuntos/{conjunto_id}/publicar",
                       headers=_cab(uid=APROBADOR))
    assert r.status_code == 422
    assert r.json()["detail"]["code"] in ("SIMULACION_REQUERIDA", "CONJUNTO_INVALIDO")


async def test_import_export_json(cli):
    """RF-23: exportar el semilla e importarlo crea un conjunto válido."""
    await _semilla()
    async with async_session_factory() as db:
        from agroia_backend.models.costeo import CosteoConjunto
        semilla = (await db.execute(
            select(CosteoConjunto).where(CosteoConjunto.estado == "publicado")
            .order_by(CosteoConjunto.version.desc())
        )).scalars().first()
        semilla_id = str(semilla.id)
    r = await cli.get(f"/api/v1/costeo/conjuntos/{semilla_id}/exportar", headers=_cab())
    assert r.status_code == 200
    payload = r.json()
    r = await cli.post("/api/v1/costeo/importar", headers=_cab(uid=EDITOR), json=payload)
    assert r.status_code == 201, r.text
    importado = await _conjunto_dict(cli, r.json()["id"])
    assert importado["servicios"]


async def test_import_json_invalido(cli):
    r = await cli.post("/api/v1/costeo/importar", headers=_cab(uid=EDITOR),
                       json={"conjunto": {"nombre": "x", "servicios": [
                           {"codigo": "s", "nombre": "S", "componentes": []}]}})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "IMPORT_VALIDACION_FALLIDA"


# ─────────────────────────── F3 · estimaciones ───────────────────────────

async def _crear_estimacion(cli, *, rol="Admin", descuento=None) -> str:
    finca = await _finca_id()
    r = await cli.post("/api/v1/estimaciones", headers=_cab(rol=rol), json={
        "finca_id": finca,
        "lotes": [{"area_ha": 1, "puntos": 10,
                   "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": 10}]}],
        "factores": {"dificultad": "plano"},
        "descuento_pct": descuento,
    })
    assert r.status_code == 201, r.text
    return r.json()["estimacion"]["id"]


async def test_estimacion_ciclo_completo_y_ca07_snapshot(cli):
    """F3: crear → emitir → snapshot reproducible (CA-07) → aceptar."""
    await _semilla()
    est_id = await _crear_estimacion(cli)
    r = await cli.get(f"/api/v1/estimaciones/{est_id}", headers=_cab())
    assert r.status_code == 200, r.text
    e = r.json()["estimacion"]
    assert e["estado"] == "borrador"
    assert e["total_final"] == 250000.0

    r = await cli.post(f"/api/v1/estimaciones/{est_id}/emitir", headers=_cab(), json={})
    assert r.status_code == 200, r.text
    e = r.json()["estimacion"]
    assert e["estado"] == "emitida"
    assert e["consecutivo"].startswith("COT-")
    assert e["hash_snapshot"]

    # CA-07: recalcular con el snapshot → mismo total al peso.
    r = await cli.post(f"/api/v1/estimaciones/{est_id}/recalcular", headers=_cab())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["coincide"] is True
    assert body["total_snapshot"] == 250000.0

    r = await cli.post(f"/api/v1/estimaciones/{est_id}/aceptar", headers=_cab(), json={})
    assert r.status_code == 200, r.text
    assert r.json()["estimacion"]["estado"] == "aceptada"


async def test_estimacion_vencida_no_se_acepta(cli):
    """RF-19: vencida no puede aceptarse (ESTIMACION_VENCIDA)."""
    await _semilla()
    est_id = await _crear_estimacion(cli)
    r = await cli.post(f"/api/v1/estimaciones/{est_id}/emitir", headers=_cab(), json={})
    assert r.status_code == 200
    async with async_session_factory() as db:
        e = (await db.execute(select(Estimacion).where(Estimacion.id == uuid.UUID(est_id)))).scalars().one()
        e.vence_en = date.today() - timedelta(days=1)
        await db.commit()
    r = await cli.post(f"/api/v1/estimaciones/{est_id}/aceptar", headers=_cab(), json={})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "ESTIMACION_VENCIDA"


async def test_piso_rentabilidad_bloquea_y_permite_autorizar(cli):
    """RF-12: por debajo del piso exige autorización de administrador con motivo."""
    await _semilla()
    async with async_session_factory() as db:
        from agroia_backend.models.costeo import CosteoConjunto
        semilla = (await db.execute(
            select(CosteoConjunto).where(CosteoConjunto.estado == "publicado")
            .order_by(CosteoConjunto.version.desc())
        )).scalars().first()
        semilla_id = str(semilla.id)

    async def editar(cli, conjunto_id):
        r = await cli.put(f"/api/v1/costeo/conjuntos/{conjunto_id}/politica",
                          headers=_cab(uid=EDITOR), json={
                              "margen_objetivo": 0, "margen_minimo": 0,
                              "piso_visita": 400000, "vigencia_cotizacion_dias": 30,
                              "redondeo_multiplo": 1, "redondeo_modo": "ninguno",
                          })
        assert r.status_code == 200, r.text

    await _crear_y_publicar(cli, nombre="Piso 400k", clon_de=semilla_id, editar=editar)

    est_id = await _crear_estimacion(cli, rol="Agronomo")
    r = await cli.post(f"/api/v1/estimaciones/{est_id}/emitir",
                       headers=_cab(rol="Agronomo", email="maria.cliente@agroia.co"), json={})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "BAJO_PISO_RENTABILIDAD"

    r = await cli.post(f"/api/v1/estimaciones/{est_id}/emitir", headers=_cab(), json={
        "autorizar_bajo_piso": True,
        "motivo_excepcion": "Cliente estratégico: se autoriza bajo piso.",
    })
    assert r.status_code == 200, r.text
    assert r.json()["estimacion"]["estado"] == "emitida"


async def test_ca09_descuento_tope_por_rol(cli):
    """CA-09: el agrónomo no puede exceder su tope; el administrador sí."""
    await _semilla()
    async with async_session_factory() as db:
        from agroia_backend.models.costeo import CosteoConjunto
        semilla = (await db.execute(
            select(CosteoConjunto).where(CosteoConjunto.estado == "publicado")
            .order_by(CosteoConjunto.version.desc())
        )).scalars().first()
        semilla_id = str(semilla.id)

    async def editar(cli, conjunto_id):
        r = await cli.post(f"/api/v1/costeo/conjuntos/{conjunto_id}/descuentos",
                           headers=_cab(uid=EDITOR), json={
                               "codigo": "manual", "criterio": "manual", "umbral": 0,
                               "porcentaje": 50,
                               "tope_rol": {"agronomo": 5, "agrónomo": 5, "admin": 50},
                           })
        assert r.status_code == 201, r.text

    await _crear_y_publicar(cli, nombre="Topes descuento", clon_de=semilla_id, editar=editar)

    r = await cli.post("/api/v1/estimaciones", headers=_cab(rol="Agronomo"), json={
        "finca_id": await _finca_id(),
        "lotes": [{"area_ha": 1, "puntos": 10,
                   "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": 10}]}],
        "factores": {"dificultad": "plano"},
        "descuento_pct": 20,
    })
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "DESCUENTO_EXCEDE_TOPE"

    r = await cli.post("/api/v1/estimaciones", headers=_cab(rol="Admin"), json={
        "finca_id": await _finca_id(),
        "lotes": [{"area_ha": 1, "puntos": 10,
                   "servicios": [{"codigo": "muestreo_en_grilla", "cantidad": 10}]}],
        "factores": {"dificultad": "plano"},
        "descuento_pct": 20,
    })
    assert r.status_code == 201, r.text


async def test_export_html_y_pdf(cli):
    """RF-21/26: exportación HTML/PDF de una cotización emitida."""
    await _semilla()
    est_id = await _crear_estimacion(cli)
    await cli.post(f"/api/v1/estimaciones/{est_id}/emitir", headers=_cab(), json={})
    r = await cli.get(f"/api/v1/estimaciones/{est_id}/export?formato=html&audiencia=agricultor",
                      headers=_cab())
    assert r.status_code == 200
    assert "COTIZACIÓN" in r.text
    r = await cli.get(f"/api/v1/estimaciones/{est_id}/export?formato=pdf&audiencia=agricultor",
                      headers=_cab())
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")


# ─────────────────────────── F4 · identidad ───────────────────────────

async def test_ca10_ca11_identidad_telefonos_logo_pdf(cli):
    """CA-10/CA-11: teléfonos ordenados y logo nuevo se reflejan en el PDF."""
    r = await cli.get("/api/v1/costeo/identidad", headers=_cab())
    assert r.status_code == 200
    r = await cli.put("/api/v1/costeo/identidad", headers=_cab(), json={
        "nombre_comercial": "AgroIA Pruebas",
        "sitio_web": "https://ejemplo.co",
        "telefonos": [
            {"etiqueta": "Principal", "numero": "3001111111", "whatsapp": False, "orden": 0},
            {"etiqueta": "WhatsApp", "numero": "3242013807", "whatsapp": True, "orden": 1},
        ],
    })
    assert r.status_code == 200, r.text
    telefonos = r.json()["identidad"]["telefonos"]
    assert [t["etiqueta"] for t in telefonos] == ["Principal", "WhatsApp"]

    # Logo PNG válido (mínimo 32 bytes) — reportlab lo descarga al componer el PDF.
    logo = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0dIDATx\x9cc\xf8\xcf"
        b"\xc0\xf0\x1f\x00\x05\x05\x02\x00\x9f\x9b\x83U\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    r = await cli.post("/api/v1/costeo/identidad/logo", headers=_cab(),
                       files={"archivo": ("logo.png", logo, "image/png")},
                       data={"oscuro": "false"})
    assert r.status_code == 200, r.text
    assert r.json()["logo_url"].startswith("/media/logos/")

    r = await cli.get("/api/v1/costeo/identidad", headers=_cab())
    assert r.status_code == 200
    assert r.json()["identidad"]["telefonos"][1]["etiqueta"] == "WhatsApp"


# ─────────────────────────── F5 · cobros ───────────────────────────

async def _aceptada(cli) -> str:
    await _semilla()
    est_id = await _crear_estimacion(cli)
    await cli.post(f"/api/v1/estimaciones/{est_id}/emitir", headers=_cab(), json={})
    await cli.post(f"/api/v1/estimaciones/{est_id}/aceptar", headers=_cab(), json={})
    return est_id


async def test_ca12_conversion_y_numeracion(cli):
    """CA-12: hereda líneas y total, recibe consecutivo y queda enlazado."""
    est_id = await _aceptada(cli)
    r = await cli.post(f"/api/v1/cobros?estimacion_id={est_id}", headers=_cab())
    assert r.status_code == 201, r.text
    doc = r.json()["documento"]
    assert doc["estado"] == "borrador"
    assert doc["total"] == 250000.0
    assert doc["lineas"]

    r = await cli.post(f"/api/v1/cobros/{doc['id']}/emitir", headers=_cab())
    assert r.status_code == 200, r.text
    doc = r.json()["documento"]
    assert doc["estado"] == "emitido"
    assert doc["numero"] == "CC-1"

    r = await cli.get("/api/v1/cobros?limite=100", headers=_cab())
    assert any(d["id"] == doc["id"] for d in r.json()["data"])


async def test_ca13_pagos_y_saldo(cli):
    """CA-13: abono parcial → pagado parcial; completar → pagado."""
    est_id = await _aceptada(cli)
    r = await cli.post(f"/api/v1/cobros?estimacion_id={est_id}", headers=_cab())
    doc_id = r.json()["documento"]["id"]
    await cli.post(f"/api/v1/cobros/{doc_id}/emitir", headers=_cab())

    r = await cli.post(f"/api/v1/cobros/{doc_id}/pagos", headers=_cab(),
                       json={"valor": 100000, "medio": "transferencia"})
    assert r.status_code == 201, r.text
    doc = r.json()["documento"]
    assert doc["estado"] == "pagado_parcial"
    assert doc["saldo"] == 150000.0

    r = await cli.post(f"/api/v1/cobros/{doc_id}/pagos", headers=_cab(),
                       json={"valor": 150000, "medio": "efectivo"})
    assert r.status_code == 201, r.text
    doc = r.json()["documento"]
    assert doc["estado"] == "pagado"
    assert doc["saldo"] == 0.0


async def test_ca14_anulacion_y_nuevo_documento(cli):
    """CA-14: anular con motivo no borra; la estimación admite documento nuevo."""
    est_id = await _aceptada(cli)
    r = await cli.post(f"/api/v1/cobros?estimacion_id={est_id}", headers=_cab())
    doc_id = r.json()["documento"]["id"]
    await cli.post(f"/api/v1/cobros/{doc_id}/emitir", headers=_cab())

    r = await cli.post(f"/api/v1/cobros/{doc_id}/anular", headers=_cab(),
                       json={"motivo": "Error de digitación en los valores."})
    assert r.status_code == 200, r.text
    doc = r.json()["documento"]
    assert doc["estado"] == "anulado"
    assert doc["motivo_anulacion"]

    r = await cli.post(f"/api/v1/cobros?estimacion_id={est_id}", headers=_cab())
    assert r.status_code == 201, r.text


async def test_ca15_numeracion_agotada(cli):
    """CA-15: con el rango agotado la emisión se rechaza con NUMERACION_AGOTADA."""
    est_id = await _aceptada(cli)
    r = await cli.post(f"/api/v1/cobros?estimacion_id={est_id}", headers=_cab())
    doc_id = r.json()["documento"]["id"]
    await cli.post(f"/api/v1/cobros/{doc_id}/emitir", headers=_cab())

    r = await cli.put("/api/v1/costeo/cobro-config", headers=_cab(), json={
        "tipo_documento": "cuenta_cobro", "prefijo": "CC",
        "numero_desde": 1, "numero_hasta": 1,
        "plazo_pago_dias": 30, "medios_pago": {}, "textos_legales": {},
        "aviso_numeracion_restante": 0,
    })
    assert r.status_code == 200, r.text

    est2 = await _aceptada(cli)
    r = await cli.post(f"/api/v1/cobros?estimacion_id={est2}", headers=_cab())
    doc2 = r.json()["documento"]["id"]
    r = await cli.post(f"/api/v1/cobros/{doc2}/emitir", headers=_cab())
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "NUMERACION_AGOTADA"


# ─────────────────────────── F6 · comisión ───────────────────────────

async def test_f6_convertir_en_comision(cli):
    """RF-20: la comisión creada referencia la estimación y precarga el equipo."""
    est_id = await _aceptada(cli)
    r = await cli.post(f"/api/v1/estimaciones/{est_id}/convertir-comision", headers=_cab())
    assert r.status_code == 200, r.text
    comision = r.json()["comision"]
    assert comision["valor_comision_cop"] == 250000.0
    # Segunda conversión se rechaza.
    r = await cli.post(f"/api/v1/estimaciones/{est_id}/convertir-comision", headers=_cab())
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "COMISION_YA_CREADA"


async def test_f6_lista_trabajos_etapa_estimacion(cli):
    """F6: el semáforo incluye la etapa «estimación» previa a la comisión."""
    r = await cli.get("/api/v1/admin/lista-trabajos", headers=_cab())
    assert r.status_code == 200, r.text
    body = r.json()
    assert "estimacion" in body["etiquetas_etapa"]
    assert body["etiquetas_etapa"]["estimacion"].startswith("Estimación de costos")


# ─────────────────────────── F7 · tablero ───────────────────────────

async def test_f7_tablero(cli):
    await _semilla()
    await _crear_estimacion(cli)
    r = await cli.get("/api/v1/estimaciones/tablero", headers=_cab())
    assert r.status_code == 200, r.text
    body = r.json()
    assert "totales" in body
    assert "tasa_conversion" in body
    assert isinstance(body["totales"]["total"], int)
