"""Motor de composición de documentos AGC-COST (F4/F5).

Un solo motor para cotización y documento de cobro (RFP §17):
- HTML exportable por audiencia (agricultor = lenguaje claro; técnico =
  desglose completo).
- PDF tamaño carta con numeración «página X de Y», logo PNG con degradación
  al nombre comercial si no hay logo o el archivo es SVG/inaccesible.
- Todo el contenido variable viene de parámetros o del snapshot; la plantilla
  no contiene datos de la empresa escritos en código (RF-26/27/28).
"""

import io
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_CENTIMOS = Decimal("0.01")


def _num(v) -> str:
    """Formato colombiano con separador de miles (RNF-08)."""
    if v is None:
        return "—"
    d = Decimal(str(v)).quantize(_CENTIMOS)
    if d == d.to_integral_value():
        return f"${d:,.0f}"
    return f"${d:,.2f}".replace(",", "·").replace(".", ",").replace("·", ".")


def _identidad_dict(identidad) -> dict:
    """Normaliza la identidad (ORM o dict) a un dict plano."""
    if isinstance(identidad, dict):
        return identidad
    return {
        "nombre_comercial": identidad.nombre_comercial,
        "razon_social": identidad.razon_social,
        "nit": identidad.nit,
        "regimen": identidad.regimen,
        "sitio_web": identidad.sitio_web,
        "correo": identidad.correo,
        "direccion": identidad.direccion,
        "ciudad": identidad.ciudad,
        "logo_url": identidad.logo_url,
        "color_acento": identidad.color_acento or "#1b5e20",
        "pie_legal": identidad.pie_legal,
        "terminos_condiciones": identidad.terminos_condiciones,
        "telefonos": [],
    }


# ─────────────────────────────── HTML ────────────────────────────────────────

def _telefonos_html(identidad: dict) -> str:
    tels = identidad.get("telefonos") or []
    if not tels:
        return ""
    return " · ".join(
        f"{t.get('etiqueta', 'Tel')}: {t.get('numero')}" for t in sorted(tels, key=lambda x: x.get("orden", 0))
    )


