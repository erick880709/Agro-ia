"""Servicio de dashboards y reportes PDF.

Agrega datos de múltiples fuentes para el dashboard por finca
y genera reportes PDF con WeasyPrint usando plantilla HTML/CSS.
"""

from datetime import datetime, timedelta

from agroia.logging import get_logger

from agroia_backend.models.sensor_reading import SensorReading

logger = get_logger(__name__)

# ── Colores semáforo ──
COLOR_ALTA = "#2E7D32"   # verde oscuro
COLOR_MEDIA = "#F9A825"  # amarillo
COLOR_BAJA = "#E65100"   # naranja
COLOR_NO_APTA = "#C62828"  # rojo

COLOR_MAP = {
    "Alta": COLOR_ALTA,
    "Media": COLOR_MEDIA,
    "Baja": COLOR_BAJA,
    "NoApta": COLOR_NO_APTA,
}


async def get_dashboard_data(finca_id: str) -> dict:
    """Agrega todos los datos necesarios para el dashboard de una finca.

    Returns:
        Dict con: finca, ultima_recomendacion, series_sensores, kpis, alertas, clima
    """
    from agroia.database import async_session_factory
    from sqlalchemy import desc, select

    from agroia_backend.models.recomendacion import Recomendacion

    async with async_session_factory() as session:
        # Última recomendación
        stmt = (
            select(Recomendacion)
            .where(Recomendacion.finca_id == finca_id)
            .order_by(desc(Recomendacion.created_at))
            .limit(1)
        )
        result = await session.execute(stmt)
        ultima_rec = result.scalar_one_or_none()

        # Últimas 30 lecturas de sensores (series temporales)
        cutoff = datetime.utcnow() - timedelta(days=30)
        stmt = (
            select(SensorReading)
            .where(SensorReading.finca_id == finca_id, SensorReading.ts >= cutoff)
            .order_by(SensorReading.ts)
            .limit(100)
        )
        result = await session.execute(stmt)
        readings = result.scalars().all()

    # ── Construir respuesta ──
    dashboard = {
        "finca_id": finca_id,
        "generado_en": datetime.utcnow().isoformat(),
    }

    # Última recomendación
    if ultima_rec:
        dashboard["ultima_recomendacion"] = {
            "id": str(ultima_rec.id),
            "cultivo": "Cultivo",  # TODO: resolver nombre del cultivo vía relación
            "clasificacion_upra": ultima_rec.clasificacion_upra.value,
            "color": COLOR_MAP.get(ultima_rec.clasificacion_upra.value, COLOR_MEDIA),
            "confianza": round(ultima_rec.confianza * 100),
            "fecha": ultima_rec.created_at.isoformat() if ultima_rec.created_at else None,
        }

    # KPIs
    dashboard["kpis"] = _build_kpis(readings)

    # Series temporales (últimas 30 lecturas)
    dashboard["series"] = _build_time_series(readings)

    # Alertas
    dashboard["alertas"] = _build_alertas(readings, ultima_rec)

    return dashboard


def _build_kpis(readings: list) -> list[dict]:
    """Construye KPIs desde las lecturas de sensor."""
    if not readings:
        return []

    latest = readings[-1]
    kpis = []
    for var, label, unidad in [
        ("ph", "pH del suelo", ""),
        ("nitrogeno", "Nitrógeno (N)", "ppm"),
        ("fosforo", "Fósforo (P)", "ppm"),
        ("potasio", "Potasio (K)", "ppm"),
        ("materia_organica", "Mat. Orgánica", "%"),
        ("humedad", "Humedad", "%"),
    ]:
        val = getattr(latest, var, None)
        if val is not None:
            kpis.append({"variable": label, "valor": round(val, 1), "unidad": unidad})
    return kpis[:6]


def _build_time_series(readings: list) -> list[dict]:
    """Construye series temporales para gráficos."""
    if not readings:
        return []

    return [
        {
            "ts": r.ts.isoformat() if r.ts else None,
            "ph": r.ph,
            "nitrogeno": r.nitrogeno,
            "fosforo": r.fosforo,
            "potasio": r.potasio,
            "humedad": r.humedad,
        }
        for r in readings[-30:]  # últimas 30 lecturas
    ]


