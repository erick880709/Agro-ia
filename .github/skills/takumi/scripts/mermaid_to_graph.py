# -*- coding: utf-8 -*-
"""Parser de un subconjunto de Mermaid flowchart (el que usan las plantillas de esta skill) a un grafo.

Soporta: `flowchart TD|LR`, nodos `ID[Label]` / `ID{Label}`, aristas `A --> B` y `A -->|label| B`,
`subgraph NAME ... end`. Cualquier línea no reconocida se ignora (se reporta en `warnings`, no se
lanza excepción) — el objetivo es tolerar variaciones menores del Mermaid real, no validarlo.
"""
import re

_NODE_DEF_RE = re.compile(r"^([A-Za-z0-9_]+)\s*(\[([^\]]*)\]|\{([^}]*)\})\s*$")
_SUBGRAPH_RE = re.compile(r"^subgraph\s+([A-Za-z0-9_]+)\s*(\[([^\]]*)\])?\s*$")
_EDGE_RE = re.compile(
    r"^([A-Za-z0-9_]+)"
    r"(?:\s*(\[[^\]]*\]|\{[^}]*\}))?"
    r"\s*-->\s*(?:\|([^|]*)\|)?\s*"
    r"([A-Za-z0-9_]+)"
    r"(?:\s*(\[[^\]]*\]|\{[^}]*\}))?\s*$"
)


def _label_and_type(bracket_text):
    if bracket_text is None:
        return None, None
    if bracket_text.startswith("["):
        return bracket_text[1:-1].strip(), "rect"
    if bracket_text.startswith("{"):
        return bracket_text[1:-1].strip(), "gateway"
    return None, None


def parse_mermaid(source):
    nodes = {}
    edges = []
    warnings = []
    current_group = None
    group_stack = []

    def ensure_node(node_id, label=None, ntype=None):
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "label": label or node_id,
                "type": ntype or "rect",
                "group": current_group,
            }
        else:
            if label:
                nodes[node_id]["label"] = label
            if ntype:
                nodes[node_id]["type"] = ntype

    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("%%"):
            continue
        if re.match(r"^flowchart\s+(TD|LR|TB|RL|BT)\s*$", line, re.IGNORECASE):
            continue

        m_sub = _SUBGRAPH_RE.match(line)
        if m_sub:
            group_id = m_sub.group(1)
            group_stack.append(group_id)
            current_group = group_id
            continue
        if line == "end":
            if group_stack:
                group_stack.pop()
                current_group = group_stack[-1] if group_stack else None
                continue
            warnings.append(f"'end' sin subgraph abierto: {raw_line!r}")
            continue

        m_edge = _EDGE_RE.match(line)
        if m_edge:
            src, src_bracket, edge_label, dst, dst_bracket = m_edge.groups()
            src_label, src_type = _label_and_type(src_bracket)
            dst_label, dst_type = _label_and_type(dst_bracket)
            ensure_node(src, src_label, src_type)
            ensure_node(dst, dst_label, dst_type)
            edges.append({"from": src, "to": dst, "label": (edge_label or "").strip() or None})
            continue

        m_node = _NODE_DEF_RE.match(line)
        if m_node:
            node_id, _, rect_label, gw_label = m_node.groups()
            if rect_label is not None:
                ensure_node(node_id, rect_label, "rect")
            else:
                ensure_node(node_id, gw_label, "gateway")
            continue

        warnings.append(f"Línea no reconocida, ignorada: {raw_line!r}")

    return {"nodes": list(nodes.values()), "edges": edges, "warnings": warnings}


if __name__ == "__main__":
    import sys
    import json

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        result = parse_mermaid(f.read())
    print(json.dumps(result, ensure_ascii=False, indent=2))
