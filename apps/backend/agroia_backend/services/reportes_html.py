"""Generador de reportes HTML de AgroIA (estilo informe de laboratorio).

Tipos de reporte:
  - siembra:  recomendación de siembra (UC1).
  - cultivo:  recomendación para el cultivo sembrado (UC2).
  - completo: UC1 + UC2 en un solo documento.

El HTML es auto-contenido (solo Google Fonts externos) e incluye un botón
de impresión para guardarlo como PDF desde el navegador.
"""

from datetime import datetime, timezone
from html import escape as esc

from agroia_backend.services.lenguaje_campesino import generar_explicacion_campesina

_CSS = """
  :root {
    --bg:        #16130f;   --surface:   #201b14;   --surface-2: #292219;
    --line:      #3a3126;   --text:      #ede6d8;   --muted:     #a4947d;
    --moss:      #87a95c;   --amber:     #d99a3d;   --clay:      #c05b45;
    --sky:       #6b87ad;   --accent:    #e3b04b;
    --mono: "IBM Plex Mono", "Cascadia Mono", Consolas, monospace;
    --sans: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
    --serif: "Fraunces", Georgia, "Times New Roman", serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: radial-gradient(1100px 500px at 85% -10%, rgba(227,176,75,.07), transparent 60%),
                radial-gradient(900px 420px at -10% 110%, rgba(135,169,92,.05), transparent 55%), var(--bg);
    color: var(--text); font-family: var(--sans); line-height: 1.55; padding: 40px 20px 72px;
  }
  .sheet { max-width: 860px; margin: 0 auto; border: 1px solid var(--line); background: var(--surface); box-shadow: 0 24px 60px rgba(0,0,0,.45); }

  header.specimen { border-bottom: 1px solid var(--line); padding: 28px 32px 24px; display: flex; flex-wrap: wrap; gap: 18px; justify-content: space-between; align-items: flex-end; }
  .brand { font-family: var(--serif); font-weight: 900; font-size: 1.9rem; letter-spacing: -.01em; }
  .brand em { font-style: normal; color: var(--accent); }
  .kicker { font-family: var(--mono); font-size: .72rem; letter-spacing: .18em; text-transform: uppercase; color: var(--muted); }
  .specimen-label { text-align: right; font-family: var(--mono); font-size: .8rem; color: var(--muted); border: 1px dashed var(--line); padding: 8px 12px; }
  .specimen-label strong { display: block; color: var(--text); font-size: 1rem; font-weight: 500; }

  .ph-scale { padding: 22px 32px; border-bottom: 1px solid var(--line); background: linear-gradient(180deg, rgba(0,0,0,.18), transparent); }
  .ph-scale .label { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
  .ph-scale .label span:first-child { font-family: var(--mono); font-size: .72rem; letter-spacing: .16em; text-transform: uppercase; color: var(--muted); }
  .ph-scale .reading { font-family: var(--mono); font-size: 1.05rem; }
  .ph-scale .reading b { color: var(--accent); font-weight: 500; }
  .ph-track { position: relative; height: 14px; border-radius: 7px; background: linear-gradient(90deg, #c65b3f 0%, #d98a4e 18%, #c9a94e 32%, #87a95c 47%, #6b87ad 70%, #7d6ba6 100%); }
  .ph-ticks { display: flex; justify-content: space-between; font-family: var(--mono); font-size: .68rem; color: var(--muted); margin-top: 6px; }
  .ph-marker { position: absolute; top: -4px; width: 2px; height: 22px; background: #fff; border-radius: 1px; }
  .ph-marker::after { content: attr(data-ph); position: absolute; bottom: -20px; left: 50%; transform: translateX(-50%); font-family: var(--mono); font-size: .68rem; color: #fff; background: rgba(0,0,0,.55); padding: 2px 8px; border-radius: 10px; white-space: nowrap; }

  section.block { padding: 26px 32px; border-bottom: 1px solid var(--line); }
  section.block:last-of-type { border-bottom: none; }
  .block-head { display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px; }
  .block-num { font-family: var(--serif); font-weight: 300; font-size: 1.5rem; color: var(--muted); }
  .block-title { font-family: var(--serif); font-weight: 600; font-size: 1.25rem; }
  .block-sub { font-family: var(--mono); font-size: .7rem; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }

  .telemetry { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
  .tile { background: var(--surface-2); border: 1px solid var(--line); padding: 12px 14px; }
  .tile .k { font-family: var(--mono); font-size: .66rem; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }
  .tile .v { font-family: var(--mono); font-size: 1.02rem; margin-top: 4px; }
  .tile .v small { color: var(--muted); font-size: .72rem; }

  table { width: 100%; border-collapse: collapse; font-size: .88rem; }
  th { text-align: left; font-family: var(--mono); font-weight: 500; font-size: .68rem; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); padding: 8px 10px; border-bottom: 1px solid var(--line); }
  td { padding: 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  td.mono, td.num { font-family: var(--mono); font-size: .86rem; }
  td.num { text-align: right; }

  .badge { display: inline-block; font-family: var(--mono); font-size: .66rem; letter-spacing: .1em; text-transform: uppercase; padding: 3px 8px; border-radius: 3px; border: 1px solid; }
  .badge-exceso  { color: #f0a08e; border-color: rgba(192,91,69,.55); background: rgba(192,91,69,.12); }
  .badge-deficit { color: #ecc27a; border-color: rgba(217,154,61,.55); background: rgba(217,154,61,.10); }
  .badge-ok      { color: #a9c584; border-color: rgba(135,169,92,.55); background: rgba(135,169,92,.10); }
  .badge-noapta  { color: #f0a08e; border-color: var(--clay); background: rgba(192,91,69,.18); }
  .badge-apta    { color: #a9c584; border-color: rgba(135,169,92,.55); background: rgba(135,169,92,.10); }

  .verdict { margin-top: 16px; padding: 12px 16px; border-left: 3px solid var(--clay); background: rgba(192,91,69,.08); font-family: var(--mono); font-size: .82rem; }
  .verdict b { font-weight: 500; }

  .rank { display: flex; align-items: center; gap: 14px; padding: 10px 0; border-bottom: 1px solid var(--line); }
  .rank:last-child { border-bottom: none; }
  .rank .pos { font-family: var(--serif); font-weight: 900; font-size: 1.3rem; color: var(--accent); min-width: 28px; }
  .rank .crop { flex: 1; }
  .rank .crop b { font-family: var(--serif); font-weight: 600; font-size: 1.02rem; }
  .rank .crop span { display: block; color: var(--muted); font-size: .78rem; }
  .scorebar { width: 160px; height: 8px; border-radius: 4px; background: var(--surface-2); border: 1px solid var(--line); overflow: hidden; }
  .scorebar i { display: block; height: 100%; background: linear-gradient(90deg, var(--amber), var(--moss)); }
  .rank .score { font-family: var(--mono); font-size: .95rem; min-width: 92px; text-align: right; }

  ul.warnings { list-style: none; }
  ul.warnings li { padding: 10px 0 10px 26px; position: relative; border-bottom: 1px solid var(--line); font-size: .88rem; }
  ul.warnings li:last-child { border-bottom: none; }
  ul.warnings li::before { content: "⚠"; position: absolute; left: 0; color: var(--amber); }

  ol.steps { list-style: none; counter-reset: paso; }
  ol.steps li { counter-increment: paso; position: relative; padding: 8px 0 8px 34px; border-bottom: 1px solid var(--line); font-size: .88rem; }
  ol.steps li:last-child { border-bottom: none; }
  ol.steps li::before { content: counter(paso, decimal-leading-zero); position: absolute; left: 0; top: 10px; font-family: var(--mono); font-size: .72rem; color: var(--accent); }

  .stamp { text-align: right; padding: 18px 32px; font-family: var(--mono); font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; color: var(--amber); border-top: 1px solid var(--line); }
  footer.colophon { text-align: center; color: var(--muted); font-family: var(--mono); font-size: .7rem; padding: 26px 0 0; }

  /* ── Lenguaje de campo ── */
  .field-talk { background: linear-gradient(180deg, rgba(135,169,92,.06), transparent); }
  .field-talk .block-title { color: var(--moss); }
  .heatmap .heat-var { margin-bottom: 18px; }
  .heatmap .heat-var.hidden { display: none; }
  .heat-tabs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
  .heat-tab { font-family: var(--mono); font-size: .72rem; letter-spacing: .04em;
    padding: 6px 12px; border-radius: 999px; border: 1px solid var(--line);
    background: #fff; color: var(--text); cursor: pointer; }
  .heat-tab.active { background: var(--moss); color: #fff; border-color: var(--moss); }
  .heatmap .heat-title { font-weight: 600; margin-bottom: 6px; }
  .heat-legend { display: flex; align-items: center; gap: 8px; font-size: .78rem; color: var(--muted); margin-bottom: 8px; }
  .heat-legend .chip { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  .heat-grid { display: grid; gap: 2px; max-width: 560px; margin-bottom: 4px; }
  .heat-cell { aspect-ratio: 1.6 / 1; display: flex; align-items: center; justify-content: center;
    font-family: var(--mono); font-size: .68rem; border-radius: 3px; }
  .heat-cell:hover { outline: 2px solid var(--moss); }
  .heatmap .heat-var, .plano-lote { break-inside: avoid; page-break-inside: avoid; }
  .plano-svg { max-width: 560px; border: 1px solid var(--line); border-radius: 8px; background: #fbfcf8; }
  .plano-stats { display: flex; flex-wrap: wrap; gap: 10px; margin: 8px 0 12px; }
  .plano-stat { background: var(--surface-2); border: 1px solid var(--line); border-radius: 8px;
    padding: 8px 14px; font-size: .82rem; }
  .plano-stat b { display: block; font-family: var(--mono); font-size: 1.05rem; color: var(--moss); }
  .clima-muestra { margin-top: 16px; padding: 14px 16px; border: 1px solid var(--line);
    border-radius: 10px; background: rgba(135,169,92,.07); }
  .ft-intro { font-family: var(--serif); font-size: 1.08rem; margin-bottom: 16px; }
  .ft-sub { font-family: var(--mono); font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; color: var(--moss); margin: 16px 0 8px; }
  .ft-para { font-size: .92rem; }
  ul.ft-list { list-style: none; }
  ul.ft-list li { padding: 12px 0 12px 26px; position: relative; border-bottom: 1px solid var(--line); font-size: .9rem; }
  ul.ft-list li:last-child { border-bottom: none; }
  ul.ft-list li::before { content: "🌿"; position: absolute; left: 0; color: var(--moss); }
  ol.ft-steps { list-style: none; counter-reset: tarea; }
  ol.ft-steps li { counter-increment: tarea; position: relative; padding: 10px 0 10px 34px; border-bottom: 1px solid var(--line); font-size: .9rem; }
  ol.ft-steps li:last-child { border-bottom: none; }
  ol.ft-steps li::before { content: counter(tarea, decimal-leading-zero); position: absolute; left: 0; top: 12px; font-family: var(--mono); font-size: .72rem; color: var(--moss); }
  .ft-note { margin-top: 16px; padding: 12px 16px; border-left: 3px solid var(--amber); background: rgba(217,154,61,.08); font-size: .85rem; }

  .toolbar { position: fixed; top: 14px; right: 18px; z-index: 50; display: flex; gap: 8px; }
  .toolbar button { font-family: var(--sans); font-size: .82rem; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--line); background: var(--surface-2); color: var(--text); cursor: pointer; }
  .toolbar button:hover { border-color: var(--accent); color: var(--accent); }

  @media print {
    body { background: #fff; color: #111; padding: 0; }
    .sheet { box-shadow: none; border: none; max-width: none; background: #fff; }
    header.specimen, .ph-scale, section.block, .stamp { border-color: #ccc; }
    .tile { background: #f6f6f6; border-color: #ccc; }
    td, th { border-color: #ccc; }
    .toolbar { display: none; }
    .badge-exceso, .badge-deficit, .badge-noapta, .badge-apta, .badge-ok { background: none; }
    /* PDF: una matriz por parámetro, sin pestañas ni vista unificada */
    .heatmap .heat-tabs { display: none !important; }
    .heatmap .heat-var { display: block !important; }
    .heatmap .heat-var[data-var="__resumen__"] { display: none !important; }
  }
"""

