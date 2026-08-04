#!/usr/bin/env python3
"""
graphify2obsidian.py — Convierte el knowledge graph de Graphify en un vault de Obsidian.
Cada comunidad se convierte en una nota .md con wikilinks a sus nodos y comunidades vecinas.
Los nodos individuales se agrupan en notas por comunidad para mantener navegabilidad.
"""

import json
import os
import re
import hashlib
from pathlib import Path
from collections import defaultdict

# ── Config ──────────────────────────────────────────────
GRAPH_PATH = "graphify-out/graph.json"
VAULT_PATH = "obsidian-vault"
INCLUDE_PATTERNS = [
    "resources/",           # todos los artefactos del proyecto
    "context/",             # documentos RFP y contexto
    ".github/skills/archi/",   # skill archi (referencias)
    ".github/skills/epicureo/",
    ".github/skills/janus/",
    ".github/skills/genesis/",
    ".github/skills/builder/",
    ".github/skills/figma-prd-mockups/",
    ".github/skills/front/",
    ".github/skills/ranger/",
    ".github/skills/specter/",
]
EXCLUDE_PATTERNS = [
    ".github/skills/obsidian-skills/",
    ".github/skills/docx/scripts/",
    ".github/skills/pptx/scripts/",
    ".github/skills/xlsx/scripts/",
    ".github/skills/pdf/scripts/",
    "node_modules/",
    "__pycache__/",
]
MIN_COMMUNITY_SIZE = 3  # comunidades con al menos 3 nodos para aparecer

# ── Helpers ─────────────────────────────────────────────

def sanitize_filename(name: str, max_len: int = 80) -> str:
    """Convierte un nombre de nodo/comunidad en un filename seguro para Obsidian."""
    # Reemplazar chars problemáticos
    name = name.replace("/", "⁄").replace("\\", "⁄")
    name = name.replace(":", "∶").replace("*", "∗")
    name = name.replace("?", "？").replace('"', "''")
    name = name.replace("<", "‹").replace(">", "›")
    name = name.replace("|", "¦").replace("#", "♯")
    name = name.replace("^", "↑").replace("[", "❲").replace("]", "❳")
    # Quitar espacios iniciales/finales
    name = name.strip()
    # Truncar si es muy largo
    if len(name) > max_len:
        # Usar hash para unicidad
        h = hashlib.md5(name.encode()).hexdigest()[:8]
        name = name[:max_len - 9] + "_" + h
    return name


def is_project_node(node: dict) -> bool:
    """Determina si un nodo pertenece al proyecto (no a dependencias/skills externas)."""
    sf = node.get("source_file", "")
    if not sf:
        # Nodos sin source_file pueden ser símbolos built-in — excluir
        return False
    
    # Excluir patterns
    for pat in EXCLUDE_PATTERNS:
        if pat in sf:
            return False
    
    # Incluir patterns
    for pat in INCLUDE_PATTERNS:
        if pat in sf:
            return True
    
    # También incluir nodos sin source_file si tienen community_name relevante
    cn = node.get("community_name", "").lower()
    for keyword in ["agro", "recomend", "cultivo", "iot", "sensor", "seguridad", 
                    "arquitect", "ml", "rag", "dashboar", "usuario", "rol",
                    "infraestruct", "devops", "ingesta", "ficha", "catalogo",
                    "membresia", "requisito", "funcional", "epicureo", "janus"]:
        if keyword in cn:
            return True
    
    return False


def extract_community_label(node: dict) -> str:
    """Extrae una etiqueta legible para la comunidad del nodo."""
    cn = node.get("community_name", "")
    if cn and cn != node.get("label", ""):
        return cn
    # Fallback: usar el nombre del archivo
    sf = node.get("source_file", "")
    if sf:
        parts = sf.replace("\\", "/").split("/")
        if len(parts) >= 2:
            return "/".join(parts[-2:])
    return node.get("label", "unknown")[:60]


# ── Main ────────────────────────────────────────────────

