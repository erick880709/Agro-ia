#!/usr/bin/env node
// add-memoria-section.mjs — Añade (idempotente) la sección "Registro de avance en
// memoria" al final de cada SKILL.md del kit, salvo el de la propia skill memoria.
// Uso: node .claude/skills/memoria/scripts/add-memoria-section.mjs [--check]
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const skillsRoot = path.resolve(__dirname, "..", "..");
const MARKER = "## Registro de avance en memoria";

function sectionFor(name) {
  return [
    "",
    "## Registro de avance en memoria",
    "",
    `Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill`,
    "[`memoria`](../memoria/SKILL.md)) con el payload mínimo",
    `\`{ "skill": "${name}", "type": "avance", "title": "...", "summary": "..." }\`:`,
    "",
    "    node .claude/skills/memoria/scripts/memoria.mjs record \\",
    `      --skill ${name} --type avance --title "..." --summary "..." \\`,
    "      --file <ruta del artefacto> [--link <id-del-nodo-previo>]",
    "",
    "O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop",
    "lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo",
    "(mismo `skill` + `title`), actualízalo en vez de duplicarlo.",
  ].join("\n");
}

function skillDirs() {
  return fs.readdirSync(skillsRoot, { withFileTypes: true })
    .filter(e => e.isDirectory() && fs.existsSync(path.join(skillsRoot, e.name, "SKILL.md")))
    .map(e => e.name)
    .sort();
}

const check = process.argv.includes("--check");
let changed = 0;
let missing = 0;

for (const name of skillDirs()) {
  if (name === "memoria") continue;
  const file = path.join(skillsRoot, name, "SKILL.md");
  const text = fs.readFileSync(file, "utf8");
  if (text.includes(MARKER)) continue;
  if (check) {
    console.log(`falta sección: ${name}/SKILL.md`);
    missing++;
    continue;
  }
  const block = sectionFor(name);
  fs.writeFileSync(file, text.replace(/\s*$/, "\n") + block + "\n", "utf8");
  changed++;
  console.log(`actualizado ${name}/SKILL.md`);
}

if (check) {
  console.log(`${missing} skill(s) sin la sección de memoria.`);
  process.exitCode = missing ? 1 : 0;
} else {
  console.log(`${changed} skill(s) actualizadas.`);
}
