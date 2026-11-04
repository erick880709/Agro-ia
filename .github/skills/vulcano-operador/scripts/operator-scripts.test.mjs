import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { resolveOperatorAdapters } from './adapter-registry.mjs';

const scripts = path.dirname(fileURLToPath(import.meta.url));
const script = name => path.join(scripts, name);
const terraformProfile = {
  required_version: '>= 1.9, < 2.0', provider_constraints: { azurerm: '~> 4.0' },
  module_standard: 'internal', execution_backend: 'azure_devops', test_strategy: 'plan_mock',
  registry_source: 'public', registry_mcp: 'read_only', adoption_mode: 'none'
};
const capabilities = {
  terraform_registry_mcp: 'missing', terraform_style_guide: 'missing', terraform_test: 'missing',
  azure_verified_modules: 'not_required', refactor_module: 'not_required', terraform_search_import: 'disabled'
};

function run(root, name, ...args) {
  return spawnSync(process.execPath, [script(name), '--root', root, ...args], { encoding: 'utf8' });
}

function output(result) { return `${result.stdout}\n${result.stderr}`; }

function parseYaml(file) {
  const result = spawnSync('python', ['-c', 'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))))', file], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

function bobSelection(overrides = {}) {
  return {
    adapter_selection: {
      cloud: 'azure', pipeline: 'azure_devops', remote_operator: 'vulcano-operador', status: 'implemented',
      ...overrides
    }
  };
}

function fixture({ pipeline = 'azure_devops', cloud = 'azure' } = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-operator-'));
  const stateDir = path.join(root, 'resources', '.vulcano');
  fs.mkdirSync(stateDir, { recursive: true });
  const bobPath = path.join(stateDir, 'bob-manifest.yaml');
  const bob = {
    schema_version: 4, project: 'fixture', ...bobSelection({ pipeline, cloud }),
    artifacts: {
      'pipeline-iac': { path: 'infra/pipelines/iac.yml', status: 'generated' },
      'env-qa': { path: 'infra/environments/qa', status: 'generated' }
    }
  };
  fs.writeFileSync(bobPath, JSON.stringify(bob));
  const bobHash = crypto.createHash('sha256').update(fs.readFileSync(bobPath)).digest('hex');
  const operationsPath = path.join(stateDir, 'operations-manifest.yaml');
  fs.writeFileSync(operationsPath, JSON.stringify({
    schema_version: 2, project: 'fixture', updated_at: '2026-07-16',
    source: { bob_manifest: 'resources/.vulcano/bob-manifest.yaml', bob_sha256: bobHash, git_commit: null },
    operator_selection: { platform: pipeline, cloud, status: 'implemented' },
    gate: { status: 'pending', checked_at: null, blockers: [] }, mode: 'reconcile',
    target: { organization: 'org', project: 'fixture', repository: 'repo', branch: 'main' },
    capabilities: { platform_mcp: 'unknown', cloud_mcp: 'unknown' },
    reconciliation: { observed_at: null, tool: null, snapshot_sha256: null },
    actions: {}, validation: { last_run: null, errors: null, warnings: null }
  }));
  return { root, operationsPath };
}

function closedBobFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-operator-init-'));
  const resources = path.join(root, 'resources');
  const stateDir = path.join(resources, '.vulcano');
  const sourceRelative = 'infrastructure-as-code/01-architecture.md';
  const source = path.join(resources, sourceRelative);
  fs.mkdirSync(path.dirname(source), { recursive: true });
  fs.mkdirSync(stateDir, { recursive: true });
  fs.writeFileSync(source, '# Arquitectura\n');
  fs.writeFileSync(path.join(resources, '03-iac-pipelines-index.md'), '# Índice\n');
  fs.writeFileSync(path.join(stateDir, 'manifest.yaml'), JSON.stringify({
    schema_version: 1, project: 'closed fixture', updated_at: '2026-07-16', resources_root: 'resources',
    decisions: { cloud_provider: 'azure', iac: 'terraform', devops_platform: 'azure_devops', terraform: terraformProfile },
    files: { architecture: { path: sourceRelative, status: 'generated' } }
  }));
  const ids = ['bootstrap-backend', 'module-example', 'env-dev', 'env-qa', 'env-prod', 'pipeline-iac', 'pipeline-drift', 'pipeline-app'];
  const artifacts = Object.fromEntries(ids.map((id, index) => [id, {
    path: `omitted/${String(index + 1).padStart(2, '0')}-${id}`,
    status: 'omitted', reason: 'No aplica en fixture', depends_on: [],
    contract: { inputs: [], outputs: [] }, source_docs: [sourceRelative], source_hashes: {},
    validated: { format: null, validate: null, test: null, lint: null, security: null, syntax: null, last_run: null }
  }]));
  fs.writeFileSync(path.join(stateDir, 'bob-manifest.yaml'), JSON.stringify({
    schema_version: 4, project: 'closed fixture', updated_at: '2026-07-16', resources_root: 'resources',
    source_manifest: 'resources/.vulcano/manifest.yaml',
    source_snapshot: { manifest_updated_at: '2026-07-16', cloud_provider: 'azure', iac: 'terraform', devops_platform: 'azure_devops' },
    adapter_selection: { cloud: 'azure', iac: 'terraform', pipeline: 'azure_devops', remote_operator: 'vulcano-operador', status: 'implemented' },
    terraform_profile: terraformProfile,
    preflight: { status: 'ready', checked_at: '2026-07-16T00:00:00Z', conflicts: [], capabilities },
    target_repo: { iac_root: 'infra', pipeline_files: [] }, closure_index: 'resources/03-iac-pipelines-index.md',
    artifacts, operational_pending: [], manual_steps_done: [],
    validation: { last_run: null, errors: null, warnings: null }
  }));
  return { root, stateDir };
}

test('resuelve plataforma y nube sin crear una skill por combinación', () => {
  const resolved = resolveOperatorAdapters(bobSelection());
  assert.equal(resolved.selection.platform, 'azure_devops');
  assert.equal(resolved.selection.cloud, 'azure');
  assert.equal(resolved.platform.allowed_actions.queue_pipeline, 'execute');
});

test('GitHub y AWS resuelven allowlists independientes', () => {
  const future = bobSelection({ pipeline: 'github_actions', cloud: 'aws' });
  const resolved = resolveOperatorAdapters(future);
  assert.equal(resolved.selection.status, 'implemented');
  assert.equal(resolved.platform.allowed_actions.dispatch_workflow, 'execute');
  assert.equal(resolved.cloud.mode, 'read_only_verification');
});

test('GCP resuelve como cloud implementado en modo read_only_verification', () => {
  const resolved = resolveOperatorAdapters(bobSelection({ pipeline: 'github_actions', cloud: 'gcp' }));
  assert.equal(resolved.selection.status, 'implemented');
  assert.equal(resolved.cloud.id, 'gcp');
  assert.equal(resolved.cloud.mode, 'read_only_verification');
});

test('GitLab resuelve acciones configure y execute', () => {
  const resolved = resolveOperatorAdapters(bobSelection({ pipeline: 'gitlab' }));
  assert.equal(resolved.platform.allowed_actions.configure_protected_branch, 'configure');
  assert.equal(resolved.platform.allowed_actions.run_pipeline, 'execute');
});

test('plan aplica el allowlist específico de GitHub y GitLab', () => {
  for (const selection of [
    { pipeline: 'github_actions', cloud: 'aws', allowed: 'dispatch_workflow' },
    { pipeline: 'gitlab', cloud: 'azure', allowed: 'run_pipeline' }
  ]) {
    const { root } = fixture(selection);
    fs.writeFileSync(path.join(root, 'snapshot.json'), '{}');
    let result = run(root, 'record-reconciliation.mjs', '--platform-mcp', 'available', '--cloud-mcp', 'available',
      '--tool', `${selection.pipeline}-mcp`, '--snapshot-file', 'snapshot.json');
    assert.equal(result.status, 0, output(result));
    fs.writeFileSync(path.join(root, 'desired.json'), '{}');
    result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-101', '--type', selection.allowed,
      '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/main', '--desired-file', 'desired.json', '--summary', 'Ejecutar');
    assert.equal(result.status, 0, output(result));
    result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-102', '--type', 'queue_pipeline',
      '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/main', '--desired-file', 'desired.json', '--summary', 'No permitido');
    assert.equal(result.status, 1);
    assert.match(output(result), /Tipo no permitido/);
  }
});

