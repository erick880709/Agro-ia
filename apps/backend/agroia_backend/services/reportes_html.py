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
  .heatmap .heat-title { font-weight: 600; margin-bottom: 6px; }
  .heat-legend { display: flex; align-items: center; gap: 8px; font-size: .78rem; color: var(--muted); margin-bottom: 8px; }
  .heat-legend .chip { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  .heat-grid { display: grid; gap: 2px; max-width: 560px; margin-bottom: 4px; }
  .heat-cell { aspect-ratio: 1.6 / 1; display: flex; align-items: center; justify-content: center;
    font-family: var(--mono); font-size: .68rem; border-radius: 3px; }
  .heat-cell:hover { outline: 2px solid var(--moss); }
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


def _hex_a_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mezclar(c1: str, c2: str, t: float) -> str:
    a, b = _hex_a_rgb(c1), _hex_a_rgb(c2)
    t = max(0.0, min(1.0, t))
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _color_por_estado(valor: float, minimo: float | None, maximo: float | None) -> str:
    """Verde dentro del ideal, ámbar cerca, rojo fuera. Sin rango: gradiente."""
    if minimo is None and maximo is None:
        return ""
    lo = minimo if minimo is not None else float("-inf")
    hi = maximo if maximo is not None else float("inf")
    if lo <= valor <= hi:
        return _VERDE
    margen = (hi - lo) * 0.25 if minimo is not None and maximo is not None else 0
    if (minimo is not None and lo - margen <= valor < lo) or (
        maximo is not None and hi < valor <= hi + margen
    ):
        return _AMBAR
    return _ROJO


def _seccion_mapa_calor(muestras: list[dict] | None, umbrales: dict | None) -> str:
    """Mapa de calor del lote: una cuadrícula por variable con sus muestras (x, y)."""
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
    bloques = []
    for attr, simbolo, unidad in variables:
        rango = umbrales.get(simbolo) or umbrales.get(simbolo.lower())
        valores = [m[attr] for m in celdas.values() if m.get(attr) is not None]
        vmin, vmax = min(valores), max(valores)

        def _color(valor):
            if rango:
                return _color_por_estado(valor, rango[0], rango[1])
            if vmax == vmin:
                return _mezclar("#64b5f6", "#e53935", 0.5)
            return _mezclar("#64b5f6", "#e53935", (valor - vmin) / (vmax - vmin))

        filas = []
        for y in reversed(ys):  # fila superior = y mayor
            celdas_fila = []
            for x in xs:
                m = celdas.get((x, y))
                valor = m.get(attr) if m else None
                if valor is None:
                    bg, fg, texto = _GRIS, "#90a4ae", "·"
                else:
                    bg = _color(valor)
                    texto = _num(valor, 1)
                    # texto oscuro sobre fondos claros (ámbar/gradiente azul), blanco sobre oscuros
                    r, g, b = _hex_a_rgb(bg)
                    fg = "#263238" if (r * 0.299 + g * 0.587 + b * 0.114) > 150 else "#ffffff"
                celdas_fila.append(
                    f'<div class="heat-cell" style="background:{bg};color:{fg}">{esc(texto)}</div>'
                )
            filas.append("".join(celdas_fila))

        if rango:
            lo = "—" if (rango[0] is None) else _num(rango[0], 1)
            hi = "—" if (rango[1] is None) else _num(rango[1], 1)
            leyenda = (
                f'<div class="heat-legend"><span class="chip" style="background:{_VERDE}"></span>dentro del ideal'
                f'<span class="chip" style="background:{_AMBAR}"></span>cerca'
                f'<span class="chip" style="background:{_ROJO}"></span>fuera'
                f'<span class="mono" style="color:var(--muted)">· ideal {lo}–{hi} {esc(unidad)}</span></div>'
            )
        else:
            leyenda = (
                f'<div class="heat-legend"><span class="chip" style="background:#64b5f6"></span>'
                f'{_num(vmin, 1)} <span style="flex:1;height:8px;border-radius:4px;'
                f'background:linear-gradient(90deg,#64b5f6,#f9a825,#e53935)"></span>'
                f'{_num(vmax, 1)} {esc(unidad)}</div>'
            )
        grid = (
            f'<div class="heat-grid" style="grid-template-columns:repeat({len(xs)},1fr)">'
            + "".join(filas)
            + "</div>"
        )
        bloques.append(
            f'<div class="heat-var"><div class="heat-title">🌡️ {esc(simbolo)}'
            f'{" · " + esc(unidad) if unidad else ""}</div>{leyenda}{grid}</div>'
        )

    return f"""
  <section class="block heatmap">
    <div class="block-head"><span class="block-num">M</span>
      <div><div class="block-title">Mapa de calor del lote</div>
      <div class="block-sub">Muestreo en cuadrícula · {len(xs)} × {len(ys)} tomas ({len(celdas)} puntos)</div></div>
    </div>
    <p class="muted">Cada celda es una toma de muestra en la posición (x, y) del lote;
    los colores muestran la variación de cada parámetro del suelo entre puntos.</p>
    {''.join(bloques)}
  </section>"""


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
