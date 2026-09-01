"""API de visión por computadora — diagnóstico de plagas desde foto (P12).

AgroVision (contextoVision): el modelo propio entrena progresivamente;
mientras tanto, el motor entrega diagnóstico visual PRELIMINAR vía fallback
OpenCV (sección 14 de la especificación) y abstención explicada cuando la
foto no es válida o la confianza es insuficiente (sección 24).
"""

import os
import time
import uuid as uuid_mod
from pathlib import Path

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.usuario import Usuario
from agroia_backend.models.vision_diagnostico import VisionDiagnostico
from agroia_backend.services.acceso import exigir_no_cliente, verificar_acceso_finca
from agroia_backend.services.auditoria import registrar_auditoria
from agroia_backend.services.dataset_estado import estado_datasets
from agroia_backend.services.vision_engine import diagnosticar_imagen

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/vision", tags=["vision-plagas"])

TIPOS_IMAGEN = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_FOTO_BYTES = 5 * 1024 * 1024  # 5 MB


def _media_root() -> Path:
    return Path(
        os.environ.get("AGROIA_MEDIA_DIR")
        or Path(__file__).resolve().parents[4] / "media"
    )


async def _usuario_por_email(db, email: str | None) -> Usuario | None:
    if not email:
        return None
    return (
        await db.execute(select(Usuario).where(Usuario.email == email.lower()))
    ).scalar_one_or_none()


@router.post("/analizar-plaga")
async def analizar_plaga(
    finca_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
    file: UploadFile = File(...),
):
    """Sube una foto de cultivo/síntoma y registra un diagnóstico.

    Contrato de respuesta: plaga, confianza (0-1), severidad, recomendacion,
    fuente, imagen_url + estado (preliminary/abstain), modelo_version,
    evidencia y requiere_revision (sección 24).
    """
    exigir_no_cliente(x_user_role)
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    ext = TIPOS_IMAGEN.get(file.content_type or "")
    if ext is None:
        raise HTTPException(status_code=415, detail={
            "code": "FORMATO_NO_SOPORTADO",
            "message": "Solo se admiten imágenes JPEG, PNG o WebP.",
        })
    contenido = await file.read()
    if not contenido:
        raise HTTPException(status_code=422, detail={
            "code": "IMAGEN_VACIA", "message": "La imagen está vacía.",
        })
    if len(contenido) > MAX_FOTO_BYTES:
        raise HTTPException(status_code=413, detail={
            "code": "FOTO_MUY_GRANDE",
            "message": "La foto supera el límite de 5 MB.",
        })

    media_root = _media_root()
    dir_vision = media_root / "vision"
    dir_vision.mkdir(parents=True, exist_ok=True)
    nombre = f"plaga_{uuid_mod.uuid4().hex[:10]}_{int(time.time())}{ext}"
    (dir_vision / nombre).write_bytes(contenido)
    imagen_url = f"/media/vision/{nombre}"

    # ── Inferencia: motor AgroVision (modelo → fallback OpenCV → abstención) ──
    resultado = diagnosticar_imagen(contenido)

    usuario = await _usuario_por_email(db, x_user_email)
    diagnostico = VisionDiagnostico(
        finca_id=uuid_mod.UUID(finca_id),
        usuario_id=usuario.id if usuario else None,
        imagen_url=imagen_url,
        resultado_json=resultado,
    )
    db.add(diagnostico)
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        rol=x_user_role,
        accion="vision.analizar_plaga",
        entidad="vision_diagnostico",
        entidad_id=str(diagnostico.id),
        detalle={"finca_id": finca_id, "imagen_url": imagen_url, "fuente": resultado["fuente"]},
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    logger.info(
        "vision_diagnostico_guardado",
        diagnostico_id=str(diagnostico.id),
        finca_id=finca_id,
        fuente=resultado["fuente"],
        estado=resultado["estado"],
    )
    return {
        "diagnostico_id": str(diagnostico.id),
        "finca_id": finca_id,
        "imagen_url": imagen_url,
        "estado": resultado["estado"],
        "modelo_version": resultado["modelo_version"],
        "plaga": resultado["plaga"],
        "confianza": resultado["confianza"],
        "severidad": resultado["severidad"],
        "recomendacion": resultado["recomendacion"],
        "evidencia": resultado["evidence"],
        "explicacion": resultado.get("explicacion", ""),
        "requiere_revision": resultado["requiere_revision"],
        "fuente": resultado["fuente"],
        "nota": "Diagnóstico visual preliminar (no confirmatorio) — sección 24.",
    }


