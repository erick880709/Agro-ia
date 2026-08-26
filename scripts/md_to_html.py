"""Convierte documentación Markdown a HTML con el estilo AgroIA.

Uso: python scripts/md_to_html.py <entrada.md> <salida.html>
"""

import sys

import markdown

CSS = """
:root { --moss:#1e5c2e; --moss-soft:#eef6ef; --line:#e3e9e4; --muted:#5a725e;
  --amber:#f9a825; --text:#1d3322; }
* { box-sizing: border-box; }
body { margin:0; font-family:'IBM Plex Sans',system-ui,Segoe UI,sans-serif;
  color:var(--text); background:#f6f9f6; line-height:1.6; }
.sheet { max-width:860px; margin:0 auto; padding:48px 40px 72px; background:#fff; }
header.specimen { display:flex; justify-content:space-between; align-items:flex-end;
  border-bottom:1px solid var(--line); padding-bottom:18px; margin-bottom:28px; }
.brand { font-family:Fraunces,Georgia,serif; font-size:1.6rem; font-weight:600; }
.brand em { color:var(--moss); font-style:normal; }
.kicker { font-family:Consolas,monospace; font-size:.7rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--muted); }
h1 { font-family:Fraunces,Georgia,serif; font-size:1.9rem; line-height:1.2; }
h2 { font-family:Fraunces,Georgia,serif; font-size:1.3rem; margin-top:2.2em;
  border-bottom:1px solid var(--line); padding-bottom:6px; color:var(--moss); }
h3 { font-size:1.05rem; margin-top:1.6em; }
p, li { font-size:.95rem; }
code { font-family:Consolas,monospace; font-size:.85em; background:var(--moss-soft);
  padding:2px 6px; border-radius:4px; }
pre { background:#102318; color:#e8f5e9; padding:16px 18px; border-radius:8px;
  overflow-x:auto; font-size:.85rem; }
pre code { background:none; color:inherit; padding:0; }
table { border-collapse:collapse; width:100%; margin:16px 0; font-size:.88rem; }
th { background:var(--moss); color:#fff; text-align:left; padding:8px 10px; }
td { border:1px solid var(--line); padding:8px 10px; vertical-align:top; }
tr:nth-child(even) td { background:#fbfdfb; }
blockquote { margin:16px 0; padding:10px 16px; border-left:4px solid var(--moss);
  background:var(--moss-soft); border-radius:0 8px 8px 0; }
blockquote p { margin:.3em 0; }
hr { border:none; border-top:1px solid var(--line); margin:2em 0; }
a { color:var(--moss); }
footer { text-align:center; color:var(--muted); font-size:.8rem; padding:24px; }
@media print { body { background:#fff; } .sheet { max-width:none; padding:0; } }
"""


def main() -> None:
    if len(sys.argv) != 3:
        print("Uso: python scripts/md_to_html.py <entrada.md> <salida.html>")
        sys.exit(1)
    entrada, salida = sys.argv[1], sys.argv[2]
    with open(entrada, encoding="utf-8") as f:
        texto = f.read()
    cuerpo = markdown.markdown(
        texto, extensions=["extra", "toc", "sane_lists", "fenced_code"]
    )
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AgroIA · Documentación del Servicio de Ingesta de Sensores</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,600;9..144,900&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="sheet">
  <header class="specimen">
    <div>
      <div class="brand">Agro<em>IA</em></div>
      <div class="kicker">Documentación técnica · servicio de ingesta de sensores</div>
    </div>
    <div class="kicker">AgroInteligente Colombia · v0.1.0</div>
  </header>
  {cuerpo}
</div>
<footer>AgroIA — AgroInteligente Colombia · Documentación generada desde
  <code>resources/architecture/api_sensor_muestreo.md</code></footer>
</body>
</html>"""
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: {salida}")


if __name__ == "__main__":
    main()
