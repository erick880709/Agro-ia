"""API de estado de los modelos de ML (validación de entrenamiento).

GET /api/v1/ml/estado — modelos registrados, métricas y artefactos.
GET /api/v1/ml/etiquetas-doradas — Ground Truth disponible (Admin).
"""

import json

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia.database import get_db
from agroia_backend.models.aceptacion_recomendacion import AceptacionRecomendacion
from agroia_backend.models.metrica_modelo import MetricaModelo
from agroia_backend.models.modelo_ml import ModeloML
from agroia_backend.services.ml_oracle import MLOracleService
from agroia_backend.services.ml_labels import resumen_etiquetas_doradas

router = APIRouter(prefix="/ml", tags=["ml"])


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
