"""API de análisis de agua de riego (clasificación FAO-29)."""

import uuid as uuid_mod
from datetime import date

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.analisis_agua_riego import AnalisisAguaRiego
from agroia_backend.models.usuario import Usuario
from agroia_backend.services.acceso import verificar_acceso_finca

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["agua-riego"])

ROL_ESCRITURA = {"admin", "administrador", "agronomo", "agrónomo", "extensionista"}


class AguaRiegoRequest(BaseModel):
    lote_id: str | None = None
    fecha: date
    ce_agua_ds_m: float | None = Field(None, ge=0, le=100)
    ras: float | None = Field(None, ge=0, le=100)
    cloruros_mg_l: float | None = Field(None, ge=0)
    boro_mg_l: float | None = Field(None, ge=0, le=50)
    ph_agua: float | None = Field(None, ge=0, le=14)
    fuente: str = Field("laboratorio", pattern="^(laboratorio|manual|sin_dato)$")


def _clasificar_fao29(datos: dict) -> tuple[str, list[dict]]:
    """Clasifica restricción de uso FAO-29 (peor parámetro manda)."""
    reglas = [
        ("CE", datos.get("ce_agua_ds_m"), 0.7, 3.0, "dS/m"),
        ("RAS", datos.get("ras"), 3.0, 9.0, ""),
        ("Cloruros", datos.get("cloruros_mg_l"), 140.0, 350.0, "mg/L"),
        ("Boro", datos.get("boro_mg_l"), 0.7, 3.0, "mg/L"),
    ]
    orden = {"ninguna": 0, "leve_moderada": 1, "severa": 2}
    detalle = []
    peor = "ninguna"
    for nombre, valor, umbral_leve, umbral_severa, unidad in reglas:
        if valor is None:
            continue
        if valor < umbral_leve:
            estado = "ninguna"
        elif valor <= umbral_severa:
            estado = "leve_moderada"
        else:
            estado = "severa"
        detalle.append({
            "parametro": nombre,
            "valor": float(valor),
            "rango_ninguna": f"<{umbral_leve:g} {unidad}".strip(),
            "rango_severa": f">{umbral_severa:g} {unidad}".strip(),
            "estado": estado,
        })
        if orden[estado] > orden[peor]:
            peor = estado
    return peor, detalle


_RECOMENDACIONES = {
    "ninguna": "Agua apta para riego sin restricciones relevantes. Mantener monitoreo anual.",
    "leve_moderada": "Vigilar acumulación de sales en el perfil; considerar lavado periódico del suelo y cultivos con tolerancia media a sales.",
    "severa": "Restricción severa: requiere lavado frecuente, drenaje adecuado y cultivos tolerantes a salinidad; analizar agua cada temporada.",
}


def _a_dict(a: AnalisisAguaRiego) -> dict:
    return {
        "id": str(a.id),
        "finca_id": str(a.finca_id),
        "lote_id": str(a.lote_id) if a.lote_id else None,
        "fecha": a.fecha.isoformat(),
        "ce_agua_ds_m": float(a.ce_agua_ds_m) if a.ce_agua_ds_m is not None else None,
        "ras": float(a.ras) if a.ras is not None else None,
        "cloruros_mg_l": float(a.cloruros_mg_l) if a.cloruros_mg_l is not None else None,
        "boro_mg_l": float(a.boro_mg_l) if a.boro_mg_l is not None else None,
        "ph_agua": float(a.ph_agua) if a.ph_agua is not None else None,
        "fuente": a.fuente,
        "clasificacion_restriccion": a.clasificacion_restriccion,
        "creado_en": a.creado_en.isoformat() if a.creado_en else None,
    }


@router.post("/fincas/{finca_id}/agua-riego", status_code=201)
async def registrar_agua_riego(
    finca_id: str,
    body: AguaRiegoRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Registra un análisis de agua de riego y lo clasifica con FAO-29."""
    rol = (x_user_role or "").strip().lower()
    if rol not in ROL_ESCRITURA:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo Admin, Agrónomo o Extensionista pueden registrar análisis de agua.",
        })
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })

    usuario = None
    if x_user_email:
        usuario = (
            await db.execute(select(Usuario).where(Usuario.email == (x_user_email or "").lower()))
        ).scalar_one_or_none()

    clasificacion, detalle = _clasificar_fao29(body.model_dump())
    analisis = AnalisisAguaRiego(
        finca_id=finca_uuid,
        lote_id=uuid_mod.UUID(body.lote_id) if body.lote_id else None,
        fecha=body.fecha,
        ce_agua_ds_m=body.ce_agua_ds_m,
        ras=body.ras,
        cloruros_mg_l=body.cloruros_mg_l,
        boro_mg_l=body.boro_mg_l,
        ph_agua=body.ph_agua,
        fuente=body.fuente,
        clasificacion_restriccion=clasificacion,
        creado_por=usuario.id if usuario else None,
    )
    db.add(analisis)
    await db.commit()
    await db.refresh(analisis)
    logger.info("agua_riego_registrado", finca_id=finca_id, clasificacion=clasificacion, rol=rol)
    return {
        "id": str(analisis.id),
        "clasificacion_restriccion": clasificacion,
        "detalle": detalle,
        "recomendacion": _RECOMENDACIONES[clasificacion],
    }


@router.get("/fincas/{finca_id}/agua-riego")
async def historial_agua_riego(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Historial de análisis de agua de riego de la finca."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        finca_uuid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })
    analisis = (
        await db.execute(
            select(AnalisisAguaRiego)
            .where(AnalisisAguaRiego.finca_id == finca_uuid)
            .order_by(AnalisisAguaRiego.fecha.desc())
            .limit(50)
        )
    ).scalars().all()
    return {"data": [_a_dict(a) for a in analisis], "total": len(analisis)}
