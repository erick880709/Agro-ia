"""API AGC-COST (F4) — identidad administrable y logo; config de cobro (P-15).

RF-26/27: logo con validación PNG/SVG, sitio web, correo, dirección y
teléfonos ordenables; los cambios se reflejan en el PDF sin desplegar.
El logo se guarda en el directorio de medios y se referencia por URL estable.
"""

import os
from pathlib import Path

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.costeo_fases import CobroConfig, CosteoIdentidad, CosteoTelefono
from agroia_backend.services.auth_contexto import ROLES_ADMIN, contexto_usuario
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/costeo", tags=["costeo-identidad"])

_MAX_LOGO_BYTES = 2 * 1024 * 1024
# Mismo directorio de medios que sirve main.py en /media (StaticFiles).
_MEDIA_BASE = Path(
    os.environ.get("AGROIA_MEDIA_DIR")
    or Path(__file__).resolve().parents[4] / "media"
)
_MEDIA_DIR = _MEDIA_BASE / "logos"


def _err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


async def _identidad_o_crear(db: AsyncSession) -> CosteoIdentidad:
    identidad = (
        await db.execute(select(CosteoIdentidad).order_by(CosteoIdentidad.creado_en.desc()))
    ).scalars().first()
    if identidad is None:
        identidad = CosteoIdentidad(nombre_comercial="AgroIA — AgroInteligente Colombia")
        db.add(identidad)
        await db.flush()
    return identidad


def _identidad_a_dict(identidad: CosteoIdentidad, telefonos: list[CosteoTelefono]) -> dict:
    return {
        "id": str(identidad.id),
        "nombre_comercial": identidad.nombre_comercial,
        "razon_social": identidad.razon_social,
        "nit": identidad.nit,
        "regimen": identidad.regimen,
        "sitio_web": identidad.sitio_web,
        "correo": identidad.correo,
        "direccion": identidad.direccion,
        "ciudad": identidad.ciudad,
        "logo_url": identidad.logo_url,
        "logo_oscuro_url": identidad.logo_oscuro_url,
        "color_acento": identidad.color_acento,
        "pie_legal": identidad.pie_legal,
        "terminos_condiciones": identidad.terminos_condiciones,
        "sede_latitud": identidad.sede_latitud,
        "sede_longitud": identidad.sede_longitud,
        "telefonos": [
            {"id": str(t.id), "etiqueta": t.etiqueta, "numero": t.numero,
             "whatsapp": t.whatsapp, "orden": t.orden}
            for t in sorted(telefonos, key=lambda x: x.orden)
        ],
    }


@router.get("/identidad")
async def ver_identidad(request: Request, db: AsyncSession = Depends(get_db)):
    """Identidad y contactos vigentes para encabezados y PDF (autenticado)."""
    contexto_usuario(request)
    identidad = await _identidad_o_crear(db)
    telefonos = (
        await db.execute(select(CosteoTelefono).where(CosteoTelefono.identidad_id == identidad.id))
    ).scalars().all()
    return {"identidad": _identidad_a_dict(identidad, telefonos)}


class TelefonoIn(BaseModel):
    etiqueta: str = Field(..., min_length=1, max_length=40)
    numero: str = Field(..., min_length=3, max_length=20)
    whatsapp: bool = False
    orden: int = 0


class IdentidadIn(BaseModel):
    nombre_comercial: str = Field(..., min_length=2, max_length=150)
    razon_social: str | None = Field(None, max_length=150)
    nit: str | None = Field(None, max_length=30)
    regimen: str | None = Field(None, max_length=40)
    sitio_web: str | None = Field(None, max_length=200)
    correo: str | None = Field(None, max_length=120)
    direccion: str | None = Field(None, max_length=200)
    ciudad: str | None = Field(None, max_length=100)
    color_acento: str | None = Field(None, max_length=9)
    pie_legal: str | None = None
    terminos_condiciones: str | None = None
    sede_latitud: float | None = Field(None, ge=-90, le=90)
    sede_longitud: float | None = Field(None, ge=-180, le=180)
    telefonos: list[TelefonoIn] = Field(default_factory=list)


