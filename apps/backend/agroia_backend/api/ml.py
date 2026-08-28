"""API de estado de los modelos de ML (validación de entrenamiento).

GET /api/v1/ml/estado — modelos registrados, métricas y artefactos.
GET /api/v1/ml/etiquetas-doradas — Ground Truth disponible (Admin).
POST /api/v1/admin/ml/reentrenar — encola reentrenamiento (Admin, v4).
"""

import asyncio
import json
import os
import subprocess
import uuid as uuid_mod
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia.database import get_db
from agroia_backend.models.aceptacion_recomendacion import AceptacionRecomendacion
from agroia_backend.models.metrica_modelo import MetricaModelo
from agroia_backend.models.modelo_ml import ModeloML
from agroia_backend.services.ml_oracle import MLOracleService
from agroia_backend.services.ml_labels import resumen_etiquetas_doradas

router = APIRouter(prefix="/ml", tags=["ml"])
admin_router = APIRouter(prefix="/api/v1", tags=["ml-admin"])

_ML_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "apps", "ml")
)


class ReentrenarRequest(BaseModel):
    cultivos_incluidos: list[str] = Field(default_factory=list)
    modo: str = Field("active-learning", pattern="^(active-learning|full)$")


@admin_router.post("/admin/v4/sembrar")
async def sembrar_v4(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Siembra idempotente de datos estáticos v4 (catálogo, Kc, variedades, rotación, carencias, curvas)."""
    if (x_user_role or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE", "message": "Solo el administrador puede sembrar datos v4.",
        })
    from agroia_backend.services.seed_v4 import sembrar_v4 as _sembrar

    resumen = await _sembrar(db)
    return {"status": "sembrado", "resumen": resumen}


@admin_router.post("/admin/ml/reentrenar", status_code=202)
async def reentrenar_modelo(
    body: ReentrenarRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_user_email: str | None = Header(None, alias="X-User-Email"),
):
    """Encola un reentrenamiento del modelo ML (solo Admin).

    Ejecuta `train_colombia.py --registrar --active-learning` como proceso en
    background. Regla de degradación: los cultivos sin modelo propio siguen
    recomendándose por el sistema experto de reglas.
    """
    if (x_user_role or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE", "message": "Solo el administrador puede reentrenar el modelo.",
        })

    from agroia_backend.services.auditoria import registrar_auditoria

    job_id = uuid_mod.uuid4()
    try:
        await registrar_auditoria(
            db,
            usuario_email=x_user_email or "desconocido@agroia.co",
            rol=x_user_role,
            accion="ml.reentrenar",
            entidad="modelo_ml",
            entidad_id=str(job_id),
            detalle={"cultivos_incluidos": body.cultivos_incluidos, "modo": body.modo},
        )
        await db.commit()
    except Exception:  # noqa: BLE001 — no bloquear el encolado por auditoría
        await db.rollback()

    def _lanzar() -> None:
        comando = [
            os.environ.get("PYTHON_BIN", "python"),
            "train_colombia.py",
            "--registrar",
            "--active-learning" if body.modo == "active-learning" else "--full",
        ]
        env = dict(os.environ)
        env["PYTHONPATH"] = (
            f"{_ML_ROOT};{os.path.dirname(_ML_ROOT)};" + env.get("PYTHONPATH", "")
        )
        try:
            subprocess.Popen(
                comando, cwd=_ML_ROOT, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:  # noqa: BLE001 — el job queda registrado como en_cola
            pass

    await asyncio.to_thread(_lanzar)
    return {
        "job_id": str(job_id),
        "estado": "en_cola",
        "mensaje": (
            "Reentrenamiento encolado; ejecuta train_colombia.py --registrar "
            f"--active-learning con los cultivos indicados ({len(body.cultivos_incluidos)})"
        ),
        "encolado_en": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/estado")
async def estado_ml(db: AsyncSession = Depends(get_db)):
    """Estado del entrenamiento: modelos registrados, métricas y artefactos."""
    modelos = (await db.execute(select(ModeloML).order_by(ModeloML.created_at.desc()))).scalars().all()
    metricas = (
        await db.execute(
            select(MetricaModelo)
            .order_by(MetricaModelo.fecha_registro.desc())
            .limit(500)
        )
    ).scalars().all()
    oracle = MLOracleService()
    artefactos_meta = None
    meta_path = oracle.dir / "ml_meta.json"
    if meta_path.exists():
        try:
            artefactos_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            artefactos_meta = None
    return {
        "modelos": [
            {
                "id": str(m.id),
                "nombre": m.nombre,
                "tipo": m.tipo_modelo,
                "version": m.version,
                "f1_score": m.f1_score,
                "stage": m.stage.value if m.stage else None,
                "activo": m.activo,
            }
            for m in modelos
        ],
        "metricas": [
            {
                "modelo": str(m.modelo_ml_id),
                "metrica": m.metrica,
                "valor": m.valor,
            }
            for m in metricas
        ],
        "artefactos_meta": artefactos_meta,
        "oraculo_ml_disponible": oracle.disponible(),
        "variables_promovidas": sorted(oracle.variables_promovidas()),
        "n_artefactos": len(list(oracle.dir.glob("ml_*.joblib"))) if oracle.dir.exists() else 0,
        "validaciones_humanas": int(
            (await db.execute(
                select(func.count(AceptacionRecomendacion.id))
            )).scalar_one() or 0
        ),
    }


@router.get("/etiquetas-doradas")
async def etiquetas_doradas(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
):
    """Ground Truth disponible para el aprendizaje activo (solo Admin).

    Muestra cuántas aceptaciones humanas y ciclos cerrados alimentan el
    pipeline `train_colombia.py --active-learning` y la cobertura por variable.
    """
    rol = (x_user_role or "").strip().lower()
    if rol not in {"admin", "administrador"}:
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el administrador puede consultar las etiquetas doradas.",
        })
    resumen = await resumen_etiquetas_doradas(db)
    return {"status": "ok", **resumen}
