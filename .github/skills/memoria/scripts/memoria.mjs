#!/usr/bin/env node
// memoria.mjs — Motor de memoria y contexto del proyecto (skill `memoria`).
//
// Grafo de conocimiento persistente, legible y rastreable en git: cada skill del kit
// registra un nodo cuando termina una tarea y la memoria del proyecto crece como un
// grafo de nodos (avances, decisiones, hitos, estado, notas, tareas) conectados por
// enlaces. Sin base de datos ni dependencias: solo JSON + Markdown.
//
// Subcomandos:
//   init        Prepara .memoria/ en el proyecto y enlaza hook + workflow.
//   record      Crea o actualiza un nodo (--skill --type --title --summary ...).
//   query       Busca nodos por tipo/skill/estado/texto.
//   report      Regenera .memoria/index.md y muestra el resumen.
//   merge       Consolida duplicados y archiva nodos completados antiguos.
//   validate    Valida el esquema de .memoria/graph.json (exit != 0 si falla).
//   promote     Consolida .memoria/pending/*.json en el grafo (uso manual).
//   hook-stop   Igual que promote, pero pensado para el hook Stop (nunca bloquea).
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { pathToFileURL, fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const MEM_DIR = ".memoria";
const GRAPH_FILE = "graph.json";
const INDEX_FILE = "index.md";
const PENDING_DIR = "pending";
const CONFIG_FILE = "config.json";
const SCHEMA = "memoria/v1";

const NODE_TYPES = ["avance", "decision", "hito", "estado", "nota", "tarea"];
const STATUSES = ["activo", "completado", "pendiente", "archivado"];
const DEFAULT_TYPE = "avance";
const DEFAULT_STATUS = "completado";

// ───────────────────────────── utilidades ─────────────────────────────

function nowIso() {
  return new Date().toISOString();
}

function slug(text) {
  return String(text)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)+/g, "")
    .slice(0, 60);
}

function nodeId(skill, title, createdAt) {
  const base = slug(`${skill} ${title}`);
  const stamp = createdAt.replace(/\D/g, "").slice(0, 14);
  const hash = crypto.createHash("sha1").update(`${skill}|${title}`).digest("hex").slice(0, 6);
  return `mem-${stamp}-${hash}-${base}`.replace(/-{2,}/g, "-").replace(/-+$/, "").slice(0, 120);
}

function readJSON(file) {
  return JSON.parse(fs.readFileSync(file, "utf8").replace(/^\uFEFF/, ""));
}

function writeJSON(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + "\n", "utf8");
}

function readGraph(root) {
  const file = path.join(root, MEM_DIR, GRAPH_FILE);
  if (!fs.existsSync(file)) {
    return { schema: SCHEMA, updatedAt: nowIso(), nodes: [], edges: [] };
  }
  const graph = readJSON(file);
  graph.nodes = graph.nodes || [];
  graph.edges = graph.edges || [];
  graph.schema = graph.schema || SCHEMA;
  return graph;
}

function writeGraph(root, graph) {
  graph.schema = SCHEMA;
  graph.updatedAt = nowIso();
  writeJSON(path.join(root, MEM_DIR, GRAPH_FILE), graph);
  regenerateIndex(root, graph);
}

function normalizeFile(file, root) {
  if (typeof file !== "string") return null;
  const abs = path.resolve(root, file);
  if (!fs.existsSync(abs)) return file;
  return path.relative(root, abs).split(path.sep).join("/");
}

function assertValidNode(node, root) {
  const errors = [];
  if (!node || typeof node !== "object") errors.push("el nodo debe ser un objeto");
  if (!NODE_TYPES.includes(node.type)) errors.push(`type inválido (${node.type}); usar: ${NODE_TYPES.join(", ")}`);
  if (!STATUSES.includes(node.status)) errors.push(`status inválido (${node.status}); usar: ${STATUSES.join(", ")}`);
  if (typeof node.skill !== "string" || !node.skill.trim()) errors.push("skill es obligatorio");
  if (typeof node.title !== "string" || !node.title.trim()) errors.push("title es obligatorio");
  if (typeof node.summary !== "string" || !node.summary.trim()) errors.push("summary es obligatorio");
  if (node.files !== undefined) {
    if (!Array.isArray(node.files) || node.files.some(f => typeof f !== "string")) {
      errors.push("files debe ser un array de strings");
    }
  }
  if (node.links !== undefined) {
    if (!Array.isArray(node.links) || node.links.some(l => typeof l !== "string")) {
      errors.push("links debe ser un array de ids");
    }
  }
  if (errors.length) throw new Error(errors.join("; "));
}