_TOOLBAR = """
  <div class="toolbar">
    <button onclick="window.print()">🖨 Guardar PDF</button>
    <a id="dl-html" download="reporte.html"><button>⬇ Descargar HTML</button></a>
  </div>
"""


def _num(v, dec=2):
    if v is None:
        return "—"
    try:
        s = f"{float(v):.{dec}f}"
        return s.rstrip("0").rstrip(".") if "." in s else s
    except (TypeError, ValueError):
        return str(v)


def _badge(estado: str) -> str:
    e = (estado or "").upper()
    if e == "EXCESO":
        return '<span class="badge badge-exceso">EXCESO</span>'
    if e == "DEFICIT":
        return '<span class="badge badge-deficit">DÉFICIT</span>'
    return '<span class="badge badge-ok">OK</span>'


def _badge_clasificacion(clas: str) -> str:
    c = (clas or "").lower()
    if "no apta" in c or c == "noapta":
        return '<span class="badge badge-noapta">NO APTA</span>'
    if "apta" in c or c == "alta":
        return '<span class="badge badge-apta">APTA</span>'
    return '<span class="badge badge-deficit">' + esc(clas or "—").upper() + "</span>"


def _telemetria(lectura, dispositivo, finca) -> str:
    tiles = [
        ("Dispositivo", dispositivo.get("device_id") if dispositivo else (lectura.get("sensor_id") or "—"), ""),
        ("Finca", finca.get("nombre"), f"{finca.get('municipio') or ''}, {finca.get('departamento') or ''}".strip(", ")),
        ("Última transmisión", _fecha(lectura.get("ts")), ""),
        ("RSSI", _num(dispositivo.get("rssi") if dispositivo else None), "dBm"),
        ("Uptime", _num((dispositivo.get("uptime_s") or 0) / 60 if dispositivo else None, 0), "min"),
        ("Calidad NPK", "Calibrado" if dispositivo and dispositivo.get("npk_calibrado") else "Sin calibrar", ""),
        ("pH", _num(lectura.get("ph")), ""),
        ("Conductividad", _num(lectura.get("conductividad_electrica")), "dS/m"),
        ("N", _num(lectura.get("nitrogeno")), "ppm"),
        ("P", _num(lectura.get("fosforo")), "ppm"),
        ("K", _num(lectura.get("potasio")), "ppm"),
        ("HR ambiente", _num(lectura.get("humedad_ambiental")), "%"),
        ("T ambiente", _num(lectura.get("temperatura_ambiental")), "°C"),
    ]
    return '<div class="telemetry">' + "".join(
        f'<div class="tile"><div class="k">{esc(k)}</div><div class="v">{esc(v)} {f"<small>{esc(u)}</small>" if u else ""}</div></div>'
        for k, v, u in tiles
    ) + "</div>"


