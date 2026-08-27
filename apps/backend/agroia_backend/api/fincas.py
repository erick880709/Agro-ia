"""API de fincas: listado (público) y registro (solo administrador).

El registro exige el rol administrador vía cabecera `X-User-Role`.
Nota: es una comprobación de rol de etapa MVP mientras el Auth Service
(JWT/RBAC) no esté desplegado; el frontend envía la cabecera con el rol
activo de la sesión demo.
"""

import re
import uuid as uuid_mod

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.finca import Finca

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["fincas"])

ROL_ADMIN = {"admin", "administrador"}
ROL_EXPERTOS = {"admin", "administrador", "agronomo", "agrónomo"}

# Enlaces Google Maps con coordenadas: q=lat,lng · @lat,lng,zoom · place/.../@lat,lng
_RE_LATLNG_URL = re.compile(r"(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)")
_RE_PAR = re.compile(r"^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$")


def _extraer_coordenadas(texto: str) -> tuple[float | None, float | None]:
    """Extrae (lat, lng) de un enlace de Google Maps o de texto 'lat, lng'."""
    if not texto:
        return None, None
    t = texto.strip()
    m = _RE_PAR.match(t)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = _RE_LATLNG_URL.search(t)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


class FincaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    departamento: str = Field(..., min_length=2, max_length=100)
    municipio: str = Field(..., min_length=1, max_length=100)
    coordenadas_google: str = Field(
        "", max_length=500,
        description="Enlace de Google Maps o 'lat, lng' (opcional si se envían latitud/longitud)",
    )
    latitud: float | None = Field(None, ge=-90, le=90, description="Latitud WGS84 directa")
    longitud: float | None = Field(None, ge=-180, le=180, description="Longitud WGS84 directa")
    propietario: str = Field(..., min_length=2, max_length=200)
    contacto_telefono: str = Field(..., min_length=7, max_length=50)
    contacto_email: str | None = Field(None, max_length=255)
    area_hectareas: float | None = Field(None, ge=0, le=1_000_000)
    largo_metros: float | None = Field(None, ge=0)
    ancho_metros: float | None = Field(None, ge=0)
    altitud_msnm: float | None = None
    # ── Topografía, drenaje, historial y fenología (2026-08-27) ──
    pendiente_pct: float | None = Field(None, ge=0, le=90, description="Pendiente del lote en %")
    drenaje: str | None = Field(None, max_length=20, description="Bueno | Regular | Deficiente")
    historial_agronomico: dict | None = Field(
        None, description="Historial de manejo: cultivo anterior, fertilización, encalado"
    )
    validacion_laboratorio: bool = Field(False, description="¿Validado en laboratorio?")
    cultivo_sembrado: str | None = Field(None, max_length=100)
    edad_anos: float | None = Field(None, ge=0, le=500)
    etapa_fenologica: str | None = Field(None, max_length=30, description="Vegetativa | Floración | Fructificación | Cosecha")
    # ── Georreferenciación y loteo (2026-08-27) ──
    vereda: str | None = Field(None, max_length=100, description="Vereda / corregimiento")
    precision_gps: float | None = Field(None, ge=0, le=10_000, description="Precisión GPS en metros")
    fuente_geolocalizacion: str | None = Field(
        None, max_length=30, description="gps_navegador | mapa | google_maps | manual"
    )
    geometria: dict | None = Field(None, description="Geometría GeoJSON (polígono del predio)")
    area_declarada_ha: float | None = Field(None, ge=0, le=1_000_000, description="Área declarada (ha)")
    tipo_area: str = Field("finca_completa", max_length=30, description="finca_completa | lote | parcela")
    tiene_multiples_lotes: bool = Field(False, description="¿La finca tiene varios lotes?")

    @field_validator("contacto_email")
    @classmethod
    def _email(cls, v: str | None) -> str | None:
        if v and "@" not in v:
            raise ValueError("Email de contacto inválido")
        return v


