"""Servicio de dominio AGC-COST — documentos de cobro (F5).

El documento hereda las líneas de una estimación aceptada, se emite con
numeración consecutiva asignada en el servidor con bloqueo (CA-12/CA-15),
recibe pagos con cálculo de saldo (CA-13) y se anula con motivo sin
borrarse nunca (CA-14 / RF-31).
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.cobros import (
    CobroDocumento,
    CobroEvento,
    CobroLinea,
    CobroPago,
)
from agroia_backend.models.costeo_fases import CobroConfig
from agroia_backend.models.estimaciones import Estimacion, EstimacionLinea

_ESTADOS_VIGENTES = {"emitido", "enviado", "pagado_parcial", "vencido"}


class CobroError(Exception):
    """Error de negocio del flujo de cobro."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _dec(v) -> Decimal:
    if v is None:
        return Decimal("0")
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


async def _config_vigente(db: AsyncSession, for_update: bool = False) -> CobroConfig:
    stmt = select(CobroConfig).order_by(CobroConfig.creado_en.desc()).limit(1)
    if for_update:
        stmt = stmt.with_for_update()
    config = (await db.execute(stmt)).scalars().one_or_none()
    if config is None:
        raise CobroError(
            "COBRO_SIN_CONFIGURACION",
            "No hay configuración de documentos de cobro. Configúrela en Parámetros de costeo.",
        )
    return config


async def crear_desde_estimacion(
    db: AsyncSession,
    estimacion: Estimacion,
    *,
    usuario_id,
    identidad_snapshot: dict | None,
    usuario_email: str,
    usuario_nombre: str | None,
    rol: str | None,
    auditor,
) -> CobroDocumento:
    """Crea el documento de cobro (borrador) desde una estimación aceptada."""
    if estimacion.estado != "aceptada":
        raise CobroError(
            "ESTIMACION_NO_ACEPTADA",
            "Solo una estimación aceptada puede convertirse en documento de cobro.",
        )
    if estimacion.vence_en and estimacion.vence_en < date.today():
        raise CobroError(
            "ESTIMACION_VENCIDA",
            "La estimación está vencida y ya no puede convertirse en documento de cobro.",
        )
    existente = (
        await db.execute(
            select(CobroDocumento).where(
                CobroDocumento.estimacion_id == estimacion.id,
                CobroDocumento.estado != "anulado",
            )
        )
    ).scalars().first()
    if existente is not None:
        raise CobroError(
            "COBRO_YA_EXISTE",
            "La estimación ya tiene un documento de cobro vigente.",
        )

    config = await _config_vigente(db)
    documento = CobroDocumento(
        estimacion_id=estimacion.id,
        cliente_id=estimacion.cliente_id,
        tipo=config.tipo_documento,
        estado="borrador",
        subtotal=estimacion.total_final,
        impuestos=Decimal("0"),
        total=estimacion.total_final,
        saldo=estimacion.total_final,
        identidad_snapshot=identidad_snapshot,
    )
    db.add(documento)
    await db.flush()

    lineas = (
        await db.execute(
            select(EstimacionLinea).where(
                EstimacionLinea.estimacion_id == estimacion.id
            ).order_by(EstimacionLinea.creado_en)
        )
    ).scalars().all()
    for ln in lineas:
        db.add(CobroLinea(
            documento_id=documento.id,
            descripcion=ln.descripcion,
            cantidad=ln.cantidad,
            unidad=ln.unidad,
            valor_unitario=ln.valor_unitario,
            valor=ln.valor,
        ))
    db.add(CobroEvento(
        documento_id=documento.id,
        evento="creado",
        usuario_id=usuario_id,
        comentario=f"Desde la estimación {estimacion.consecutivo or estimacion.id}.",
    ))
    if auditor is not None:
        await auditor(
            db,
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            rol=rol,
            accion="cobro.crear",
            entidad="cobro_documento",
            entidad_id=str(documento.id),
            detalle={"estimacion_id": str(estimacion.id)},
        )
    await db.flush()
    return documento


async def emitir(
    db: AsyncSession,
    documento: CobroDocumento,
    *,
    usuario_id,
    usuario_email: str,
    usuario_nombre: str | None,
    rol: str | None,
    auditor,
) -> CobroDocumento:
    """Asigna consecutivo con bloqueo en servidor y congela el documento."""
    if documento.estado != "borrador":
        raise CobroError("COBRO_YA_EMITIDO", "El documento ya fue emitido o anulado.")

    # Bloquea la configuración para serializar la numeración (CA-15 / RF-30).
    config = await _config_vigente(db, for_update=True)
    hoy = date.today()
    if config.tipo_documento == "factura_venta" and config.resolucion_vigencia_hasta:
        if config.resolucion_vigencia_hasta < hoy:
            raise CobroError(
                "RESOLUCION_VENCIDA",
                "La resolución DIAN configurada venció; no se pueden emitir documentos.",
            )

    ultimo = (
        await db.execute(
            select(func.max(CobroDocumento.consecutivo)).where(
                CobroDocumento.prefijo == config.prefijo
            )
        )
    ).scalar_one_or_none()
    siguiente = int(ultimo or 0) + 1 if ultimo else config.numero_desde
    if siguiente > config.numero_hasta:
        raise CobroError(
            "NUMERACION_AGOTADA",
            f"La numeración del prefijo «{config.prefijo}» se agotó (límite "
            f"{config.numero_hasta}). Configure un rango nuevo o una resolución nueva.",
        )

    documento.prefijo = config.prefijo
    documento.consecutivo = siguiente
    documento.fecha_emision = hoy
    documento.fecha_vencimiento = hoy + timedelta(days=config.plazo_pago_dias or 30)
    documento.estado = "emitido"
    if documento.identidad_snapshot is None:
        documento.identidad_snapshot = {}
    db.add(CobroEvento(
        documento_id=documento.id,
        evento="emitido",
        usuario_id=usuario_id,
        comentario=f"Consecutivo {config.prefijo}-{siguiente}.",
    ))
    if auditor is not None:
        await auditor(
            db,
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            rol=rol,
            accion="cobro.emitir",
            entidad="cobro_documento",
            entidad_id=str(documento.id),
            detalle={"numero": f"{config.prefijo}-{siguiente}"},
        )
    await db.flush()
    return documento


