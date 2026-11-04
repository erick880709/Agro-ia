# -*- coding: utf-8 -*-
"""Convierte un grafo (de mermaid_to_graph.parse_mermaid) a BPMN 2.0 XML importable en Bizagi Modeler.

Heurística de clasificación de nodos:
- Sin aristas entrantes            -> startEvent
- Sin aristas salientes            -> endEvent
- type == "gateway"                -> exclusiveGateway
- resto                            -> task

Layout: capas por BFS desde los start events (x = capa * LAYER_W, y = indice_en_capa * ROW_H), solo
para que Bizagi no importe todo apilado en (0,0). No es un layout definitivo — el analista lo reorganiza
en Bizagi.
"""
import re
import xml.dom.minidom as minidom
from collections import deque

LAYER_W = 200
ROW_H = 130
NODE_W = 140
NODE_H = 80
EVENT_SIZE = 36
GATEWAY_SIZE = 50

_ID_SAFE_RE = re.compile(r"[^A-Za-z0-9_]")


def _xml_escape(text):
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _safe_id(prefix, raw_id):
    return f"{prefix}_{_ID_SAFE_RE.sub('_', str(raw_id))}"


def _classify_nodes(graph):
    incoming = {n["id"]: 0 for n in graph["nodes"]}
    outgoing = {n["id"]: 0 for n in graph["nodes"]}
    for e in graph["edges"]:
        outgoing[e["from"]] = outgoing.get(e["from"], 0) + 1
        incoming[e["to"]] = incoming.get(e["to"], 0) + 1

    classified = []
    for n in graph["nodes"]:
        if incoming.get(n["id"], 0) == 0:
            kind = "startEvent"
        elif outgoing.get(n["id"], 0) == 0:
            kind = "endEvent"
        elif n["type"] == "gateway":
            kind = "exclusiveGateway"
        else:
            kind = "task"
        classified.append({**n, "kind": kind})
    return classified


def _layout(nodes, edges):
    node_by_id = {n["id"]: n for n in nodes}
    adjacency = {n["id"]: [] for n in nodes}
    for e in edges:
        if e["from"] in adjacency:
            adjacency[e["from"]].append(e["to"])

    layer = {}
    starts = [n["id"] for n in nodes if n["kind"] == "startEvent"] or [nodes[0]["id"]] if nodes else []
    queue = deque()
    for s in starts:
        layer[s] = 0
        queue.append(s)
    visited_edges = set()
    while queue:
        current = queue.popleft()
        for nxt in adjacency.get(current, []):
            edge_key = (current, nxt)
            proposed = layer[current] + 1
            if nxt not in layer or proposed > layer[nxt]:
                if edge_key in visited_edges and nxt in layer:
                    continue  # evita loops infinitos en ciclos
                visited_edges.add(edge_key)
                layer[nxt] = max(layer.get(nxt, 0), proposed)
                queue.append(nxt)

    for n in nodes:
        layer.setdefault(n["id"], 0)

    rows_per_layer = {}
    positions = {}
    for n in nodes:
        l = layer[n["id"]]
        row = rows_per_layer.get(l, 0)
        rows_per_layer[l] = row + 1
        positions[n["id"]] = (l * LAYER_W + 60, row * ROW_H + 60)

    return positions


def _shape_size(kind):
    if kind in ("startEvent", "endEvent"):
        return EVENT_SIZE, EVENT_SIZE
    if kind == "exclusiveGateway":
        return GATEWAY_SIZE, GATEWAY_SIZE
    return NODE_W, NODE_H


