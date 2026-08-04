"""API endpoints del dashboard y reportes PDF."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from agroia.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/dashboard/{finca_id}")
async def dashboard_finca(finca_id: str, modo: str = Query("agricultor", regex="^(agricultor|experto)$")):
    """Dashboard completo de una finca.

    Args:
        finca_id: UUID de la finca
        modo: 'agricultor' (coloquial, semáforos) o 'experto' (datos crudos, métricas)
    """
    from agroia_backend.services.dashboard_service import get_dashboard_data

    try:
        data = await get_dashboard_data(finca_id)
    except Exception as e:
        logger.error("dashboard_error", finca_id=finca_id, error=str(e))
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": "Error al generar dashboard"})

    if modo == "agricultor":
        # Lenguaje coloquial, sin datos crudos
        return _format_agricultor(data)
    else:
        # Modo experto: datos crudos + métricas + anotaciones
        return _format_experto(data)


def _format_agricultor(data: dict) -> dict:
    """Formatea el dashboard para modo agricultor (lenguaje coloquial, semáforos)."""
    rec = data.get("ultima_recomendacion", {})
    clasificacion = rec.get("clasificacion_upra", "Sin datos")

    mensajes = {
        "Alta": "✅ ¡Excelente! Su suelo está en condiciones óptimas para el cultivo.",
        "Media": "🟡 Su suelo es apto, pero puede mejorar con algunas correcciones.",
        "Baja": "🟠 Su suelo necesita atención. Revise las recomendaciones.",
        "NoApta": "🔴 Su suelo no es apto para este cultivo. Se sugieren alternativas.",
    }

    return {
        "finca_id": data["finca_id"],
        "modo": "agricultor",
        "mensaje": mensajes.get(clasificacion, "Analizando su suelo..."),
        "semaforo": {
            "clasificacion": clasificacion,
            "color": rec.get("color", "#F9A825"),
            "confianza": rec.get("confianza", 0),
        },
        "kpis": data.get("kpis", []),
        "alertas": data.get("alertas", []),
        "guia": "Revise las recomendaciones paso a paso en la sección 'Recomendaciones'.",
    }


def _format_experto(data: dict) -> dict:
    """Formatea el dashboard para modo experto (datos crudos, métricas, exportables)."""
    return {
        "finca_id": data["finca_id"],
        "modo": "experto",
        "ultima_recomendacion": data.get("ultima_recomendacion"),
        "kpis": data.get("kpis", []),
        "series": data.get("series", []),
        "alertas": data.get("alertas", []),
        "exportar": {
            "csv": f"/api/v1/dashboard/{data['finca_id']}/export?format=csv",
            "json": f"/api/v1/dashboard/{data['finca_id']}/export?format=json",
            "excel": f"/api/v1/dashboard/{data['finca_id']}/export?format=excel",
        },
    }


@router.get("/reportes/{finca_id}/pdf", response_class=HTMLResponse)
async def generar_reporte_pdf(finca_id: str):
    """Genera un reporte PDF para una finca.

    En producción, usa WeasyPrint para convertir HTML → PDF.
    En desarrollo, retorna el HTML para previsualizar en navegador.
    """
    from agroia_backend.services.dashboard_service import generate_pdf_html, get_dashboard_data

    try:
        data = await get_dashboard_data(finca_id)
        html = generate_pdf_html(data, f"Finca {finca_id[:8]}")
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error("reporte_error", finca_id=finca_id, error=str(e))
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": "Error al generar reporte"})


@router.get("/dashboard/{finca_id}/export")
async def exportar_datos(finca_id: str, format: str = Query("json", regex="^(csv|json|excel)$")):
    """Exporta datos del dashboard en CSV, JSON o Excel."""
    from agroia_backend.services.dashboard_service import get_dashboard_data

    data = await get_dashboard_data(finca_id)

    if format == "csv":
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ts", "ph", "nitrogeno", "fosforo", "potasio", "humedad"])
        for r in data.get("series", []):
            writer.writerow([r.get("ts"), r.get("ph"), r.get("nitrogeno"), r.get("fosforo"), r.get("potasio"), r.get("humedad")])
        return HTMLResponse(content=f"<pre>{output.getvalue()}</pre>", media_type="text/csv")

    return {"finca_id": finca_id, "format": format, "data": data["series"]}