async def registrar_pago(
    db: AsyncSession,
    documento: CobroDocumento,
    *,
    usuario_id,
    fecha: date,
    valor: Decimal,
    medio: str | None,
    referencia: str | None,
    usuario_email: str,
    usuario_nombre: str | None,
    rol: str | None,
    auditor,
) -> CobroPago:
    """Registra un pago y recalcula saldo y estado (CA-13 / RF-32)."""
    if documento.estado not in _ESTADOS_VIGENTES:
        raise CobroError(
            "COBRO_NO_PAGABLE",
            f"Un documento en estado «{documento.estado}» no admite pagos.",
        )
    valor = _dec(valor)
    if valor <= 0:
        raise CobroError("PAGO_INVALIDO", "El valor del pago debe ser mayor que cero.")
    if valor > documento.saldo:
        raise CobroError(
            "PAGO_EXCEDE_SALDO",
            f"El pago (${valor:,.0f}) supera el saldo pendiente (${documento.saldo:,.0f}).",
        )
    pago = CobroPago(
        documento_id=documento.id,
        fecha=fecha or date.today(),
        valor=valor,
        medio=medio,
        referencia=referencia,
        registrado_por=usuario_id,
    )
    db.add(pago)
    documento.saldo = documento.saldo - valor
    if documento.saldo <= 0:
        documento.estado = "pagado"
    else:
        documento.estado = "pagado_parcial"
    db.add(CobroEvento(
        documento_id=documento.id,
        evento="pago",
        usuario_id=usuario_id,
        comentario=(
            f"Abono de ${valor:,.0f} por {medio or '—'}. "
            f"Saldo pendiente: ${documento.saldo:,.0f}."
        ),
    ))
    if auditor is not None:
        await auditor(
            db,
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            rol=rol,
            accion="cobro.pago",
            entidad="cobro_documento",
            entidad_id=str(documento.id),
            detalle={"valor": str(valor), "medio": medio},
        )
    await db.flush()
    return pago


async def anular(
    db: AsyncSession,
    documento: CobroDocumento,
    *,
    usuario_id,
    motivo: str,
    usuario_email: str,
    usuario_nombre: str | None,
    rol: str | None,
    auditor,
) -> CobroDocumento:
    """Anula un documento emitido con motivo obligatorio (CA-14 / RF-31)."""
    if documento.estado not in _ESTADOS_VIGENTES:
        raise CobroError(
            "COBRO_NO_ANULABLE",
            f"Un documento en estado «{documento.estado}» no se puede anular.",
        )
    if not motivo or not motivo.strip():
        raise CobroError(
            "MOTIVO_ANULACION_REQUERIDO",
            "La anulación exige un motivo obligatorio.",
        )
    documento.estado = "anulado"
    documento.anulado_por = usuario_id
    documento.motivo_anulacion = motivo.strip()
    documento.saldo = Decimal("0")
    db.add(CobroEvento(
        documento_id=documento.id,
        evento="anulado",
        usuario_id=usuario_id,
        comentario=motivo.strip(),
    ))
    if auditor is not None:
        await auditor(
            db,
            usuario_email=usuario_email,
            usuario_nombre=usuario_nombre,
            rol=rol,
            accion="cobro.anular",
            entidad="cobro_documento",
            entidad_id=str(documento.id),
            detalle={"motivo": motivo.strip()},
        )
    await db.flush()
    return documento


async def marcar_enviado(
    db: AsyncSession,
    documento: CobroDocumento,
    *,
    usuario_id,
    canal: str,
    destinatario: str,
) -> CobroDocumento:
    """Marca el documento como enviado y registra el evento (RF-33)."""
    if documento.estado == "borrador":
        raise CobroError("COBRO_NO_ENVIABLE", "El documento debe emitirse antes de enviarse.")
    if documento.estado in ("anulado", "pagado"):
        raise CobroError("COBRO_NO_ENVIABLE", "El documento no se puede enviar en su estado.")
    db.add(CobroEvento(
        documento_id=documento.id,
        evento="enviado",
        usuario_id=usuario_id,
        comentario=f"Enviado por {canal} a {destinatario}.",
    ))
    if documento.estado == "emitido":
        documento.estado = "enviado"
    await db.flush()
    return documento


async def _id_valido(valor: str | None) -> uuid.UUID | None:
    """Convierte un string a UUID o devuelve None (sin lanzar)."""
    if not valor:
        return None
    try:
        return uuid.UUID(str(valor))
    except ValueError:
        return None