function buildNode(input, root) {
  const now = input.createdAt || nowIso();
  const type = input.type || DEFAULT_TYPE;
  const status = input.status || DEFAULT_STATUS;
  const node = {
    id: input.id || nodeId(input.skill, input.title, now),
    type,
    status,
    skill: input.skill,
    title: input.title,
    summary: input.summary,
    files: (input.files || []).map(f => normalizeFile(f, root)).filter(Boolean),
    links: (input.links || []).filter(l => typeof l === "string" && l.trim()),
    source: input.source || "manual",
    createdAt: input.createdAt || now,
    updatedAt: nowIso(),
  };
  assertValidNode(node, root);
  return node;
}

function syncEdges(graph) {
  const ids = new Set(graph.nodes.map(n => n.id));
  const edges = [];
  const seen = new Set();
  for (const node of graph.nodes) {
    for (const target of node.links || []) {
      const key = `${node.id}|${target}`;
      if (!seen.has(key) && ids.has(target)) {
        seen.add(key);
        edges.push({ from: node.id, to: target, type: "relacionado" });
      }
    }
  }
  graph.edges = edges;
}

// ───────────────────────────── índice humano ─────────────────────────────

function typeLabel(type) {
  return {
    avance: "Avances",
    decision: "Decisiones",
    hito: "Hitos",
    estado: "Estado y contexto",
    nota: "Notas",
    tarea: "Tareas",
  }[type] || type;
}

