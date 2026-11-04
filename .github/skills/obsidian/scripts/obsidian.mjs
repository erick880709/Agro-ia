#!/usr/bin/env node
// obsidian.mjs — puente del kit hacia Obsidian (vault + JSON Canvas + validación).
// Solo stdlib de Node; salida determinista y en UTF-8.
//
// Comandos:
//   export [--root <dir>] [--out <dir>]   Proyecta .memoria/graph.json a un vault + .canvas.
//   validate-canvas <archivo.canvas>      Valida un JSON Canvas (exit != 0 si falla).

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const USAGE = `Uso:
  node obsidian.mjs export [--root <dir>] [--out <dir>]
  node obsidian.mjs validate-canvas <archivo.canvas>
`;

const COLS = 4;
const NODE_W = 380;
const NODE_H = 180;
const GAP_X = 40;
const GAP_Y = 40;

const COLOR_BY_TYPE = {
  avance: "5",
  decision: "6",
  hito: "2",
  estado: "3",
  nota: "1",
  tarea: "4",
};

const CALLOUT_BY_TYPE = {
  decision: "important",
  hito: "success",
  avance: "note",
  estado: "info",
  nota: "quote",
  tarea: "todo",
};

const TYPE_ORDER = ["avance", "decision", "hito", "estado", "nota", "tarea"];

function parseArgs(argv) {
  const args = { root: process.cwd(), out: null, file: null };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--root") args.root = argv[++i];
    else if (a === "--out") args.out = argv[++i];
    else if (a === "--root=") args.root = a.slice("--root=".length);
    else if (a.startsWith("--root=")) args.root = a.slice("--root=".length);
    else if (a.startsWith("--out=")) args.out = a.slice("--out=".length);
    else if (!a.startsWith("--")) args.file = a;
  }
  return args;
}

function stableId(prefix, value) {
  return crypto.createHash("sha256").update(`${prefix}:${value}`).digest("hex").slice(0, 16);
}

function yamlScalar(value) {
  if (typeof value !== "string") return JSON.stringify(value);
  if (value === "") return '""';
  // Las claves que queremos emitir son identificadores simples; escapamos comillas y barras.
  return `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

function readGraph(root) {
  const file = path.join(root, ".memoria", "graph.json");
  if (!fs.existsSync(file)) {
    throw new Error(`No existe ${file}. Ejecuta primero 'memoria init' en el proyecto.`);
  }
  const graph = JSON.parse(fs.readFileSync(file, "utf8"));
  if (!Array.isArray(graph.nodes)) {
    throw new Error("graph.json inválido: falta el array 'nodes'.");
  }
  return graph;
}

function edgesOf(graph) {
  if (Array.isArray(graph.edges) && graph.edges.length > 0) return graph.edges;
  const byId = new Set(graph.nodes.map((n) => n.id));
  const edges = [];
  for (const node of graph.nodes) {
    for (const link of node.links || []) {
      if (byId.has(link)) edges.push({ from: node.id, to: link, type: "relacionado" });
    }
  }
  return edges;
}

function noteMarkdown(node) {
  const type = node.type || "nota";
  const status = node.status || "activo";
  const skill = node.skill || "kit";
  const title = node.title || node.id;
  const summary = node.summary || "";
  const created = (node.createdAt || "").slice(0, 10) || "";
  const callout = CALLOUT_BY_TYPE[type] || "note";
  const lines = [];
  lines.push("---");
  lines.push(`title: ${yamlScalar(title)}`);
  lines.push(`type: ${type}`);
  lines.push(`skill: ${skill}`);
  lines.push(`status: ${status}`);
  if (created) lines.push(`created: ${created}`);
  lines.push("tags:");
  lines.push("  - memoria");
  lines.push(`  - ${type}`);
  lines.push(`  - ${skill}`);
  lines.push(`  - ${status}`);
  lines.push("---");
  lines.push("");
  lines.push(`# ${title}`);
  lines.push("");
  lines.push(`> [!${callout}] ${type} · ${status}`);
  for (const line of summary.split("\n")) lines.push(`> ${line}`);
  lines.push("");
  lines.push("## Resumen");
  lines.push("");
  lines.push(summary || "_Sin resumen._");
  lines.push("");
  lines.push("## Archivos");
  lines.push("");
  if (Array.isArray(node.files) && node.files.length > 0) {
    for (const file of node.files) lines.push(`- \`${file}\``);
  } else {
    lines.push("_Sin archivos registrados._");
  }
  lines.push("");
  lines.push("## Relacionado");
  lines.push("");
  const links = (node.links || []).filter((l) => typeof l === "string" && l.length > 0);
  if (links.length > 0) {
    for (const link of links) lines.push(`- [[${link}]]`);
  } else {
    lines.push("_Sin enlaces._");
  }
  lines.push("");
  return lines.join("\n");
}