test('init crea schema v2 después del cierre estricto de Bob', () => {
  const { root } = closedBobFixture();
  const result = run(root, 'init-operations-manifest.mjs',
    '--organization', 'org', '--project', 'closed-fixture', '--repository', 'repo', '--branch', 'main');
  assert.equal(result.status, 0, output(result));
  const state = parseYaml(path.join(root, 'resources', '.vulcano', 'operations-manifest.yaml'));
  assert.equal(state.schema_version, 2);
  assert.deepEqual(state.operator_selection, { platform: 'azure_devops', cloud: 'azure', status: 'implemented' });
  assert.equal(state.gate.status, 'pending');
});

test('migra schema v1, traduce capacidades e invalida autorización', () => {
  const { root, stateDir } = closedBobFixture();
  const bobPath = path.join(stateDir, 'bob-manifest.yaml');
  const scope = 'e'.repeat(64);
  fs.writeFileSync(path.join(stateDir, 'operations-manifest.yaml'), JSON.stringify({
    schema_version: 1, project: 'closed fixture', updated_at: '2026-07-16',
    source: { bob_manifest: 'resources/.vulcano/bob-manifest.yaml', bob_sha256: crypto.createHash('sha256').update(fs.readFileSync(bobPath)).digest('hex'), git_commit: null },
    gate: { status: 'ready', checked_at: '2026-07-16', blockers: [] }, mode: 'operate',
    target: { organization: 'org', project: 'closed-fixture', repository: 'repo', branch: 'main' },
    capabilities: { azure_devops_mcp: 'available', azure_mcp: 'missing' },
    reconciliation: { observed_at: '2026-07-16', tool: 'ado', snapshot_sha256: 'a'.repeat(64) },
    actions: { 'OP-ACT-001': {
      type: 'register_pipeline', risk: 'configure', logical_id: 'pipeline-iac', target_ref: 'org/repo/iac',
      desired_sha256: 'b'.repeat(64), observed_sha256: null, diff_summary: ['crear'], scope_hash: scope,
      status: 'authorized', proposed_at: '2026-07-16',
      authorization: { authorized_by: 'user', authorized_at: '2026-07-16', expires_at: '2099-01-01', scope_hash: scope, confirmation_sha256: 'c'.repeat(64) },
      execution: null, verification: null
    } }, validation: { last_run: null, errors: null, warnings: null }
  }));
  const result = run(root, 'init-operations-manifest.mjs', '--migrate');
  assert.equal(result.status, 0, output(result));
  const state = parseYaml(path.join(stateDir, 'operations-manifest.yaml'));
  assert.equal(state.schema_version, 2);
  assert.deepEqual(state.capabilities, { platform_mcp: 'available', cloud_mcp: 'missing' });
  assert.equal(state.actions['OP-ACT-001'].status, 'proposed');
  assert.equal(state.actions['OP-ACT-001'].authorization, null);
  assert.equal(state.gate.status, 'pending');
});