@router.put("/identidad")
async def actualizar_identidad(
    body: IdentidadIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza identidad y lista de teléfonos con etiqueta y orden (RF-27)."""
    usuario = contexto_usuario(request, ROLES_ADMIN)
    identidad = await _identidad_o_crear(db)
    for campo in (
        "nombre_comercial", "razon_social", "nit", "regimen", "sitio_web",
        "correo", "direccion", "ciudad", "color_acento",
        "pie_legal", "terminos_condiciones", "sede_latitud", "sede_longitud",
    ):
        setattr(identidad, campo, getattr(body, campo))
    await db.flush()

    await db.execute(
        delete(CosteoTelefono).where(CosteoTelefono.identidad_id == identidad.id)
    )
    for t in body.telefonos:
        db.add(CosteoTelefono(
            identidad_id=identidad.id,
            etiqueta=t.etiqueta,
            numero=t.numero,
            whatsapp=t.whatsapp,
            orden=t.orden,
        ))
    await db.flush()
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion="costeo.identidad.editar",
        entidad="costeo_identidad",
        entidad_id=str(identidad.id),
        detalle={"telefonos": [t.model_dump() for t in body.telefonos]},
    )
    await db.commit()
    telefonos = (
        await db.execute(select(CosteoTelefono).where(CosteoTelefono.identidad_id == identidad.id))
    ).scalars().all()
    return {"identidad": _identidad_a_dict(identidad, telefonos)}


@router.post("/identidad/logo")
async def cargar_logo(
    request: Request,
    db: AsyncSession = Depends(get_db),
    archivo: UploadFile = File(...),
    oscuro: bool = Form(False),
):
    """Carga el logo PNG/SVG con validación de formato y tamaño (RF-27)."""
    usuario = contexto_usuario(request, ROLES_ADMIN)
    nombre = (archivo.filename or "").lower()
    if not (nombre.endswith(".png") or nombre.endswith(".svg")):
        raise _err(
            422,
            "LOGO_FORMATO_INVALIDO",
            "El logo debe ser PNG o SVG.",
        )
    contenido = await archivo.read()
    if len(contenido) > _MAX_LOGO_BYTES:
        raise _err(422, "LOGO_MUY_GRANDE", "El logo supera el tamaño máximo (2 MB).")
    if len(contenido) < 32:
        raise _err(422, "LOGO_VACIO", "El archivo del logo está vacío o corrupto.")

    identidad = await _identidad_o_crear(db)
    _MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    extension = "png" if nombre.endswith(".png") else "svg"
    archivo_nombre = f"logo_{identidad.id.hex[:12]}_{'oscuro' if oscuro else 'claro'}.{extension}"
    destino = _MEDIA_DIR / archivo_nombre
    destino.write_bytes(contenido)

    url = f"/media/logos/{archivo_nombre}"
    if oscuro:
        identidad.logo_oscuro_url = url
    else:
        identidad.logo_url = url
    await db.flush()
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion="costeo.identidad.logo",
        entidad="costeo_identidad",
        entidad_id=str(identidad.id),
        detalle={"url": url, "oscuro": oscuro, "formato": extension},
    )
    await db.commit()
    return {"logo_url": url, "oscuro": oscuro}


# ─────────────────────────── Config de cobro (P-15) ─────────────────────────

class CobroConfigIn(BaseModel):
    tipo_documento: str = Field("cuenta_cobro", pattern="^(cuenta_cobro|factura_venta)$")
    prefijo: str = Field("CC", min_length=1, max_length=10)
    numero_desde: int = Field(1, ge=1)
    numero_hasta: int = Field(10000, ge=1)
    resolucion_dian: str | None = Field(None, max_length=40)
    resolucion_vigencia_hasta: str | None = None
    plazo_pago_dias: int = Field(30, ge=1, le=3650)
    medios_pago: dict = Field(default_factory=dict)
    cuenta_bancaria: str | None = None
    textos_legales: dict = Field(default_factory=dict)
    aviso_numeracion_restante: int = Field(10, ge=0)


def _config_a_dict(c: CobroConfig) -> dict:
    return {
        "id": str(c.id),
        "tipo_documento": c.tipo_documento,
        "prefijo": c.prefijo,
        "numero_desde": c.numero_desde,
        "numero_hasta": c.numero_hasta,
        "resolucion_dian": c.resolucion_dian,
        "resolucion_vigencia_hasta": c.resolucion_vigencia_hasta.isoformat()
        if c.resolucion_vigencia_hasta else None,
        "plazo_pago_dias": c.plazo_pago_dias,
        "medios_pago": c.medios_pago or {},
        "cuenta_bancaria": c.cuenta_bancaria,
        "textos_legales": c.textos_legales or {},
        "aviso_numeracion_restante": c.aviso_numeracion_restante,
    }


@router.get("/cobro-config")
async def ver_cobro_config(request: Request, db: AsyncSession = Depends(get_db)):
    contexto_usuario(request, ROLES_ADMIN)
    config = (
        await db.execute(select(CobroConfig).order_by(CobroConfig.creado_en.desc()))
    ).scalars().first()
    if config is None:
        raise _err(404, "COBRO_SIN_CONFIGURACION", "Aún no hay configuración de documentos de cobro.")
    return {"config": _config_a_dict(config)}


@router.put("/cobro-config")
async def actualizar_cobro_config(
    body: CobroConfigIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    usuario = contexto_usuario(request, ROLES_ADMIN)
    config = (
        await db.execute(select(CobroConfig).order_by(CobroConfig.creado_en.desc()))
    ).scalars().first()
    datos = body.model_dump()
    if datos.get("resolucion_vigencia_hasta"):
        from datetime import date as _date

        datos["resolucion_vigencia_hasta"] = _date.fromisoformat(datos["resolucion_vigencia_hasta"])
    else:
        datos["resolucion_vigencia_hasta"] = None
    if config is None:
        config = CobroConfig(**datos)
        db.add(config)
    else:
        for campo, valor in datos.items():
            setattr(config, campo, valor)
    await db.flush()
    await registrar_auditoria(
        db,
        usuario_email=usuario["email"],
        usuario_nombre=usuario["nombre"],
        rol=usuario["rol"],
        accion="costeo.cobro_config.editar",
        entidad="cobro_config",
        entidad_id=str(config.id),
        detalle={"prefijo": config.prefijo, "rango": [config.numero_desde, config.numero_hasta]},
    )
    await db.commit()
    return {"config": _config_a_dict(config)}
