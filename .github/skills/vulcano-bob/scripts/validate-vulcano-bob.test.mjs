import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const validator = path.join(path.dirname(fileURLToPath(import.meta.url)), 'validate-vulcano-bob.mjs');
const assetsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'assets');
const logicalIds = [
  'bootstrap-backend', 'module-networking', 'module-key-vault', 'module-observability-base',
  'module-database', 'module-compute', 'module-observability-rules', 'env-dev', 'env-qa',
  'env-prod', 'pipeline-iac', 'pipeline-drift', 'pipeline-app'
];
const terraformProfile = {
  required_version: '>= 1.9, < 2.0', provider_constraints: { azurerm: '~> 4.0' },
  module_standard: 'internal', execution_backend: 'azure_devops', test_strategy: 'plan_mock',
  registry_source: 'public', registry_mcp: 'read_only', adoption_mode: 'none'
};
const capabilities = {
  terraform_registry_mcp: 'missing', terraform_style_guide: 'missing', terraform_test: 'missing',
  azure_verified_modules: 'not_required', refactor_module: 'not_required', terraform_search_import: 'disabled'
};

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-'));
  const resources = path.join(root, 'resources');
  fs.mkdirSync(path.join(resources, '.vulcano'), { recursive: true });
  fs.mkdirSync(path.join(resources, 'infrastructure-as-code'), { recursive: true });
  fs.writeFileSync(path.join(resources, 'infrastructure-as-code', '01-architecture.md'), '# Arquitectura valida\n');
  return { root, resources };
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
}

function vulcanoManifest() {
  return {
    schema_version: 1,
    project: 'fixture',
    updated_at: '2026-07-16',
    resources_root: 'resources',
    decisions: { cloud_provider: 'azure', iac: 'terraform', devops_platform: 'azure_devops', terraform: terraformProfile },
    files: {
      architecture: { path: 'infrastructure-as-code/01-architecture.md', status: 'generated' }
    }
  };
}

function bobManifest(overrides = {}) {
  const artifacts = Object.fromEntries(logicalIds.map((logicalId, index) => [logicalId, {
    path: `generated/${String(index + 1).padStart(2, '0')}-${logicalId}`,
    status: 'pending',
    depends_on: [],
    contract: { inputs: ['input'], outputs: ['output'] },
    source_docs: ['infrastructure-as-code/01-architecture.md'],
    source_hashes: {},
    validated: { format: null, validate: null, test: null, lint: null, security: null, syntax: null, last_run: null }
  }]));
  return {
    schema_version: 4,
    project: 'fixture',
    updated_at: '2026-07-16',
    resources_root: 'resources',
    source_manifest: 'resources/.vulcano/manifest.yaml',
    source_snapshot: {
      manifest_updated_at: '2026-07-16',
      cloud_provider: 'azure',
      iac: 'terraform',
      devops_platform: 'azure_devops'
    },
    adapter_selection: {
      cloud: 'azure', iac: 'terraform', pipeline: 'azure_devops',
      remote_operator: 'vulcano-operador', status: 'implemented'
    },
    terraform_profile: terraformProfile,
    preflight: { status: 'ready', checked_at: '2026-07-16', conflicts: [], capabilities },
    target_repo: { iac_root: 'infra', pipeline_files: [] },
    closure_index: 'resources/03-iac-pipelines-index.md',
    artifacts,
    operational_pending: [],
    manual_steps_done: [],
    validation: { last_run: null, errors: null, warnings: null },
    ...overrides
  };
}

function run(root, ...extraArgs) {
  const withTools = extraArgs.includes('--with-tools');
  const forwarded = extraArgs.filter(arg => arg !== '--with-tools');
  return spawnSync(process.execPath, [validator, '--root', root, ...(withTools ? [] : ['--skip-tools']), ...forwarded], {
    encoding: 'utf8'
  });
}

function output(result) {
  return `${result.stdout}\n${result.stderr}`;
}

test('falla cuando faltan ambos manifiestos', () => {
  const { root } = fixture();
  const result = run(root);
  assert.equal(result.status, 1);
  assert.match(output(result), /manifest\.yaml de Vulcano/);
  assert.match(output(result), /bob-manifest\.yaml/);
});