class DiagnoseRequest(BaseModel):
    """Contrato de inferencia (sección 18): POST /api/v1/vision/diagnose."""

    image_uri: str = Field(..., description="Ruta relativa /media/... de la imagen.")
    crop_hint: str | None = Field(None, description="Cultivo sugerido, p.ej. coffee.")
    location: dict | None = None
    capture_timestamp: str | None = None


class ConfirmarDiagnosticoRequest(BaseModel):
    """RQ-V6-01: etiqueta confirmada por el agrónomo al revisar."""

    etiqueta: str = Field(..., min_length=2, max_length=500)


@router.post("/diagnose")
async def diagnose(
    body: DiagnoseRequest,
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Inferencia del motor AgroVision (modelo → fallback OpenCV → abstención).

    Devuelve el contrato de la sección 18: diagnóstico preliminar, confianza,
    evidencia visual y estado de seguridad. Sin persistencia (para persistir
    por finca usar POST /analizar-plaga).
    """
    exigir_no_cliente(x_user_role)
    uri = body.image_uri
    if not uri.startswith("/media/"):
        raise HTTPException(status_code=422, detail={
            "code": "IMAGE_URI_NO_SOPORTADO",
            "message": "image_uri debe ser una ruta relativa /media/... del repositorio.",
        })
    ruta = _media_root() / uri.removeprefix("/media/").lstrip("/")
    if not ruta.is_file():
        raise HTTPException(status_code=404, detail={
            "code": "IMAGEN_NO_ENCONTRADA", "message": "La imagen indicada no existe.",
        })
    contenido = ruta.read_bytes()
    if len(contenido) > MAX_FOTO_BYTES:
        raise HTTPException(status_code=413, detail={
            "code": "FOTO_MUY_GRANDE",
            "message": "La foto supera el límite de 5 MB.",
        })
    resultado = diagnosticar_imagen(contenido, crop_hint=body.crop_hint)
    return {
        "model_version": resultado["modelo_version"],
        "status": resultado["estado"],
        "crop": resultado["crop"],
        "diagnosis": resultado["diagnosis"],
        "severity": resultado["severity"],
        "evidence": [{"type": "texto", "detalle": e} for e in resultado["evidence"]],
        "explicacion": resultado.get("explicacion", ""),
        "recommend_review": resultado["requiere_revision"],
        "dataset_lineage": [],
    }


@router.get("/diagnosticos/{finca_id}")
async def diagnosticos_finca(
    finca_id: str,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Historial de diagnósticos de visión de una finca (acceso por rol)."""
    await verificar_acceso_finca(db, x_user_role, x_user_email, finca_id)
    try:
        fid = uuid_mod.UUID(finca_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "FINCA_INVALIDA", "message": "finca_id no es un UUID válido.",
        })
    filas = (
        await db.execute(
            select(VisionDiagnostico)
            .where(VisionDiagnostico.finca_id == fid)
            .order_by(VisionDiagnostico.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return {
        "finca_id": finca_id,
        "total": len(filas),
        "diagnosticos": [
            {
                "id": str(d.id),
                "finca_id": str(d.finca_id),
                "imagen_url": d.imagen_url,
                "resultado": d.resultado_json,
                "etiqueta_confirmada": d.etiqueta_confirmada,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in filas
        ],
    }


@router.post("/diagnosticos/{diagnostico_id}/confirmar")
async def confirmar_diagnostico(
    diagnostico_id: str,
    body: ConfirmarDiagnosticoRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """RQ-V6-01: el agrónomo confirma/corrige la etiqueta de un diagnóstico.

    Convierte cada revisión de campo en un ejemplo etiquetado por experto
    para el dataset propio de AgroIA (DS09 en datasets/manifest)."""
    exigir_no_cliente(x_user_role)
    try:
        did = uuid_mod.UUID(diagnostico_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={
            "code": "DIAGNOSTICO_INVALIDO",
            "message": "diagnostico_id no es un UUID válido.",
        })
    diagnostico = (
        await db.execute(select(VisionDiagnostico).where(VisionDiagnostico.id == did))
    ).scalar_one_or_none()
    if diagnostico is None:
        raise HTTPException(status_code=404, detail={
            "code": "DIAGNOSTICO_NO_ENCONTRADO",
            "message": "El diagnóstico indicado no existe.",
        })
    await verificar_acceso_finca(
        db, x_user_role, x_user_email, str(diagnostico.finca_id)
    )
    etiqueta_anterior = diagnostico.etiqueta_confirmada
    diagnostico.etiqueta_confirmada = body.etiqueta.strip()
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        rol=x_user_role,
        accion="vision.confirmar_diagnostico",
        entidad="vision_diagnostico",
        entidad_id=str(diagnostico.id),
        detalle={
            "etiqueta": diagnostico.etiqueta_confirmada,
            "etiqueta_anterior": etiqueta_anterior,
            "diagnosis_preliminar": (
                diagnostico.resultado_json or {}
            ).get("plaga"),
        },
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    logger.info(
        "vision_etiqueta_confirmada",
        diagnostico_id=str(diagnostico.id),
        etiqueta=diagnostico.etiqueta_confirmada,
    )
    return {
        "id": str(diagnostico.id),
        "etiqueta_confirmada": diagnostico.etiqueta_confirmada,
        "nota": "Etiqueta registrada; alimenta el dataset propio AgroIA (aprendizaje activo).",
    }


@router.get("/admin/dataset-estado")
async def dataset_estado(
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """RQ v6 §2.5: estado/trazabilidad del pipeline de datasets AgroVision.

    Resumen read-only del árbol datasets/ (manifest, metadata, curación y
    modelos empaquetados). No reemplaza /admin/reentrenar, lo complementa."""
    if (x_user_role or "").lower() not in ("admin", "administrador"):
        raise HTTPException(status_code=403, detail={
            "code": "SOLO_ADMIN",
            "message": "Solo el administrador puede consultar el estado de datasets.",
        })
    raiz = Path(
        os.environ.get("AGROIA_DATASETS_DIR")
        or Path(__file__).resolve().parents[4] / "datasets"
    )
    return estado_datasets(raiz)


@router.post("/admin/reentrenar")
async def reentrenar_modelo(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Solicita el reentrenamiento del modelo de visión (solo admin).

    Orquestación del pipeline AgroVision (datasets/scripts): registra la
    solicitud y devuelve el estado. El entrenamiento real corre fuera del
    ciclo de la API (datasets/scripts/train.py + MLflow)."""
    if (x_user_role or "").lower() not in ("admin", "administrador"):
        raise HTTPException(status_code=403, detail={
            "code": "SOLO_ADMIN",
            "message": "Solo el administrador puede reentrenar el modelo.",
        })
    estado = {
        "estado": "programado",
        "modelo": "agroia-vision-v1",
        "pipeline": "agrovision",
        "mensaje": (
            "Reentrenamiento programado. El pipeline AgroVision entrenará "
            "con los datasets curados (datasets/curated)."
        ),
    }
    await registrar_auditoria(
        db,
        usuario_email=x_user_email or "desconocido@agroia.co",
        rol=x_user_role,
        accion="vision.reentrenar",
        entidad="modelo_vision",
        entidad_id="agroia-vision-v1",
        detalle=estado,
    )
    await db.commit()
    return estado
