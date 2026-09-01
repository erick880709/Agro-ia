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
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.finca import Finca
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["fincas"])

ROL_ADMIN = {"admin", "administrador"}
ROL_EXPERTOS = {"admin", "administrador", "agronomo", "agrónomo"}

# Enlaces Google Maps con coordenadas: q=lat,lng · @lat,lng,zoom · place/.../@lat,lng
_RE_LATLNG_URL = re.compile(r"(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)")
_RE_PAR = re.compile(r"^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$")
# Google Maps también codifica coordenadas como !3d<lat>!4d<lng> (sin coma)
_RE_D = re.compile(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)")


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
    m = _RE_D.search(t)
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
    largo_metros: float = Field(
        ..., gt=0, le=1_000_000,
        description="Largo del terreno (m) — obligatorio: enriquece el estudio del lote",
    )
    ancho_metros: float = Field(
        ..., gt=0, le=1_000_000,
        description="Ancho del terreno (m) — obligatorio: enriquece el estudio del lote",
    )
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
    # ── Características físicas del suelo y riego (2026-08-27) ──
    tipo_riego: str | None = Field(None, description="Goteo | Aspersión | Gravedad | Secano")
    profundidad_suelo_cm: int = Field(
        ..., ge=5, le=500,
        description="Profundidad efectiva del suelo del lote principal (cm) — obligatoria; categorías: 25, 45, 75, 100",
    )
    pedregosidad: str = Field(
        ..., max_length=20,
        description="Pedregosidad del lote principal — obligatoria: Ninguna | Moderada | Alta",
    )

    @field_validator("contacto_email")
    @classmethod
    def _email(cls, v: str | None) -> str | None:
        if v and "@" not in v:
            raise ValueError("Email de contacto inválido")
        return v

    @field_validator("pedregosidad")
    @classmethod
    def _pedregosidad(cls, v: str) -> str:
        if v.strip().lower() not in {"ninguna", "moderada", "alta"}:
            raise ValueError("Pedregosidad debe ser Ninguna, Moderada o Alta")
        return v.strip()


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
        "tipo_riego": f.tipo_riego.value if f.tipo_riego else None,
        "fecha_georreferenciacion": (
            f.fecha_georreferenciacion.isoformat()
            if f.fecha_georreferenciacion else None
        ),
    }


