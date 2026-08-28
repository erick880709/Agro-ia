"""Lista de trabajos (Admin) — traza operativa de fincas por etapa/estado.

Cada finca es una orden de trabajo: se muestra en qué etapa está (semáforo),
qué actividades le faltan, y los conteos por etapa/estado para gráficos.
"""

import uuid as uuid_mod  # noqa: F401 — reservado para filtros futuros por id
from datetime import date

from agroia.database import get_db
from agroia.logging import get_logger
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agroia_backend.models.auditoria import Auditoria
from agroia_backend.models.comision import Comision
from agroia_backend.models.finca import Finca
from agroia_backend.models.lote import Lote
from agroia_backend.models.recomendacion import Recomendacion
from agroia_backend.models.sensor_reading import SensorReading

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["lista-trabajos"])

ETAPAS = (
    "registro", "asignacion_comision", "toma_muestras",
    "recomendacion", "reporte", "finalizada",
)
ETAPA_ETIQUETA = {
    "registro": "Registro (finca/lote)",
    "asignacion_comision": "Asignación de comisión",
    "toma_muestras": "Toma de muestras (parámetros)",
    "recomendacion": "Generación de recomendación",
    "reporte": "Generación de reporte",
    "finalizada": "Fin de actividad",
}
SEMAFORO = {
    "registro": "#9aa4b2",
    "asignacion_comision": "#f0ad4e",
    "toma_muestras": "#f0ad4e",
    "recomendacion": "#5bc0de",
    "reporte": "#5cb85c",
    "finalizada": "#1b5e20",
}


def _exigir_admin(rol: str | None) -> str:
    rol_norm = (rol or "").strip().lower()
    if rol_norm != "admin":
        raise HTTPException(status_code=403, detail={
            "code": "FORBIDDEN_ROLE",
            "message": "Solo el rol administrador puede ver la lista de trabajos.",
        })
    return rol_norm


