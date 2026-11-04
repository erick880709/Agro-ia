import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { prepare, check, digest, resultsFolder, SKILLS, CAPABILITIES, readJSON } from '../scripts/evaluate.mjs';
function destination(t) { const root = fs.mkdtempSync(path.join(os.tmpdir(), 'qa-eval-node-')); t.after(() => { assert(path.basename(root).startsWith('qa-eval-node-')); fs.rmSync(root, { recursive: true, force: true }); }); return path.join(root, 'evaluation'); }
function output(dest, example) {
  const value = readJSON(path.join(SKILLS, 'qa-ranger-plan-pruebas/contracts/examples', example)), invocation = readJSON(path.join(dest, 'host-manifest.json')).invocations[0];
  const workspace = path.join(dest, 'workspace');
  for (const item of value.artifacts) { delete item.content; delete item.uri; item.path = `resources/qa/plans/${item.id}.md`; const file = path.join(workspace, item.path); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, 'Salida sintética para probar el evaluador', 'utf8'); }
  const file = path.join(resultsFolder(dest), invocation.resultFile); fs.writeFileSync(file, JSON.stringify(value)); return { file, value };
}
test('evaluate: todos los escenarios registrados conservan fuentes fuera de oráculos', t => {
  const dest = destination(t);
  for (const skill of CAPABILITIES) for (const scenario of readJSON(path.join(SKILLS, skill, 'evals/evals.json')).evals) {
    const folder = path.join(path.dirname(dest), `${skill}-${scenario.id}`); prepare(skill, scenario.id, folder);
    assert.deepEqual(readJSON(path.join(folder, 'oracle.json')).oracle, scenario.oracle);
    const invocation = readJSON(path.join(folder, 'host-manifest.json')).invocations[0];
    assert.equal(invocation.capabilityId, scenario.oracle.capabilityId); assert.equal(invocation.resultFile, `${scenario.oracle.capabilityId}-1.json`);
    assert.equal(invocation.task, scenario.oracle.task); assert.equal(readJSON(path.join(folder, 'oracle.json')).runId, `eval-${skill}-${scenario.id}`);
    for (const source of readJSON(path.join(folder, 'oracle.json')).inputs) assert.equal(digest(path.join(folder, 'workspace', source.path)), source.sha256);
    assert.equal(fs.existsSync(path.join(folder, 'workspace/oracle.json')), false);
    assert.equal(fs.existsSync(path.join(folder, 'workspace/.claude/skills', skill, 'evals/evals.json')), false);
    assert.equal(path.basename(resultsFolder(folder)), `eval-${skill}-${scenario.id}`);
  }
});
test('evaluate: trace conserva reproducer sin copiar oracle', t => {
  const dest = destination(t); prepare('qa-ranger-playwright', 3, dest);
  assert(fs.existsSync(path.join(dest, 'workspace/.claude/skills/qa-ranger-playwright/evals/prepare_trace.py')));
  assert.throws(() => prepare('qa-ranger-playwright', 3, dest), /directorio nuevo/);
});
test('evaluate: copia las suites de las plantillas sin copiar tests internos ni oráculos', t => {
  const dest = destination(t); prepare('qa-ranger-plan-pruebas', 2, dest);
  const skills = path.join(dest, 'workspace/.claude/skills');
  assert(fs.existsSync(path.join(skills, 'qa-ranger-playwright/templates/project/tests/login.spec.ts')));
  assert(fs.existsSync(path.join(skills, 'qa-ranger-selenium/templates/python-pytest/tests/test_login.py')));
  for (const capability of CAPABILITIES) {
    assert.equal(fs.existsSync(path.join(skills, capability, 'tests')), false);
    assert.equal(fs.existsSync(path.join(skills, capability, 'evals/evals.json')), false);
  }
});
test('evaluate: waiting_input no oculta documentación inventada', async t => {
  const dest = destination(t); prepare('qa-ranger-plan-pruebas', 2, dest); output(dest, 'qa-ranger-plan-pruebas-sin-requisitos.json');
  assert.equal((await check(dest)).valid, true);
  const file = path.join(dest, 'workspace/resources/qa/plans/inventado.md'); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, 'Requisitos inventados');
  await assert.rejects(check(dest), /requisitos inexistentes/); assert.equal(fs.existsSync(path.join(dest, 'receipt.json')), false);
});
test('evaluate: contrato válido no oculta modificación de fuentes ni conserva recibo previo', async t => {
  const dest = destination(t); prepare('qa-ranger-plan-pruebas', 1, dest); const { file, value } = output(dest, 'qa-ranger-plan-pruebas-completo.json');
  const requirements = ['RF-01', 'CA-01', 'RF-02', 'CA-02', 'RF-03', 'CA-03']; value.data.deliverables = ['test_plan']; value.artifacts = value.artifacts.filter(item => item.kind === 'test_plan');
  Object.assign(value.data, { requirements, cases: [{ id: 'TC-01', requirements, expectedResult: 'Resultado sintético' }], exclusions: [] }); fs.writeFileSync(file, JSON.stringify(value));
  assert.equal((await check(dest)).valid, true); fs.writeFileSync(path.join(dest, 'workspace/requisitos-transferencias.md'), 'Fuente alterada');
  await assert.rejects(check(dest), /Fuente modificada/); assert.equal(fs.existsSync(path.join(dest, 'receipt.json')), false);
});
test('evaluate: CLI prepara y comprueba sin Python ni procesos auxiliares', t => {
  const dest = destination(t), script = fileURLToPath(new URL('../scripts/evaluate.mjs', import.meta.url));
  const cli = (...args) => spawnSync(process.execPath, [script, ...args], { encoding: 'utf8', env: { ...process.env, PATH: path.dirname(process.execPath), PYTHON: 'missing-python' } });
  const prepared = cli('prepare', 'qa-ranger-plan-pruebas', '2', dest); assert.equal(prepared.status, 0, prepared.stdout + prepared.stderr);
  assert.equal(JSON.parse(prepared.stdout).workspace, path.join(dest, 'workspace'));
  output(dest, 'qa-ranger-plan-pruebas-sin-requisitos.json'); const checked = cli('check', dest);
  assert.equal(checked.status, 0, checked.stdout + checked.stderr); assert.equal(JSON.parse(checked.stdout).valid, true);
  const invalid = cli('prepare', 'qa-ranger-plan-pruebas', '2', dest); assert.equal(invalid.status, 1); assert.equal(JSON.parse(invalid.stdout).valid, false);
  assert.equal(cli('prepare').status, 2); assert.equal(cli('--help').status, 0);
});