def _fecha(ts):
    if not ts:
        return "—"
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return str(ts)


def _ph_scale(ph) -> str:
    if ph is None:
        return ""
    pct = max(0.0, min(1.0, float(ph) / 14.0)) * 100
    neutro = "neutro" if 6.5 <= float(ph) <= 7.5 else ("ácido" if float(ph) < 6.5 else "alcalino")
    return f"""
  <div class="ph-scale">
    <div class="label">
      <span>Firma de acidez · escala pH</span>
      <span class="reading">pH <b>{_num(ph)}</b> — {neutro}</span>
    </div>
    <div class="ph-track"><div class="ph-marker" data-ph="pH {_num(ph)}" style="left:{pct:.1f}%"></div></div>
    <div class="ph-ticks"><span>0</span><span>3</span><span>5</span><span>7</span><span>9</span><span>11</span><span>14</span></div>
  </div>"""


def _seccion_uc2(a) -> str:
    if not a:
        return ""
    filas = "".join(
        f"""<tr><td class="mono">{esc(r.get("variable"))}</td>
        <td>{_badge(r.get("estado"))}</td>
        <td class="num">{_num(r.get("valor_actual"))}</td>
        <td class="mono">{esc(str(r.get("rango_ideal") or "—"))}</td>
        <td>{esc(r.get("accion") or "—")}</td>
        <td class="mono">{esc(r.get("prioridad") or "—")}</td></tr>"""
        for r in (a.get("recomendaciones") or [])
    )
    clas = a.get("clasificacion_upra")
    return f"""
  <section class="block">
    <div class="block-head"><span class="block-num">01</span>
      <div><div class="block-title">Diagnóstico para cultivo sembrado — {esc(a.get("cultivo") or "—")}</div>
      <div class="block-sub">Recomendación para el cultivo · motor de reglas</div></div>
    </div>
    <div style="margin-bottom:14px">{_badge_clasificacion(clas)} &nbsp; <span class="mono" style="color:var(--muted)">confianza {(a.get("confianza") or 0) * 100:.0f}%</span></div>
    <table>
      <tr><th>Variable</th><th>Estado</th><th>Lectura</th><th>Rango ideal</th><th>Acción</th><th>Prioridad</th></tr>
      {filas or '<tr><td colspan="6">Sin violaciones de reglas.</td></tr>'}
    </table>
    <div class="verdict"><b>Clasificación: {esc(clas or "—")}</b> — {esc((a.get("justificacion") or {}).get("resumen") or "")}</div>
  </section>"""


