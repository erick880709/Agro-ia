"""Seed idempotente del conjunto de parámetros semilla de costeo (RFP §15).

El conjunto semilla carga los valores ilustrativos del estudio de tarifas de
muestreo en grilla, marcados como provisionales y sustituibles el primer día
de operación (RFP §20). Es dato sembrado, no constante del código: el motor
solo interpreta lo que encuentra en `costeo_*`.

  - Tarifa base:        $100.000
  - Tramos escalonados: 1–15 → $15.000 · 16–30 → $10.000 · 31+ → $7.000
  - Factor dificultad:  plano 0% · pendiente moderada 15% · acceso difícil 30%
  - Política:           sin margen, sin descuento, sin redondeo
  - IVA 19% informativo (no suma al total)
"""

from datetime import date
from decimal import Decimal

from agroia.logging import get_logger
from sqlalchemy import select, text

logger = get_logger(__name__)

SEMILLA_NOMBRE = "Estudio de tarifas — semilla (ilustrativo)"
SEMILLA_VERSION = 1


async def asegurar_conjunto_semilla(db=None) -> dict:
    """Crea el conjunto publicado vigente si no existe. Devuelve resumen."""
    if db is not None:
        return await _sembrar(db)
    from agroia.database import async_session_factory

    async with async_session_factory() as db:
        return await _sembrar(db)


async def _sembrar(db) -> dict:
    from agroia_backend.models.costeo import (
        CosteoComponente,
        CosteoConjunto,
        CosteoFactor,
        CosteoFactorOpcion,
        CosteoImpuesto,
        CosteoPolitica,
        CosteoServicio,
        CosteoTramo,
    )

    await db.execute(text("SET LOCAL search_path TO public, agroia"))
    existente = (
        await db.execute(
            select(CosteoConjunto).where(
                CosteoConjunto.nombre == SEMILLA_NOMBRE,
                CosteoConjunto.estado == "publicado",
            )
        )
    ).scalars().first()
    if existente is not None:
        await asegurar_identidad_semilla(db)
        await asegurar_cobro_config_semilla(db)
        return {"creado": False, "conjunto_id": str(existente.id)}

    conjunto = CosteoConjunto(
        nombre=SEMILLA_NOMBRE,
        version=SEMILLA_VERSION,
        estado="publicado",
        vigencia_desde=date(2026, 1, 1),
        moneda="COP",
        notas=(
            "Valores ilustrativos del estudio interno de tarifas; no constituyen "
            "tarifa de mercado confirmada. Sustituir antes de operación real."
        ),
    )
    db.add(conjunto)
    await db.flush()

    servicio = CosteoServicio(
        conjunto_id=conjunto.id,
        codigo="muestreo_en_grilla",
        nombre="Muestreo de suelos en grilla",
        unidad="punto",
        requiere_lote=True,
        activo=True,
        orden=1,
    )
    db.add(servicio)
    await db.flush()

    base = CosteoComponente(
        servicio_id=servicio.id,
        codigo="tarifa_base",
        nombre="Tarifa base (desplazamiento + montaje)",
        tipo="fijo",
        orden=1,
        afectable_por_factores=True,
        config={"valor": "100000"},
    )
    db.add(base)
    await db.flush()

    puntos_comp = CosteoComponente(
        servicio_id=servicio.id,
        codigo="puntos_muestreo",
        nombre="Puntos de muestreo (escalonado)",
        tipo="escalonado",
        orden=2,
        afectable_por_factores=True,
        config={},
    )
    db.add(puntos_comp)
    await db.flush()

    for desde, hasta, valor in (
        ("1", "15", "15000"),
        ("16", "30", "10000"),
        ("31", None, "7000"),
    ):
        db.add(CosteoTramo(
            componente_id=puntos_comp.id,
            desde=Decimal(desde),
            hasta=Decimal(hasta) if hasta else None,
            valor=Decimal(valor),
            modo="marginal",
        ))

    factor = CosteoFactor(
        conjunto_id=conjunto.id,
        codigo="dificultad",
        nombre="Dificultad del terreno",
        aplicacion="porcentual",
        combinacion="suma",
    )
    db.add(factor)
    await db.flush()

    for orden, (codigo, etiqueta, pct) in enumerate((
        ("plano", "Plano", "0"),
        ("pendiente_moderada", "Pendiente moderada", "15"),
        ("acceso_dificil", "Acceso difícil", "30"),
    ), start=1):
        db.add(CosteoFactorOpcion(
            factor_id=factor.id,
            codigo=codigo,
            etiqueta=etiqueta,
            porcentaje=Decimal(pct),
            orden=orden,
        ))

    db.add(CosteoPolitica(
        conjunto_id=conjunto.id,
        margen_objetivo=Decimal("0"),
        margen_minimo=Decimal("0"),
        piso_visita=Decimal("0"),
        vigencia_cotizacion_dias=30,
        redondeo_multiplo=Decimal("1"),
        redondeo_modo="ninguno",
    ))

    db.add(CosteoImpuesto(
        conjunto_id=conjunto.id,
        codigo="IVA",
        nombre="IVA",
        porcentaje=Decimal("19"),
        base="subtotal",
        informativo=True,
    ))

    await db.commit()
    logger.info("costeo_semilla_creada", conjunto_id=str(conjunto.id))
    await asegurar_identidad_semilla(db)
    await asegurar_cobro_config_semilla(db)
    return {"creado": True, "conjunto_id": str(conjunto.id)}