@router.get("/fincas")
async def listar_fincas(
    search: str | None = Query(None),
    filtro: str | None = Query(None, pattern="^(con_comision|con_recomendacion)$"),
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Lista las fincas visibles para el rol actual.

    Admin/Agrónomo ven todas; Cliente solo las suyas.

    Filtros de etapa (regla de comisiones):
      - `con_comision`: fincas con una comisión asignada (estado distinto de
        cancelada) — candidatas a generar recomendación.
      - `con_recomendacion`: fincas que ya pasaron por la etapa de
        recomendación (comisión en `en_recomendacion` o
        `generacion_reporte_fin_etapa`) — candidatas a reporte.
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
    if filtro:
        from agroia_backend.models.comision import Comision

        if filtro == "con_recomendacion":
            condicion = Comision.estado.in_(
                ("en_recomendacion", "generacion_reporte_fin_etapa")
            )
        else:  # con_comision
            condicion = Comision.estado != "cancelada"
        stmt = stmt.where(
            select(Comision.id)
            .where(Comision.finca_id == Finca.id, condicion)
            .exists()
        )
    fincas = (await db.execute(stmt)).scalars().all()
    return {"data": [_finca_a_dict(f) for f in fincas], "total": len(fincas)}


def _ip(request: Request) -> str | None:
    """IP de origen de la petición (para la auditoría)."""
    fwd = request.headers.get("x-forwarded-for") if request else None
    if fwd:
        return fwd.split(",")[0].strip()[:45]
    return (request.client.host if request and request.client else None)


@router.post("/fincas", status_code=201)
async def registrar_finca(
    body: FincaCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
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

    # Endurecer contra search_path frágil (casts de enum en INSERT)
    await db.execute(text("SET LOCAL search_path TO public, agroia"))

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
    # Normalizar tipo de riego al nombre del enum (mayúsculas)
    tipo_riego = body.tipo_riego
    if tipo_riego:
        normalizado = (
            tipo_riego.strip().upper().replace("Á", "A").replace("É", "E")
        )
        tipo_riego = (
            normalizado
            if normalizado in {"GOTEO", "ASPERSION", "GRAVEDAD", "SECANO"}
            else None
        )
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
        tipo_riego=tipo_riego,
        fecha_georreferenciacion=(
            datetime.now(timezone.utc) if (lat is not None and lng is not None) else None
        ),
    )
    db.add(finca)
    await db.flush()

    # ── Separación Finca ≠ Lote: crear el lote productivo principal ──
    from agroia_backend.models.lote import Lote, Pedregosidad

    lote = Lote(
        finca_id=finca.id,
        nombre="Lote principal" if body.tipo_area == "finca_completa" else body.nombre,
        area_ha=area_calculada or area_declarada,
        geometria=body.geometria,
        profundidad_suelo_cm=body.profundidad_suelo_cm,
        pedregosidad=Pedregosidad[body.pedregosidad.strip().upper()],
    )
    db.add(lote)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="finca.crear",
        entidad="finca",
        entidad_id=str(finca.id),
        detalle={
            "nombre": finca.nombre,
            "departamento": finca.departamento,
            "municipio": finca.municipio,
            "area_ha": finca.area_hectareas,
            "tipo_area": finca.tipo_area,
        },
        ip=_ip(request),
    )
    await db.commit()
    await db.refresh(finca)
    await db.refresh(lote)

    # ── Enriquecimiento SIG (IGAC/UPRA): precarga textura/MO/CIC oficiales ──
    # Si la finca tiene coordenadas, se intersecta el polígono con las zonas
    # de referencia del Estudio General de Suelos y se guarda una lectura con
    # calidad 'estimado_por_sig'. El sensor gana si llega a medir.
    enriquecimiento = None
    if lat is not None and lng is not None:
        try:
            from agroia_backend.services.sig_suelos import enriquecer_finca_sig

            enriquecimiento = await enriquecer_finca_sig(db, finca)
            await db.refresh(lote)  # el enriquecimiento pudo completar el lote
        except Exception as e:  # noqa: BLE001 — no bloquear el registro
            logger.warning("sig_enriquecimiento_fallo", finca_id=str(finca.id), error=str(e))

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
        "enriquecimiento_sig": enriquecimiento,
        "lote_principal": {
            "id": str(lote.id),
            "nombre": lote.nombre,
            "area_ha": lote.area_ha,
            "profundidad_suelo_cm": lote.profundidad_suelo_cm,
            "pedregosidad": lote.pedregosidad.value if lote.pedregosidad else None,
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
    tipo_riego: str | None = Field(None, max_length=30, description="Goteo | Aspersión | Gravedad | Secano")


@router.patch("/fincas/{finca_id}")
async def actualizar_datos_agronomicos(
    finca_id: str,
    body: FincaAgroUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
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

    await db.execute(text("SET LOCAL search_path TO public, agroia"))
    cambios = body.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(finca, campo, valor)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="finca.agronomicos",
        entidad="finca",
        entidad_id=str(finca.id),
        detalle={"nombre": finca.nombre, "campos": sorted(cambios)},
        ip=_ip(request),
    )
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
                "profundidad_suelo_cm": lote.profundidad_suelo_cm,
                "pedregosidad": lote.pedregosidad.value if lote.pedregosidad else None,
                "activo": lote.activo,
                "fecha_siembra": lote.fecha_siembra.isoformat() if lote.fecha_siembra else None,
                "variedad": lote.variedad,
                "densidad_siembra_plantas_ha": (
                    float(lote.densidad_siembra_plantas_ha)
                    if lote.densidad_siembra_plantas_ha is not None else None
                ),
            }
            for lote in lotes
        ],
        "total": len(lotes),
    }


# ══════════════════ Edición y eliminación de fincas (Admin) ══════════════════