def _seccion_uc1(a) -> str:
    if not a:
        return ""
    sugerencias = a.get("sugerencias_cultivos") or []
    ranking = "".join(
        f"""<div class="rank">
          <div class="pos">{i + 1}</div>
          <div class="crop"><b>{esc(s.get("icono") or "")} {esc(s.get("cultivo"))}</b>
          <span>{_badge_clasificacion(s.get("clasificacion"))} · {esc(str(s.get("reglas_especificas") or ""))} reglas</span></div>
          <div class="scorebar"><i style="width:{min(100.0, float(s.get("score") or 0))}%"></i></div>
          <div class="score">{_num(s.get("score"), 1)} · {((s.get("confianza") or 0) * 100):.0f}%</div>
        </div>"""
        for i, s in enumerate(sugerencias)
    )
    return f"""
  <section class="block">
    <div class="block-head"><span class="block-num">02</span>
      <div><div class="block-title">Recomendación de siembra</div>
      <div class="block-sub">¿Qué conviene sembrar? · ranking del motor</div></div>
    </div>
    {ranking or '<p>Sin cultivos evaluables.</p>'}
    <div class="verdict"><b>Top:</b> {esc(a.get("cultivo") or "—")} ({esc(a.get("clasificacion_upra") or "—")})</div>
  </section>"""


# ── Mapa de calor del lote (muestreo en cuadrícula) ──

_VAR_HEAT = [
    ("ph", "pH", ""),
    ("nitrogeno", "N", "ppm"),
    ("fosforo", "P", "ppm"),
    ("potasio", "K", "ppm"),
    ("calcio", "Ca", "ppm"),
    ("magnesio", "Mg", "ppm"),
    ("azufre", "S", "ppm"),
    ("hierro", "Fe", "ppm"),
    ("manganeso", "Mn", "ppm"),
    ("zinc", "Zn", "ppm"),
    ("cobre", "Cu", "ppm"),
    ("boro", "B", "ppm"),
    ("materia_organica", "MO", "%"),
    ("cic", "CIC", "meq/100g"),
    ("humedad", "Humedad", "%"),
    ("temperatura_suelo", "T suelo", "°C"),
    ("conductividad_electrica", "CE", "dS/m"),
]

_VERDE = "#2e7d32"
_AMBAR = "#f9a825"
_ROJO = "#c62828"
_GRIS = "#eceff1"
# Rampa de intensidad por valor: más intenso = valor más alto (cada parámetro)
_VERDE_CLARO = "#e8f5e9"
_VERDE_INTENSO = "#1b5e20"