def _encabezado_html(identidad: dict, titulo: str, subtitulo: str) -> str:
    nombre = identidad.get("nombre_comercial") or "AgroIA"
    color = identidad.get("color_acento") or "#1b5e20"
    logo_html = ""
    logo = identidad.get("logo_url")
    if logo and str(logo).lower().endswith(".png"):
        logo_html = f'<img src="{logo}" alt="Logo" style="max-height:56px;margin-right:12px;" />'
    fila = "".join(
        f"<span style=\"margin-right:14px\">{t}</span>" for t in (
            (identidad.get("sitio_web") or ""),
            (identidad.get("correo") or ""),
            _telefonos_html(identidad),
            (identidad.get("ciudad") or ""),
        ) if t
    )
    return f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
         border-bottom:3px solid {color};padding-bottom:10px;margin-bottom:14px;">
      <div style="display:flex;align-items:center;">
        {logo_html}
        <div>
          <div style="font-size:20px;font-weight:700;color:{color};">{nombre}</div>
          <div style="font-size:11px;color:#555;">
            {identidad.get('razon_social') or ''}{' · NIT ' + identidad['nit'] if identidad.get('nit') else ''}
          </div>
        </div>
      </div>
      <div style="text-align:right;font-size:11px;color:#333;">{fila}</div>
    </div>
    <h2 style="margin:4px 0;color:{color};">{titulo}</h2>
    <p style="margin:0 0 12px;color:#666;font-size:12px;">{subtitulo}</p>
    """


def html_cotizacion(estimacion: dict, identidad: dict, audiencia: str = "agricultor") -> str:
    """HTML de la cotización con desglose (RF-21, audiencia agricultor/técnico)."""
    es_tecnico = audiencia == "tecnico"
    lineas = estimacion.get("lineas") or []
    filas = "".join(
        f"""<tr>
          <td>{ln.get('lote') or '—'}</td>
          <td>{ln.get('descripcion')}</td>
          <td style="text-align:right">{ln.get('cantidad')}</td>
          <td>{ln.get('unidad') or '—'}</td>
          <td style="text-align:right">{_num(ln.get('valor'))}</td>
        </tr>"""
        for ln in lineas
    )
    bloques_tecnicos = ""
    if es_tecnico:
        bloques_tecnicos = f"""
        <table style="width:100%;border-collapse:collapse;margin-top:10px;font-size:11px;">
          <tr><td style="padding:4px;border:1px solid #ddd;">Subtotal directo</td>
              <td style="text-align:right;border:1px solid #ddd;">{_num(estimacion.get('total_directo'))}</td></tr>
          <tr><td style="padding:4px;border:1px solid #ddd;">Subtotal ajustado (factores)</td>
              <td style="text-align:right;border:1px solid #ddd;">{_num(estimacion.get('total_ajustado'))}</td></tr>
          <tr><td style="padding:4px;border:1px solid #ddd;">Precio de lista</td>
              <td style="text-align:right;border:1px solid #ddd;">{_num(estimacion.get('precio_lista'))}</td></tr>
          <tr><td style="padding:4px;border:1px solid #ddd;">Descuento aplicado</td>
              <td style="text-align:right;border:1px solid #ddd;">−{_num(estimacion.get('descuento_aplicado'))}</td></tr>
        </table>"""
    impuestos = estimacion.get("impuestos_informativos") or []
    impuestos_html = "".join(
        f"""<tr><td style="padding:4px;border:1px solid #ddd;">{i.get('nombre')} ({i.get('porcentaje')}% informativo)</td>
            <td style="text-align:right;border:1px solid #ddd;">{_num(i.get('valor'))}</td></tr>"""
        for i in impuestos
    )
    explicacion_ha = (
        "💡 En lotes pequeños el costo por hectárea se ve alto porque el viaje y el "
        "montaje del equipo cuestan casi lo mismo en 1 ha que en 50 ha: ese costo fijo "
        "se reparte entre menos hectáreas (RFP §2)."
        if not es_tecnico else ""
    )
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/>
<title>Cotización {estimacion.get('consecutivo')}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #222; margin: 24px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; }}
  th {{ background: #f0f7f0; }}
  .total {{ font-size: 18px; font-weight: 700; color: {identidad.get('color_acento', '#1b5e20')}; }}
  @media print {{ body {{ margin: 0; }} }}
</style></head><body>
{_encabezado_html(
    identidad,
    "COTIZACIÓN " + str(estimacion.get('consecutivo') or ''),
    f"Emitida: {estimacion.get('emitida')} · Válida hasta: {estimacion.get('vence')} · "
    f"Asesor: {estimacion.get('asesor') or '—'}",
)}
<div style="font-size:12px;margin-bottom:10px;">
  <strong>Cliente:</strong> {estimacion.get('cliente') or '—'} ·
  <strong>Finca:</strong> {estimacion.get('finca')} ·
  <strong>Municipio:</strong> {estimacion.get('municipio') or '—'} ·
  <strong>Área:</strong> {estimacion.get('area_ha')} ha
</div>
<table>
  <tr><th>Lote</th><th>Descripción</th><th style="text-align:right">Cant.</th><th>Unidad</th><th style="text-align:right">Valor</th></tr>
  {filas}
</table>
{bloques_tecnicos}
{impuestos_html}
<p class="total" style="margin-top:12px;">TOTAL: {_num(estimacion.get('total_final'))} COP</p>
<p style="font-size:11px;color:#555;">{explicacion_ha}</p>
<p style="font-size:11px;color:#555;margin-top:14px;white-space:pre-line;">{identidad.get('terminos_condiciones') or ''}</p>
<p style="font-size:10px;color:#777;white-space:pre-line;">{identidad.get('pie_legal') or ''}</p>
</body></html>"""