def build_bpmn(graph, process_id, process_name):
    nodes = _classify_nodes(graph)
    positions = _layout(nodes, graph["edges"])

    process_id = _safe_id("Process", process_id)
    flow_nodes_xml = []
    shapes_xml = []

    for n in nodes:
        node_id = _safe_id("Node", n["id"])
        label = _xml_escape(n["label"])
        w, h = _shape_size(n["kind"])
        x, y = positions[n["id"]]

        incoming_ids = [
            _safe_id("Flow", f"{e['from']}_{e['to']}") for e in graph["edges"] if e["to"] == n["id"]
        ]
        outgoing_ids = [
            _safe_id("Flow", f"{e['from']}_{e['to']}") for e in graph["edges"] if e["from"] == n["id"]
        ]
        incoming_xml = "".join(f"<bpmn:incoming>{i}</bpmn:incoming>" for i in incoming_ids)
        outgoing_xml = "".join(f"<bpmn:outgoing>{o}</bpmn:outgoing>" for o in outgoing_ids)

        if n["kind"] == "startEvent":
            flow_nodes_xml.append(
                f'<bpmn:startEvent id="{node_id}" name="{label}">{outgoing_xml}</bpmn:startEvent>'
            )
        elif n["kind"] == "endEvent":
            flow_nodes_xml.append(
                f'<bpmn:endEvent id="{node_id}" name="{label}">{incoming_xml}</bpmn:endEvent>'
            )
        elif n["kind"] == "exclusiveGateway":
            flow_nodes_xml.append(
                f'<bpmn:exclusiveGateway id="{node_id}" name="{label}">'
                f"{incoming_xml}{outgoing_xml}</bpmn:exclusiveGateway>"
            )
        else:
            flow_nodes_xml.append(
                f'<bpmn:task id="{node_id}" name="{label}">{incoming_xml}{outgoing_xml}</bpmn:task>'
            )

        shapes_xml.append(
            f'<bpmndi:BPMNShape id="{node_id}_di" bpmnElement="{node_id}">'
            f'<dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}"/>'
            f"</bpmndi:BPMNShape>"
        )

    sequence_flows_xml = []
    edges_xml = []
    for e in graph["edges"]:
        flow_id = _safe_id("Flow", f"{e['from']}_{e['to']}")
        src_id = _safe_id("Node", e["from"])
        dst_id = _safe_id("Node", e["to"])
        name_attr = f' name="{_xml_escape(e["label"])}"' if e.get("label") else ""
        sequence_flows_xml.append(
            f'<bpmn:sequenceFlow id="{flow_id}" sourceRef="{src_id}" targetRef="{dst_id}"{name_attr}/>'
        )
        sx, sy = positions[e["from"]]
        dx, dy = positions[e["to"]]
        sw, sh = _shape_size(next(n["kind"] for n in nodes if n["id"] == e["from"]))
        dw, dh = _shape_size(next(n["kind"] for n in nodes if n["id"] == e["to"]))
        edges_xml.append(
            f'<bpmndi:BPMNEdge id="{flow_id}_di" bpmnElement="{flow_id}">'
            f'<di:waypoint x="{sx + sw}" y="{sy + sh // 2}"/>'
            f'<di:waypoint x="{dx}" y="{dy + dh // 2}"/>'
            f"</bpmndi:BPMNEdge>"
        )

    xml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                   xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                   xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                   xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                   id="Definitions_{process_id}"
                   targetNamespace="http://procesos.bureau/bpmn">
  <bpmn:process id="{process_id}" name="{_xml_escape(process_name)}" isExecutable="false">
    {''.join(flow_nodes_xml)}
    {''.join(sequence_flows_xml)}
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Diagram_{process_id}">
    <bpmndi:BPMNPlane id="Plane_{process_id}" bpmnElement="{process_id}">
      {''.join(shapes_xml)}
      {''.join(edges_xml)}
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""
    minidom.parseString(xml_str)  # valida bien-formado; lanza si no lo es
    return xml_str


if __name__ == "__main__":
    import sys
    import json

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        graph = json.load(f)
    xml_out = build_bpmn(graph, sys.argv[2] if len(sys.argv) > 2 else "Process1", sys.argv[3] if len(sys.argv) > 3 else "Proceso")
    with open(sys.argv[4], "w", encoding="utf-8") as f:
        f.write(xml_out)
    print("OK ->", sys.argv[4])