def _hex_a_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mezclar(c1: str, c2: str, t: float) -> str:
    a, b = _hex_a_rgb(c1), _hex_a_rgb(c2)
    t = max(0.0, min(1.0, t))
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _seccion_mapa_calor(muestras: list[dict] | None, umbrales: dict | None) -> str:
    """Mapa de calor del lote: un solo mapa con selector de parámetro.

    - «Resumen» (por defecto): todas las variables a la vez — cada punto se
      pinta según cuántas variables están fuera de su rango ideal.
    - Botones por parámetro: se observa cada variable de manera independiente.
    - «Ver todos»: despliega los mapas uno debajo del otro (útil para imprimir).
    """
    if not muestras or len(muestras) < 2:
        return ""
    xs = sorted({m["pos_x"] for m in muestras if m.get("pos_x") is not None})
    ys = sorted({m["pos_y"] for m in muestras if m.get("pos_y") is not None})
    if len(xs) < 2 and len(ys) < 2:
        return ""
    # Mapa (x, y) → muestra (la más reciente si hay varias en el mismo punto)
    celdas: dict[tuple[float, float], dict] = {}
    for m in muestras:
        clave = (m["pos_x"], m["pos_y"])
        if clave not in celdas:
            celdas[clave] = m

    variables = []
    for attr, simbolo, unidad in _VAR_HEAT:
        valores = [m[attr] for m in celdas.values() if m.get(attr) is not None]
        if len(valores) >= 2:
            variables.append((attr, simbolo, unidad))

    if not variables:
        return ""

    umbrales = umbrales or {}

    def _rango(simbolo):
        return umbrales.get(simbolo) or umbrales.get(simbolo.lower())

    def _celda(bg: str, texto: str) -> str:
        r, g, b = _hex_a_rgb(bg)
        fg = "#263238" if (r * 0.299 + g * 0.587 + b * 0.114) > 150 else "#ffffff"
        return f'<div class="heat-cell" style="background:{bg};color:{fg}">{esc(texto)}</div>'

    def _grid(celdas_fila: list[str]) -> str:
        return (
            f'<div class="heat-grid" style="grid-template-columns:repeat({len(xs)},1fr)">'
            + "".join(celdas_fila)
            + "</div>"
        )

    # ── Mapa resumen: todas las variables a la vez ──
    filas_resumen = []
    for y in reversed(ys):  # fila superior = y mayor
        fila = []
        for x in xs:
            m = celdas.get((x, y))
            if m is None:
                fila.append(_celda(_GRIS, "·"))
                continue
            fuera = dentro = 0
            for attr, simbolo, _unidad in variables:
                rango = _rango(simbolo)
                valor = m.get(attr)
                if rango is None or valor is None:
                    continue
                lo = rango[0] if rango[0] is not None else float("-inf")
                hi = rango[1] if rango[1] is not None else float("inf")
                if lo <= valor <= hi:
                    dentro += 1
                else:
                    fuera += 1
            total = fuera + dentro
            if total == 0:
                fila.append(_celda(_GRIS, "·"))
            else:
                prop = fuera / total
                bg = _mezclar(_VERDE, _ROJO, prop)
                fila.append(_celda(bg, f"{fuera}/{total}"))
        filas_resumen.append("".join(fila))

    leyenda_resumen = (
        f'<div class="heat-legend"><span class="chip" style="background:{_VERDE}"></span>todo en orden'
        f'<span class="chip" style="background:{_mezclar(_VERDE, _ROJO, 0.5)}"></span>algunas variables fuera'
        f'<span class="chip" style="background:{_ROJO}"></span>muchas variables fuera'
        '<span class="mono" style="color:var(--muted)">· cada celda muestra: variables fuera del ideal / variables con regla</span></div>'
    )
    bloque_resumen = (
        f'<div class="heat-var" data-var="__resumen__">'
        f'<div class="heat-title">🧭 Resumen del lote (todas las variables a la vez)</div>'
        f'{leyenda_resumen}{_grid(filas_resumen)}</div>'
    )

    # ── Mapas por parámetro (independientes) ──
    # Regla de color: intensidad = valor del parámetro. Cada parámetro se
    # normaliza con su propio mínimo y máximo del lote: la celda más clara
    # es el valor más bajo y la más intensa el valor más alto.
    bloques = []
    for attr, simbolo, unidad in variables:
        rango = _rango(simbolo)
        valores = [m[attr] for m in celdas.values() if m.get(attr) is not None]
        vmin, vmax = min(valores), max(valores)

        def _color(valor):
            if vmax == vmin:
                return _mezclar(_VERDE_CLARO, _VERDE_INTENSO, 0.5)
            t = (valor - vmin) / (vmax - vmin)
            return _mezclar(_VERDE_CLARO, _VERDE_INTENSO, t)

        filas = []
        for y in reversed(ys):
            fila = []
            for x in xs:
                m = celdas.get((x, y))
                valor = m.get(attr) if m else None
                if valor is None:
                    fila.append(_celda(_GRIS, "·"))
                else:
                    fila.append(_celda(_color(valor), _num(valor, 1)))
            filas.append("".join(fila))

        nota_ideal = ""
        if rango:
            lo = "—" if (rango[0] is None) else _num(rango[0], 1)
            hi = "—" if (rango[1] is None) else _num(rango[1], 1)
            nota_ideal = (
                f'<span class="mono" style="color:var(--muted)">· ideal {lo}–{hi} {esc(unidad)}</span>'
            )
        leyenda = (
            f'<div class="heat-legend"><span class="chip" style="background:{_VERDE_CLARO}"></span>'
            f'{_num(vmin, 1)} <span style="flex:1;height:8px;border-radius:4px;'
            f'background:linear-gradient(90deg,{_VERDE_CLARO},{_VERDE_INTENSO})"></span>'
            f'{_num(vmax, 1)} {esc(unidad)}{nota_ideal}</div>'
            f'<div class="heat-legend"><span class="mono" style="color:var(--muted)">'
            f'más intenso = valor más alto · menos intenso = valor más bajo</span></div>'
        )
        bloques.append(
            f'<div class="heat-var hidden" data-var="{esc(str(simbolo).lower())}">'
            f'<div class="heat-title">🌡️ {esc(simbolo)}'
            f'{" · " + esc(unidad) if unidad else ""}</div>{leyenda}{_grid(filas)}</div>'
        )

    pestañas = (
        '<div class="heat-tabs">'
        '<button type="button" class="heat-tab active" data-var="__resumen__">🧭 Resumen</button>'
        + "".join(
            f'<button type="button" class="heat-tab" data-var="{esc(str(simbolo).lower())}">{esc(simbolo)}</button>'
            for _attr, simbolo, _unidad in variables
        )
        + '<button type="button" class="heat-tab" data-var="__todos__">📋 Ver todos</button>'
        "</div>"
    )

    script = """
<script>
(function () {
  var tabs = document.querySelectorAll('.heatmap .heat-tab');
  var vars = document.querySelectorAll('.heatmap .heat-var');
  function verMapa(v) {
    tabs.forEach(function (b) { b.classList.toggle('active', b.dataset.var === v); });
    vars.forEach(function (el) {
      el.classList.toggle('hidden', v !== '__todos__' && el.dataset.var !== v);
    });
  }
  tabs.forEach(function (b) { b.addEventListener('click', function () { verMapa(b.dataset.var); }); });
})();
</script>"""

    return f"""
  <section class="block heatmap">
    <div class="block-head"><span class="block-num">M</span>
      <div><div class="block-title">Mapa de calor del lote</div>
      <div class="block-sub">Muestreo en cuadrícula · {len(xs)} × {len(ys)} tomas ({len(celdas)} puntos) · seleccione el parámetro a observar</div></div>
    </div>
    <p class="muted">Cada celda es una toma de muestra en la posición (x, y) del lote.
    La intensidad del color indica el valor del parámetro: más intenso = valor más alto,
    menos intenso = valor más bajo (cada parámetro usa su propia escala).
    Use los botones para ver un parámetro por separado o todos a la vez.</p>
    {pestañas}
    {bloque_resumen}
    {''.join(bloques)}
    {script}
  </section>"""