test('acepta un manifiesto no estricto con artefactos pendientes', () => {
  const { root, resources } = fixture();
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcanoManifest());
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bobManifest());
  const result = run(root);
  assert.equal(result.status, 0, output(result));
  assert.match(output(result), /0 error\(es\)/);
});

test('conflict siempre es bloqueante', () => {
  const { root, resources } = fixture();
  const bob = bobManifest();
  bob.artifacts['module-networking'].status = 'conflict';
  bob.artifacts['module-networking'].reason = 'Contrato ciclico';
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcanoManifest());
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bob);
  const result = run(root);
  assert.equal(result.status, 1);
  assert.match(output(result), /Artefacto en conflict: module-networking/);
});

test('rechaza rutas que salen del workspace', () => {
  const { root, resources } = fixture();
  const bob = bobManifest();
  bob.artifacts['module-networking'].path = '../escape';
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcanoManifest());
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bob);
  const result = run(root);
  assert.equal(result.status, 1);
  assert.match(output(result), /sale del directorio permitido/);
});

test('el cierre estricto rechaza pendientes', () => {
  const { root, resources } = fixture();
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcanoManifest());
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bobManifest());
  const result = run(root, '--strict-completeness');
  assert.equal(result.status, 1);
  assert.match(output(result), /sigue pending/);
});

test('rechaza deployment jobs sin pasos', () => {
  const { root, resources } = fixture();
  const source = path.join(resources, 'infrastructure-as-code', '01-architecture.md');
  fs.writeFileSync(path.join(root, 'azure-pipelines.yml'), 'stages:\n  - stage: Deploy\n    jobs:\n      - deployment: EmptyDeploy\n        environment: dev\n');
  const bob = bobManifest();
  bob.target_repo.pipeline_files = ['azure-pipelines.yml'];
  bob.artifacts['pipeline-app'] = {
    path: 'azure-pipelines.yml',
    status: 'generated',
    depends_on: [],
    contract: { inputs: ['serviceConnection'], outputs: ['app-package'] },
    source_docs: ['infrastructure-as-code/01-architecture.md'],
    source_hashes: {
      'infrastructure-as-code/01-architecture.md': crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex')
    },
    validated: { format: null, validate: null, test: null, lint: null, security: null, syntax: true, last_run: '2026-07-16' }
  };
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcanoManifest());
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bob);
  const result = run(root);
  assert.equal(result.status, 1);
  assert.match(output(result), /no tiene strategy\.runOnce\.deploy\.steps/);
});

test('rechaza una combinacion sin adaptador', () => {
  const { root, resources } = fixture();
  const vulcano = vulcanoManifest();
  vulcano.decisions.iac = 'bicep';
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcano);
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bobManifest());
  const result = run(root);
  assert.equal(result.status, 1);
  assert.match(output(result), /unsupported_adapter/);
});

test('detecta el ciclo declarado por la definicion fuente', () => {
  const { root, resources } = fixture();
  fs.writeFileSync(
    path.join(resources, 'infrastructure-as-code', '06-modules.md'),
    '# Modulos\nExiste una dependencia circular que se resuelve con depends_on.\n'
  );
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcanoManifest());
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bobManifest());
  const result = run(root);
  assert.equal(result.status, 1);
  assert.match(output(result), /source_conflict: 06-modules\.md/);
});

test('detecta ciclos en el grafo de artefactos', () => {
  const { root, resources } = fixture();
  const bob = bobManifest();
  bob.artifacts['module-networking'].depends_on = ['module-key-vault'];
  bob.artifacts['module-key-vault'].depends_on = ['module-networking'];
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcanoManifest());
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bob);
  const result = run(root);
  assert.equal(result.status, 1);
  assert.match(output(result), /Ciclo en depends_on/);
});