def html_cobro(documento: dict, identidad: dict, audiencia: str = "agricultor") -> str:
    """HTML del documento de cobro (hereda líneas de la estimación)."""
    lineas = documento.get("lineas") or []
    filas = "".join(
        f"""<tr>
          <td>{ln.get('descripcion')}</td>
          <td style="text-align:right">{ln.get('cantidad')}</td>
          <td>{ln.get('unidad') or '—'}</td>
          <td style="text-align:right">{_num(ln.get('valor'))}</td>
        </tr>"""
        for ln in lineas
    )
    pagos = documento.get("pagos") or []
    pagos_html = "".join(
        f"""<tr><td>{p.get('fecha')}</td><td>{p.get('medio') or '—'}</td>
        <td style="text-align:right">{_num(p.get('valor'))}</td></tr>"""
        for p in pagos
    )
    bloque_pagos = ""
    if pagos:
        bloque_pagos = (
            '<h3>Pagos</h3><table><tr><th>Fecha</th><th>Medio</th>'
            '<th style="text-align:right">Valor</th></tr>'
            + pagos_html + "</table>"
        )
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/>
<title>Documento de cobro {documento.get('numero')}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #222; margin: 24px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: left; }}
  th {{ background: #f0f7f0; }}
  .total {{ font-size: 18px; font-weight: 700; color: {identidad.get('color_acento', '#1b5e20')}; }}
  @media print {{ body {{ margin: 0; }} }}
</style></head><body>
{_encabezado_html(
    identidad,
    str(documento.get('tipo_titulo') or 'Documento de cobro').upper() + " " + str(documento.get('numero') or ''),
    f"Emisión: {documento.get('fecha_emision')} · Vencimiento: {documento.get('fecha_vencimiento')} · "
    f"Estado: {documento.get('estado')}",
)}
<div style="font-size:12px;margin-bottom:10px;">
  <strong>Cliente:</strong> {documento.get('cliente') or '—'} ·
  <strong>Finca:</strong> {documento.get('finca') or '—'} ·
  <strong>Cotización de origen:</strong> {documento.get('estimacion') or '—'}
</div>
<table>
  <tr><th>Descripción</th><th style="text-align:right">Cant.</th><th>Unidad</th><th style="text-align:right">Valor</th></tr>
  {filas}
</table>
<p class="total" style="margin-top:12px;">TOTAL: {_num(documento.get('total'))} COP · Saldo: {_num(documento.get('saldo'))} COP</p>
{bloque_pagos}
<p style="font-size:11px;color:#555;margin-top:14px;white-space:pre-line;">{documento.get('textos_legales') or ''}</p>
<p style="font-size:10px;color:#777;white-space:pre-line;">{identidad.get('pie_legal') or ''}</p>
</body></html>"""


# ─────────────────────────────── PDF ─────────────────────────────────────────

class _PaginasXY(pdf_canvas.Canvas):
    """Canvas con numeración «página X de Y» en el pie (RFP §17)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas: list[dict] = []

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            self._dibujar_pie(total)
            super().showPage()
        super().save()

    def _dibujar_pie(self, total):
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))
        ancho, _ = letter
        self.drawRightString(ancho - 18 * mm, 10 * mm, f"Página {self._pageNumber} de {total}")


def _logo_imagen(identidad: dict) -> Image | None:
    """Descarga el logo PNG para el PDF; degrada a nombre si falla (RFP §17)."""
    logo = identidad.get("logo_url")
    if not logo or not str(logo).lower().endswith(".png"):
        return None
    try:
        import httpx

        res = httpx.get(str(logo), timeout=8, follow_redirects=True)
        res.raise_for_status()
        if len(res.content) > 2 * 1024 * 1024:
            return None
        img = Image(io.BytesIO(res.content), width=42 * mm, height=14 * mm)
        img.hAlign = "LEFT"
        return img
    except Exception:  # noqa: BLE001 — degradación exigida por el RFP
        return None