def _build_alertas(readings: list, ultima_rec) -> list[dict]:
    """Construye alertas desde lecturas y recomendación."""
    alertas = []

    # Alerta: sin datos recientes
    if not readings:
        alertas.append({"tipo": "warning", "mensaje": "No hay datos de sensor en los últimos 30 días."})
    else:
        latest = readings[-1]
        if latest.ts and (datetime.utcnow() - latest.ts).total_seconds() > 86400:
            alertas.append({"tipo": "warning", "mensaje": "Datos desactualizados (>24h). Verifique los sensores."})

    # Alerta: baja confianza
    if ultima_rec and ultima_rec.confianza < 0.80:
        alertas.append({"tipo": "warning", "mensaje": f"Recomendación con baja confianza ({ultima_rec.confianza:.0%}). Un técnico la revisará."})

    return alertas


# ═══════════════════════════════════════════════════
# Generación de PDF
# ═══════════════════════════════════════════════════

PDF_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Reporte AgroIA — {finca_nombre}</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 2cm; color: #333; }}
    .header {{ border-bottom: 3px solid #2E7D32; padding-bottom: 10px; margin-bottom: 20px; }}
    .header img {{ height: 50px; }}
    .header h1 {{ color: #2E7D32; margin: 0; }}
    .header p {{ color: #666; font-size: 12px; }}
    .section {{ margin-bottom: 25px; }}
    .section h2 {{ color: #2E7D32; font-size: 18px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
    .upra-badge {{ display: inline-block; padding: 8px 16px; border-radius: 4px; color: white; font-weight: bold; font-size: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f5f5f5; }}
    .kpi {{ display: inline-block; width: 30%; margin: 10px; padding: 15px; border-radius: 8px; background: #f9f9f9; text-align: center; }}
    .kpi .valor {{ font-size: 28px; font-weight: bold; color: #2E7D32; }}
    .kpi .label {{ font-size: 12px; color: #666; }}
    .alerta {{ padding: 10px; margin: 5px 0; border-radius: 4px; }}
    .alerta.warning {{ background: #FFF3E0; border-left: 4px solid #F9A825; }}
    .alerta.critica {{ background: #FFEBEE; border-left: 4px solid #C62828; }}
    .footer {{ margin-top: 30px; font-size: 10px; color: #999; text-align: center; border-top: 1px solid #eee; padding-top: 10px; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>🌱 AgroIA — Reporte de Diagnóstico</h1>
    <p>Finca: {finca_nombre} | Fecha: {fecha} | Confidencial — Ley 1581/2012</p>
  </div>

  <div class="section">
    <h2>📊 Clasificación de Aptitud (UPRA)</h2>
    <div class="upra-badge" style="background-color:{color_upra}">
      {clasificacion_upra} — Confianza: {confianza}%
    </div>
    <p>{recomendacion_texto}</p>
  </div>

  <div class="section">
    <h2>📈 KPIs del Suelo</h2>
    {kpis_html}
  </div>

  <div class="section">
    <h2>🔬 Variables vs. Umbrales Ideales</h2>
    {variables_html}
  </div>

  <div class="section">
    <h2>⚠️ Alertas</h2>
    {alertas_html}
  </div>

  <div class="footer">
    <p>Generado por AgroInteligente Colombia (AgroIA) — {fecha_generacion}</p>
    <p>Este reporte es de uso exclusivo del agricultor. No compartir sin autorización.</p>
  </div>
</body>
</html>
"""


def generate_pdf_html(dashboard_data: dict, finca_nombre: str = "Mi Finca") -> str:
    """Genera el HTML para el reporte PDF."""
    rec = dashboard_data.get("ultima_recomendacion", {})
    kpis = dashboard_data.get("kpis", [])
    alertas = dashboard_data.get("alertas", [])

    kpis_html = ""
    for kpi in kpis:
        kpis_html += f'<div class="kpi"><div class="valor">{kpi["valor"]}</div><div class="label">{kpi["variable"]} ({kpi["unidad"]})</div></div>\n'

    alertas_html = ""
    for a in alertas:
        alertas_html += f'<div class="alerta {a.get("tipo", "warning")}">⚠️ {a["mensaje"]}</div>\n'

    return PDF_TEMPLATE.format(
        finca_nombre=finca_nombre,
        fecha=datetime.utcnow().strftime("%d/%m/%Y"),
        color_upra=rec.get("color", COLOR_MEDIA),
        clasificacion_upra=rec.get("clasificacion_upra", "Sin datos"),
        confianza=rec.get("confianza", 0),
        recomendacion_texto="Revise las recomendaciones en la plataforma AgroIA para acciones correctivas detalladas.",
        kpis_html=kpis_html,
        variables_html="<p>Consulte la plataforma para el detalle completo de variables.</p>",
        alertas_html=alertas_html or "<p>✅ No hay alertas activas para esta finca.</p>",
        fecha_generacion=datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
    )