test('las plantillas de pipeline pasan validacion semantica local', () => {
  const { root, resources } = fixture();
  const source = path.join(resources, 'infrastructure-as-code', '01-architecture.md');
  const sourceHash = crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex');
  const bob = bobManifest();
  const templates = [
    ['pipeline-iac', 'infra/pipelines/iac.yml', 'azure-pipelines.terraform.template.yml'],
    ['pipeline-drift', 'infra/pipelines/drift.yml', 'azure-pipelines.terraform-drift.template.yml'],
    ['pipeline-app', 'azure-pipelines.yml', 'azure-pipelines.node-angular-app.template.yml']
  ];
  for (const [logicalId, destination, template] of templates) {
    const target = path.join(root, destination);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(assetsDir, template), target);
    bob.artifacts[logicalId] = {
      path: destination,
      status: 'generated',
      depends_on: [],
      contract: { inputs: ['operations'], outputs: ['artifact'] },
      source_docs: ['infrastructure-as-code/01-architecture.md'],
      source_hashes: { 'infrastructure-as-code/01-architecture.md': sourceHash },
      validated: { format: null, validate: null, test: null, lint: null, security: null, syntax: true, last_run: '2026-07-16' }
    };
  }
  bob.target_repo.pipeline_files = templates.map(([, destination]) => destination);
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcanoManifest());
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bob);
  const result = run(root);
  assert.equal(result.status, 0, output(result));
});

test('workflows GitHub pasan política OIDC, environments y plan inmutable', () => {
  const { root, resources } = fixture();
  const vulcano = vulcanoManifest();
  vulcano.decisions.devops_platform = 'github';
  vulcano.decisions.terraform = { ...terraformProfile, execution_backend: 'github_actions' };
  const bob = bobManifest();
  bob.source_snapshot.devops_platform = 'github';
  bob.adapter_selection.pipeline = 'github_actions';
  bob.terraform_profile = { ...terraformProfile, execution_backend: 'github_actions' };
  const definitions = [
    ['.github/workflows/iac.yml', 'github-actions.terraform.template.yml'],
    ['.github/workflows/drift.yml', 'github-actions.terraform-drift.template.yml'],
    ['.github/workflows/application.yml', 'github-actions.application.template.yml']
  ];
  for (const [destination, asset] of definitions) {
    const target = path.join(root, destination);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(assetsDir, asset), target);
  }
  bob.target_repo.pipeline_files = definitions.map(([destination]) => destination);
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcano);
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bob);
  const result = run(root);
  assert.equal(result.status, 0, output(result));
});

test('pipelines GitLab pasan política de jobs, artifacts y environments', () => {
  const { root, resources } = fixture();
  const vulcano = vulcanoManifest();
  vulcano.decisions.devops_platform = 'gitlab';
  vulcano.decisions.terraform = { ...terraformProfile, execution_backend: 'gitlab_ci' };
  const bob = bobManifest();
  bob.source_snapshot.devops_platform = 'gitlab';
  bob.adapter_selection.pipeline = 'gitlab';
  bob.terraform_profile = { ...terraformProfile, execution_backend: 'gitlab_ci' };
  const definitions = [
    ['.gitlab/ci/iac.yml', 'gitlab.terraform.template.yml'],
    ['.gitlab/ci/drift.yml', 'gitlab.terraform-drift.template.yml'],
    ['.gitlab-ci.yml', 'gitlab.application.template.yml']
  ];
  for (const [destination, asset] of definitions) {
    const target = path.join(root, destination);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(path.join(assetsDir, asset), target);
  }
  bob.target_repo.pipeline_files = definitions.map(([destination]) => destination);
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcano);
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bob);
  const result = run(root);
  assert.equal(result.status, 0, output(result));
});