def _finca_a_dict(f: Finca) -> dict:
    return {
        "id": str(f.id),
        "nombre": f.nombre,
        "departamento": f.departamento,
        "municipio": f.municipio,
        "altitud_msnm": f.altitud_msnm,
        "area_hectareas": f.area_hectareas,
        "largo_metros": f.largo_metros,
        "ancho_metros": f.ancho_metros,
        "latitud": f.latitud,
        "longitud": f.longitud,
        "coordenadas_google": f.coordenadas_google,
        "propietario": f.propietario,
        "contacto_telefono": f.contacto_telefono,
        "contacto_email": f.contacto_email,
        "pendiente_pct": f.pendiente_pct,
        "drenaje": f.drenaje,
        "historial_agronomico": f.historial_agronomico,
        "validacion_laboratorio": f.validacion_laboratorio,
        "cultivo_sembrado": f.cultivo_sembrado,
        "edad_anos": f.edad_anos,
        "etapa_fenologica": f.etapa_fenologica,
        "vereda": f.vereda,
        "precision_gps": f.precision_gps,
        "fuente_geolocalizacion": f.fuente_geolocalizacion,
        "geometria": f.geometria,
        "area_declarada_ha": f.area_declarada_ha,
        "area_calculada_ha": f.area_calculada_ha,
        "perimetro_m": f.perimetro_m,
        "tipo_area": f.tipo_area,
        "tiene_multiples_lotes": f.tiene_multiples_lotes,
        "fecha_georreferenciacion": (
            f.fecha_georreferenciacion.isoformat()
            if f.fecha_georreferenciacion else None
        ),
    }


@router.get("/fincas")
async def listar_fincas(
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Lista las fincas visibles para el rol actual.

    Admin/Agrónomo ven todas; Cliente solo las suyas.
    """
    from agroia_backend.services.acceso import fincas_permitidas_ids

    stmt = select(Finca).order_by(Finca.nombre)
    permitidas = await fincas_permitidas_ids(db, x_user_role, x_user_email)
    if permitidas is not None:
        if not permitidas:
            return {"data": [], "total": 0}
        stmt = stmt.where(Finca.id.in_(permitidas))
    if search:
        stmt = stmt.where(
            Finca.nombre.ilike(f"%{search}%") | Finca.departamento.ilike(f"%{search}%")
        )
    fincas = (await db.execute(stmt)).scalars().all()
    return {"data": [_finca_a_dict(f) for f in fincas], "total": len(fincas)}


@router.post("/fincas", status_code=201)
async def registrar_finca(
    body: FincaCreate,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Registra una finca. Solo disponible para el rol administrador."""
    rol = (x_user_role or "").strip().lower()
    if rol not in ROL_ADMIN:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": (
                "Solo el rol administrador puede registrar fincas. "
                "Envíe la cabecera X-User-Role: Admin."
            ),
        })

    lat, lng = body.latitud, body.longitud
    if lat is None or lng is None:
        lat, lng = _extraer_coordenadas(body.coordenadas_google or "")

    # ── Cadena de validación al guardar finca ──
    #  1. ¿Departamento existe? · 2. ¿Municipio pertenece? · 3. ¿Coordenadas válidas?
    #  4. ¿Coinciden con el municipio? · 5. ¿Área razonable? · 6. ¿Precisión aceptable?
    from agroia_backend.services.geografia import (
        calcular_geometria_geojson,
        validar_creacion_finca,
    )

    pasos, errores, advertencias = validar_creacion_finca(
        departamento=body.departamento,
        municipio=body.municipio,
        lat=lat,
        lng=lng,
        area_ha=body.area_declarada_ha or body.area_hectareas,
        precision_m=body.precision_gps,
    )
    if errores:
        raise HTTPException(status_code=422, detail={
            "code": "VALIDACION_FINCA",
            "message": "La finca no pasó la validación: " + ", ".join(errores),
            "errores": errores,
            "advertencias": advertencias,
            "validaciones": pasos,
        })

    # ── Área/perímetro calculados desde la geometría (si hay polígono) ──
    area_calculada, perimetro = calcular_geometria_geojson(body.geometria)

    # MVP: sin Auth Service, la finca se asocia al primer usuario admin semilla
    # (o a cualquier usuario si no existe admin). tenant_id se hereda de ese usuario.
    from agroia_backend.models.usuario import Usuario

    usuario = (
        await db.execute(
            select(Usuario).order_by(Usuario.created_at).limit(1)
        )
    ).scalar_one_or_none()
    if usuario is None:
        raise HTTPException(status_code=422, detail={
            "code": "NO_USERS",
            "message": "No hay usuarios base en el sistema. Ejecute la semilla de usuarios primero.",
        })

    from datetime import datetime, timezone

    area_declarada = body.area_declarada_ha or body.area_hectareas
    finca = Finca(
        id=uuid_mod.uuid4(),
        tenant_id=usuario.tenant_id,
        usuario_id=usuario.id,
        nombre=body.nombre,
        departamento=body.departamento,
        municipio=body.municipio,
        latitud=lat,
        longitud=lng,
        coordenadas_google=body.coordenadas_google.strip(),
        propietario=body.propietario,
        contacto_telefono=body.contacto_telefono,
        contacto_email=body.contacto_email,
        area_hectareas=area_declarada,
        largo_metros=body.largo_metros,
        ancho_metros=body.ancho_metros,
        altitud_msnm=body.altitud_msnm,
        pendiente_pct=body.pendiente_pct,
        drenaje=body.drenaje,
        historial_agronomico=body.historial_agronomico,
        validacion_laboratorio=body.validacion_laboratorio,
        cultivo_sembrado=body.cultivo_sembrado,
        edad_anos=body.edad_anos,
        etapa_fenologica=body.etapa_fenologica,
        vereda=body.vereda,
        precision_gps=body.precision_gps,
        fuente_geolocalizacion=body.fuente_geolocalizacion,
        geometria=body.geometria,
        area_declarada_ha=area_declarada,
        area_calculada_ha=area_calculada,
        perimetro_m=perimetro,
        tipo_area=body.tipo_area,
        tiene_multiples_lotes=body.tiene_multiples_lotes,
        fecha_georreferenciacion=(
            datetime.now(timezone.utc) if (lat is not None and lng is not None) else None
        ),
    )
    db.add(finca)
    await db.flush()

    # ── Separación Finca ≠ Lote: crear el lote productivo principal ──
    from agroia_backend.models.lote import Lote

    lote = Lote(
        finca_id=finca.id,
        nombre="Lote principal" if body.tipo_area == "finca_completa" else body.nombre,
        area_ha=area_calculada or area_declarada,
        geometria=body.geometria,
    )
    db.add(lote)
    await db.commit()
    await db.refresh(finca)
    await db.refresh(lote)

    logger.info(
        "finca_registrada",
        finca_id=str(finca.id), nombre=finca.nombre, rol=rol,
        tipo_area=finca.tipo_area, advertencias=advertencias,
    )
    return {
        "status": "registered",
        "finca": _finca_a_dict(finca),
        "validaciones": pasos,
        "advertencias": advertencias,
        "lote_principal": {
            "id": str(lote.id),
            "nombre": lote.nombre,
            "area_ha": lote.area_ha,
        },
    }


