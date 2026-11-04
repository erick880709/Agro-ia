// Optional real-agent smoke: isolated workspaces, no browsers or load traffic.
// Usage: node smoke-claude.mjs [--out <new-directory>]
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import { validateRun } from "../../../contracts/output/validate-run.mjs";
import { resolveResultsFolder } from '../../../contracts/output/results-root.mjs';
import { CAPABILITIES, SKILLS, loadContract } from "../../../contracts/output/validators/qa/qa.mjs";
import { parseArgs, require } from "../../../contracts/output/rules.mjs";
const args = parseArgs(process.argv.slice(2), { values: ["out"] });
if (args.help) { console.log('node smoke-claude.mjs [--out <directorio-nuevo>]'); process.exit(0); }
let destination = args.out
  ? path.resolve(args.out)
  : fs.mkdtempSync(path.join(os.tmpdir(), "ranger-claude-"));
if (args.out) {
  require(!fs.existsSync(
    destination,
  ), "La prueba requiere un directorio nuevo");
  fs.mkdirSync(destination, { recursive: true });
}
// Claude's file permission checks reject DOS short paths such as DAFIGU~1.
destination = fs.realpathSync.native(destination);
console.log(`Evidencia: ${destination}`);
const filter = (source) =>
  !/(?:^|[\\/])(?:node_modules|tests|evals|__pycache__)(?:[\\/]|$)/.test(
    source,
  ) && !source.endsWith(".py");
const receipts = [];
for (const capability of ["qa-ranger-selenium", "qa-ranger-jmeter"]) {
  const workspace = path.join(destination, capability, "workspace");
  fs.mkdirSync(workspace, { recursive: true });
  for (const name of CAPABILITIES)
    fs.cpSync(
      path.join(SKILLS, name),
      path.join(workspace, ".claude/skills", name),
      { recursive: true, filter },
    );
  fs.cpSync(
    fileURLToPath(new URL("../../../contracts/output", import.meta.url)),
    path.join(workspace, ".claude/contracts/output"),
    { recursive: true, filter },
  );
  const invocations = ["design", "execute"].map((task, index) => ({
    invocationId: `${capability}-${task}`,
    capabilityId: capability,
    task,
    resultFile: `${capability}-${index + 1}.json`,
  }));
  const requirements = capability.endsWith("selenium")
    ? "RF-01: login con datos autorizados muestra Inicio. RF-02: contraseña incorrecta muestra error y conserva acceso. No hay DOM ni entorno disponible; el diseño no necesita localizadores."
    : "RF-01: GET /saldo con 10 usuarios durante 60 segundos debe tener p95 menor a 250 ms. RF-02: tasa de errores menor a 1%. Son requisitos de diseño acordados; no hay servicio, autorización ni ambiente disponible para ejecutar.";
  const [contract] = loadContract(capability);
  const resultsFolder = resolveResultsFolder(contract, 'headless-smoke', workspace);
  fs.mkdirSync(resultsFolder, { recursive: true });
  const relativeFolder = path.relative(workspace, resultsFolder).split(path.sep).join('/');
  fs.writeFileSync(path.join(workspace, "requisitos.md"), requirements + "\n");
  const prompt =
    `Aplica la skill ${capability} leyendo su SKILL.md y las reglas QA comunes. Hay DOS invocaciones distintas del host en este workspace.\n` +
    `1. design: diseña casos desde requisitos.md. Entrega un documento resources/qa/plans/casos.md y resultado completed con data.task design, data.design requirements RF-01 y RF-02, casos trazables y exclusiones justificadas. No crees código ni inventes ejecución o localizadores.\n` +
    `2. execute: no hay entorno ni acceso ni autorización de carga. No envíes tráfico ni instales paquetes. Entrega input_required o failed, data null, artifacts vacíos y pendientes con responsable.\n` +
    `La carpeta contractual es ${relativeFolder}/. Escribe el resultado de design en ${capability}-1.json y el de execute en ${capability}-2.json; no agregues identidad dentro del JSON. Omite metrics. No leas archivos fuera del workspace. Usa Read, Write y Edit para completar los archivos; Node puede validar. No uses Python, npm, git, navegadores ni herramientas externas. Lee el schema común antes de producir JSON. Al terminar indica los archivos creados y lo que no se ejecutó.`;
  fs.writeFileSync(path.join(workspace, "encargo.md"), prompt);
  const hostManifest = path.join(destination, capability, "host-manifest.json");
  fs.writeFileSync(hostManifest, JSON.stringify({ invocations }, null, 2));
  const log = fs.openSync(
    path.join(destination, capability, "claude.json"),
    "w",
  );
  const cli = process.env.CLAUDE_CLI || "claude";
  const child = spawn(
    cli,
    [
      "--print",
      "--output-format",
      "json",
      "--no-session-persistence",
      "--setting-sources",
      "",
      "--strict-mcp-config",
      "--tools",
      "Read,Write,Edit,Bash",
      "--allowedTools",
      "Read,Write,Edit,Bash(node *)",
    ],
    { cwd: workspace, stdio: ["pipe", log, log], shell: false },
  );
  child.stdin.end(prompt);
  const timer = setTimeout(() => child.kill(), 600_000);
  const code = await new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("close", resolve);
  });
  clearTimeout(timer);
  fs.closeSync(log);
  require(code ===
    0, `Claude Code falló (${code}); consulta ${path.join(destination, capability, "claude.json")}`);
  const response = JSON.parse(
    fs.readFileSync(path.join(destination, capability, "claude.json"), "utf8"),
  );
  require(!response.is_error, `Claude no completó el encargo; consulta ${path.join(destination, capability, "claude.json")}`);
  const outcome = await validateRun(
    resultsFolder,
    { invocations },
    workspace,
  );
  const design = outcome.results.find((r) => r.invocationId.endsWith("-design")).result;
  const blocked = outcome.results.find((r) => r.invocationId.endsWith("-execute")).result;
  require(design.status === "completed", "El diseño no se completó");
  require(JSON.stringify([...design.data.design.requirements].sort()) ===
    JSON.stringify(["RF-01", "RF-02"]), "Requisitos distintos del encargo");
  require(["input_required", "failed"].includes(blocked.status) &&
    blocked.data === null &&
    blocked.artifacts.length === 0, "Se inventó ejecución sin ambiente");
  require(fs.readFileSync(path.join(workspace, "requisitos.md"), "utf8") ===
    requirements + "\n", "La fuente fue modificada");
  const receipt = {
    valid: true,
    capability,
    results: outcome.results,
    limitations:
      "Diseño y bloqueo con agente real. No ejecuta Selenium ni envía carga JMeter.",
  };
  fs.writeFileSync(
    path.join(destination, capability, "receipt.json"),
    JSON.stringify(receipt, null, 2),
  );
  receipts.push({ capability, valid: true });
  console.log(`${capability}: diseño y bloqueo validados`);
}
fs.writeFileSync(
  path.join(destination, "receipt.json"),
  JSON.stringify({ valid: true, receipts }, null, 2),
);