def main():
    print(f"📂 Cargando {GRAPH_PATH}...")
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        graph = json.load(f)
    
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    
    print(f"   {len(nodes)} nodos, {len(links)} enlaces")
    
    # ── Indexar nodos por ID ──
    node_by_id = {n["id"]: n for n in nodes}
    
    # ── Filtrar nodos del proyecto ──
    project_nodes = [n for n in nodes if is_project_node(n)]
    project_ids = {n["id"] for n in project_nodes}
    print(f"   {len(project_nodes)} nodos del proyecto (filtrados)")
    
    # ── Construir adjacency por comunidad ──
    community_nodes = defaultdict(list)      # community_id → [nodes]
    community_labels = {}                     # community_id → label
    community_edges = defaultdict(set)       # community_id → {neighbor_community_ids}
    
    for node in project_nodes:
        cid = node.get("community", -1)
        community_nodes[cid].append(node)
        if cid not in community_labels:
            community_labels[cid] = extract_community_label(node)
    
    # ── Construir edges entre comunidades ──
    for link in links:
        src = link.get("source", "")
        tgt = link.get("target", "")
        if src in project_ids and tgt in project_ids:
            src_node = node_by_id.get(src)
            tgt_node = node_by_id.get(tgt)
            if src_node and tgt_node:
                src_cid = src_node.get("community", -1)
                tgt_cid = tgt_node.get("community", -1)
                if src_cid != tgt_cid:
                    community_edges[src_cid].add(tgt_cid)
                    community_edges[tgt_cid].add(src_cid)
    
    # ── Crear vault ──
    vault = Path(VAULT_PATH)
    vault.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🏗️  Creando vault Obsidian en '{VAULT_PATH}/'...")
    
    # ── Nota índice (HOME) ──
    communities_sorted = sorted(
        [(cid, nodes) for cid, nodes in community_nodes.items() if len(nodes) >= MIN_COMMUNITY_SIZE],
        key=lambda x: len(x[1]), reverse=True
    )
    
    home_lines = [
        "---",
        "title: AgroIA - Knowledge Graph",
        "tags: [agroia, graphify, architecture]",
        "date: 2026-08-03",
        "nodes_total: " + str(len(project_nodes)),
        "communities_total: " + str(len(communities_sorted)),
        "links_total: " + str(len(links)),
        "---",
        "",
        "# 🧠 AgroIA — Grafo de Contexto del Proyecto",
        "",
        f"> **{len(project_nodes)} nodos** extraídos del código y documentación del proyecto.",
        f"> **{len(communities_sorted)} comunidades** detectadas (mín. {MIN_COMMUNITY_SIZE} nodos cada una).",
        f"> **{len(links)} enlaces** entre componentes.",
        "",
        "## 🗺️ Mapa de Comunidades",
        "",
        "| # | Comunidad | Nodos | Links externos |",
        "|---|-----------|-------|---------------|",
    ]
    
    for rank, (cid, cnodes) in enumerate(communities_sorted[:100], 1):  # top 100
        label = community_labels.get(cid, f"Community_{cid}")
        safe_label = sanitize_filename(label)
        ext_links = len(community_edges.get(cid, set()))
        home_lines.append(f"| {rank} | [[{safe_label}\|{label[:50]}]] | {len(cnodes)} | {ext_links} |")
    
    home_lines += [
        "",
        "---",
        "",
        "## 📊 Comunidades por tamaño",
        "",
        "```mermaid",
        "pie title Distribución de nodos por comunidad (top 10)",
    ]
    for _, (cid, cnodes) in enumerate(communities_sorted[:10]):
        label = community_labels.get(cid, f"C{cid}")[:30]
        home_lines.append(f'    "{label}": {len(cnodes)}')
    home_lines.append("```")
    
    home_lines += [
        "",
        "## 🔍 Cómo navegar este vault",
        "",
        "- Cada comunidad tiene su propia nota con la lista de nodos que la componen.",
        "- Los **wikilinks** `[[doble corchete]]` conectan comunidades relacionadas.",
        "- Usa el **Graph View** de Obsidian (`Ctrl+G`) para ver el grafo completo.",
        "- Activa **Local Graph** en cualquier nota para ver sus conexiones inmediatas.",
        "- Los tags permiten filtrar por tipo: `#code`, `#markdown`, `#functional`, `#architecture`.",
    ]
    
    home_path = vault / "🏠 AgroIA - Home.md"
    home_path.write_text("\n".join(home_lines), encoding="utf-8")
    print(f"   ✅ Home: {home_path.name}")
    
    # ── Notas por comunidad ──
    for cid, cnodes in communities_sorted:
        label = community_labels.get(cid, f"Community_{cid}")
        safe_label = sanitize_filename(label)
        
        # Obtener tipos de archivo presentes
        file_types = set(n.get("file_type", "unknown") for n in cnodes)
        file_types.discard("unknown")
        
        # Agrupar nodos por source_file para detectar artefactos principales
        sf_groups = defaultdict(list)
        for n in cnodes:
            sf = n.get("source_file", "_sin_archivo")
            sf_groups[sf].append(n)
        
        # Construir tags
        tags = ["agroia", "community"]
        for ft in file_types:
            tags.append(ft)
        
        lines = [
            "---",
            f"title: \"{label[:80]}\"",
            f"tags: [{', '.join(tags)}]",
            f"community_id: {cid}",
            f"node_count: {len(cnodes)}",
            "---",
            "",
            f"# {label}",
            "",
            f"> **{len(cnodes)} nodos** | Tipos: {', '.join(sorted(file_types)) if file_types else 'variados'}",
            "",
        ]
        
        # Listar archivos fuente principales
        main_files = sorted(sf_groups.keys(), key=lambda sf: len(sf_groups[sf]), reverse=True)[:10]
        if main_files:
            lines.append("## 📄 Archivos principales")
            lines.append("")
            for sf in main_files:
                count = len(sf_groups[sf])
                lines.append(f"- `{sf}` ({count} símbolos)")
            lines.append("")
        
        # Listar nodos clave (top 15 por tipo)
        lines.append("## 🔗 Nodos clave")
        lines.append("")
        for n in cnodes[:15]:
            nl = n.get("label", "?")[:80]
            ft = n.get("file_type", "?")
            sf = n.get("source_file", "")
            short_sf = sf.replace("\\", "/").split("/")[-1] if sf else ""
            lines.append(f"- **{nl}** `[{ft}]` _{short_sf}_")
        
        if len(cnodes) > 15:
            lines.append(f"- ... y {len(cnodes) - 15} nodos más")
        lines.append("")
        
        # Links a comunidades vecinas
        neighbors = community_edges.get(cid, set())
        neighbors = {nid for nid in neighbors if nid in community_labels and len(community_nodes.get(nid, [])) >= MIN_COMMUNITY_SIZE}
        if neighbors:
            lines.append("## 🌐 Comunidades conectadas")
            lines.append("")
            for nid in sorted(neighbors, key=lambda nid: len(community_nodes.get(nid, [])), reverse=True)[:15]:
                nlabel = community_labels.get(nid, f"Community_{nid}")
                nsafe = sanitize_filename(nlabel)
                nsize = len(community_nodes.get(nid, []))
                lines.append(f"- [[{nsafe}|{nlabel[:50]}]] ({nsize} nodos)")
            lines.append("")
        
        # Escribir nota
        note_path = vault / f"{safe_label}.md"
        note_path.write_text("\n".join(lines), encoding="utf-8")
    
    # ── Nota de tags ──
    all_file_types = set()
    for _, cnodes in communities_sorted:
        for n in cnodes:
            ft = n.get("file_type", "")
            if ft:
                all_file_types.add(ft)
    
    tag_lines = [
        "---",
        "title: Tags Index",
        "tags: [meta]",
        "---",
        "",
        "# 🏷️ Tags del Grafo",
        "",
    ]
    for ft in sorted(all_file_types):
        tag_lines.append(f"- # {ft}")
    tag_lines += [
        "",
        "## Navegación por tipo",
        "",
        "Usa el filtro de tags en el Graph View para aislar:",
        "- `#code` — Archivos de código fuente",
        "- `#markdown` — Documentación y specs",
        "- `#rationale` — Docstrings y justificaciones",
        "- `#functional` — Requerimientos funcionales",
        "- `#architecture` — Definiciones de arquitectura",
    ]
    (vault / "🏷️ Tags Index.md").write_text("\n".join(tag_lines), encoding="utf-8")
    
    # ── Resumen ──
    total_notes = len(communities_sorted) + 2  # comunidades + home + tags
    print(f"\n✨ Vault generado: {total_notes} notas en '{VAULT_PATH}/'")
    print(f"   🏠 Abre '🏠 AgroIA - Home.md' en Obsidian para empezar.")
    print(f"   📊 Graph View: Ctrl+G → Local Graph o Global Graph")
    print(f"\n⚡ Para abrir en Obsidian:")
    print(f"   1. Abre Obsidian")
    print(f"   2. 'Open folder as vault' → selecciona '{Path(VAULT_PATH).absolute()}'")
    print(f"   3. Activa Graph View (Ctrl+G)")


if __name__ == "__main__":
    main()
