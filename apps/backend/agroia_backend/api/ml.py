"""API de estado de los modelos de ML (validación de entrenamiento).

GET /api/v1/ml/estado — modelos registrados, métricas y artefactos.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia.database import get_db
from agroia_backend.models.metrica_modelo import MetricaModelo
from agroia_backend.models.modelo_ml import ModeloML
from agroia_backend.services.ml_oracle import MLOracleService

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
        "n_artefactos": len(list(oracle.dir.glob("ml_*.joblib"))) if oracle.dir.exists() else 0,
    }