test('ciclo completo conserva gates, allowlist y evidencia', () => {
  const { root, operationsPath } = fixture();
  fs.writeFileSync(path.join(root, 'snapshot.json'), JSON.stringify({ pipelines: [] }));
  let result = run(root, 'record-reconciliation.mjs', '--platform-mcp', 'available', '--cloud-mcp', 'available',
    '--tool', 'azure-devops-mcp', '--snapshot-file', 'snapshot.json');
  assert.equal(result.status, 0, output(result));
  fs.writeFileSync(path.join(root, 'desired.json'), JSON.stringify({ name: 'iac' }));
  result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-001', '--type', 'register_pipeline',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/fixture/repo/iac', '--desired-file', 'desired.json', '--summary', 'Crear');
  assert.equal(result.status, 0, output(result));
  fs.writeFileSync(path.join(root, 'confirmation.txt'), 'Autorizo OP-ACT-001.');
  assert.equal(run(root, 'authorize-operation.mjs', '--id', 'OP-ACT-001', '--authorized-by', 'user', '--confirmation-file', 'confirmation.txt').status, 0);
  let state = parseYaml(operationsPath);
  const scope = state.actions['OP-ACT-001'].scope_hash;
  assert.equal(run(root, 'begin-operation.mjs', '--id', 'OP-ACT-001').status, 0);
  const evidence = tool => ({ tool, result: 'succeeded', scope_hash: scope, request_sha256: 'a'.repeat(64), response_sha256: 'b'.repeat(64), external_id: '42' });
  fs.writeFileSync(path.join(root, 'execution.json'), JSON.stringify(evidence('ado_create')));
  assert.equal(run(root, 'record-operation-evidence.mjs', '--id', 'OP-ACT-001', '--phase', 'execution', '--evidence-file', 'execution.json').status, 0);
  fs.writeFileSync(path.join(root, 'verification.json'), JSON.stringify(evidence('ado_get')));
  assert.equal(run(root, 'record-operation-evidence.mjs', '--id', 'OP-ACT-001', '--phase', 'verification', '--evidence-file', 'verification.json').status, 0);
  state = parseYaml(operationsPath);
  assert.equal(state.actions['OP-ACT-001'].status, 'verified');
  result = run(root, 'validate-operations-manifest.mjs', '--strict');
  assert.equal(result.status, 0, output(result));
});

