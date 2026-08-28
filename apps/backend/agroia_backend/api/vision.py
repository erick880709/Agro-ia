"""API de visión por computadora — diagnóstico de plagas desde foto (P12).

Modelo de inferencia: el modelo propio AgroIA v1.0 está en entrenamiento.
Mientras tanto el endpoint entrega una respuesta de DEGRADACIÓN GRACIOSA
(estructura definitiva del contrato) para que el flujo completo
carga → persistencia → historial quede operativo.
"""

import os
import time
import uuid as uuid_mod
from pathlib import Path

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.usuario import Usuario
from agroia_backend.models.vision_diagnostico import VisionDiagnostico
from agroia_backend.services.acceso import exigir_no_cliente, verificar_acceso_finca
from agroia_backend.services.auditoria import registrar_auditoria

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/vision", tags=["vision-plagas"])

TIPOS_IMAGEN = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_FOTO_BYTES = 5 * 1024 * 1024  # 5 MB
FUENTE_MODELO = "modelo_agroia_v1_stub"


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

    Contrato de respuesta definitivo (el stub de inferencia lo respeta):
    plaga, confianza (0-1), severidad, recomendacion, fuente, imagen_url.
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

    media_root = Path(
        os.environ.get("AGROIA_MEDIA_DIR") or Path(__file__).resolve().parents[4] / "media"
    )
    dir_vision = media_root / "vision"
    dir_vision.mkdir(parents=True, exist_ok=True)
    nombre = f"plaga_{uuid_mod.uuid4().hex[:10]}_{int(time.time())}{ext}"
    (dir_vision / nombre).write_bytes(contenido)
    imagen_url = f"/media/vision/{nombre}"

    # ── Inferencia: degradación graciosa hasta que el modelo v1.0 entrene ──
    resultado = {
        "plaga": "No determinada",
        "confianza": 0.0,
        "severidad": "desconocida",
        "recomendacion": (
            "El modelo propio AgroIA v1.0 está en entrenamiento. "
            "Envía la imagen a un agrónomo desde el chat para un dictamen experto."
        ),
        "fuente": FUENTE_MODELO,
    }

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
        detalle={"finca_id": finca_id, "imagen_url": imagen_url, "fuente": FUENTE_MODELO},
        ip=request.client.host if request and request.client else None,
    )
    await db.commit()
    logger.info(
        "vision_diagnostico_guardado",
        diagnostico_id=str(diagnostico.id),
        finca_id=finca_id,
        fuente=FUENTE_MODELO,
    )
    return {
        "diagnostico_id": str(diagnostico.id),
        "finca_id": finca_id,
        "imagen_url": imagen_url,
        "plaga": resultado["plaga"],
        "confianza": resultado["confianza"],
        "severidad": resultado["severidad"],
        "recomendacion": resultado["recomendacion"],
        "fuente": FUENTE_MODELO,
        "nota": "Inferencia pendiente del modelo propio AgroIA v1.0 (degradación graciosa).",
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
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in filas
        ],
    }


@router.post("/admin/reentrenar")
async def reentrenar_modelo(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Solicita el reentrenamiento del modelo de visión (solo admin).

    Stub de orquestación: registra la solicitud y devuelve el estado del
    pipeline de entrenamiento (MLflow). El entrenamiento real se ejecuta
    fuera del ciclo de la API.
    """
    if (x_user_role or "").lower() not in ("admin", "administrador"):
        raise HTTPException(status_code=403, detail={
            "code": "SOLO_ADMIN",
            "message": "Solo el administrador puede reentrenar el modelo.",
        })
    estado = {
        "estado": "programado",
        "modelo": "agroia-vision-v1",
        "pipeline": "mlflow",
        "mensaje": (
            "Reentrenamiento programado. El modelo propio AgroIA v1.0 "
            "entrenará con las imágenes etiquetadas del dataset."
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
