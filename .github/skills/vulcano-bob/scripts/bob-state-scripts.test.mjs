import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
const initScript = path.join(scriptsDir, 'init-bob-manifest.mjs');
const recordScript = path.join(scriptsDir, 'record-bob-artifact.mjs');
const validateAndRecordScript = path.join(scriptsDir, 'validate-and-record-bob-artifact.mjs');
const indexScript = path.join(scriptsDir, 'generate-bob-index.mjs');
const compilerScript = path.join(scriptsDir, 'compile-bob-contract.mjs');
const rendererScript = path.join(scriptsDir, 'render-bob-pipelines.mjs');
const bootstrapRendererScript = path.join(scriptsDir, 'render-bob-bootstrap.mjs');
const terraformProfile = {
  required_version: '>= 1.9, < 2.0', provider_constraints: { azurerm: '~> 4.0' },
  module_standard: 'internal', execution_backend: 'azure_devops', test_strategy: 'plan_mock',
  registry_source: 'public', registry_mcp: 'read_only', adoption_mode: 'none'
};

function createFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-state-'));
  const resources = path.join(root, 'resources');
  fs.mkdirSync(path.join(resources, '.vulcano'), { recursive: true });
  fs.mkdirSync(path.join(resources, 'infrastructure-as-code'), { recursive: true });
  fs.writeFileSync(path.join(resources, '.vulcano', 'manifest.yaml'), JSON.stringify({
    schema_version: 1,
    project: 'state fixture',
    updated_at: '2026-07-16',
    resources_root: 'resources',
    decisions: { cloud_provider: 'azure', iac: 'terraform', devops_platform: 'azure_devops', terraform: terraformProfile }
  }));
  fs.writeFileSync(
    path.join(resources, 'infrastructure-as-code', '05-state-management.md'),
    '# State management\n'
  );
  return { root, resources };
}

function run(script, root, ...args) {
  return spawnSync(process.execPath, [script, '--root', root, ...args], { encoding: 'utf8' });
}

test('init crea schema v4 con selección de adaptadores y no sobrescribe por defecto', () => {
  const { root, resources } = createFixture();
  const first = run(initScript, root);
  assert.equal(first.status, 0, `${first.stdout}\n${first.stderr}`);
  const manifestPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  const text = fs.readFileSync(manifestPath, 'utf8');
  assert.match(text, /schema_version: 4/);
  assert.match(text, /project: state fixture/);
  assert.match(text, /required_version: '>= 1.9, < 2.0'/);
  assert.match(text, /terraform_registry_mcp: unknown/);
  assert.match(text, /adapter_selection:[\s\S]*cloud: azure[\s\S]*pipeline: azure_devops/);

  const second = run(initScript, root);
  assert.equal(second.status, 1);
  assert.match(second.stderr, /ya existe; no se sobrescribio|ya existe; no se sobrescribió/);

  const legacy = JSON.parse(runPythonYaml(manifestPath));
  legacy.schema_version = 3;
  delete legacy.adapter_selection;
  delete legacy.source_snapshot.cloud_provider;
  fs.writeFileSync(manifestPath, `${JSON.stringify(legacy, null, 2)}\n`);
  const migrated = run(initScript, root, '--migrate-adapters');
  assert.equal(migrated.status, 0, `${migrated.stdout}\n${migrated.stderr}`);
  const migratedText = fs.readFileSync(manifestPath, 'utf8');
  assert.match(migratedText, /schema_version: 4/);
  assert.match(migratedText, /adapter_selection:[\s\S]*remote_operator: vulcano-operador/);
  assert.match(migratedText, /status: pending/);
  assert.match(migratedText, /pipeline-app:/);
});

test('generated se registra solo con validacion ejecutada y evidencia', () => {
  const { root, resources } = createFixture();
  assert.equal(run(initScript, root).status, 0);
  const rejected = run(
    recordScript,
    root,
    '--logical-id', 'pipeline-app',
    '--status', 'generated'
  );
  assert.equal(rejected.status, 1);
  assert.match(rejected.stderr, /validate-and-record-bob-artifact/);

  for (const environment of ['env-dev', 'env-qa', 'env-prod']) {
    assert.equal(run(recordScript, root, '--logical-id', environment, '--status', 'omitted', '--reason', 'fixture').status, 0);
  }
  const sourceDocs = [
    'devops-strategy/05-environments.md', 'devops-strategy/06-ci-cd.md',
    'devops-strategy/07-continuous-testing.md', 'devops-strategy/08-security.md'
  ];
  for (const source of sourceDocs) {
    const target = path.join(resources, source);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, `# ${source}\n`);
  }
  fs.writeFileSync(path.join(root, 'azure-pipelines.yml'), 'stages:\n  - stage: Build\n    jobs:\n      - job: Test\n        steps:\n          - script: npm test\n');
  const result = run(validateAndRecordScript, root, '--logical-id', 'pipeline-app');
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  const text = fs.readFileSync(path.join(resources, '.vulcano', 'bob-manifest.yaml'), 'utf8');
  assert.match(text, /pipeline-app:[\s\S]*status: generated/);
  assert.match(text, /[a-f0-9]{64}/);
  assert.match(text, /evidence:[\s\S]*status: passed/);
});