class FincaUpdate(BaseModel):
    """Edición de los datos básicos de la finca (solo Admin)."""

    nombre: str = Field(..., min_length=2, max_length=200)
    departamento: str = Field(..., min_length=2, max_length=100)
    municipio: str = Field(..., min_length=1, max_length=100)
    propietario: str = Field(..., min_length=2, max_length=200)
    contacto_telefono: str = Field(..., min_length=7, max_length=50)
    contacto_email: str | None = Field(None, max_length=255)
    area_hectareas: float | None = Field(None, ge=0, le=1_000_000)
    altitud_msnm: float | None = None
    latitud: float | None = Field(None, ge=-90, le=90)
    longitud: float | None = Field(None, ge=-180, le=180)
    vereda: str | None = Field(None, max_length=100)


def _exigir_rol(rol: str, permitidos: set[str], mensaje: str) -> None:
    if rol not in permitidos:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE", "message": mensaje,
        })


async def _obtener_finca(db, finca_id: str) -> Finca:
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
    return finca


@router.put("/fincas/{finca_id}")
async def editar_finca(
    finca_id: str,
    body: FincaUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Edita los datos básicos de una finca. Solo administrador."""
    rol = (x_user_role or "").strip().lower()
    _exigir_rol(rol, ROL_ADMIN, "Solo el rol administrador puede editar fincas.")

    finca = await _obtener_finca(db, finca_id)
    await db.execute(text("SET LOCAL search_path TO public, agroia"))

    cambios = body.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(finca, campo, valor)
    finca.area_declarada_ha = finca.area_hectareas

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="finca.actualizar",
        entidad="finca",
        entidad_id=str(finca.id),
        detalle={"nombre": finca.nombre, "campos": sorted(cambios)},
        ip=_ip(request),
    )
    await db.commit()
    await db.refresh(finca)
    logger.info("finca_editada", finca_id=str(finca.id), campos=", ".join(sorted(cambios)), rol=rol)
    return {"status": "updated", "finca": _finca_a_dict(finca)}


@router.delete("/fincas/{finca_id}")
async def eliminar_finca(
    finca_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Elimina una finca y todos sus datos asociados. Solo administrador.

    Se eliminan en cascada: lotes, relaciones finca-usuario, chat, aceptaciones
    (FK con ON DELETE CASCADE) y, de forma explícita, recomendaciones (y sus
    discordancias), lecturas de sensores y dispositivos IoT.
    """
    rol = (x_user_role or "").strip().lower()
    _exigir_rol(rol, ROL_ADMIN, "Solo el rol administrador puede eliminar fincas.")

    finca = await _obtener_finca(db, finca_id)
    await db.execute(text("SET LOCAL search_path TO public, agroia"))

    # ── Limpieza explícita de tablas sin ON DELETE CASCADE ──
    from agroia_backend.models.discordancia import Discordancia
    from agroia_backend.models.dispositivo_iot import DispositivoIoT
    from agroia_backend.models.recomendacion import Recomendacion
    from agroia_backend.models.sensor_reading import SensorReading

    rec_ids = (
        await db.execute(select(Recomendacion.id).where(Recomendacion.finca_id == finca.id))
    ).scalars().all()
    n_recomendaciones = len(rec_ids)
    if rec_ids:
        await db.execute(delete(Discordancia).where(Discordancia.recomendacion_id.in_(rec_ids)))
        await db.execute(delete(Recomendacion).where(Recomendacion.finca_id == finca.id))
    lecturas = (
        await db.execute(delete(SensorReading).where(SensorReading.finca_id == finca.id))
    )
    dispositivos = (
        await db.execute(delete(DispositivoIoT).where(DispositivoIoT.finca_id == finca.id))
    )

    detalle = {
        "nombre": finca.nombre,
        "recomendaciones": n_recomendaciones,
        "lecturas": lecturas.rowcount,
        "dispositivos": dispositivos.rowcount,
    }
    nombre_eliminada = finca.nombre
    await db.delete(finca)  # lotes/chat/aceptaciones/finca_usuario caen en cascada
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="finca.eliminar",
        entidad="finca",
        entidad_id=finca_id,
        detalle=detalle,
        ip=_ip(request),
    )
    await db.commit()
    logger.info("finca_eliminada", finca_id=finca_id, nombre=nombre_eliminada, rol=rol)
    return {"status": "deleted", "finca_id": finca_id, "detalle": detalle}


