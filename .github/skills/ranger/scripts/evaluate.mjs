// Prepara evaluaciones y comprueba entregas. No inicia agentes ni califica razonamiento.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { parseArgs } from 'node:util';
import { validateRun } from '../../../contracts/output/validate-run.mjs';
import { ContractError, require, readJSON, isMain } from '../../../contracts/output/rules.mjs';
import { resolveResultsFolder } from '../../../contracts/output/results-root.mjs';

export { ContractError, readJSON };
export const SKILLS = fileURLToPath(new URL('../../', import.meta.url));
export const OUTPUT = fileURLToPath(new URL('../../../contracts/output/', import.meta.url));
export const CAPABILITIES = Object.keys(readJSON(path.join(OUTPUT, 'validators.json')));
export function digest(file) { return createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
function writeJSON(file, value) { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, JSON.stringify(value, null, 2), 'utf8'); }
function workspaceFilter(sourceRoot) {
  return source => {
    const relative = path.relative(sourceRoot, source).split(path.sep).join('/');
    const first = relative.split('/')[0];
    // Excluye tests/oráculos de la skill, conserva los tests de las plantillas.
    return !['evals', 'tests'].includes(first)
      && !/(?:^|\/)(?:__pycache__|node_modules)(?:\/|$)/.test(relative)
      && !relative.endsWith('.pyc');
  };
}
function filesUnder(folder) { if (!fs.existsSync(folder)) return []; return fs.readdirSync(folder, { withFileTypes: true }).flatMap(item => item.isDirectory() ? filesUnder(path.join(folder, item.name)) : item.isFile() ? [path.join(folder, item.name)] : []); }
export function resultsFolder(destination) {
  const workspace = path.join(path.resolve(destination), 'workspace'), manifest = readJSON(path.join(destination, 'host-manifest.json'));
  const invocation = manifest.invocations[0], { runId } = readJSON(path.join(destination, 'oracle.json'));
  const contract = readJSON(path.join(workspace, '.claude/skills', invocation.capabilityId, 'contracts/output-contract.json'));
  return resolveResultsFolder(contract, runId, workspace);
}
export function prepare(skill, caseId, destination) {
  const catalog = readJSON(path.join(SKILLS, skill, 'evals/evals.json')), scenario = catalog.evals.find(item => item.id === caseId);
  require(scenario, 'Caso de evaluación inexistente');
  destination = path.resolve(destination);
  require(!fs.existsSync(destination), 'La evaluación requiere un directorio nuevo');
  const workspace = path.join(destination, 'workspace'); fs.mkdirSync(workspace, { recursive: true });
  for (const capability of CAPABILITIES) {
    const source = path.join(SKILLS, capability);
    fs.cpSync(source, path.join(workspace, '.claude/skills', capability), { recursive: true, filter: workspaceFilter(source) });
  }
  if (skill === 'qa-ranger-playwright' && caseId === 3) for (const relative of ['prepare_trace.py', 'files/transferencia-flaky.spec.ts', 'files/banca-demo/server.js']) {
    const target = path.join(workspace, '.claude/skills', skill, 'evals', relative); fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(SKILLS, skill, 'evals', relative), target);
  }
  fs.cpSync(OUTPUT, path.join(workspace, '.claude/contracts/output'), { recursive: true, filter: workspaceFilter(OUTPUT) });
  const inputs = [];
  for (const relative of scenario.files ?? []) {
    const source = path.resolve(SKILLS, skill, relative); require(fs.existsSync(source) && fs.statSync(source).isFile(), `Fixture inexistente: ${relative}`);
    const target = path.join(workspace, path.basename(source)); require(!fs.existsSync(target), `Nombre de fixture duplicado: ${path.basename(source)}`);
    fs.copyFileSync(source, target); inputs.push({ path: path.relative(workspace, target).split(path.sep).join('/'), sha256: digest(target) });
  }
  const runId = `eval-${skill}-${caseId}`, oracle = scenario.oracle;
  const invocation = { invocationId: `invoke-${caseId}`, capabilityId: oracle.capabilityId, task: oracle.task, resultFile: `${oracle.capabilityId}-1.json` };
  for (const field of ['evidencePolicy', 'deliverables']) if (Object.hasOwn(oracle, field)) invocation[field] = oracle[field];
  writeJSON(path.join(destination, 'host-manifest.json'), { invocations: [invocation] });
  writeJSON(path.join(destination, 'oracle.json'), { skill, id: caseId, runId, oracle, inputs });
  const folder = path.relative(workspace, resultsFolder(destination)).split(path.sep).join('/');
  fs.mkdirSync(path.join(workspace, folder), { recursive: true });
  let prompt = `Aplica $${skill} en este workspace.\n\n${scenario.prompt}\n\nFuentes locales: ${inputs.map(item => item.path).join(', ') || 'no hay fuentes disponibles'}.\nEl host pide el resultado contractual en ${folder}/${invocation.resultFile} (tarea: ${invocation.task}).\nNo leas los oráculos de evaluación fuera de este workspace. Declara lo que ejecutaste realmente.\n`;
  if (Object.hasOwn(invocation, 'deliverables')) prompt += `Entregables solicitados: ${JSON.stringify(invocation.deliverables)}.\n`;
  if (Object.hasOwn(invocation, 'evidencePolicy')) prompt += `Política de evidencia del host: ${JSON.stringify(invocation.evidencePolicy)}.\n`;
  fs.writeFileSync(path.join(workspace, 'encargo.md'), prompt, 'utf8');
  return { workspace, request: path.join(workspace, 'encargo.md') };
}
export async function check(destination) {
  destination = path.resolve(destination); fs.rmSync(path.join(destination, 'receipt.json'), { force: true });
  const workspace = path.join(destination, 'workspace'), scenario = readJSON(path.join(destination, 'oracle.json')), oracle = scenario.oracle;
  const folder = resultsFolder(destination), outcome = await validateRun(folder, readJSON(path.join(destination, 'host-manifest.json')), workspace), { invocationId, resultFile, result } = outcome.results[0];
  if (Object.hasOwn(oracle, 'status')) require((Array.isArray(oracle.status) ? oracle.status : [oracle.status]).includes(result.status), 'Estado distinto del esperado para el encargo');
  if (oracle.protectFixtures) for (const item of scenario.inputs) { const file = path.join(workspace, item.path); require(fs.existsSync(file) && fs.statSync(file).isFile() && digest(file) === item.sha256, `Fuente modificada: ${item.path}`); }
  if (oracle.noSource) {
    require(result.data === null && !result.artifacts.length, 'Se fabricó una entrega sin requisitos');
    require(!filesUnder(path.join(workspace, 'resources')).some(file => file.endsWith('.md')), 'Se creó documentación basada en requisitos inexistentes');
  }
  if (Object.hasOwn(oracle, 'requirements') && result.status === 'completed') {
    const design = result.capabilityId === 'qa-ranger-plan-pruebas' ? result.data : result.data.design ?? {};
    require(JSON.stringify([...new Set(design.requirements ?? [])].sort()) === JSON.stringify([...new Set(oracle.requirements)].sort()), 'Trazabilidad distinta de las fuentes');
  }
  if (Object.hasOwn(oracle, 'deliverables')) {
    const kinds = [...new Set(result.artifacts.filter(item => ['test_plan', 'test_runbook'].includes(item.kind)).map(item => item.kind))].sort();
    require(JSON.stringify(kinds) === JSON.stringify([...new Set(oracle.deliverables)].sort()), 'Se omitió o agregó un documento fuera del encargo');
  }
  const receipt = { valid: true, skill: scenario.skill, caseId: scenario.id, evaluatedAt: new Date().toISOString(), invocation: { runId: scenario.runId, invocationId, resultFile },
    results: Object.fromEntries(fs.readdirSync(folder).filter(file => file.endsWith('.json')).map(file => [file, digest(path.join(folder, file))])),
    artifacts: Object.fromEntries(result.artifacts.filter(item => Object.hasOwn(item, 'path')).map(item => [item.path, digest(path.join(workspace, item.path))])),
    checks: 'Contrato, correlación, alcance documental, trazabilidad declarada y fuentes protegidas', limitations: 'No demuestra por sí solo exactitud semántica, exploración UI o ejecución de suites.' };
  writeJSON(path.join(destination, 'receipt.json'), receipt); return receipt;
}
export async function main(argv = process.argv.slice(2)) {
  try {
    if (argv.includes('--help') || argv.includes('-h')) { console.log('node evaluate.mjs prepare <skill> <case_id> <destination>\nnode evaluate.mjs check <destination>'); return 0; }
    const [action, ...rest] = argv;
    let positions;
    try {
      positions = parseArgs({ args: rest, allowPositionals: true }).positionals;
      if (!['prepare', 'check'].includes(action) || positions.length !== (action === 'prepare' ? 3 : 1)) throw new Error('acción o argumentos no válidos');
      if (action === 'prepare' && (!CAPABILITIES.includes(positions[0]) || !/^-?\d+$/.test(positions[1]))) throw new Error('skill o case_id no válido');
    } catch (error) { error.exitCode = 2; throw error; }
    const outcome = action === 'prepare' ? prepare(positions[0], Number(positions[1]), positions[2]) : await check(positions[0]);
    console.log(JSON.stringify(outcome, null, 2)); return 0;
  } catch (error) { if (error.exitCode === 2) { console.error(error.message); return 2; } console.log(JSON.stringify({ valid: false, errors: [error.message] })); return 1; }
}
if (isMain(import.meta.url)) process.exitCode = await main();