def _construir_pdf(
    identidad: dict,
    titulo: str,
    subtitulo: str,
    secciones: list[dict],
    pie: str,
) -> bytes:
    """Construye un PDF carta con encabezado de marca y bloques de contenido."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=titulo,
    )
    estilos = getSampleStyleSheet()
    color = identidad.get("color_acento") or "#1b5e20"
    st_titulo = ParagraphStyle(
        "TituloDoc", parent=estilos["Heading1"], fontSize=16,
        textColor=colors.HexColor(color), spaceAfter=2,
    )
    st_sub = ParagraphStyle(
        "SubDoc", parent=estilos["Normal"], fontSize=9,
        textColor=colors.HexColor("#555555"), spaceAfter=8,
    )
    st_seccion = ParagraphStyle(
        "SeccionDoc", parent=estilos["Heading2"], fontSize=11,
        textColor=colors.HexColor(color), spaceBefore=8, spaceAfter=3,
    )
    st_celda = ParagraphStyle(
        "Celda", parent=estilos["Normal"], fontSize=9, leading=11,
    )
    st_celda_der = ParagraphStyle(
        "CeldaDer", parent=st_celda, alignment=2,
    )
    st_pie = ParagraphStyle(
        "PieDoc", parent=estilos["Normal"], fontSize=8,
        textColor=colors.HexColor("#777777"), alignment=TA_CENTER,
    )

    elementos: list = []
    logo = _logo_imagen(identidad)
    if logo is not None:
        elementos.append(logo)
        elementos.append(Spacer(1, 4))
    nombre = identidad.get("nombre_comercial") or "AgroIA"
    elementos.append(Paragraph(f"<b>{nombre}</b>", st_titulo))
    contacto = " · ".join(
        t for t in (
            identidad.get("nit") and f"NIT {identidad['nit']}",
            identidad.get("sitio_web"),
            identidad.get("correo"),
            identidad.get("ciudad"),
        ) if t
    )
    if contacto:
        elementos.append(Paragraph(contacto, st_sub))
    for telefono in identidad.get("telefonos") or []:
        elementos.append(Paragraph(
            f"{telefono.get('etiqueta', 'Tel')}: {telefono.get('numero')}", st_sub,
        ))
    elementos.append(Paragraph(titulo, st_seccion))
    elementos.append(Paragraph(subtitulo, st_sub))

    for seccion in secciones:
        if seccion.get("titulo"):
            elementos.append(Paragraph(seccion["titulo"], st_seccion))
        for parrafo in seccion.get("parrafos") or []:
            elementos.append(Paragraph(parrafo, estilos["Normal"]))
        tabla = seccion.get("tabla")
        if tabla:
            datos = [[Paragraph(str(h), st_celda_der if i == len(tabla["headers"]) - 1 else st_celda)
                      for i, h in enumerate(tabla["headers"])]]
            for fila in tabla["rows"]:
                datos.append([
                    Paragraph(str(c), st_celda_der if i == len(fila) - 1 else st_celda)
                    for i, c in enumerate(fila)
                ])
            t = Table(datos, colWidths=tabla.get("colWidths"), repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf3ea")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elementos.append(t)
        if seccion.get("salto"):
            elementos.append(PageBreak())

    elementos.append(Spacer(1, 10))
    if pie:
        elementos.append(Paragraph(pie, st_pie))

    doc.build(elementos, canvasmaker=_PaginasXY)
    return buffer.getvalue()


def pdf_cotizacion(estimacion: dict, identidad: dict) -> bytes:
    """PDF de cotización tamaño carta (CA-10/CA-11)."""
    lineas = estimacion.get("lineas") or []
    tabla = {
        "headers": ["Lote", "Descripción", "Cant.", "Unidad", "Valor"],
        "colWidths": [20 * mm, 76 * mm, 14 * mm, 18 * mm, 26 * mm],
        "rows": [
            [ln.get("lote") or "—", ln.get("descripcion"), ln.get("cantidad"),
             ln.get("unidad") or "—", _num(ln.get("valor"))]
            for ln in lineas
        ],
    }
    totales_rows = [
        ["Subtotal directo", _num(estimacion.get("total_directo"))],
        ["Subtotal ajustado", _num(estimacion.get("total_ajustado"))],
        ["Descuento aplicado", "−" + _num(estimacion.get("descuento_aplicado"))],
    ]
    for i in estimacion.get("impuestos_informativos") or []:
        totales_rows.append([
            f"{i.get('nombre')} ({i.get('porcentaje')}% informativo)", _num(i.get("valor")),
        ])
    totales_rows.append(["TOTAL", _num(estimacion.get("total_final")) + " COP"])
    tabla_totales = {
        "headers": ["Concepto", "Valor"],
        "colWidths": [128 * mm, 26 * mm],
        "rows": totales_rows,
    }
    secciones = [
        {"titulo": "Datos del cliente y la finca", "parrafos": [
            f"<b>Cliente:</b> {estimacion.get('cliente') or '—'} · "
            f"<b>Finca:</b> {estimacion.get('finca')} · "
            f"<b>Municipio:</b> {estimacion.get('municipio') or '—'} · "
            f"<b>Área:</b> {estimacion.get('area_ha')} ha",
            f"<b>Vigencia:</b> válida hasta {estimacion.get('vence')} · "
            f"<b>Consecutivo:</b> {estimacion.get('consecutivo')}",
        ]},
        {"titulo": "Desglose de servicios", "tabla": tabla},
        {"titulo": "Totales", "tabla": tabla_totales},
        {"titulo": "Condiciones comerciales", "parrafos": [
            estimacion.get("terminos") or "",
        ]},
    ]
    return _construir_pdf(
        identidad,
        f"COTIZACIÓN {estimacion.get('consecutivo') or ''}",
        f"Emitida: {estimacion.get('emitida')} · Asesor: {estimacion.get('asesor') or '—'}",
        secciones,
        identidad.get("pie_legal") or "",
    )


def pdf_cobro(documento: dict, identidad: dict) -> bytes:
    """PDF del documento de cobro (hereda líneas y totales)."""
    lineas = documento.get("lineas") or []
    tabla = {
        "headers": ["Descripción", "Cant.", "Unidad", "Valor"],
        "colWidths": [104 * mm, 16 * mm, 18 * mm, 26 * mm],
        "rows": [
            [ln.get("descripcion"), ln.get("cantidad"), ln.get("unidad") or "—", _num(ln.get("valor"))]
            for ln in lineas
        ],
    }
    secciones = [
        {"titulo": "Datos del documento", "parrafos": [
            f"<b>Cliente:</b> {documento.get('cliente') or '—'} · "
            f"<b>Finca:</b> {documento.get('finca') or '—'}",
            f"<b>Cotización de origen:</b> {documento.get('estimacion') or '—'} · "
            f"<b>Vencimiento:</b> {documento.get('fecha_vencimiento') or '—'}",
        ]},
        {"titulo": "Líneas", "tabla": tabla},
        {"titulo": "Totales", "parrafos": [
            f"<b>TOTAL:</b> {_num(documento.get('total'))} COP · "
            f"<b>Saldo pendiente:</b> {_num(documento.get('saldo'))} COP",
        ]},
    ]
    if documento.get("pagos"):
        secciones.append({
            "titulo": "Pagos registrados",
            "tabla": {
                "headers": ["Fecha", "Medio", "Valor"],
                "colWidths": [40 * mm, 70 * mm, 44 * mm],
                "rows": [
                    [p.get("fecha"), p.get("medio") or "—", _num(p.get("valor"))]
                    for p in documento.get("pagos") or []
                ],
            },
        })
    return _construir_pdf(
        identidad,
        f"{(documento.get('tipo_titulo') or 'Documento de cobro').upper()} {documento.get('numero') or ''}",
        f"Emisión: {documento.get('fecha_emision') or '—'} · Estado: {documento.get('estado') or '—'}",
        secciones,
        (documento.get("textos_legales") or "") + "\n" + (identidad.get("pie_legal") or ""),
    )