# ══════════════════ Lotes: crear, editar y eliminar ══════════════════

PEDREGOSIDADES = {"ninguna", "moderada", "alta"}


class LoteCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    area_ha: float | None = Field(None, ge=0, le=100_000)
    geometria: dict | None = Field(None, description="Geometría GeoJSON del lote")
    profundidad_suelo_cm: int | None = Field(None, ge=0, le=500)
    pedregosidad: str | None = Field(None, description="Ninguna | Moderada | Alta")


class LoteUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=100)
    area_ha: float | None = Field(None, ge=0, le=100_000)
    geometria: dict | None = None
    profundidad_suelo_cm: int | None = Field(None, ge=0, le=500)
    pedregosidad: str | None = Field(None, description="Ninguna | Moderada | Alta")


def _lote_a_dict(lote) -> dict:
    return {
        "id": str(lote.id),
        "finca_id": str(lote.finca_id),
        "nombre": lote.nombre,
        "area_ha": lote.area_ha,
        "geometria": lote.geometria,
        "profundidad_suelo_cm": lote.profundidad_suelo_cm,
        "pedregosidad": lote.pedregosidad.value if lote.pedregosidad else None,
        "activo": lote.activo,
        "fecha_siembra": lote.fecha_siembra.isoformat() if lote.fecha_siembra else None,
        "variedad": lote.variedad,
        "densidad_siembra_plantas_ha": (
            float(lote.densidad_siembra_plantas_ha)
            if lote.densidad_siembra_plantas_ha is not None else None
        ),
    }


@router.post("/fincas/{finca_id}/lotes", status_code=201)
async def crear_lote(
    finca_id: str,
    body: LoteCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Agrega un lote (unidad productiva) a una finca. Admin/Agrónomo."""
    from agroia_backend.models.lote import Lote, Pedregosidad

    rol = (x_user_role or "").strip().lower()
    _exigir_rol(
        rol, ROL_EXPERTOS,
        "Solo el administrador o el agrónomo pueden agregar lotes.",
    )
    finca = await _obtener_finca(db, finca_id)
    await db.execute(text("SET LOCAL search_path TO public, agroia"))

    pedregosidad = None
    if body.pedregosidad and body.pedregosidad.lower() in PEDREGOSIDADES:
        pedregosidad = Pedregosidad[body.pedregosidad.strip().upper()]

    lote = Lote(
        finca_id=finca.id,
        nombre=body.nombre,
        area_ha=body.area_ha,
        geometria=body.geometria,
        profundidad_suelo_cm=body.profundidad_suelo_cm,
        pedregosidad=pedregosidad,
    )
    db.add(lote)
    await db.flush()

    # Si ahora hay más de un lote activo, marcar la finca como multi-lote
    n_lotes = (
        await db.execute(
            select(Lote).where(Lote.finca_id == finca.id, Lote.activo.is_(True))
        )
    ).scalars().all()
    if len(n_lotes) > 1:
        finca.tiene_multiples_lotes = True

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="lote.crear",
        entidad="lote",
        entidad_id=str(lote.id),
        detalle={
            "finca_id": str(finca.id),
            "finca": finca.nombre,
            "nombre": lote.nombre,
            "area_ha": lote.area_ha,
            "profundidad_suelo_cm": lote.profundidad_suelo_cm,
        },
        ip=_ip(request),
    )
    await db.commit()
    await db.refresh(lote)
    logger.info("lote_creado", lote_id=str(lote.id), finca_id=str(finca.id), rol=rol)
    return {"status": "created", "lote": _lote_a_dict(lote)}


@router.patch("/fincas/{finca_id}/lotes/{lote_id}")
async def editar_lote(
    finca_id: str,
    lote_id: str,
    body: LoteUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Edita las características de un lote. Admin/Agrónomo."""
    from agroia_backend.models.lote import Lote, Pedregosidad

    rol = (x_user_role or "").strip().lower()
    _exigir_rol(rol, ROL_EXPERTOS, "Solo el administrador o el agrónomo pueden editar lotes.")
    await _obtener_finca(db, finca_id)
    await db.execute(text("SET LOCAL search_path TO public, agroia"))

    try:
        lote_uuid = uuid_mod.UUID(lote_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "LOTE_INVALIDO", "message": "lote_id no es un UUID válido.",
        })
    lote = (
        await db.execute(
            select(Lote).where(Lote.id == lote_uuid, Lote.finca_id == uuid_mod.UUID(finca_id))
        )
    ).scalar_one_or_none()
    if lote is None:
        raise HTTPException(status_code=404, detail={
            "code": "LOTE_NOT_FOUND", "message": "El lote no pertenece a esta finca o no existe.",
        })

    cambios = body.model_dump(exclude_unset=True)
    pedregosidad = cambios.pop("pedregosidad", None)
    if pedregosidad is not None:
        cambios["pedregosidad"] = (
            Pedregosidad[pedregosidad.strip().upper()]
            if pedregosidad.strip().lower() in PEDREGOSIDADES else None
        )
    for campo, valor in cambios.items():
        setattr(lote, campo, valor)

    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="lote.actualizar",
        entidad="lote",
        entidad_id=str(lote.id),
        detalle={"finca_id": finca_id, "nombre": lote.nombre, "campos": sorted(body.model_dump(exclude_unset=True))},
        ip=_ip(request),
    )
    await db.commit()
    await db.refresh(lote)
    logger.info("lote_editado", lote_id=str(lote.id), finca_id=finca_id, rol=rol)
    return {"status": "updated", "lote": _lote_a_dict(lote)}


