"""Regenera resources/architecture/Documento_Funcional_Tecnico_AgroIA.html desde el .md canónico.

Uso:  python scripts/sync_doc_funcional_html.py
El .md es la fuente de verdad; el HTML es un artefacto derivado para lectura en navegador.
"""
from __future__ import annotations

import datetime
import pathlib

import markdown

ROOT = pathlib.Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "resources" / "architecture" / "Documento_Funcional_Tecnico_AgroIA.md"
HTML_PATH = ROOT / "resources" / "architecture" / "Documento_Funcional_Tecnico_AgroIA.html"

CSS = """
:root { --bg:#f6f8f4; --surface:#ffffff; --surface2:#eef4ec; --line:#dfe8dc;
  --ink:#1f2a21; --muted:#6b7c66; --moss:#2e7d32; --moss-dark:#1b5e20;
  --amber:#b45309; --mono:'Consolas','Courier New',monospace; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
  font:15px/1.65 'Segoe UI',system-ui,-apple-system,sans-serif; }
header.portada { background:linear-gradient(135deg,#17381f 0%,#2e7d32 60%,#66a85b 100%);
  color:#fff; padding:48px 28px 38px; }
header.portada .brand { font-size:2rem; font-weight:700; }
header.portada .kicker { letter-spacing:.18em; text-transform:uppercase; font-size:.78rem; opacity:.85; }
header.portada h1 { margin:12px 0 4px; font-size:1.8rem; }
header.portada .meta { opacity:.85; font-size:.9rem; }
.wrap { max-width:1020px; margin:0 auto; padding:26px 18px 80px; }
nav.toc { background:var(--surface); border:1px solid var(--line); border-radius:12px;
  padding:14px 20px; margin-bottom:24px; columns:2; column-gap:28px; font-size:.86rem; }
nav.toc a { color:var(--moss-dark); text-decoration:none; display:block; padding:2px 0; }
nav.toc a:hover { text-decoration:underline; }
h1,h2,h3,h4 { color:var(--moss-dark); }
h2 { border-bottom:3px solid var(--moss); padding-bottom:6px; margin:40px 0 14px; font-size:1.45rem; }
h3 { font-size:1.1rem; margin:22px 0 8px; color:#24512b; }
h4 { margin:16px 0 6px; }
p { margin:8px 0; }
ul,ol { margin:8px 0; padding-left:24px; }
li { margin:4px 0; }
code { background:var(--surface2); border:1px solid var(--line); border-radius:5px;
  padding:1px 6px; font-family:var(--mono); font-size:.86em; color:#24492c; }
pre { background:#102015; color:#cfe3d2; border-radius:10px; padding:14px 16px;
  overflow-x:auto; font-size:.85rem; line-height:1.5; }
pre code { background:none; border:none; color:inherit; padding:0; font-size:.9em; }
blockquote { border-left:4px solid var(--moss); background:var(--surface2);
  margin:12px 0; padding:8px 16px; border-radius:0 8px 8px 0; color:#33503a; }
table { width:100%; border-collapse:collapse; margin:12px 0; background:var(--surface);
  border:1px solid var(--line); border-radius:10px; overflow:hidden; font-size:.87rem; }
th { background:#244d2c; color:#fff; text-align:left; padding:8px 12px;
  font-size:.78rem; text-transform:uppercase; letter-spacing:.04em; }
td { padding:8px 12px; border-top:1px solid var(--line); vertical-align:top; }
tr:nth-child(even) td { background:#f8fbf6; }
hr { border:none; border-top:1px solid var(--line); margin:26px 0; }
.mermaid { background:var(--surface); border:1px solid var(--line); border-radius:12px;
  padding:16px; margin:14px 0; text-align:center; }
footer { background:#17381f; color:#cfe3d2; text-align:center; padding:20px; font-size:.85rem; }
@media (max-width:760px) { nav.toc { columns:1; } }
@media print { header.portada { background:#17381f !important; -webkit-print-color-adjust:exact; } }
"""


def main() -> None:
    text = MD_PATH.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "toc", "sane_lists"],
    )
    # Los bloques mermaid quedan como <pre>; se marcan para render con mermaid.js.
    body = body.replace('<pre><code class="language-mermaid">',
                        '<div class="mermaid">').replace("</code></pre>", "</div>")
    hoy = datetime.date.today().isoformat()
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Documento Funcional-Técnico — AgroIA</title>
<style>{CSS}</style>
</head>
<body>
<header class="portada">
  <div class="brand">Agro<em>IA</em></div>
  <div class="kicker">AgroInteligente Colombia · Documento funcional-técnico</div>
  <h1>Documento Funcional-Técnico — AgroIA</h1>
  <div class="meta">Generado automáticamente desde
    <code>resources/architecture/Documento_Funcional_Tecnico_AgroIA.md</code> (fuente de verdad) ·
    {hoy} · Repositorio erick880709/Agro-ia (rama master)</div>
</header>
<div class="wrap">
{body}
</div>
<footer>AgroIA — AgroInteligente Colombia · Documento funcional-técnico ·
  no editar este HTML directamente: editar el .md y regenerar con
  <code>python scripts/sync_doc_funcional_html.py</code></footer>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true, theme:"neutral"}});</script>
</body>
</html>
"""
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"OK -> {HTML_PATH}")


if __name__ == "__main__":
    main()
