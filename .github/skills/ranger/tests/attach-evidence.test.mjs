import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { attachEvidence, main } from '../scripts/attach-evidence.mjs';
import { executionFromCtrf } from '../../../contracts/output/validators/qa/ctrf.mjs';

function project(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'qa-attachments-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}
test('Adjuntos: enlaza archivos existentes, conserva los anteriores y no duplica evidencia', t => {
  const root = project(t), dir = 'resources/qa/test-results/run';
  fs.mkdirSync(path.join(root, dir, 'TC-01'), { recursive: true });
  for (const name of ['video.webm', 'trace.zip', 'screenshot.png', 'consola.log'])
    fs.writeFileSync(path.join(root, dir, 'TC-01', name), 'Fixture ficticia.');
  const report = { reportFormat: 'CTRF', results: { tests: [{ name: 'TC-01 [high]', status: 'passed' }, { name: 'TC-02 [high]', status: 'skipped' }] } };
  assert.deepEqual(attachEvidence(report, dir, root, { project: 'chrome' }), { matched: 1, missing: ['TC-02'] });
  assert.deepEqual(report.results.tests[0].attachments.map(a => a.name).sort(), ['log', 'screenshot', 'trace', 'video']);
  attachEvidence(report, dir, root);
  assert.equal(report.results.tests[0].attachments.length, 4);
  assert.equal(report.results.tests[0].browser, 'chrome');
  fs.writeFileSync(path.join(root, 'ctrf.json'), JSON.stringify(report));
  assert.equal(main(['--ctrf', 'ctrf.json', '--evidence', dir, '--project-root', root]), 0);
  const repeated = structuredClone(report);
  repeated.results.tests.push({ name: 'TC-01 [high]', status: 'passed', browser: 'firefox' });
  assert.throws(() => attachEvidence(repeated, dir, root), /IDs repetidos/);
  report.results.tests[0].extra = { annotations: [{ type: 'case', description: '../fuera' }] };
  assert.throws(() => attachEvidence(report, dir, root), /ID de caso inválido/);
});
test('CTRF: verificación usa los casos de la suite y excluye preparación del resumen', t => {
  const root = project(t);
  const report = { results: { summary: { passed: 999, failed: 0 }, tests: [
    { name: 'preparación', status: 'passed', browser: 'setup' },
    { name: 'unidad', status: 'failed', suite: ['com.example', 'PreciosTest'] },
  ] } };
  const opts = { evidencePolicy: { level: 'unit', required: ['raw_results'], override: null } };
  assert.deepEqual(executionFromCtrf('ctrf', report, root, opts).summary, { passed: 0, failed: 1, skipped: 0 });
  assert.equal(executionFromCtrf('ctrf', report, root, opts).execution.cases[0].project, '');
  report.results.tests.pop();
  assert.deepEqual(executionFromCtrf('ctrf', report, root, opts).summary, { passed: 0, failed: 0, skipped: 0 });
});