test('genera el indice de cierre desde el manifiesto', () => {
  const { root, resources } = createFixture();
  assert.equal(run(initScript, root).status, 0);
  const result = run(indexScript, root);
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  const index = fs.readFileSync(path.join(resources, '03-iac-pipelines-index.md'), 'utf8');
  assert.match(index, /## Modulos Terraform|## Módulos Terraform/);
  assert.match(index, /bootstrap-backend/);
  assert.match(index, /pipeline-drift/);
});

test('compila módulos y dependencias desde 06-modules.md', () => {
  const { root, resources } = createFixture();
  fs.writeFileSync(path.join(resources, 'infrastructure-as-code', '06-modules.md'), [
    '# Módulos',
    '## `networking`',
    '- **Inputs:**',
    '| Nombre | Tipo | Default | Descripción |',
    '|---|---|---|---|',
    '| `environment` | string | — | ambiente |',
    '- **Outputs:** `subnet_id`.',
    '- **Origen:** propio, `infra/modules/networking`.',
    '## `compute`',
    '- **Inputs:**',
    '| Nombre | Tipo | Default | Descripción |',
    '|---|---|---|---|',
    '| `subnet_id` | string | — | output de `networking` |',
    '- **Outputs:** `app_id` (se consume en `another-module`).',
    '- **Origen:** propio, `infra/modules/compute`.',
    ''
  ].join('\n'));
  const initialized = run(initScript, root);
  assert.equal(initialized.status, 0, `${initialized.stdout}\n${initialized.stderr}`);
  const manifest = JSON.parse(runPythonYaml(path.join(resources, '.vulcano', 'bob-manifest.yaml')));
  assert.deepEqual(Object.keys(manifest.artifacts).filter(id => id.startsWith('module-')).sort(), ['module-compute', 'module-networking']);
  assert.deepEqual(manifest.artifacts['module-compute'].depends_on, ['module-networking']);
  assert.deepEqual(manifest.artifacts['module-compute'].contract.inputs, ['subnet_id']);
  assert.deepEqual(manifest.artifacts['module-compute'].contract.outputs, ['app_id']);
});

test('anotacion explicita "Depende de" crea una dependencia no inferible por nombre', () => {
  const { root, resources } = createFixture();
  assert.equal(run(initScript, root).status, 0);
  fs.writeFileSync(path.join(resources, 'infrastructure-as-code', '06-modules.md'), [
    '# Módulos',
    '## `foundation`',
    '- **Inputs:**',
    '| Nombre | Tipo | Default | Descripción |',
    '|---|---|---|---|',
    '| `environment` | string | — | ambiente |',
    '- **Outputs:** `workspace_id`.',
    '- **Origen:** propio, `infra/modules/foundation`.',
    '## `frontend`',
    '- **Inputs:**',
    '| Nombre | Tipo | Default | Descripción |',
    '|---|---|---|---|',
    '| `environment` | string | — | ambiente |',
    '- **Outputs:** `frontend_id`.',
    '- **Depende de:** `foundation`.',
    '- **Origen:** propio, `infra/modules/frontend`.',
    ''
  ].join('\n'));
  const compiled = run(compilerScript, root);
  assert.equal(compiled.status, 0, `${compiled.stdout}\n${compiled.stderr}`);
  const manifest = JSON.parse(runPythonYaml(path.join(resources, '.vulcano', 'bob-manifest.yaml')));
  assert.deepEqual(manifest.artifacts['module-frontend'].depends_on, ['module-foundation']);
});

test('"Depende de" con módulo desconocido bloquea la compilación en vez de adivinar', () => {
  const { root, resources } = createFixture();
  assert.equal(run(initScript, root).status, 0);
  fs.writeFileSync(path.join(resources, 'infrastructure-as-code', '06-modules.md'), [
    '# Módulos',
    '## `frontend`',
    '- **Inputs:**',
    '| Nombre | Tipo | Default | Descripción |',
    '|---|---|---|---|',
    '| `environment` | string | — | ambiente |',
    '- **Outputs:** `frontend_id`.',
    '- **Depende de:** `nonexistent-module`.',
    '- **Origen:** propio, `infra/modules/frontend`.',
    ''
  ].join('\n'));
  const compiled = run(compilerScript, root);
  assert.equal(compiled.status, 1);
  assert.match(compiled.stderr, /no existe en el catálogo|no existe en el catalogo/);
});

test('un 06-modules.md escrito con la plantilla real de vulcano compila sin ajustes manuales', () => {
  // Regresión: la plantilla de vulcano (references/plantillas-archivos.md) y el parser de
  // compile-bob-contract.mjs deben coincidir exactamente en formato (encabezado y nombres en
  // backticks, Outputs como lista). Este fixture reproduce esa plantilla al pie de la letra.
  const { root, resources } = createFixture();
  fs.writeFileSync(path.join(resources, 'infrastructure-as-code', '06-modules.md'), [
    '# Catálogo de Módulos — Proyecto Demo',
    '',
    '## `networking`',
    '- **Propósito:** VNet, subnets y NSG por ambiente',
    '- **Inputs:**',
    '',
    '| Nombre | Tipo | Default | Descripción |',
    '|---|---|---|---|',
    '| `environment` | string | — | Ambiente |',
    '',
    '- **Outputs:**',
    '  - `subnet_id`: ID de la subnet de aplicación.',
    '  - `vnet_id`: ID de la VNet donde se despliega el módulo.',
    '- **Origen:** propio, `infra/modules/networking`.',
    '',
    '## `compute`',
    '- **Propósito:** App Service del backend',
    '- **Inputs:**',
    '',
    '| Nombre | Tipo | Default | Descripción |',
    '|---|---|---|---|',
    '| `subnet_id` | string | — | output de `networking` |',
    '',
    '- **Outputs:**',
    '  - `app_id`: ID del App Service.',
    '- **Depende de:** ninguno.',
    '- **Origen:** propio, `infra/modules/compute`.',
    '',
    '## Convención de versionado de módulos',
    'SemVer con tags de git.',
    '',
    '## Pruebas, publicación y soporte',
    'Tests con harness local.',
    ''
  ].join('\n'));
  const initialized = run(initScript, root);
  assert.equal(initialized.status, 0, `${initialized.stdout}\n${initialized.stderr}`);
  const manifest = JSON.parse(runPythonYaml(path.join(resources, '.vulcano', 'bob-manifest.yaml')));
  assert.deepEqual(Object.keys(manifest.artifacts).filter(id => id.startsWith('module-')).sort(), ['module-compute', 'module-networking']);
  assert.deepEqual(manifest.artifacts['module-networking'].contract.outputs.sort(), ['subnet_id', 'vnet_id']);
  assert.deepEqual(manifest.artifacts['module-compute'].depends_on, ['module-networking']);
});

test('renderer exige valores operativos y materializa los tres pipelines', () => {
  const { root } = createFixture();
  const missing = run(rendererScript, root);
  assert.equal(missing.status, 1);
  const rendered = run(
    rendererScript, root,
    '--terraform-variable-group', 'vg-iac',
    '--application-variable-group', 'vg-app',
    '--drift-cron', '15 4 * * *',
    '--terraform-version', '1.14.3'
  );
  assert.equal(rendered.status, 0, `${rendered.stdout}\n${rendered.stderr}`);
  assert.match(fs.readFileSync(path.join(root, 'infra', 'pipelines', 'drift.yml'), 'utf8'), /cron: "15 4 \* \* \*"/);
  const iacText = fs.readFileSync(path.join(root, 'infra', 'pipelines', 'iac.yml'), 'utf8');
  assert.match(iacText, /terraform -chdir="\$module" test -no-color/);
  assert.match(iacText, /Install Terraform 1\.14\.3, tflint and trivy/);
  assert.match(iacText, /terraform_1\.14\.3_linux_amd64\.zip/);
  assert.doesNotMatch(iacText, /__INSTALL_TERRAFORM/);
  assert.match(fs.readFileSync(path.join(root, 'azure-pipelines.yml'), 'utf8'), /group: vg-app/);
});

test('renderer rechaza un cron sintacticamente invalido en vez de aceptarlo literal', () => {
  const { root } = createFixture();
  const invalidRange = run(
    rendererScript, root,
    '--terraform-variable-group', 'vg-iac',
    '--application-variable-group', 'vg-app',
    '--drift-cron', '99 99 * * *'
  );
  assert.equal(invalidRange.status, 1);
  assert.match(invalidRange.stderr, /fuera de rango/);

  const invalidToken = run(
    rendererScript, root,
    '--terraform-variable-group', 'vg-iac',
    '--application-variable-group', 'vg-app',
    '--drift-cron', 'a b c d e'
  );
  assert.equal(invalidToken.status, 1);
  assert.match(invalidToken.stderr, /campo .* inválido/);
});

test('GitHub Actions ajusta manifiesto y renderiza OIDC para AWS', () => {
  const { root, resources } = createFixture();
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  const source = JSON.parse(fs.readFileSync(vulcanoPath, 'utf8'));
  source.decisions.cloud_provider = 'aws';
  source.decisions.devops_platform = 'github';
  source.decisions.terraform.provider_constraints = { aws: '~> 6.0' };
  source.decisions.terraform.execution_backend = 'github_actions';
  fs.writeFileSync(vulcanoPath, JSON.stringify(source));

  const initialized = run(initScript, root);
  assert.equal(initialized.status, 0, `${initialized.stdout}\n${initialized.stderr}`);
  const manifest = JSON.parse(runPythonYaml(path.join(resources, '.vulcano', 'bob-manifest.yaml')));
  assert.deepEqual(manifest.target_repo.pipeline_files, [
    '.github/workflows/iac.yml', '.github/workflows/drift.yml', '.github/workflows/application.yml'
  ]);
  assert.deepEqual(manifest.artifacts['bootstrap-backend'].contract.inputs, ['AWS_REGION', 'TFSTATE_BUCKET', 'TFSTATE_KMS_KEY_ID']);
  const bootstrap = run(bootstrapRendererScript, root);
  assert.equal(bootstrap.status, 0, `${bootstrap.stdout}\n${bootstrap.stderr}`);
  const bootstrapText = fs.readFileSync(path.join(root, 'infra', 'bootstrap', 'create-backend.sh'), 'utf8');
  assert.match(bootstrapText, /put-public-access-block/);
  assert.match(bootstrapText, /put-bucket-versioning/);

  const rendered = run(rendererScript, root, '--drift-cron', '15 4 * * *', '--terraform-version', '1.14.3');
  assert.equal(rendered.status, 0, `${rendered.stdout}\n${rendered.stderr}`);
  const iac = fs.readFileSync(path.join(root, '.github', 'workflows', 'iac.yml'), 'utf8');
  assert.match(iac, /aws-actions\/configure-aws-credentials@v5/);
  assert.match(iac, /terraform apply -input=false -auto-approve tfplan/);
  assert.doesNotMatch(iac, /__CLOUD_AUTH__/);
  assert.match(fs.readFileSync(path.join(root, '.github', 'workflows', 'drift.yml'), 'utf8'), /cron: '15 4 \* \* \*'/);
});

test('GitLab ajusta manifiesto y renderiza includes con OIDC', () => {
  const { root, resources } = createFixture();
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  const source = JSON.parse(fs.readFileSync(vulcanoPath, 'utf8'));
  source.decisions.devops_platform = 'gitlab';
  source.decisions.terraform.execution_backend = 'gitlab_ci';
  fs.writeFileSync(vulcanoPath, JSON.stringify(source));

  const initialized = run(initScript, root);
  assert.equal(initialized.status, 0, `${initialized.stdout}\n${initialized.stderr}`);
  const manifest = JSON.parse(runPythonYaml(path.join(resources, '.vulcano', 'bob-manifest.yaml')));
  assert.equal(manifest.adapter_selection.pipeline, 'gitlab');
  assert.equal(manifest.artifacts['pipeline-app'].path, '.gitlab-ci.yml');

  const rendered = run(rendererScript, root, '--drift-cron', '30 3 * * *', '--terraform-version', '1.14.3');
  assert.equal(rendered.status, 0, `${rendered.stdout}\n${rendered.stderr}`);
  assert.match(fs.readFileSync(path.join(root, '.gitlab', 'ci', 'iac.yml'), 'utf8'), /id_tokens:/);
  assert.match(fs.readFileSync(path.join(root, '.gitlab-ci.yml'), 'utf8'), /local: \.gitlab\/ci\/iac\.yml/);
  assert.doesNotMatch(fs.readFileSync(path.join(root, '.gitlab', 'ci', 'drift.yml'), 'utf8'), /__DRIFT_CRON__/);
});

test('bootstrap GCP se renderiza con contrato gcs y locking nativo', () => {
  const { root, resources } = createFixture();
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  const source = JSON.parse(fs.readFileSync(vulcanoPath, 'utf8'));
  source.decisions.cloud_provider = 'gcp';
  source.decisions.terraform.provider_constraints = { google: '~> 6.0' };
  fs.writeFileSync(vulcanoPath, JSON.stringify(source));

  const initialized = run(initScript, root);
  assert.equal(initialized.status, 0, `${initialized.stdout}\n${initialized.stderr}`);
  const manifest = JSON.parse(runPythonYaml(path.join(resources, '.vulcano', 'bob-manifest.yaml')));
  assert.equal(manifest.adapter_selection.cloud, 'gcp');
  assert.deepEqual(
    manifest.artifacts['bootstrap-backend'].contract.inputs,
    ['GCP_PROJECT_ID', 'GCP_REGION', 'TFSTATE_BUCKET', 'TFSTATE_KMS_KEY']
  );

  const bootstrap = run(bootstrapRendererScript, root);
  assert.equal(bootstrap.status, 0, `${bootstrap.stdout}\n${bootstrap.stderr}`);
  const bootstrapText = fs.readFileSync(path.join(root, 'infra', 'bootstrap', 'create-backend.sh'), 'utf8');
  assert.match(bootstrapText, /gcloud storage buckets create/);
  assert.match(bootstrapText, /--uniform-bucket-level-access/);
  assert.match(bootstrapText, /state_locking=gcs_native/);
});

test('render-github-actions y render-gitlab cambian el deploy directo por actualizar manifiestos GitOps', () => {
  const ghRenderer = path.join(scriptsDir, 'renderers', 'render-github-actions.mjs');
  const glRenderer = path.join(scriptsDir, 'renderers', 'render-gitlab.mjs');
  const ghRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-gh-gitops-'));
  const glRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-gl-gitops-'));

  const gh = spawnSync(process.execPath, [
    ghRenderer, '--root', ghRoot, '--adapter-cloud', 'aws',
    '--drift-cron', '0 5 * * *', '--terraform-version', '1.9.0', '--deployment-model', 'gitops'
  ], { encoding: 'utf8' });
  assert.equal(gh.status, 0, `${gh.stdout}\n${gh.stderr}`);
  const ghApp = fs.readFileSync(path.join(ghRoot, '.github', 'workflows', 'application.yml'), 'utf8');
  assert.match(ghApp, /Update GitOps manifests/);
  assert.match(ghApp, /ci-update-gitops-manifests\.sh/);
  assert.doesNotMatch(ghApp, /Deploy and verify health/);

  const gl = spawnSync(process.execPath, [
    glRenderer, '--root', glRoot, '--adapter-cloud', 'azure',
    '--drift-cron', '0 5 * * *', '--terraform-version', '1.9.0', '--deployment-model', 'gitops'
  ], { encoding: 'utf8' });
  assert.equal(gl.status, 0, `${gl.stdout}\n${gl.stderr}`);
  const glApp = fs.readFileSync(path.join(glRoot, '.gitlab-ci.yml'), 'utf8');
  assert.match(glApp, /ci-update-gitops-manifests\.sh/);
  assert.doesNotMatch(glApp, /ci-deploy\.sh/);
});

test('render-azure-devops rechaza deployment-model gitops en vez de generar un deploy inconsistente', () => {
  const azRenderer = path.join(scriptsDir, 'renderers', 'render-azure-devops.mjs');
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-az-gitops-'));
  const result = spawnSync(process.execPath, [
    azRenderer, '--root', root,
    '--terraform-variable-group', 'tf-ops', '--application-variable-group', 'app-deploy',
    '--drift-cron', '0 5 * * *', '--deployment-model', 'gitops'
  ], { encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /unsupported_adapter/);
  assert.match(result.stderr, /Azure Web App slots/);
});

test('render-bob-gitops materializa Kustomize base/overlays y Applications de ArgoCD', () => {
  const gitopsScript = path.join(scriptsDir, 'render-bob-gitops.mjs');
  const { root, resources } = createFixture();
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');

  const off = run(gitopsScript, root);
  assert.equal(off.status, 1);
  assert.match(off.stderr, /deployment_model/);

  const source = JSON.parse(fs.readFileSync(vulcanoPath, 'utf8'));
  source.decisions.deployment_model = 'gitops';
  fs.writeFileSync(vulcanoPath, JSON.stringify(source));

  const missingArg = run(gitopsScript, root, '--app-name', 'checkout-api');
  assert.equal(missingArg.status, 1);
  assert.match(missingArg.stderr, /--container-port es obligatorio/);

  const badName = run(
    gitopsScript, root,
    '--app-name', 'Checkout_API', '--container-port', '8080',
    '--image-repository', 'ghcr.io/acme/checkout-api',
    '--manifests-repo-url', 'https://github.com/acme/checkout-api',
    '--initial-image-tag', 'placeholder',
    '--replicas-dev', '1', '--replicas-qa', '2', '--replicas-prod', '3'
  );
  assert.equal(badName.status, 1);
  assert.match(badName.stderr, /DNS-safe/);

  const rendered = run(
    gitopsScript, root,
    '--app-name', 'checkout-api', '--container-port', '8080',
    '--image-repository', 'ghcr.io/acme/checkout-api',
    '--manifests-repo-url', 'https://github.com/acme/checkout-api',
    '--initial-image-tag', 'placeholder',
    '--replicas-dev', '1', '--replicas-qa', '2', '--replicas-prod', '3'
  );
  assert.equal(rendered.status, 0, `${rendered.stdout}\n${rendered.stderr}`);

  const deployment = fs.readFileSync(path.join(root, 'infra', 'gitops', 'base', 'deployment.yaml'), 'utf8');
  assert.match(deployment, /image: checkout-api:placeholder/);
  assert.match(deployment, /containerPort: 8080/);
  assert.doesNotMatch(deployment, /__[A-Z_]+__/);

  const prodOverlay = fs.readFileSync(path.join(root, 'infra', 'gitops', 'overlays', 'prod', 'kustomization.yaml'), 'utf8');
  assert.match(prodOverlay, /namespace: checkout-api-prod/);
  assert.match(prodOverlay, /newName: ghcr\.io\/acme\/checkout-api/);
  assert.match(prodOverlay, /count: 3/);

  const devOverlay = fs.readFileSync(path.join(root, 'infra', 'gitops', 'overlays', 'dev', 'kustomization.yaml'), 'utf8');
  assert.match(devOverlay, /count: 1/);

  const argocdProd = fs.readFileSync(path.join(root, 'infra', 'gitops', 'argocd', 'application-prod.yaml'), 'utf8');
  assert.match(argocdProd, /repoURL: https:\/\/github\.com\/acme\/checkout-api/);
  assert.match(argocdProd, /path: infra\/gitops\/overlays\/prod/);
  assert.doesNotMatch(argocdProd, /__[A-Z_]+__/);
});

test('render-bob-dora materializa el colector solo cuando dora_collection_method es automated', () => {
  const doraScript = path.join(scriptsDir, 'render-bob-dora.mjs');
  const { root, resources } = createFixture();
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');

  const off = run(doraScript, root);
  assert.equal(off.status, 1);
  assert.match(off.stderr, /dora_collection_method/);

  const source = JSON.parse(fs.readFileSync(vulcanoPath, 'utf8'));
  source.decisions.dora_collection_method = 'automated';
  fs.writeFileSync(vulcanoPath, JSON.stringify(source));

  const missingCron = run(doraScript, root);
  assert.equal(missingCron.status, 1);
  assert.match(missingCron.stderr, /--dora-cron es obligatorio/);

  const rendered = run(doraScript, root, '--dora-cron', '0 6 * * 1');
  assert.equal(rendered.status, 0, `${rendered.stdout}\n${rendered.stderr}`);
  const scriptContent = fs.readFileSync(path.join(root, 'scripts', 'dora-collect.mjs'), 'utf8');
  assert.match(scriptContent, /export function computeDoraMetrics/);
  const pipeline = fs.readFileSync(path.join(root, 'infra', 'pipelines', 'dora.yml'), 'utf8');
  assert.match(pipeline, /cron: "0 6 \* \* 1"/);
  assert.doesNotMatch(pipeline, /__DORA_CRON__/);
});

test('render-bob-dora no exige cron para GitLab (se programa en la plataforma)', () => {
  const doraScript = path.join(scriptsDir, 'render-bob-dora.mjs');
  const { root, resources } = createFixture();
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  const source = JSON.parse(fs.readFileSync(vulcanoPath, 'utf8'));
  source.decisions.devops_platform = 'gitlab';
  source.decisions.dora_collection_method = 'automated';
  source.decisions.terraform.execution_backend = 'gitlab_ci';
  fs.writeFileSync(vulcanoPath, JSON.stringify(source));

  const rendered = run(doraScript, root);
  assert.equal(rendered.status, 0, `${rendered.stdout}\n${rendered.stderr}`);
  const pipeline = fs.readFileSync(path.join(root, '.gitlab', 'ci', 'dora.yml'), 'utf8');
  assert.match(pipeline, /dora_metrics:/);
  assert.match(pipeline, /node scripts\/dora-collect\.mjs/);
});

test('render-bob-azure-devops-setup exige azure_devops y valida topología/componentes', () => {
  const setupScript = path.join(scriptsDir, 'render-bob-azure-devops-setup.mjs');
  const { root, resources } = createFixture();
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  const source = JSON.parse(fs.readFileSync(vulcanoPath, 'utf8'));
  source.decisions.devops_platform = 'github_actions';
  fs.writeFileSync(vulcanoPath, JSON.stringify(source));

  const wrongPlatform = run(setupScript, root,
    '--terraform-variable-group', 'vg-terraform', '--application-variable-group', 'vg-app',
    '--pipeline-topology', 'single', '--min-reviewers', '1');
  assert.equal(wrongPlatform.status, 1);
  assert.match(wrongPlatform.stderr, /específico de Azure DevOps/);

  source.decisions.devops_platform = 'azure_devops';
  fs.writeFileSync(vulcanoPath, JSON.stringify(source));

  const missingComponents = run(setupScript, root,
    '--terraform-variable-group', 'vg-terraform', '--application-variable-group', 'vg-app',
    '--pipeline-topology', 'per_component', '--min-reviewers', '1');
  assert.equal(missingComponents.status, 1);
  assert.match(missingComponents.stderr, /--components es obligatorio/);

  const extraComponents = run(setupScript, root,
    '--terraform-variable-group', 'vg-terraform', '--application-variable-group', 'vg-app',
    '--pipeline-topology', 'single', '--components', 'backend', '--min-reviewers', '1');
  assert.equal(extraComponents.status, 1);
  assert.match(extraComponents.stderr, /--components no aplica/);

  const badReviewers = run(setupScript, root,
    '--terraform-variable-group', 'vg-terraform', '--application-variable-group', 'vg-app',
    '--pipeline-topology', 'single', '--min-reviewers', '0');
  assert.equal(badReviewers.status, 1);
  assert.match(badReviewers.stderr, /--min-reviewers debe ser un entero positivo/);
});

test('render-bob-azure-devops-setup genera un Environment compartido por ambiente en topología single', () => {
  const setupScript = path.join(scriptsDir, 'render-bob-azure-devops-setup.mjs');
  const { root } = createFixture();
  const rendered = run(setupScript, root,
    '--terraform-variable-group', 'vg-psoft-terraform', '--application-variable-group', 'vg-psoft-application',
    '--pipeline-topology', 'single', '--min-reviewers', '2');
  assert.equal(rendered.status, 0, `${rendered.stdout}\n${rendered.stderr}`);
  const content = fs.readFileSync(path.join(root, 'infra', 'bootstrap', 'setup-azure-devops.sh'), 'utf8');
  assert.match(content, /create_environment "dev" "Deploy a dev"/);
  assert.match(content, /create_environment "qa" "Deploy a qa"/);
  assert.match(content, /create_environment "prod" "Deploy a prod/);
  assert.match(content, /vg-psoft-terraform/);
  assert.match(content, /vg-psoft-application/);
  assert.match(content, /create_branch_policy_min_reviewers "\$TARGET_BRANCH" 2/);
  assert.doesNotMatch(content, /__[A-Z_]+__/);
});

test('render-bob-azure-devops-setup genera un Environment por componente, nunca compartido', () => {
  const setupScript = path.join(scriptsDir, 'render-bob-azure-devops-setup.mjs');
  const { root } = createFixture();
  const rendered = run(setupScript, root,
    '--terraform-variable-group', 'vg-psoft-terraform', '--application-variable-group', 'vg-psoft-application',
    '--pipeline-topology', 'per_component', '--components', 'backend,frontend', '--min-reviewers', '1');
  assert.equal(rendered.status, 0, `${rendered.stdout}\n${rendered.stderr}`);
  const content = fs.readFileSync(path.join(root, 'infra', 'bootstrap', 'setup-azure-devops.sh'), 'utf8');
  for (const name of ['dev-backend', 'qa-backend', 'prod-backend', 'dev-frontend', 'qa-frontend', 'prod-frontend']) {
    assert.match(content, new RegExp(`create_environment "${name}"`));
  }
  // Nunca un Environment "prod" compartido entre componentes — eso mezclaría deployment records.
  assert.doesNotMatch(content, /create_environment "prod" /);
  assert.match(content, /ENV_ID_PROD_BACKEND="\$\(create_environment "prod-backend"/);
  assert.match(content, /echo "prod-backend -> \$\{ENV_ID_PROD_BACKEND\}"/);
  assert.doesNotMatch(content, /__[A-Z_]+__/);
});

test('renderer materializa despliegue progresivo cuando decisions.deployment_strategy no es rolling', () => {
  const { root } = createFixture();
  const rolling = run(
    rendererScript, root,
    '--terraform-variable-group', 'vg-iac',
    '--application-variable-group', 'vg-app',
    '--drift-cron', '15 4 * * *',
    '--terraform-version', '1.14.3'
  );
  assert.equal(rolling.status, 0, `${rolling.stdout}\n${rolling.stderr}`);
  const rollingApp = fs.readFileSync(path.join(root, 'azure-pipelines.yml'), 'utf8');
  assert.doesNotMatch(rollingApp, /Analyze rollout/);
  assert.doesNotMatch(rollingApp, /__PROGRESSIVE_DELIVERY/);

  const { root: canaryRoot } = createFixture();
  const canary = run(
    rendererScript, canaryRoot,
    '--terraform-variable-group', 'vg-iac',
    '--application-variable-group', 'vg-app',
    '--drift-cron', '15 4 * * *',
    '--terraform-version', '1.14.3',
    '--deployment-strategy', 'canary'
  );
  assert.equal(canary.status, 0, `${canary.stdout}\n${canary.stderr}`);
  const canaryApp = fs.readFileSync(path.join(canaryRoot, 'azure-pipelines.yml'), 'utf8');
  assert.match(canaryApp, /Analyze rollout \(canary\)/);
  assert.match(canaryApp, /ANALYSIS_METRICS_SOURCE/);
  assert.doesNotMatch(canaryApp, /__PROGRESSIVE_DELIVERY/);
});

test('render-github-actions y render-gitlab exponen los mismos steps de analisis y rollback', () => {
  const ghRenderer = path.join(scriptsDir, 'renderers', 'render-github-actions.mjs');
  const glRenderer = path.join(scriptsDir, 'renderers', 'render-gitlab.mjs');
  const ghRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-gh-'));
  const glRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-gl-'));

  const gh = spawnSync(process.execPath, [
    ghRenderer, '--root', ghRoot, '--adapter-cloud', 'aws',
    '--drift-cron', '0 5 * * *', '--terraform-version', '1.9.0', '--deployment-strategy', 'canary'
  ], { encoding: 'utf8' });
  assert.equal(gh.status, 0, `${gh.stdout}\n${gh.stderr}`);
  const ghApp = fs.readFileSync(path.join(ghRoot, '.github', 'workflows', 'application.yml'), 'utf8');
  assert.match(ghApp, /Analyze rollout \(canary\)/);
  assert.match(ghApp, /Abort and rollback \(canary\)/);
  assert.match(ghApp, /if: failure\(\)/);

  const gl = spawnSync(process.execPath, [
    glRenderer, '--root', glRoot, '--adapter-cloud', 'azure',
    '--drift-cron', '0 5 * * *', '--terraform-version', '1.9.0', '--deployment-strategy', 'blue_green'
  ], { encoding: 'utf8' });
  assert.equal(gl.status, 0, `${gl.stdout}\n${gl.stderr}`);
  const glApp = fs.readFileSync(path.join(glRoot, '.gitlab-ci.yml'), 'utf8');
  assert.match(glApp, /ci-analyze-rollout\.sh/);
  assert.match(glApp, /application_rollback:/);
  assert.match(glApp, /when: on_failure/);
});

test('renderer materializa policy engine y notificaciones cuando el manifiesto los declara', () => {
  const { root } = createFixture();
  const rendered = run(
    rendererScript, root,
    '--terraform-variable-group', 'vg-iac',
    '--application-variable-group', 'vg-app',
    '--drift-cron', '15 4 * * *',
    '--terraform-version', '1.14.3',
    '--policy-engine', 'opa',
    '--notification-channel', 'slack'
  );
  assert.equal(rendered.status, 0, `${rendered.stdout}\n${rendered.stderr}`);
  const iac = fs.readFileSync(path.join(root, 'infra', 'pipelines', 'iac.yml'), 'utf8');
  assert.match(iac, /POLICY_ENGINE=opa \.\/scripts\/ci-policy-check\.sh infra\/environments\/dev\/tfplan/);
  assert.match(iac, /POLICY_ENGINE=opa \.\/scripts\/ci-policy-check\.sh infra\/environments\/qa\/tfplan/);
  assert.match(iac, /POLICY_ENGINE=opa \.\/scripts\/ci-policy-check\.sh infra\/environments\/prod\/tfplan/);
  const app = fs.readFileSync(path.join(root, 'azure-pipelines.yml'), 'utf8');
  assert.match(app, /stage: NotifyResult/);
  assert.match(app, /condition: always\(\)/);
  assert.doesNotMatch(app, /__NOTIFICATION_STAGE__|__POLICY_AS_CODE/);
});

test('renderers rechazan un policy engine o canal de notificacion desconocido', () => {
  const ghRenderer = path.join(scriptsDir, 'renderers', 'render-github-actions.mjs');
  const badPolicy = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-badpolicy-'));
  const policyResult = spawnSync(process.execPath, [
    ghRenderer, '--root', badPolicy, '--adapter-cloud', 'aws',
    '--drift-cron', '0 5 * * *', '--terraform-version', '1.9.0', '--policy-engine', 'sentinel'
  ], { encoding: 'utf8' });
  assert.equal(policyResult.status, 1);
  assert.match(policyResult.stderr, /--policy-engine debe ser none, opa o conftest/);

  const badChannel = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-badchannel-'));
  const channelResult = spawnSync(process.execPath, [
    ghRenderer, '--root', badChannel, '--adapter-cloud', 'aws',
    '--drift-cron', '0 5 * * *', '--terraform-version', '1.9.0', '--notification-channel', 'discord'
  ], { encoding: 'utf8' });
  assert.equal(channelResult.status, 1);
  assert.match(channelResult.stderr, /--notification-channel debe ser none, slack o teams/);
});

test('renderers rechazan una estrategia de despliegue desconocida', () => {
  const ghRenderer = path.join(scriptsDir, 'renderers', 'render-github-actions.mjs');
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-badstrategy-'));
  const result = spawnSync(process.execPath, [
    ghRenderer, '--root', root, '--adapter-cloud', 'aws',
    '--drift-cron', '0 5 * * *', '--terraform-version', '1.9.0', '--deployment-strategy', 'green-blue'
  ], { encoding: 'utf8' });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /--deployment-strategy debe ser rolling, canary o blue_green/);
});

function runPythonYaml(file) {
  const result = spawnSync('python', ['-c', 'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))))', file], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout;
}
