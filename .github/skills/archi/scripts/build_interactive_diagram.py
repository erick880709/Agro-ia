#!/usr/bin/env python3
"""Construye y valida el diagrama interactivo de archi (guia-diagramas-interactivos.md).

Lee una especificación JSON (`15.1.1-Flujos-Interactivos_<Proyecto>.json`), la valida y la
inserta en `assets/plantilla-diagrama-interactivo.html` para producir un HTML autocontenido
(`15.1-Flujos-Interactivos_<Proyecto>.html`). Con --markdown genera además la tabla de pasos
para el artefacto dueño (`15`). Con --owner cruza que cada ID de nodo exista en los
artefactos dueños.

Uso:
    python build_interactive_diagram.py spec.json -o salida.html [--markdown pasos.md] [--owner 14-Vistas-C4.md ...] [--strict]
    python build_interactive_diagram.py spec.json --check [--owner ...]
    python build_interactive_diagram.py --self-test
Sale con 1 si hay errores (o advertencias con --strict); 2 si no puede leer.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROLES = {"canal", "borde", "servicio", "foco", "mensajeria", "datos", "externo", "seguridad", "observabilidad"}
KINDS = {"sync", "async", "return", "self"}
STATUSES = {"nuevo", "retirado", "modificado"}
ZONE_KINDS = {"trust", "system", "network", "env", "domain"}
MAX_NODES, MAX_FOCUS, MIN_STEPS, MAX_STEPS, MAX_FLOWS, MAX_LABEL = 14, 2, 3, 9, 6, 40
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "plantilla-diagrama-interactivo.html"
PLACEHOLDER = "/*__ARCH_SPEC__*/null"
ID_RX = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,40}$")


def validate(spec: dict, owner_text: str | None = None) -> tuple[list[str], list[str]]:
    e: list[str] = []
    w: list[str] = []
    if not spec.get("title"):
        e.append("title es obligatorio (pregunta que responde el diagrama)")
    if not spec.get("description"):
        w.append("description vacía: se usa como <desc> accesible")
    nodes = spec.get("nodes") or []
    if not nodes:
        return e + ["nodes vacío"], w
    ids = [n.get("id") for n in nodes]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        e.append(f"nodo duplicado {d}")
    modes = spec.get("modes") or []
    if spec.get("defaultMode") and spec["defaultMode"] not in modes:
        e.append(f"defaultMode {spec['defaultMode']} no está en modes")
    positions = {}
    for n in nodes:
        nid = n.get("id", "?")
        if not ID_RX.match(str(nid)):
            e.append(f"id de nodo inválido: {nid}")
        if not n.get("label"):
            e.append(f"{nid}: label obligatorio")
        if n.get("role", "servicio") not in ROLES:
            e.append(f"{nid}: role '{n.get('role')}' no es uno de {sorted(ROLES)}")
        for m, v in (n.get("status") or {}).items():
            if m not in modes:
                e.append(f"{nid}: status para modo inexistente '{m}'")
            if v not in STATUSES:
                e.append(f"{nid}: status '{v}' no es uno de {sorted(STATUSES)}")
        for m in (n.get("modes") or {}):
            if m not in modes:
                e.append(f"{nid}: overrides para modo inexistente '{m}'")
        if n.get("col") is not None and n.get("row") is not None:
            key = (n["col"], n["row"])
            if key in positions:
                e.append(f"{nid} y {positions[key]} comparten col/row {key}")
            positions[key] = nid
        if not n.get("detail"):
            w.append(f"{nid}: sin 'detail' (responsabilidad en una frase)")
    if len(nodes) > MAX_NODES:
        w.append(f"{len(nodes)} nodos (presupuesto {MAX_NODES}): divide en vista general + detalle")
    if sum(1 for n in nodes if n.get("role") == "foco") > MAX_FOCUS:
        e.append(f"más de {MAX_FOCUS} nodos en foco")
    known = set(ids)
    for z in spec.get("zones") or []:
        if z.get("kind", "system") not in ZONE_KINDS:
            e.append(f"zona {z.get('id')}: kind inválido")
        for nid in z.get("nodes") or []:
            if nid not in known:
                e.append(f"zona {z.get('id')}: nodo {nid} inexistente")
    flows = spec.get("flows") or []
    if not flows:
        e.append("flows vacío: un diagrama interactivo existe para recorrer flujos")
    if len(flows) > MAX_FLOWS:
        w.append(f"{len(flows)} flujos (recomendado ≤ {MAX_FLOWS})")
    fids = [f.get("id") for f in flows]
    for d in sorted({i for i in fids if fids.count(i) > 1}):
        e.append(f"flujo duplicado {d}")
    used = set()
    for f in flows:
        fid = f.get("id", "?")
        if not f.get("title"):
            e.append(f"flujo {fid}: title obligatorio")
        if f.get("onlyMode") and f["onlyMode"] not in modes:
            e.append(f"flujo {fid}: onlyMode '{f['onlyMode']}' no es un modo")
        steps = f.get("steps") or []
        if not (MIN_STEPS <= len(steps) <= MAX_STEPS):
            w.append(f"flujo {fid}: {len(steps)} pasos (recomendado {MIN_STEPS}–{MAX_STEPS})")
        if not f.get("source"):
            w.append(f"flujo {fid}: sin 'source' (sección de 15/14.00 que lo respalda)")
        has_error = False
        for i, s in enumerate(steps, 1):
            for p in ("from", "to"):
                if s.get(p) not in known:
                    e.append(f"flujo {fid} paso {i}: {p} '{s.get(p)}' no es un nodo")
                used.add(s.get(p))
            if s.get("kind", "sync") not in KINDS:
                e.append(f"flujo {fid} paso {i}: kind '{s.get('kind')}' inválido")
            if s.get("kind") == "self" and s.get("from") != s.get("to"):
                e.append(f"flujo {fid} paso {i}: kind self requiere from == to")
            if not (s.get("title") or s.get("label")):
                e.append(f"flujo {fid} paso {i}: requiere title o label")
            if len(str(s.get("label", ""))) > MAX_LABEL:
                w.append(f"flujo {fid} paso {i}: label > {MAX_LABEL} caracteres")
            if not s.get("desc"):
                w.append(f"flujo {fid} paso {i}: sin 'desc' (qué y por qué)")
            if "${" in str(s.get("payload", "")) or "</script" in str(s.get("payload", "")).lower():
                w.append(f"flujo {fid} paso {i}: el payload contiene '${{' o '</script' (se escapará)")
            has_error = has_error or bool(s.get("error"))
        if f.get("critical") and not has_error:
            w.append(f"flujo {fid}: marcado critical sin ningún paso de ruta de error")
    for nid in sorted(known - used):
        w.append(f"nodo {nid} no participa en ningún flujo (¿sobra o falta un flujo?)")
    if owner_text is not None:
        for nid in sorted(known):
            if re.match(r"^(CT|EXT|TB|DATA)-", nid) and nid not in owner_text:
                e.append(f"{nid} no aparece en los artefactos dueños")
    return e, w


def build(spec: dict) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in tpl:
        raise ValueError("la plantilla no contiene el marcador de especificación")
    data = json.dumps(spec, ensure_ascii=False, indent=1)
    data = data.replace("</", "<\\/").replace("<!--", "<\\!--").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    out = tpl.replace(PLACEHOLDER, data, 1)
    lang = spec.get("lang", "es")
    out = out.replace('<html lang="es">', f'<html lang="{lang}">', 1)
    title = spec.get("title", "Diagrama interactivo").replace("&", "&amp;").replace("<", "&lt;")
    return out.replace("<title>Diagrama interactivo</title>", f"<title>{title}</title>", 1)


def markdown(spec: dict) -> str:
    lines = [f"### {spec.get('title', '')}", ""]
    if spec.get("modes"):
        lines += [f"Modos: {', '.join(spec['modes'])}.", ""]
    for f in spec.get("flows") or []:
        lines += [f"#### {f.get('title')}" + (f" (solo {f['onlyMode']})" if f.get("onlyMode") else ""), ""]
        if f.get("source"):
            lines += [f"Fuente: {f['source']}", ""]
        lines += ["| # | De → A | Tipo | Mensaje | Qué y por qué | Referencias |", "|---|---|---|---|---|---|"]
        for i, s in enumerate(f.get("steps") or [], 1):
            refs = ", ".join((s.get("chips") or []) + (s.get("refs") or []))
            desc = str(s.get("desc", "")).replace("|", "\\|")
            lines.append(f"| {i} | {s.get('from')} → {s.get('to')} | {s.get('kind', 'sync')}{' · error' if s.get('error') else ''} | "
                         f"{str(s.get('label', s.get('title', ''))).replace('|', chr(92) + '|')} | {desc} | {refs} |")
        lines.append("")
    return "\n".join(lines)


SAMPLE = {
    "title": "¿Cómo se aprueba un pago con tarjeta?", "subtitle": "Flujo crítico de 15 · audiencia mixta",
    "description": "Recorrido del pago desde el canal hasta la pasarela, con modos AS-IS y TO-BE.",
    "modes": ["AS-IS", "TO-BE"], "defaultMode": "TO-BE",
    "zones": [{"id": "TB-01", "label": "Zona privada", "kind": "trust", "nodes": ["CT-01", "DATA-001"]}],
    "nodes": [
        {"id": "CANAL", "label": "App móvil", "role": "canal", "detail": "Cliente que inicia el pago"},
        {"id": "CT-01", "label": "API de Pagos", "role": "foco", "tech": "Java 21 · WebFlux", "detail": "Orquesta el pago",
         "status": {"TO-BE": "nuevo"}},
        {"id": "DATA-001", "label": "Pagos", "role": "datos", "tech": "Aurora PostgreSQL", "detail": "Fuente de verdad"},
        {"id": "EXT-01", "label": "Pasarela", "role": "externo", "detail": "Autoriza la transacción"}],
    "flows": [{"id": "pago", "title": "Pago (POST /v1/pagos)", "source": "15 §2", "critical": True, "steps": [
        {"from": "CANAL", "to": "CT-01", "label": "HTTPS · POST /v1/pagos", "desc": "Solicitud con idempotency-key",
         "payload": "{\"monto\": 1200.50}", "chips": ["SEC-004"]},
        {"from": "CT-01", "to": "EXT-01", "label": "mTLS · autoriza", "desc": "Autorización con la pasarela"},
        {"from": "EXT-01", "to": "CT-01", "kind": "return", "label": "402 rechazado", "desc": "Rechazo de la pasarela", "error": True},
        {"from": "CT-01", "to": "DATA-001", "label": "SQL/TLS · registra", "desc": "Persiste el resultado"}]}]}


def self_test() -> int:
    e, w = validate(SAMPLE, owner_text="CT-01 DATA-001 EXT-01")
    assert not e, e
    html = build(SAMPLE)
    assert PLACEHOLDER not in html and "API de Pagos" in html and "<title>¿Cómo se aprueba" in html
    bad = json.loads(json.dumps(SAMPLE))
    bad["flows"][0]["steps"][0]["to"] = "CT-99"
    bad["nodes"][0]["role"] = "raro"
    e, _ = validate(bad, owner_text="")
    joined = "\n".join(e)
    assert "CT-99" in joined and "role" in joined and "no aparece en los artefactos dueños" in joined, e
    inj = json.loads(json.dumps(SAMPLE))
    inj["flows"][0]["steps"][0]["payload"] = "</script><script>alert(1)</script>"
    assert "</script><script>alert" not in build(inj)
    assert "| 1 | CANAL → CT-01 |" in markdown(SAMPLE)
    print("SELF-TEST OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", nargs="?", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--markdown", type=Path)
    ap.add_argument("--owner", type=Path, nargs="*")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.spec:
        ap.error("falta la especificación JSON")
    try:
        spec = json.loads(a.spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: no se pudo leer {a.spec}: {exc}")
        return 2
    owner = "\n".join(p.read_text(encoding="utf-8") for p in a.owner) if a.owner else None
    errs, warns = validate(spec, owner)
    for x in warns:
        print(f"WARN: {x}")
    for x in errs:
        print(f"ERROR: {x}")
    if errs or (a.strict and warns):
        print(f"FAIL: {len(errs)} error(es), {len(warns)} advertencia(s)")
        return 1
    if a.check:
        print("OK")
        return 0
    out = a.output or a.spec.with_suffix(".html")
    out.write_text(build(spec), encoding="utf-8")
    if a.markdown:
        a.markdown.write_text(markdown(spec), encoding="utf-8")
    print(f"OK: {out}" + (f" y {a.markdown}" if a.markdown else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