test('acepta un cierre estricto completo y coherente', () => {
  const { root, resources } = fixture();
  const source = path.join(resources, 'infrastructure-as-code', '01-architecture.md');
  const sourceHash = crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex');
  const bob = bobManifest();
  bob.target_repo.pipeline_files = ['infra/pipelines/iac.yml', 'infra/pipelines/drift.yml', 'azure-pipelines.yml'];

  bob.artifacts['bootstrap-backend'].status = 'omitted';
  bob.artifacts['bootstrap-backend'].reason = 'No aplica en fixture';
  for (const [logicalId, artifact] of Object.entries(bob.artifacts)) {
    if (logicalId === 'bootstrap-backend') continue;
    if (!logicalId.startsWith('pipeline-')) {
      const target = path.join(root, artifact.path);
      fs.mkdirSync(target, { recursive: true });
      fs.writeFileSync(path.join(target, 'main.tf'), 'terraform {}\n');
      if (logicalId.startsWith('module-')) {
        fs.writeFileSync(path.join(target, 'variables.tf'), 'variable "input" { type = string }\n');
        fs.writeFileSync(path.join(target, 'outputs.tf'), 'output "output" { value = null }\n');
        fs.mkdirSync(path.join(target, 'tests'), { recursive: true });
        fs.writeFileSync(path.join(target, 'tests', 'module.tftest.hcl'), [
          'run "fixture" {',
          '  command = plan',
          '  variables { input = "fixture" }',
          '}',
          ''
        ].join('\n'));
        artifact.validated.test = true;
      }
      artifact.validated.format = true;
      artifact.validated.validate = true;
      if (logicalId.startsWith('env-')) fs.writeFileSync(path.join(target, '.terraform.lock.hcl'), '# lock\n');
    }
    artifact.status = 'generated';
    artifact.source_hashes = { 'infrastructure-as-code/01-architecture.md': sourceHash };
    artifact.validated.last_run = '2026-07-16T00:00:00.000Z';
    const checks = logicalId.startsWith('pipeline-') ? ['syntax']
      : logicalId.startsWith('module-') ? ['format', 'validate', 'test'] : ['format', 'validate'];
    artifact.validated.evidence = Object.fromEntries(checks.map(check => [check, {
      status: 'passed', tool: check === 'syntax' ? 'python' : 'terraform', run_at: '2026-07-16T00:00:00.000Z',
      output_sha256: 'a'.repeat(64)
    }]));
  }

  bob.artifacts['pipeline-iac'].path = 'infra/pipelines/iac.yml';
  bob.artifacts['pipeline-drift'].path = 'infra/pipelines/drift.yml';
  bob.artifacts['pipeline-app'].path = 'azure-pipelines.yml';
  bob.artifacts['pipeline-iac'].validated.syntax = true;
  bob.artifacts['pipeline-drift'].validated.syntax = true;
  bob.artifacts['pipeline-app'].validated.syntax = true;
  fs.mkdirSync(path.join(root, 'infra', 'pipelines'), { recursive: true });
  fs.writeFileSync(path.join(root, 'infra', 'pipelines', 'iac.yml'), [
    'stages:',
    '  - stage: Plan',
    '    jobs:',
    '      - job: BuildPlan',
    '        steps:',
    '          - publish: plan.tfplan',
    '            artifact: tfplan-dev',
    '  - stage: Apply',
    '    dependsOn: Plan',
    '    jobs:',
    '      - deployment: ApplyPlan',
    '        environment: dev',
    '        strategy:',
    '          runOnce:',
    '            deploy:',
    '              steps:',
    '                - download: current',
    '                  artifact: tfplan-dev',
    ''
  ].join('\n'));
  fs.writeFileSync(path.join(root, 'infra', 'pipelines', 'drift.yml'), [
    'stages:',
    '  - stage: Drift',
    '    jobs:',
    '      - job: DetectDrift',
    '        steps:',
    '          - script: terraform plan -detailed-exitcode',
    ''
  ].join('\n'));
  fs.writeFileSync(path.join(root, 'azure-pipelines.yml'), [
    'stages:',
    '  - stage: Build',
    '    jobs:',
    '      - job: BuildApp',
    '        steps:',
    '          - script: npm test',
    ''
  ].join('\n'));
  fs.writeFileSync(path.join(resources, '03-iac-pipelines-index.md'), '# Indice\n');
  writeJson(path.join(resources, '.vulcano', 'manifest.yaml'), vulcanoManifest());
  writeJson(path.join(resources, '.vulcano', 'bob-manifest.yaml'), bob);
  const result = run(root, '--strict-completeness', '--write-summary', '--with-tools');
  assert.equal(result.status, 0, output(result));
  assert.match(output(result), /0 error\(es\)/);
  const persisted = fs.readFileSync(path.join(resources, '.vulcano', 'bob-manifest.yaml'), 'utf8');
  assert.match(persisted, /validation:[\s\S]*errors: 0/);
});
