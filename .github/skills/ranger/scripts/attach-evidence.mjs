#!/usr/bin/env node
// Enlaza la evidencia guardada por convención en <evidencia>/<CASE-ID>/ a los casos de un CTRF.
// Sirve a runners cuyo JUnit no trae adjuntos (Selenium, Karate UI): junit-to-ctrf genera el CTRF
// y este script agrega video, trace, screenshot y logs que realmente existan en disco.
// Uso: --ctrf <ctrf.json> --evidence <resources/qa/test-results/<runId>> [--project <navegador>] [--project-root <proyecto>]
import fs from "node:fs";
import path from "node:path";
import { caseIdentity } from "../../../contracts/output/validators/qa/ctrf.mjs";
import { require, readJSON, resolveReal, within, isFile, isDirectory, isMain, parseArgs } from "../../../contracts/output/rules.mjs";

const KINDS = [
  [/\.(webm|mp4|mkv|avi|mov)$/i, "video", (ext) => `video/${ext === "mov" ? "quicktime" : ext}`],
  [/\.(png|jpe?g|gif|webp)$/i, "screenshot", (ext) => `image/${ext === "jpg" ? "jpeg" : ext}`],
  [/\.(zip|har)$/i, "trace", (ext) => (ext === "har" ? "application/json" : "application/zip")],
];
function attachment(file, projectRoot) {
  const ext = path.extname(file).slice(1).toLowerCase();
  const [, name, type] = KINDS.find(([pattern]) => pattern.test(file)) ?? [null, "log", () => "text/plain"];
  return { name, contentType: type(ext), path: path.relative(projectRoot, file).split(path.sep).join("/") };
}
function filesUnder(folder) {
  return fs.readdirSync(folder, { withFileTypes: true })
    .flatMap((item) => (item.isDirectory() ? filesUnder(path.join(folder, item.name)) : item.isFile() ? [path.join(folder, item.name)] : []))
    .sort();
}

/**
 * Agrega a cada prueba del CTRF los archivos de <evidencia>/<CASE-ID>/.
 * @returns {{matched: number, missing: string[]}} Casos con evidencia y casos sin carpeta.
 */
export function attachEvidence(report, evidenceDir, projectRoot, { project = null } = {}) {
  projectRoot = resolveReal(projectRoot);
  evidenceDir = resolveReal(path.resolve(projectRoot, evidenceDir));
  require(within(evidenceDir, projectRoot) && isDirectory(evidenceDir), "La carpeta de evidencia debe existir dentro del proyecto");
  require(Array.isArray(report?.results?.tests), "El reporte CTRF no tiene results.tests");
  const ids = report.results.tests.map((test) => caseIdentity(test).id).filter((id) => id !== null);
  require(new Set(ids).size === ids.length, "IDs repetidos: enlaza la evidencia por separado para cada proyecto o intento");
  const missing = [];
  let matched = 0;
  for (const test of report.results.tests) {
    if (project !== null) test.browser = project;
    const { id } = caseIdentity(test);
    require(id === null || /^[A-Za-z0-9-]+$/.test(id), "ID de caso inválido para la carpeta de evidencia");
    const folder = id && path.join(evidenceDir, id);
    if (!folder || !fs.existsSync(folder)) {
      missing.push(id ?? test.name);
      continue;
    }
    const realFolder = resolveReal(folder);
    require(within(realFolder, evidenceDir) && isDirectory(realFolder), "Carpeta de caso fuera de la evidencia o inválida");
    const known = new Set((test.attachments ?? []).map((a) => a.path));
    const files = filesUnder(realFolder).map((f) => {
      const real = resolveReal(f);
      require(within(real, evidenceDir) && isFile(real), "Archivo fuera de la carpeta de evidencia");
      return attachment(real, projectRoot);
    });
    test.attachments = [...(test.attachments ?? []), ...files.filter((a) => !known.has(a.path))];
    matched++;
  }
  return { matched, missing };
}

export function main(argv = process.argv.slice(2)) {
  try {
    const args = parseArgs(argv, { values: ["ctrf", "evidence", "project", "project-root"], required: ["ctrf", "evidence"] });
    if (args.help) {
      console.log("node attach-evidence.mjs --ctrf <ctrf.json> --evidence <carpeta> [--project <navegador>] [--project-root <proyecto>]");
      return 0;
    }
    const root = resolveReal(args["project-root"] ?? process.cwd());
    const file = path.resolve(root, args.ctrf);
    require(within(resolveReal(file), root) && isFile(file), "El CTRF debe existir dentro del proyecto");
    const report = readJSON(file);
    require(report?.reportFormat === "CTRF" && Array.isArray(report.results?.tests), "El archivo no es un reporte CTRF");
    const { matched, missing } = attachEvidence(report, args.evidence, root, { project: args.project ?? null });
    fs.writeFileSync(file, JSON.stringify(report, null, 2));
    console.log(`Evidencia enlazada en ${matched} casos.${missing.length ? ` Sin carpeta de evidencia: ${missing.join(", ")}` : ""}`);
    return 0;
  } catch (error) {
    console.error(error.message);
    return error.exitCode ?? 1;
  }
}
if (isMain(import.meta.url)) process.exitCode = main();