class FincaAgroUpdate(BaseModel):
    """Actualización parcial de los campos agronómicos de la finca.

    Solo Admin/Agrónomo pueden completar topografía, drenaje, historial
    de manejo y estado fenológico del cultivo sembrado.
    """
    pendiente_pct: float | None = Field(None, ge=0, le=90)
    drenaje: str | None = Field(None, max_length=20)
    historial_agronomico: dict | None = None
    validacion_laboratorio: bool | None = None
    cultivo_sembrado: str | None = Field(None, max_length=100)
    edad_anos: float | None = Field(None, ge=0, le=500)
    etapa_fenologica: str | None = Field(None, max_length=30)


@router.patch("/fincas/{finca_id}")
async def actualizar_datos_agronomicos(
    finca_id: str,
    body: FincaAgroUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Actualiza topografía/drenaje/historial/fenología de una finca.

    Disponible para administrador y agrónomo.
    """
    rol = (x_user_role or "").strip().lower()
    if rol not in ROL_EXPERTOS:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el administrador o el agrónomo pueden actualizar los datos agronómicos de la finca.",
        })

    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })

    finca = (
        await db.execute(select(Finca).where(Finca.id == finca_uuid))
    ).scalar_one_or_none()
    if finca is None:
        raise HTTPException(status_code=404, detail={
            "code": "FINCA_NOT_FOUND", "message": "La finca no está registrada.",
        })

    cambios = body.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(finca, campo, valor)
    await db.commit()
    await db.refresh(finca)
    logger.info(
        "finca_datos_agronomicos_actualizados",
        finca_id=str(finca.id), campos=", ".join(cambios), rol=rol,
    )
    return {"status": "updated", "finca": _finca_a_dict(finca)}


@router.get("/fincas/{finca_id}/lotes")
async def lotes_de_finca(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Lista los lotes (unidades productivas) de una finca."""
    from agroia_backend.models.lote import Lote
    from agroia_backend.services.acceso import verificar_acceso_finca

    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    lotes = (
        await db.execute(
            select(Lote).where(Lote.finca_id == finca_id, Lote.activo.is_(True)).order_by(Lote.created_at)
        )
    ).scalars().all()
    return {
        "data": [
            {
                "id": str(lote.id),
                "nombre": lote.nombre,
                "area_ha": lote.area_ha,
                "geometria": lote.geometria,
                "activo": lote.activo,
            }
            for lote in lotes
        ],
        "total": len(lotes),
    }