function readyFixture() {
  const { root, operationsPath } = fixture();
  fs.writeFileSync(path.join(root, 'snapshot.json'), '{}');
  assert.equal(run(root, 'record-reconciliation.mjs', '--platform-mcp', 'available', '--cloud-mcp', 'available',
    '--tool', 'azure-devops-mcp', '--snapshot-file', 'snapshot.json').status, 0);
  fs.writeFileSync(path.join(root, 'desired.json'), '{}');
  return { root, operationsPath };
}

function verifyAction(root, operationsPath, id) {
  const state = parseYaml(operationsPath);
  const scope = state.actions[id].scope_hash;
  fs.writeFileSync(path.join(root, `confirmation-${id}.txt`), `Autorizo ${id}.`);
  assert.equal(run(root, 'authorize-operation.mjs', '--id', id, '--authorized-by', 'user',
    '--confirmation-file', `confirmation-${id}.txt`).status, 0);
  assert.equal(run(root, 'begin-operation.mjs', '--id', id).status, 0);
  const evidence = { tool: 'ado_deploy', result: 'succeeded', scope_hash: scope, request_sha256: 'a'.repeat(64), response_sha256: 'b'.repeat(64), external_id: '1' };
  fs.writeFileSync(path.join(root, `execution-${id}.json`), JSON.stringify(evidence));
  assert.equal(run(root, 'record-operation-evidence.mjs', '--id', id, '--phase', 'execution', '--evidence-file', `execution-${id}.json`).status, 0);
  fs.writeFileSync(path.join(root, `verification-${id}.json`), JSON.stringify(evidence));
  assert.equal(run(root, 'record-operation-evidence.mjs', '--id', id, '--phase', 'verification', '--evidence-file', `verification-${id}.json`).status, 0);
}

test('progresión de ambiente: --environment es obligatorio para tipos que promueven despliegue', () => {
  const { root } = readyFixture();
  const result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-201', '--type', 'queue_pipeline',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/pipeline-iac', '--desired-file', 'desired.json', '--summary', 'Queue');
  assert.equal(result.status, 1);
  assert.match(output(result), /--environment .* es obligatorio/);
});

test('progresión de ambiente: bloquea promover a qa sin una acción verified en dev', () => {
  const { root } = readyFixture();
  const result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-202', '--type', 'queue_pipeline',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/pipeline-iac', '--environment', 'qa',
    '--desired-file', 'desired.json', '--summary', 'Queue qa');
  assert.equal(result.status, 1);
  assert.match(output(result), /Progresión bloqueada.*dev/);
});