function mocMarkdown(graph) {
  const byType = new Map();
  for (const node of graph.nodes) {
    const type = node.type || "nota";
    if (!byType.has(type)) byType.set(type, []);
    byType.get(type).push(node);
  }
  const types = [...byType.keys()].sort((a, b) => {
    const ia = TYPE_ORDER.indexOf(a);
    const ib = TYPE_ORDER.indexOf(b);
    if (ia === -1 && ib === -1) return a.localeCompare(b);
    if (ia === -1) return 1;
    if (ib === -1) return -1;
    return ia - ib;
  });
  const lines = [];
  lines.push("# Memoria del proyecto");
  lines.push("");
  lines.push(`> Exportado desde \`.memoria/graph.json\` el ${new Date().toISOString().slice(0, 10)}.`);
  lines.push(`> ${graph.nodes.length} nodos · ${edgesOf(graph).length} aristas.`);
  lines.push("");
  lines.push("## Por tipo");
  lines.push("");
  for (const type of types) {
    lines.push(`### ${type.charAt(0).toUpperCase() + type.slice(1)}`);
    lines.push("");
    for (const node of byType.get(type)) {
      lines.push(`- [[${node.id}]] — ${node.title || node.id}`);
    }
    lines.push("");
  }
  return lines.join("\n");
}

function canvasFor(graph) {
  const nodes = graph.nodes.map((node, index) => {
    const col = index % COLS;
    const row = Math.floor(index / COLS);
    return {
      id: stableId("node", node.id),
      type: "file",
      file: `notas/${node.id}.md`,
      x: col * (NODE_W + GAP_X),
      y: row * (NODE_H + GAP_Y),
      width: NODE_W,
      height: NODE_H,
      color: COLOR_BY_TYPE[node.type] || "1",
    };
  });
  const byMemoriaId = new Map(graph.nodes.map((n, i) => [n.id, nodes[i].id]));
  const edges = [];
  for (const edge of edgesOf(graph)) {
    const from = byMemoriaId.get(edge.from);
    const to = byMemoriaId.get(edge.to);
    if (!from || !to) continue;
    edges.push({
      id: stableId("edge", `${edge.from}->${edge.to}`),
      fromNode: from,
      toNode: to,
      toEnd: "arrow",
      label: edge.type || "relacionado",
    });
  }
  return { nodes, edges };
}

function exportMemoria(root, out) {
  const graph = readGraph(root);
  const outDir = out || path.join(root, "obsidian");
  fs.mkdirSync(path.join(outDir, "notas"), { recursive: true });
  fs.writeFileSync(path.join(outDir, "Inicio.md"), mocMarkdown(graph), "utf8");
  for (const node of graph.nodes) {
    fs.writeFileSync(path.join(outDir, "notas", `${node.id}.md`), noteMarkdown(node), "utf8");
  }
  fs.writeFileSync(path.join(outDir, "Memoria.canvas"), JSON.stringify(canvasFor(graph), null, 2) + "\n", "utf8");
  return { outDir, nodes: graph.nodes.length, edges: edgesOf(graph).length };
}