def _paso_nice(maxv: float) -> float:
    for p in (1, 2, 2.5, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if maxv / p <= 8:
            return float(p)
    return 1000.0


def _hull(puntos: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Cierre convexo (monotone chain)."""
    pts = sorted(set(puntos))
    if len(pts) <= 1:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _area_poligono(pts: list[tuple[float, float]]) -> float:
    n = len(pts)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _perimetro_poligono(pts: list[tuple[float, float]]) -> float:
    n = len(pts)
    if n < 2:
        return 0.0
    total = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        total += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return total


def _seccion_plano_lote(muestras: list[dict] | None, finca: dict | None, clima: dict | None = None) -> str:
    """Plano del lote: dibujo de los puntos de muestreo (pos_x, pos_y).

    - Los puntos (0, 0) se omiten (sensor sin posición real).
    - La silueta del lote es el cierre convexo de los puntos y de ella se
      estiman el perímetro y el área.
    - Incluye la fecha de la toma y, si la finca tiene coordenadas de
      Google, el clima del día de la muestra (IDEAM). Sin coordenadas,
      la sección de clima se omite.
    """
    if not muestras:
        return ""
    puntos = [
        (float(m["pos_x"]), float(m["pos_y"]))
        for m in muestras
        if m.get("pos_x") is not None
        and m.get("pos_y") is not None
        and not (float(m["pos_x"]) == 0 and float(m["pos_y"]) == 0)
    ]
    if len(puntos) < 2:
        return ""

    hull = _hull(puntos)
    perimetro = _perimetro_poligono(hull)
    area_m2 = _area_poligono(hull)

    def _fmt_area(v: float) -> str:
        return f"{v:,.0f}".replace(",", ".")

    def _fecha_legible(ts: str) -> str:
        try:
            from datetime import datetime

            return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).strftime("%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            return str(ts)[:10]

    # Fechas de la toma de muestras (para el plano y las estadísticas)
    fechas = sorted({str(m["ts"])[:10] for m in muestras if m.get("ts")})
    fecha_stat = ""
    if fechas:
        if len(fechas) == 1:
            fecha_stat = (
                f'<div class="plano-stat"><b>{fechas[0][8:10]}/{fechas[0][5:7]}/{fechas[0][:4]}</b>'
                'fecha de la toma de muestras</div>'
            )
        else:
            fecha_stat = (
                f'<div class="plano-stat"><b>{fechas[0][8:10]}/{fechas[0][5:7]}/{fechas[0][:4]} → '
                f'{fechas[-1][8:10]}/{fechas[-1][5:7]}/{fechas[-1][:4]}</b>rango de fechas de toma</div>'
            )

    stats = (
        '<div class="plano-stats">'
        f'<div class="plano-stat"><b>{_fmt_area(perimetro)} m</b>perímetro estimado</div>'
        f'<div class="plano-stat"><b>{_fmt_area(area_m2)} m²</b>área estimada ({_num(area_m2 / 10000, 3)} ha)</div>'
        f'<div class="plano-stat"><b>{len(puntos)}</b>puntos de muestreo</div>'
        f'{fecha_stat}'
    )
    area_reg = (finca or {}).get("area_hectareas")
    if area_reg:
        stats += (
            f'<div class="plano-stat"><b>{_num(area_reg, 2)} ha</b>'
            'área registrada de la finca (referencia)</div>'
        )
    stats += "</div>"

    # ── SVG del lote ──
    margen_x, margen_y_sup, margen_y_inf, margen_der = 46, 14, 40, 18
    W = 560
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    xmax, ymax = max(xs), max(ys)
    xmin, ymin = min(xs), min(ys)
    # Origen en el mínimo para centrar la silueta
    ox = xmin - max(2.0, (xmax - xmin) * 0.08)
    oy = ymin - max(2.0, (ymax - ymin) * 0.08)
    span_x = max(xmax - ox, 1.0)
    span_y = max(ymax - oy, 1.0)
    H_max = 360
    s = min((W - margen_x - margen_der) / span_x, (H_max - margen_y_sup - margen_y_inf) / span_y)
    H = s * span_y + margen_y_sup + margen_y_inf

    def X(v: float) -> float:
        return margen_x + (v - ox) * s

    def Y(v: float) -> float:
        return H - margen_y_inf - (v - oy) * s

    paso = _paso_nice(max(xmax - ox, ymax - oy))
    partes_svg = []
    # Rejilla y ejes
    t = ox
    while t <= xmax + paso * 0.5:
        xp = X(t)
        partes_svg.append(
            f'<line x1="{xp:.1f}" y1="{margen_y_sup}" x2="{xp:.1f}" y2="{H - margen_y_inf}" '
            'stroke="#dfe6d8" stroke-width="1" stroke-dasharray="3 4"/>'
        )
        partes_svg.append(
            f'<text x="{xp:.1f}" y="{H - margen_y_inf + 16}" font-size="9" fill="#6b7c66" '
            f'text-anchor="middle">{_num(t, 0)}</text>'
        )
        t += paso
    t = oy
    while t <= ymax + paso * 0.5:
        yp = Y(t)
        partes_svg.append(
            f'<line x1="{margen_x}" y1="{yp:.1f}" x2="{W - margen_der}" y2="{yp:.1f}" '
            'stroke="#dfe6d8" stroke-width="1" stroke-dasharray="3 4"/>'
        )
        partes_svg.append(
            f'<text x="{margen_x - 6}" y="{yp + 3:.1f}" font-size="9" fill="#6b7c66" '
            f'text-anchor="end">{_num(t, 0)}</text>'
        )
        t += paso
    partes_svg.append(
        f'<line x1="{margen_x}" y1="{H - margen_y_inf}" x2="{W - margen_der}" y2="{H - margen_y_inf}" '
        'stroke="#8aa07f" stroke-width="1.2"/>'
    )
    partes_svg.append(
        f'<line x1="{margen_x}" y1="{margen_y_sup}" x2="{margen_x}" y2="{H - margen_y_inf}" '
        'stroke="#8aa07f" stroke-width="1.2"/>'
    )
    partes_svg.append(
        f'<text x="{W / 2:.1f}" y="{H - 4}" font-size="9" fill="#8aa07f" text-anchor="middle">'
        'x (metros)</text>'
    )
    partes_svg.append(
        f'<text x="12" y="{H / 2:.1f}" font-size="9" fill="#8aa07f" '
        'transform="rotate(-90 12 ' + f"{H / 2:.1f}" + ')" text-anchor="middle">y (metros)</text>'
    )
    # Silueta (cierre convexo) si hay >= 3 puntos
    if len(hull) >= 3:
        pts_hull = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in hull)
        partes_svg.append(
            f'<polygon points="{pts_hull}" fill="rgba(135,169,92,.22)" '
            'stroke="#6f8f4f" stroke-width="2"/>'
        )
    # Puntos de muestreo (con la fecha de la toma en el tooltip)
    for i, (x, y) in enumerate(sorted(puntos), start=1):
        m = next((s for s in muestras if s.get("pos_x") == x and s.get("pos_y") == y), None)
        titulo = f'x={x:g} m, y={y:g} m' + (
            f' · toma {_fecha_legible(m["ts"])}' if m and m.get("ts") else ""
        )
        partes_svg.append(
            f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="4.2" fill="#2e5d34" '
            'stroke="#fff" stroke-width="1.4"><title>' + titulo + "</title></circle>"
        )
        partes_svg.append(
            f'<text x="{X(x) + 7:.1f}" y="{Y(y) - 6:.1f}" font-size="8.5" fill="#37474f">'
            f'{i}</text>'
        )
    svg = (
        f'<svg class="plano-svg" viewBox="0 0 {W} {H}" width="100%" '
        f'role="img" aria-label="Plano del lote con los puntos de muestreo">'
        + "".join(partes_svg)
        + "</svg>"
    )

    nota_cero = (
        '<p class="muted">Los puntos con posición (0, 0) se omiten: '
        'corresponden a tramas del sensor sin coordenada real del punto de toma.</p>'
    )

    # ── Clima del día de la muestra (solo si la finca tiene coordenadas) ──
    clima_html = ""
    if clima:
        clima_html = _bloque_clima_muestra(clima, fechas)

    return f"""
  <section class="block plano-lote">
    <div class="block-head"><span class="block-num">N</span>
      <div><div class="block-title">Plano del lote — puntos de muestreo</div>
      <div class="block-sub">Forma estimada del lote a partir de las coordenadas (x, y) de cada toma</div></div>
    </div>
    <p class="muted">Cada punto numerado es un sitio donde se tomó una muestra (pase el cursor para ver su fecha).
    La silueta verde es la forma del lote que encierran los puntos; de ella se estiman el perímetro y el área.</p>
    {stats}
    {svg}
    {clima_html}
    {nota_cero}
  </section>"""


def _bloque_clima_muestra(clima: dict, fechas: list[str]) -> str:
    """Bloque de clima del día de la muestra (IDEAM) + notas para recomendaciones."""
    tmin = clima.get("temperatura_min")
    tmax = clima.get("temperatura_max")
    tprom = clima.get("temperatura_promedio")
    precip = clima.get("precipitacion_estimada_mm", clima.get("precipitacion"))
    hum = clima.get("humedad_relativa", clima.get("humedad"))
    fuente = clima.get("fuente") or "IDEAM"
    fecha_txt = ""
    if fechas:
        fecha_txt = f'{fechas[-1][8:10]}/{fechas[-1][5:7]}/{fechas[-1][:4]}'

    def _tile(valor, unidad, etiqueta):
        if valor is None:
            return ""
        return f'<div class="plano-stat"><b>{_num(valor, 1)} {esc(unidad)}</b>{esc(etiqueta)}</div>'

    tiles = (
        '<div class="plano-stats">'
        + _tile(tmin, "°C", "temperatura mínima")
        + _tile(tmax, "°C", "temperatura máxima")
        + _tile(tprom, "°C", "temperatura promedio")
        + _tile(precip, "mm/mes", "precipitación estimada")
        + _tile(hum, "%", "humedad relativa")
        + "</div>"
    )

    notas = []
    try:
        p = float(precip) if precip is not None else 0.0
    except (TypeError, ValueError):
        p = 0.0
    try:
        h = float(hum) if hum is not None else 0.0
    except (TypeError, ValueError):
        h = 0.0
    try:
        t = float(tprom) if tprom is not None else 20.0
    except (TypeError, ValueError):
        t = 20.0
    if p >= 200:
        notas.append(
            "Mes de la toma con lluvias altas: el suelo pudo estar húmedo y los nutrientes "
            "móviles (N, K) pudieron lavarse; considere fraccionar la fertilización."
        )
    elif p <= 60:
        notas.append(
            "Mes de la toma seco: la lectura refleja el suelo sin agua reciente; "
            "interprete la conductividad y humedad con cautela."
        )
    if h >= 80:
        notas.append(
            "Humedad relativa alta: mayor riesgo de enfermedades fúngicas; "
            "vigile el cultivo y evite riegos excesivos."
        )
    if t < 10 or t > 32:
        notas.append(
            f"Temperatura promedio de {_num(t, 1)} °C fuera del rango confortable para la "
            "mayoría de cultivos de la zona; tenga en cuenta el estrés térmico."
        )
    if not notas:
        notas.append(
            "Condiciones climáticas del mes dentro de lo normal para la zona: "
            "las recomendaciones del reporte aplican sin ajustes por clima."
        )

    lista_notas = "".join(f"<li>{n}</li>" for n in notas)
    return f"""
    <div class="clima-muestra">
      <div class="heat-title">🌦️ Clima del día de la muestra{f' — {esc(fecha_txt)}' if fecha_txt else ''}</div>
      {tiles}
      <p class="muted">Fuente: {esc(fuente)}</p>
      <div class="heat-title">Cómo usar estos datos en las recomendaciones</div>
      <ul class="warnings">{lista_notas}</ul>
    </div>"""


def generar_reporte_html(
    *,
    finca: dict,
    lectura: dict,
    dispositivo: dict | None,
    tipo: str,
    uc1: dict | None,
    uc2: dict | None,
    muestras: list | None = None,
    umbrales: dict | None = None,
    clima: dict | None = None,
) -> str:
    """Construye el documento HTML completo del reporte."""
    fecha = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")
    titulo = {
        "siembra": "Recomendación de siembra",
        "cultivo": "Recomendación para el cultivo sembrado",
        "completo": "Reporte completo de análisis de suelo",
    }.get(tipo, "Reporte de análisis")

    secciones = ""
    if tipo in ("cultivo", "completo"):
        secciones += _seccion_uc2(uc2)
    if tipo in ("siembra", "completo"):
        secciones += _seccion_uc1(uc1)

    # Mapa de calor del lote (muestreo en cuadrícula con posiciones x, y)
    seccion_mapa = _seccion_mapa_calor(muestras, umbrales)

    # Plano del lote (puntos de muestreo + silueta + perímetro/área + clima)
    seccion_plano = _seccion_plano_lote(muestras, finca, clima)

    # Explicación en lenguaje campesino (siempre que haya análisis)
    explicacion_campo = generar_explicacion_campesina(uc1=uc1, uc2=uc2, lectura=lectura)

    advertencias = []
    for a in (uc2, uc1):
        if a and a.get("advertencia"):
            for w in a["advertencia"].split("."):
                w = w.strip().lstrip("⚠️").strip()
                if w:
                    advertencias.append(w)
    warnings_html = (
        '<ul class="warnings">' + "".join(f"<li>{esc(w)}</li>" for w in advertencias) + "</ul>"
    ) if advertencias else '<ul class="warnings"><li>Sin advertencias.</li></ul>'

    pasos = [
        "Validar la calibración NPK del sensor contra un análisis de laboratorio antes de aplicar fertilizantes.",
        "Corregir el pH con encalado dolomítico (suelo ácido) o yeso agrícola (suelo alcalino) según la recomendación.",
        "Aplicar el plan de fertilización fraccionado indicado en la tabla de diagnóstico.",
        "Replicar el análisis tras 3–4 semanas para verificar la evolución de las variables.",
        "Escalar al técnico agrónomo si la confianza del reporte es menor al 80%.",
    ]

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AgroIA · {esc(titulo)} — {esc(finca.get("nombre") or "")}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,600;9..144,900&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{_CSS}</style>
</head>
<body>
{_TOOLBAR}
<div class="sheet">
  <header class="specimen">
    <div>
      <div class="brand">Agro<em>IA</em></div>
      <div class="kicker">Informe de análisis de suelo · {esc(titulo)}</div>
    </div>
    <div class="specimen-label">
      Espécimen
      <strong>{esc(finca.get("nombre") or "—")}</strong>
      {esc(finca.get("municipio") or "")}, {esc(finca.get("departamento") or "")} · {esc(fecha)}
    </div>
  </header>
  {_ph_scale(lectura.get("ph"))}
  <section class="block">
    <div class="block-head"><span class="block-num">T</span>
      <div><div class="block-title">Telemetría y lectura del sensor</div>
      <div class="block-sub">Fuente de datos para el análisis</div></div>
    </div>
    {_telemetria(lectura, dispositivo, finca)}
  </section>
  {secciones}
  {seccion_mapa}
  {seccion_plano}
  {explicacion_campo}
  <section class="block">
    <div class="block-head"><span class="block-num">04</span>
      <div><div class="block-title">Advertencias del reporte</div>
      <div class="block-sub">Calidad de datos y limitaciones</div></div>
    </div>
    {warnings_html}
  </section>
  <section class="block">
    <div class="block-head"><span class="block-num">05</span>
      <div><div class="block-title">Próximos pasos</div>
      <div class="block-sub">Plan de acción sugerido</div></div>
    </div>
    <ol class="steps">{"".join(f"<li>{esc(p)}</li>" for p in pasos)}</ol>
  </section>
  <div class="stamp">AgroIA · sistema experto UPRA / Cenicafé / AGROSAVIA · generado {esc(fecha)}</div>
</div>
<footer class="colophon">AgroIA — AgroInteligente Colombia · Este reporte es una recomendación técnica de apoyo; no sustituye el análisis de laboratorio certificado.</footer>
<script>
  const htmlSrc = document.documentElement.outerHTML;
  document.getElementById('dl-html').href = 'data:text/html;charset=utf-8,' + encodeURIComponent(htmlSrc);
</script>
</body>
</html>"""
    return html
