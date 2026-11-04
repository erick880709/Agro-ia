# -*- coding: utf-8 -*-
"""Entrypoint de la Fase 2 de la skill `procesos`: genera el Word/Excel/BPMN oficial de un
PROC-###/DOC-###/ACTA-###.md.

Uso:
    python exportar_oficial.py <ruta-al-.md>

Qué genera, según el tipo de documento (front-matter `tipo_documento`, o el prefijo del `id` si no
está presente):
- PROC-###           -> <slug>.xlsx (caracterización) + <slug>.docx (procedimiento) + <slug>.bpmn
- DOC-### Manual tecnico       -> <slug>.docx (+ <slug>.bpmn si el DOC trae un bloque ```mermaid```)
- DOC-### Politica             -> <slug>.docx
- DOC-### Documento de apoyo   -> <slug>.docx
- ACTA-###                     -> <slug>.docx

Todos los archivos se escriben junto al `.md` de origen. Si el documento no está en estado
"Validado por el dueño", el archivo generado lleva una marca de BORRADOR visible — no bloquea la
generación (ver SKILL.md, sección "Generar el documento oficial").

La sincronización de los listados maestros de documentos (Paso 7b) NO se dispara automáticamente
aquí: requiere que `00-listado-maestro-documentos-internos.md` ya tenga la fila de este documento
(trabajo editorial de la skill, no de este script) — una vez esté, se corre
`export_listado_maestro.py internos` aparte.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from export_acta import export_acta  # noqa: E402
from export_caracterizacion import export_caracterizacion  # noqa: E402
from export_documento_apoyo import export_documento_apoyo  # noqa: E402
from export_manual_tecnico import export_manual_tecnico  # noqa: E402
from export_politica import export_politica  # noqa: E402
from export_procedimiento import export_procedimiento  # noqa: E402
from bpmn_writer import build_bpmn  # noqa: E402
from mermaid_to_graph import parse_mermaid  # noqa: E402
from md_parser import get_section, parse_md_file  # noqa: E402


def _detectar_tipo(parsed, md_path):
    fm = parsed["front_matter"]
    doc_id = str(fm.get("id", os.path.basename(md_path)))
    if doc_id.startswith("PROC-"):
        return "proceso"
    if doc_id.startswith("ACTA-"):
        return "acta"
    tipo = str(fm.get("tipo_documento", "")).strip().lower()
    if "manual" in tipo:
        return "manual_tecnico"
    if "politica" in tipo or "política" in tipo:
        return "politica"
    if "apoyo" in tipo:
        return "documento_apoyo"
    return None


def _generar_bpmn(parsed, md_path, mermaid_section_titles, resultados, warnings):
    fm = parsed["front_matter"]
    section = get_section(parsed, *mermaid_section_titles)
    if not section or not section.get("mermaid"):
        return
    # Mismo nombre base que el .md de origen (no el `slug` del front-matter) — así el .bpmn queda
    # consistente con el .xlsx/.docx hermanos, que también se nombran a partir del .md de origen.
    slug = os.path.splitext(os.path.basename(md_path))[0]
    graph = parse_mermaid(section["mermaid"][0])
    warnings.extend(f"[mermaid] {w}" for w in graph.get("warnings", []))
    nombre = parsed.get("titulo_documento", slug)
    xml_out = build_bpmn(graph, fm.get("id", slug), nombre)
    bpmn_path = os.path.join(os.path.dirname(md_path), f"{slug}.bpmn")
    with open(bpmn_path, "w", encoding="utf-8") as f:
        f.write(xml_out)
    resultados.append(bpmn_path)


def exportar_oficial(md_path):
    parsed = parse_md_file(md_path)
    tipo = _detectar_tipo(parsed, md_path)
    if tipo is None:
        raise ValueError(
            f"No se pudo determinar el tipo de documento de {md_path} "
            "(front-matter 'tipo_documento' ausente/no reconocido y el id no empieza por PROC-/ACTA-)."
        )

    resultados = []
    warnings = []

    if tipo == "proceso":
        r1 = export_caracterizacion(md_path)
        r2 = export_procedimiento(md_path)
        resultados += [r1["output"], r2["output"]]
        warnings += r1["warnings"] + r2["warnings"]
        _generar_bpmn(
            parsed, md_path,
            ["Diagrama de flujo borrador Mermaid", "Diagrama"],
            resultados, warnings,
        )
    elif tipo == "manual_tecnico":
        r = export_manual_tecnico(md_path)
        resultados.append(r["output"])
        warnings += r["warnings"]
        _generar_bpmn(parsed, md_path, ["Diagrama"], resultados, warnings)
    elif tipo == "politica":
        r = export_politica(md_path)
        resultados.append(r["output"])
        warnings += r["warnings"]
    elif tipo == "documento_apoyo":
        r = export_documento_apoyo(md_path)
        resultados.append(r["output"])
        warnings += r["warnings"]
    elif tipo == "acta":
        r = export_acta(md_path)
        resultados.append(r["output"])
        warnings += r["warnings"]

    return {"tipo": tipo, "archivos": resultados, "warnings": warnings}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python exportar_oficial.py <ruta-al-.md>")
        sys.exit(1)
    resultado = exportar_oficial(sys.argv[1])
    print(f"Tipo detectado: {resultado['tipo']}")
    for f in resultado["archivos"]:
        print("Generado ->", f)
    for w in resultado["warnings"]:
        print("WARN:", w)