async def asegurar_identidad_semilla(db) -> dict:
    """Identidad y contactos semilla (P-14): AgroIA con datos de la operación.

    Idempotente: solo crea si no existe identidad. Los valores son datos
    sembrados sustituibles desde la pantalla de parámetros (RF-26/27).
    """
    from agroia_backend.models.costeo_fases import CosteoIdentidad, CosteoTelefono

    existente = (
        await db.execute(select(CosteoIdentidad).limit(1))
    ).scalars().first()
    if existente is not None:
        return {"creado": False, "identidad_id": str(existente.id)}

    identidad = CosteoIdentidad(
        nombre_comercial="AgroIA — AgroInteligente Colombia",
        razon_social="Agrointeligente Colombia",
        nit="(registrar NIT)",
        regimen="Persona natural",
        sitio_web="https://jeepaoaisystems.com",
        correo="contacto@agroia.co",
        ciudad="Pereira, Colombia",
        color_acento="#1b5e20",
        pie_legal="AgroIA · Agrointeligente Colombia. Cotización generada por el "
                  "módulo AGC-COST; los valores son una oferta y no un compromiso "
                  "hasta su aceptación.",
    )
    db.add(identidad)
    await db.flush()
    db.add(CosteoTelefono(
        identidad_id=identidad.id,
        etiqueta="Principal",
        numero="3242013807",
        whatsapp=True,
        orden=0,
    ))
    await db.commit()
    logger.info("costeo_identidad_semilla_creada", identidad_id=str(identidad.id))
    return {"creado": True, "identidad_id": str(identidad.id)}


async def asegurar_cobro_config_semilla(db) -> dict:
    """Configuración de documentos de cobro semilla (P-15): cuenta de cobro.

    Cuenta de cobro CC-1 a CC-10000, plazo 30 días, aviso de numeración
    cuando queden 10. Idempotente.
    """
    from agroia_backend.models.costeo_fases import CobroConfig

    existente = (
        await db.execute(select(CobroConfig).limit(1))
    ).scalars().first()
    if existente is not None:
        return {"creado": False, "config_id": str(existente.id)}

    config = CobroConfig(
        tipo_documento="cuenta_cobro",
        prefijo="CC",
        numero_desde=1,
        numero_hasta=10000,
        plazo_pago_dias=30,
        medios_pago={"transferencia": "Transferencia bancaria", "efectivo": "Efectivo"},
        aviso_numeracion_restante=10,
        textos_legales={
            "pie": "Documento generado por AgroIA. Cuenta de cobro — no requiere "
                   "validación DIAN. La factura de venta electrónica se habilitará "
                   "en una fase posterior (RFP §17).",
        },
    )
    db.add(config)
    await db.commit()
    logger.info("costeo_cobro_config_semilla_creada", config_id=str(config.id))
    return {"creado": True, "config_id": str(config.id)}