function regenerateIndex(root, graph) {
  const lines = [];
  lines.push("# Memoria del proyecto");
  lines.push("");
  lines.push("> Grafo de conocimiento generado por la skill `memoria`. Fuente de verdad: `.memoria/graph.json`.");
  lines.push("> Este archivo se regenera; no lo edites a mano.");
  lines.push("");
  const total = graph.nodes.length;
  const edges = graph.edges.length;
  lines.push(`**${total} nodo(s)** · **${edges} enlace(s)** · actualizado ${graph.updatedAt}`);
  lines.push("");

  const active = graph.nodes
    .filter(n => n.status !== "archivado")
    .sort((a, b) => (b.updatedAt || "").localeCompare(a.updatedAt || ""))
    .slice(0, 10);
  if (active.length) {
    lines.push("## Contexto activo");
    lines.push("");
    for (const n of active) {
      lines.push(`- **${n.title}** — \`${n.skill}\` · ${n.status} · ${(n.updatedAt || "").slice(0, 10)}`);
      if (n.summary) lines.push(`  ${n.summary}`);
    }
    lines.push("");
  }

  for (const type of NODE_TYPES) {
    const group = graph.nodes.filter(n => n.type === type);
    if (!group.length) continue;
    lines.push(`## ${typeLabel(type)}`);
    lines.push("");
    for (const n of group.sort((a, b) => (b.createdAt || "").localeCompare(a.createdAt || ""))) {
      const statusIcon = { activo: "🟢", completado: "✅", pendiente: "🟡", archivado: "⚪" }[n.status] || "·";
      lines.push(`### ${statusIcon} ${n.title}`);
      lines.push("");
      lines.push(`- **id:** \`${n.id}\``);
      lines.push(`- **skill:** \`${n.skill}\` · **estado:** ${n.status} · **creado:** ${(n.createdAt || "").slice(0, 10)}`);
      if (n.summary) lines.push(`- **resumen:** ${n.summary}`);
      if (n.files && n.files.length) lines.push(`- **archivos:** ${n.files.map(f => `\`${f}\``).join(", ")}`);
      if (n.links && n.links.length) lines.push(`- **enlaza a:** ${n.links.map(l => `\`${l}\``).join(", ")}`);
      lines.push("");
    }
  }
  fs.mkdirSync(path.join(root, MEM_DIR), { recursive: true });
  fs.writeFileSync(path.join(root, MEM_DIR, INDEX_FILE), lines.join("\n"), "utf8");
}

// ───────────────────────────── subcomandos ─────────────────────────────

function cmdInit(root) {
  const memRoot = path.join(root, MEM_DIR);
  const pendingRoot = path.join(memRoot, PENDING_DIR);
  fs.mkdirSync(pendingRoot, { recursive: true });
  if (!fs.existsSync(path.join(memRoot, GRAPH_FILE))) {
    writeGraph(root, { schema: SCHEMA, updatedAt: nowIso(), nodes: [], edges: [] });
  }
  if (!fs.existsSync(path.join(memRoot, CONFIG_FILE))) {
    writeJSON(path.join(memRoot, CONFIG_FILE), {
      project: path.basename(root),
      createdAt: nowIso(),
      nodePrefix: "mem",
    });
  }
  const hookPath = path.join(root, ".claude", "settings.json");
  installHook(hookPath);
  const wf = path.join(root, ".github", "workflows", "memoria.yml");
  let copied = false;
  if (!fs.existsSync(wf)) {
    const template = path.join(__dirname, "..", "templates", "github-memoria.yml");
    if (fs.existsSync(template)) {
      fs.mkdirSync(path.dirname(wf), { recursive: true });
      fs.copyFileSync(template, wf);
      copied = true;
    }
  }
  console.log(`Memoria inicializada en ${path.join(root, MEM_DIR)}`);
  console.log("  - graph.json + index.md creados (rastreables en git)");
  console.log("  - hook de Stop enlazado en .claude/settings.json (consolida .memoria/pending/)");
  if (copied) console.log("  - workflow .github/workflows/memoria.yml instalado");
  return 0;
}

function installHook(settingsPath) {
  const HOOK_CMD = "node .claude/skills/memoria/scripts/memoria.mjs hook-stop";
  let settings = {};
  if (fs.existsSync(settingsPath)) {
    try {
      settings = readJSON(settingsPath);
    } catch {
      settings = {};
    }
  }
  settings.hooks = settings.hooks || {};
  const stop = (settings.hooks.Stop = settings.hooks.Stop || []);
  const allCommands = stop.flatMap(entry =>
    (entry && Array.isArray(entry.hooks) ? entry.hooks : []).map(h => h && h.command));
  if (allCommands.includes(HOOK_CMD)) return;
  const group = stop.find(entry => entry && Array.isArray(entry.hooks));
  if (group) {
    group.hooks.push({ type: "command", command: HOOK_CMD });
  } else {
    stop.push({ hooks: [{ type: "command", command: HOOK_CMD }] });
  }
  fs.mkdirSync(path.dirname(settingsPath), { recursive: true });
  writeJSON(settingsPath, settings);
}

function parseArgv(argv) {
  const opts = { root: process.cwd(), files: [], links: [], flags: new Set() };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const next = () => argv[++i];
    switch (arg) {
      case "--root": opts.root = path.resolve(next()); break;
      case "--skill": opts.skill = next(); break;
      case "--type": opts.type = next(); break;
      case "--title": opts.title = next(); break;
      case "--summary": opts.summary = next(); break;
      case "--status": opts.status = next(); break;
      case "--id": opts.id = next(); break;
      case "--source": opts.source = next(); break;
      case "--file": opts.files.push(next()); break;
      case "--link": opts.links.push(next()); break;
      case "--text": opts.text = next(); break;
      case "--limit": opts.limit = Number(next()); break;
      case "--json": opts.flags.add("json"); break;
      case "--table": opts.flags.add("table"); break;
      case "--new": opts.flags.add("new"); break;
      case "--archive-completed": opts.flags.add("archive"); break;
      case "--days": opts.days = Number(next()); break;
      case "--help": case "-h": opts.flags.add("help"); break;
      default: opts.extra = (opts.extra || []).concat(arg);
    }
  }
  return opts;
}

function readStdinPayload() {
  if (process.stdin.isTTY) return {};
  try {
    const raw = fs.readFileSync(0, "utf8");
    if (raw.trim()) return JSON.parse(raw);
  } catch {
    /* stdin no es JSON: se ignora */
  }
  return {};
}

function cmdRecord(root, args) {
  const opts = parseArgv(args);
  const stdin = readStdinPayload();
  const input = { ...stdin, ...opts };
  const node = buildNode(input, root);
  const graph = readGraph(root);

  let existing = null;
  if (opts.flags.has("new") || input.id) {
    existing = graph.nodes.find(n => n.id === input.id);
  } else {
    existing = graph.nodes.find(n => n.skill === node.skill && n.title === node.title);
  }

  if (existing) {
    Object.assign(existing, {
      type: node.type,
      status: node.status,
      summary: node.summary,
      files: node.files.length ? node.files : existing.files,
      links: Array.from(new Set([...(existing.links || []), ...node.links])),
      updatedAt: nowIso(),
    });
    console.log(`actualizado ${existing.id}`);
  } else {
    graph.nodes.push(node);
    console.log(`creado ${node.id}`);
  }
  syncEdges(graph);
  writeGraph(root, graph);
  return 0;
}

function cmdQuery(root, args) {
  const opts = parseArgv(args);
  let nodes = readGraph(root).nodes;
  if (opts.type) nodes = nodes.filter(n => n.type === opts.type);
  if (opts.skill) nodes = nodes.filter(n => n.skill === opts.skill);
  if (opts.status) nodes = nodes.filter(n => n.status === opts.status);
  if (opts.text) {
    const t = opts.text.toLowerCase();
    nodes = nodes.filter(n =>
      [n.title, n.summary, n.skill, n.id].some(s => String(s || "").toLowerCase().includes(t)));
  }
  nodes = nodes.sort((a, b) => (b.updatedAt || "").localeCompare(a.updatedAt || ""));
  const limit = opts.limit && opts.limit > 0 ? opts.limit : nodes.length;
  const slice = nodes.slice(0, limit);
  if (opts.flags.has("json")) {
    console.log(JSON.stringify(slice, null, 2));
  } else {
    for (const n of slice) {
      console.log(`${n.id}\t${n.type}\t${n.status}\t${n.skill}\t${n.title}`);
    }
  }
  return 0;
}

function cmdReport(root) {
  const graph = readGraph(root);
  regenerateIndex(root, graph);
  const counts = {};
  for (const n of graph.nodes) counts[n.type] = (counts[n.type] || 0) + 1;
  console.log(`index.md regenerado: ${graph.nodes.length} nodos, ${graph.edges.length} enlaces`);
  console.log(Object.entries(counts).map(([k, v]) => `${k}=${v}`).join(" "));
  return 0;
}

function cmdMerge(root, args) {
  const opts = parseArgv(args);
  const graph = readGraph(root);
  const days = opts.days && opts.days > 0 ? opts.days : 30;
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;

  const byKey = new Map();
  for (const node of graph.nodes) {
    const key = `${node.skill}|${node.title}`;
    const prev = byKey.get(key);
    if (!prev) {
      byKey.set(key, node);
    } else if ((node.updatedAt || "") > (prev.updatedAt || "")) {
      prev.files = Array.from(new Set([...(prev.files || []), ...(node.files || [])]));
      prev.links = Array.from(new Set([...(prev.links || []), ...(node.links || [])]));
      byKey.set(key, prev);
    } else {
      node.files = Array.from(new Set([...(prev.files || []), ...(node.files || [])]));
      node.links = Array.from(new Set([...(prev.links || []), ...(node.links || [])]));
      byKey.set(key, node);
    }
  }
  let archived = 0;
  const merged = [...byKey.values()].map(node => {
    if (opts.flags.has("archive") && node.status === "completado") {
      const ts = Date.parse(node.updatedAt || node.createdAt || 0);
      if (ts && ts < cutoff) {
        archived++;
        return { ...node, status: "archivado", updatedAt: nowIso() };
      }
    }
    return node;
  });
  graph.nodes = merged;
  syncEdges(graph);
  writeGraph(root, graph);
  console.log(`merge: ${graph.nodes.length} nodos finales, ${archived} archivados`);
  return 0;
}

function cmdValidate(root) {
  const graph = readGraph(root);
  const errors = [];
  const ids = new Set();
  for (const node of graph.nodes) {
    try {
      assertValidNode(node, root);
    } catch (e) {
      errors.push(`${node.id || "?"}: ${e.message}`);
    }
    if (ids.has(node.id)) errors.push(`id duplicado: ${node.id}`);
    ids.add(node.id);
  }
  for (const node of graph.nodes) {
    for (const link of node.links || []) {
      if (!ids.has(link)) errors.push(`enlace roto en ${node.id}: ${link}`);
    }
  }
  for (const edge of graph.edges) {
    if (!edge.from || !edge.to) errors.push(`enlace sin from/to: ${JSON.stringify(edge)}`);
    else if (!ids.has(edge.from) || !ids.has(edge.to)) errors.push(`enlace roto: ${edge.from} -> ${edge.to}`);
  }
  if (errors.length) {
    for (const e of errors) console.error(`- ${e}`);
    console.error(`${errors.length} error(es) en .memoria/graph.json`);
    return 1;
  }
  console.log(`graph.json válido: ${graph.nodes.length} nodos, ${graph.edges.length} enlaces`);
  return 0;
}

function promotePending(root) {
  const pendingRoot = path.join(root, MEM_DIR, PENDING_DIR);
  if (!fs.existsSync(pendingRoot)) return 0;
  const entries = fs.readdirSync(pendingRoot).filter(f => f.endsWith(".json"));
  if (!entries.length) return 0;
  const graph = readGraph(root);
  let count = 0;
  for (const name of entries) {
    const file = path.join(pendingRoot, name);
    try {
      const input = readJSON(file);
      input.skill = input.skill || input.actor;
      const node = buildNode(input, root);
      const existing = graph.nodes.find(n => n.id === node.id) ||
        graph.nodes.find(n => n.skill === node.skill && n.title === node.title);
      if (existing) {
        Object.assign(existing, {
          type: node.type,
          status: node.status,
          summary: node.summary,
          files: Array.from(new Set([...(existing.files || []), ...node.files])),
          links: Array.from(new Set([...(existing.links || []), ...node.links])),
          updatedAt: nowIso(),
        });
      } else {
        graph.nodes.push(node);
      }
      fs.rmSync(file);
      count++;
    } catch (e) {
      process.stderr.write(`memoria/pending/${name}: ${e.message}\n`);
      const invalidDir = path.join(pendingRoot, "invalid");
      fs.mkdirSync(invalidDir, { recursive: true });
      fs.renameSync(file, path.join(invalidDir, name));
    }
  }
  if (count) {
    syncEdges(graph);
    writeGraph(root, graph);
  }
  return count;
}

function cmdHookStop(root) {
  try {
    promotePending(root);
  } catch (e) {
    process.stderr.write(`memoria hook-stop: ${e.message}\n`);
  }
  return 0;
}

// ───────────────────────────── help y dispatch ─────────────────────────────

function help() {
  console.log(`memoria — memoria y contexto del proyecto como grafo de conocimiento

Uso: node .claude/skills/memoria/scripts/memoria.mjs <comando> [opciones]

Comandos:
  init        Inicializa .memoria/ (graph.json, index.md, pending/, config.json),
              enlaza el hook de Stop y copia el workflow de GitHub.
  record      Crea o actualiza un nodo. Mismo --skill + --title actualiza el nodo.
              Opciones: --skill --type --title --summary [--status] [--file ruta]*
              [--link id]* [--id id] [--new] [--root dir]
  query       Lista nodos. Filtros: --type --skill --status --text --limit --json.
  report      Regenera .memoria/index.md y muestra el conteo.
  merge       Deduplica nodos (skill+title) y, con --archive-completed, archiva
              nodos completados con más de --days (30) días.
  validate    Valida graph.json; exit != 0 si hay errores.
  promote     Consolida .memoria/pending/*.json en el grafo.
  hook-stop   Igual que promote para el hook Stop (nunca bloquea).

Tipos: ${NODE_TYPES.join(", ")}
Estados: ${STATUSES.join(", ")}`);
  return 0;
}

async function main() {
  const sub = process.argv[2];
  if (!sub || sub === "--help" || sub === "-h") return help();
  const args = process.argv.slice(3);
  const opts = parseArgv(args);
  if (opts.flags.has("help")) return help();
  const root = opts.root || process.cwd();
  let code = 0;
  switch (sub) {
    case "init": code = cmdInit(root); break;
    case "record": code = cmdRecord(root, args); break;
    case "query": code = cmdQuery(root, args); break;
    case "report": code = cmdReport(root); break;
    case "merge": code = cmdMerge(root, args); break;
    case "validate": code = cmdValidate(root); break;
    case "promote": code = promotePending(root) >= 0 ? 0 : 1; break;
    case "hook-stop": code = cmdHookStop(root); break;
    default:
      console.error(`comando desconocido: ${sub}`);
      help();
      code = 1;
  }
  process.exitCode = code;
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) await main();