@router.delete("/fincas/{finca_id}/lotes/{lote_id}")
async def eliminar_lote(
    finca_id: str,
    lote_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    x_user_nombre: str | None = Header(None, alias="X-User-Nombre"),
):
    """Elimina (desactiva) un lote. Solo administrador.

    Desactivación lógica: el lote deja de aparecer en listados pero su
    historial en auditoría se conserva. No se permite eliminar el último
    lote activo de la finca.
    """
    from agroia_backend.models.lote import Lote

    rol = (x_user_role or "").strip().lower()
    _exigir_rol(rol, ROL_ADMIN, "Solo el rol administrador puede eliminar lotes.")
    await _obtener_finca(db, finca_id)
    await db.execute(text("SET LOCAL search_path TO public, agroia"))

    try:
        lote_uuid = uuid_mod.UUID(lote_id)
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "LOTE_INVALIDO", "message": "lote_id o finca_id no es un UUID válido.",
        })
    lote = (
        await db.execute(
            select(Lote).where(Lote.id == lote_uuid, Lote.finca_id == finca_uuid)
        )
    ).scalar_one_or_none()
    if lote is None:
        raise HTTPException(status_code=404, detail={
            "code": "LOTE_NOT_FOUND", "message": "El lote no pertenece a esta finca o no existe.",
        })

    activos = (
        await db.execute(
            select(Lote).where(Lote.finca_id == finca_uuid, Lote.activo.is_(True))
        )
    ).scalars().all()
    if len(activos) <= 1 and lote.activo:
        raise HTTPException(status_code=422, detail={
            "code": "ULTIMO_LOTE",
            "message": "No se puede eliminar el último lote activo de la finca. "
                       "Cada finca debe conservar al menos un lote.",
        })

    lote.activo = False
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        usuario_nombre=x_user_nombre,
        rol=x_user_role,
        accion="lote.eliminar",
        entidad="lote",
        entidad_id=str(lote.id),
        detalle={"finca_id": str(finca_uuid), "nombre": lote.nombre},
        ip=_ip(request),
    )
    await db.commit()
    logger.info("lote_eliminado", lote_id=str(lote.id), finca_id=str(finca_uuid), rol=rol)
    return {"status": "deleted", "lote_id": str(lote.id), "nombre": lote.nombre}