test('progresión de ambiente: dev no requiere predecesor; qa se habilita tras dev verified; prod sigue bloqueado sin qa', () => {
  const { root, operationsPath } = readyFixture();
  let result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-203', '--type', 'queue_pipeline',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/pipeline-iac', '--environment', 'dev',
    '--desired-file', 'desired.json', '--summary', 'Queue dev');
  assert.equal(result.status, 0, output(result));

  // Sin dev verified todavía, qa sigue bloqueado (dev solo está "proposed", no "verified").
  result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-204', '--type', 'queue_pipeline',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/pipeline-iac', '--environment', 'qa',
    '--desired-file', 'desired.json', '--summary', 'Queue qa');
  assert.equal(result.status, 1);
  assert.match(output(result), /Progresión bloqueada.*dev/);

  verifyAction(root, operationsPath, 'OP-ACT-203');

  // Ahora que dev quedó verified, promover a qa debe funcionar.
  result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-205', '--type', 'queue_pipeline',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/pipeline-iac', '--environment', 'qa',
    '--desired-file', 'desired.json', '--summary', 'Queue qa');
  assert.equal(result.status, 0, output(result));

  // Saltar directo a prod sin que qa esté verified debe seguir bloqueado. Se usa queue_pipeline
  // (no approve_deployment) porque ese tipo ya falla antes por missing_capability — ver el test
  // dedicado más abajo — y aquí se quiere aislar la progresión, no esa otra brecha.
  result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-206', '--type', 'queue_pipeline',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/pipeline-iac', '--environment', 'prod',
    '--desired-file', 'desired.json', '--summary', 'Aprobar prod');
  assert.equal(result.status, 1);
  assert.match(output(result), /Progresión bloqueada.*qa/);
});

test('acciones sin herramienta MCP real (create_environment, update_variable_group, configure_branch_policy, approve_deployment, tag_release) fallan con missing_capability', () => {
  const { root } = readyFixture();
  const types = ['create_environment', 'update_variable_group', 'configure_branch_policy', 'tag_release'];
  for (let index = 0; index < types.length; index += 1) {
    const result = run(root, 'plan-operation.mjs', '--id', `OP-ACT-${301 + index}`, '--type', types[index],
      '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/pipeline-iac', '--desired-file', 'desired.json', '--summary', 'Probar');
    assert.equal(result.status, 1, output(result));
    assert.match(output(result), /missing_capability/);
  }
  const approveResult = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-310', '--type', 'approve_deployment',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/pipeline-iac', '--environment', 'prod',
    '--desired-file', 'desired.json', '--summary', 'Probar');
  assert.equal(approveResult.status, 1, output(approveResult));
  assert.match(output(approveResult), /missing_capability/);
});

test('rechaza acción fuera del allowlist y archivos con secretos', () => {
  const { root } = fixture();
  fs.writeFileSync(path.join(root, 'snapshot.json'), '{}');
  assert.equal(run(root, 'record-reconciliation.mjs', '--platform-mcp', 'available', '--cloud-mcp', 'missing', '--tool', 'ado', '--snapshot-file', 'snapshot.json').status, 0);
  fs.writeFileSync(path.join(root, 'desired.json'), JSON.stringify({ access_token: 'not-allowed' }));
  let result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-002', '--type', 'register_pipeline',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/iac', '--desired-file', 'desired.json', '--summary', 'Crear');
  assert.equal(result.status, 1);
  assert.match(output(result), /clave sensible/);
  fs.writeFileSync(path.join(root, 'desired.json'), JSON.stringify({ aws_access_key_id: 'not-allowed' }));
  result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-004', '--type', 'register_pipeline',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/iac', '--desired-file', 'desired.json', '--summary', 'Crear');
  assert.equal(result.status, 1);
  assert.match(output(result), /clave sensible/);
  fs.writeFileSync(path.join(root, 'desired.json'), '{}');
  result = run(root, 'plan-operation.mjs', '--id', 'OP-ACT-003', '--type', 'approve_production',
    '--logical-id', 'pipeline-iac', '--target-ref', 'org/repo/iac', '--desired-file', 'desired.json', '--summary', 'Aprobar');
  assert.equal(result.status, 1);
  assert.match(output(result), /Tipo no permitido/);
});