function validateCanvas(file) {
  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (err) {
    return { ok: false, errors: [`No se pudo leer/parsear ${file}: ${err.message}`] };
  }
  const errors = [];
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    return { ok: false, errors: ["El canvas debe ser un objeto JSON con 'nodes' y 'edges'."] };
  }
  const nodes = parsed.nodes;
  const edges = parsed.edges;
  if (!Array.isArray(nodes)) errors.push("'nodes' debe ser un array.");
  if (edges !== undefined && !Array.isArray(edges)) errors.push("'edges' debe ser un array.");

  const ids = new Set();
  const validTypes = new Set(["text", "file", "link", "group"]);
  const sides = new Set(["top", "right", "bottom", "left"]);
  const ends = new Set(["none", "arrow"]);

  if (Array.isArray(nodes)) {
    for (const node of nodes) {
      if (!node || typeof node !== "object") { errors.push("Hay un nodo que no es un objeto."); continue; }
      if (!node.id || typeof node.id !== "string") errors.push(`Nodo sin 'id' válido: ${JSON.stringify(node.id)}`);
      else if (ids.has(node.id)) errors.push(`Id de nodo duplicado: ${node.id}`);
      else ids.add(node.id);
      if (!validTypes.has(node.type)) errors.push(`Nodo ${node.id}: type inválido '${node.type}'.`);
      for (const field of ["x", "y", "width", "height"]) {
        if (typeof node[field] !== "number") errors.push(`Nodo ${node.id}: '${field}' debe ser número.`);
      }
      if (node.type === "text" && typeof node.text !== "string") errors.push(`Nodo ${node.id}: falta 'text'.`);
      if (node.type === "file" && typeof node.file !== "string") errors.push(`Nodo ${node.id}: falta 'file'.`);
      if (node.type === "link" && typeof node.url !== "string") errors.push(`Nodo ${node.id}: falta 'url'.`);
    }
  }

  if (Array.isArray(edges)) {
    const edgeIds = new Set();
    for (const edge of edges) {
      if (!edge || typeof edge !== "object") { errors.push("Hay una arista que no es un objeto."); continue; }
      if (!edge.id || typeof edge.id !== "string") errors.push(`Arista sin 'id' válido.`);
      else if (edgeIds.has(edge.id)) errors.push(`Id de arista duplicado: ${edge.id}`);
      else edgeIds.add(edge.id);
      if (typeof edge.fromNode !== "string" || !ids.has(edge.fromNode)) errors.push(`Arista ${edge.id}: 'fromNode' '${edge.fromNode}' no resuelve.`);
      if (typeof edge.toNode !== "string" || !ids.has(edge.toNode)) errors.push(`Arista ${edge.id}: 'toNode' '${edge.toNode}' no resuelve.`);
      if (edge.fromSide !== undefined && !sides.has(edge.fromSide)) errors.push(`Arista ${edge.id}: fromSide inválido '${edge.fromSide}'.`);
      if (edge.toSide !== undefined && !sides.has(edge.toSide)) errors.push(`Arista ${edge.id}: toSide inválido '${edge.toSide}'.`);
      if (edge.fromEnd !== undefined && !ends.has(edge.fromEnd)) errors.push(`Arista ${edge.id}: fromEnd inválido '${edge.fromEnd}'.`);
      if (edge.toEnd !== undefined && !ends.has(edge.toEnd)) errors.push(`Arista ${edge.id}: toEnd inválido '${edge.toEnd}'.`);
    }
  }

  return { ok: errors.length === 0, errors, nodes: Array.isArray(nodes) ? nodes.length : 0, edges: Array.isArray(edges) ? edges.length : 0 };
}

function main() {
  const argv = process.argv.slice(2);
  const command = argv[0];
  const args = parseArgs(argv.slice(1));

  if (command === "export") {
    try {
      const result = exportMemoria(args.root, args.out);
      const arista = result.edges === 1 ? "arista" : "aristas";
      console.log(`export: ${result.nodes} nodos, ${result.edges} ${arista} -> ${result.outDir}`);
      return 0;
    } catch (err) {
      console.error(`export: ${err.message}`);
      return 2;
    }
  }

  if (command === "validate-canvas") {
    if (!args.file) {
      console.error("validate-canvas requiere la ruta al .canvas.\n" + USAGE);
      return 2;
    }
    const result = validateCanvas(args.file);
    if (result.ok) {
      console.log(`Canvas válido: ${result.nodes} nodos, ${result.edges} aristas.`);
      return 0;
    }
    for (const error of result.errors) console.error(`✗ ${error}`);
    console.error(`Canvas inválido: ${result.errors.length} problema(s).`);
    return 1;
  }

  console.error(USAGE);
  return 2;
}

process.exitCode = main();