@router.get("/lista-trabajos")
async def lista_trabajos(
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    etapa: str | None = Query(None),
    estado: str | None = Query(None),
    desde: date | None = Query(None, description="Fecha inicio (>=)"),
    hasta: date | None = Query(None, description="Fecha inicio (<=)"),
):
    """Fincas como órdenes de trabajo: etapa, semáforo y actividades faltantes."""
    _exigir_admin(x_user_role)
    if etapa and etapa not in ETAPAS:
        raise HTTPException(status_code=422, detail={
            "code": "ETAPA_INVALIDA", "message": f"Etapa inválida. Use: {', '.join(ETAPAS)}.",
        })

    fincas = (await db.execute(select(Finca).order_by(Finca.nombre))).scalars().all()
    finca_ids = [f.id for f in fincas]
    if not finca_ids:
        return {"data": [], "total": 0, "conteos_por_etapa": {},
                "conteos_por_estado": {}, "etiquetas_etapa": ETAPA_ETIQUETA}

    # Lotes por finca
    lotes = (
        await db.execute(select(Lote.finca_id, func.count(Lote.id).label("n")).where(
            Lote.finca_id.in_(finca_ids)
        ).group_by(Lote.finca_id))
    ).all()
    lotes_por_finca = {row[0]: row[1] for row in lotes}

    # Comisiones (última por finca)
    comisiones = (
        await db.execute(
            select(Comision).where(Comision.finca_id.in_(finca_ids))
            .order_by(Comision.finca_id, Comision.created_at.desc())
        )
    ).scalars().all()
    comision_por_finca = {}
    for c in comisiones:
        comision_por_finca.setdefault(c.finca_id, c)

    # Lecturas (tomas de muestras)
    lecturas = (
        await db.execute(select(SensorReading.finca_id, func.count(SensorReading.id).label("n")).where(
            SensorReading.finca_id.in_(finca_ids)
        ).group_by(SensorReading.finca_id))
    ).all()
    lecturas_por_finca = {row[0]: row[1] for row in lecturas}

    # Recomendaciones
    recomendaciones = (
        await db.execute(select(Recomendacion.finca_id, func.count(Recomendacion.id).label("n")).where(
            Recomendacion.finca_id.in_(finca_ids)
        ).group_by(Recomendacion.finca_id))
    ).all()
    recomendaciones_por_finca = {row[0]: row[1] for row in recomendaciones}

    # Reportes generados (auditoría reporte.generar, entidad_id = finca_id)
    reportes = (
        await db.execute(
            select(Auditoria.entidad_id, func.max(Auditoria.created_at).label("ultimo")).where(
                Auditoria.entidad_id.in_([str(fid) for fid in finca_ids]),
                Auditoria.accion == "reporte.generar",
            ).group_by(Auditoria.entidad_id)
        )
    ).all()
    reporte_por_finca = {row[0]: row[1] for row in reportes}

    data = []
    for finca in fincas:
        n_lotes = lotes_por_finca.get(finca.id, 0)
        comision = comision_por_finca.get(finca.id)
        n_lecturas = lecturas_por_finca.get(finca.id, 0)
        n_recs = recomendaciones_por_finca.get(finca.id, 0)
        ultimo_reporte = reporte_por_finca.get(str(finca.id))

        faltantes = []
        if n_lotes == 0:
            etapa_c = "registro"
            faltantes.append("Registro de lote")
        elif comision is None:
            etapa_c = "asignacion_comision"
            faltantes.append("Asignación de comisión")
        elif comision.estado in ("asignada", "en_campo") and n_lecturas == 0:
            etapa_c = "toma_muestras"
            faltantes.append("Proceso de toma de muestras (parámetros)")
        elif n_recs == 0:
            etapa_c = "recomendacion"
            faltantes.append("Generación de recomendación")
        elif ultimo_reporte is None:
            etapa_c = "reporte"
            faltantes.append("Generación de reporte (fin de actividad)")
        else:
            etapa_c = "finalizada"

        fecha_inicio = None
        if comision is not None:
            fecha_inicio = comision.fecha_asignacion
        fecha_fin = None
        if ultimo_reporte is not None:
            fecha_fin = ultimo_reporte.date() if hasattr(ultimo_reporte, "date") else None
        if fecha_fin is None and comision is not None and comision.fecha_fin_tomas:
            fecha_fin = comision.fecha_fin_tomas

        estado_c = "finalizada" if etapa_c == "finalizada" else (
            "en_proceso" if comision is not None else "pendiente"
        )

        # Filtros
        if etapa and etapa_c != etapa:
            continue
        if estado and estado_c != estado:
            continue
        if desde and (fecha_inicio is None or fecha_inicio < desde):
            continue
        if hasta and (fecha_inicio is None or fecha_inicio > hasta):
            continue

        data.append({
            "finca_id": str(finca.id),
            "nombre": finca.nombre,
            "municipio": finca.municipio,
            "departamento": finca.departamento,
            "cultivo_sembrado": finca.cultivo_sembrado,
            "etapa": etapa_c,
            "etapa_etiqueta": ETAPA_ETIQUETA[etapa_c],
            "semaforo": SEMAFORO[etapa_c],
            "estado": estado_c,
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
            "faltantes": faltantes,
            "resumen": {
                "lotes": n_lotes,
                "comision_estado": comision.estado if comision else None,
                "lecturas": n_lecturas,
                "recomendaciones": n_recs,
                "reporte_generado": ultimo_reporte is not None,
            },
        })

    conteos_etapa = {e: sum(1 for d in data if d["etapa"] == e) for e in ETAPAS}
    conteos_estado = {
        "pendiente": sum(1 for d in data if d["estado"] == "pendiente"),
        "en_proceso": sum(1 for d in data if d["estado"] == "en_proceso"),
        "finalizada": sum(1 for d in data if d["estado"] == "finalizada"),
    }
    return {
        "data": data,
        "total": len(data),
        "conteos_por_etapa": conteos_etapa,
        "conteos_por_estado": conteos_estado,
        "etiquetas_etapa": ETAPA_ETIQUETA,
        "estados": ["pendiente", "en_proceso", "finalizada"],
    }
