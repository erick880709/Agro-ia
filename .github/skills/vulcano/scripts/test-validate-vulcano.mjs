#!/usr/bin/env node

import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const validator = path.resolve(scriptDir, 'validate-vulcano.mjs');
const manifestTemplate = fs.readFileSync(path.resolve(scriptDir, '..', 'assets', 'manifest.template.yaml'), 'utf8');
const logicalIds = [
  'devops-overview', 'repository-management', 'task-management', 'branching-strategy',
  'devops-environments', 'iac-architecture', 'iac-environments', 'naming-conventions',
  'iac-structure', 'state-management', 'modules', 'networking', 'secrets-management',
  'ci-cd', 'continuous-testing', 'security', 'release-management', 'incident-management',
  'disaster-recovery', 'monitoring', 'logging', 'tracing', 'slis-slos', 'dashboards',
  'alerting', 'runbooks'
];
const paths = {
  'devops-overview': 'devops-strategy/01-devops-overview.md',
  'repository-management': 'devops-strategy/02-repository-management.md',
  'task-management': 'devops-strategy/03-task-management.md',
  'branching-strategy': 'devops-strategy/04-branching-strategy.md',
  'devops-environments': 'devops-strategy/05-environments.md',
  'iac-architecture': 'infrastructure-as-code/01-architecture.md',
  'iac-environments': 'infrastructure-as-code/02-environments.md',
  'naming-conventions': 'infrastructure-as-code/03-naming-conventions.md',
  'iac-structure': 'infrastructure-as-code/04-pulumi-structure.md',
  'state-management': 'infrastructure-as-code/05-state-management.md',
  modules: 'infrastructure-as-code/06-modules.md',
  networking: 'infrastructure-as-code/07-networking.md',
  'secrets-management': 'infrastructure-as-code/08-secrets-management.md',
  'ci-cd': 'devops-strategy/06-ci-cd.md',
  'continuous-testing': 'devops-strategy/07-continuous-testing.md',
  security: 'devops-strategy/08-security.md',
  'release-management': 'devops-strategy/09-release-management.md',
  'incident-management': 'devops-strategy/10-incident-management.md',
  'disaster-recovery': 'devops-strategy/11-disaster-recovery.md',
  monitoring: 'observability/01-monitoring.md',
  logging: 'observability/02-logging.md',
  tracing: 'observability/03-tracing.md',
  'slis-slos': 'observability/04-slis-slos.md',
  dashboards: 'observability/05-dashboards.md',
  alerting: 'observability/06-alerting.md',
  runbooks: 'observability/07-runbooks.md'
};

const document = (body, metadata = {}) => `---
proyecto: ${metadata.project ?? 'Test'}
fecha: ${metadata.date ?? '2026-07-14'}
fuente: ${metadata.source ?? 'fixture'}
modo: ${metadata.mode ?? 'as-is'}
---

${body}
`;

const doraBody = () => `## Métricas DORA
| Aplicación/servicio | Métrica | Definición/fórmula | Fuente y ventana | Baseline/calidad | Meta 6m/12m | Equipo accountable / participantes |
|---|---|---|---|---|---|---|
| API | Deployment frequency | Despliegues por semana | Pipeline, 30 días | 2/semana, confiable | 3/5 por semana | Producto / Dev / SRE |
| API | Change lead time | Commit a producción | Git y pipeline, 30 días | 2 días, confiable | 1 día / 8 horas | Producto / Dev / SRE |
| API | Failed deployment recovery time | Fallo a recuperación | Incidentes, 90 días | 4 horas, parcial | 2 horas / 1 hora | Producto / Dev / SRE |
| API | Change fail rate | Fallos sobre despliegues | Pipeline, 90 días | 10%, confiable | 8% / 5% | Producto / Dev / SRE |
| API | Deployment rework rate | Deploys no planeados por incidente | Pipeline, 90 días | 5%, parcial | 4% / 2% | Producto / Dev / SRE |`;

const inspectionBody = () => `# CI/CD — Test

## Inspección Continua y Deuda Técnica

### Métricas y gates de calidad
| Dimensión | Métrica / definición | Baseline | Umbral en código nuevo | Tratamiento del legado | Consecuencia | Fuente | Owner |
|---|---|---|---|---|---|---|---|
| Cobertura de código nuevo | Líneas cubiertas / líneas nuevas | 70% | 80% | Backlog incremental | Bloquea merge | Reporte CI | Desarrollo |
| Duplicación | Bloques duplicados / código nuevo | 4% | 3% | Ratchet por baseline | Bloquea merge | Analizador | Desarrollo |
| Complejidad | Complejidad ciclomática por función | 12 | 10 | Refactor priorizado | Advierte | Analizador | Tech lead |
| Mantenibilidad / confiabilidad | Hallazgos abiertos por cambio | 5 | 0 críticos | Backlog con SLA | Bloquea críticos | Analizador | Tech lead |
| Issues bloqueantes | Hallazgos de severidad bloqueante | 1 | 0 | Excepción temporal | Bloquea merge | Analizador | Plataforma |

### Integración y feedback en PR
- **Herramienta/capacidad:** Analizador confirmado
- **Etapa y alcance:** PR de aplicación
- **Feedback:** Check con enlace al reporte
- **Enforcement:** Bloqueo y reejecución tras corrección

### Política de deuda técnica
- **Baseline y ratchet:** Baseline versionada
- **Regla para código nuevo:** No empeorar métricas
- **Tratamiento del legado:** Backlog incremental
- **Registro y owner:** Ítem con responsable y salida
- **Priorización / SLA:** Por impacto, revisión mensual

### Excepciones temporales
| ID | Alcance | Justificación y riesgo aceptado | Aprobador | Vencimiento / revalidación | Control compensatorio |
|---|---|---|---|---|---|
| Ninguna vigente | No aplica | No aplica | No aplica | Revisión mensual | No aplica |`;

const environmentBody = (iac = false, names = ['dev', 'prod']) => {
  const heading = iac ? '## Materialización por ambiente (mismo orden de promoción)' : '## Ambientes existentes (en orden de promoción)';
  const columns = iac ? '| Ambiente | Workspace/carpeta | Variables clave que cambian |' : '| Ambiente | Propósito | Quién lo usa |';
  const rows = names.map(name => iac ? `| ${name} | ${name} | size |` : `| **${name}** | ${name} | Equipo |`).join('\n');
  return `${heading}\n${columns}\n|---|---|---|\n${rows}`;
};

const maturityBody = `# Evaluación de Madurez

## Estándar(es) de Referencia
Framework interno.

## Completitud Documental
Completa.

## Madurez por Pilar
Intermedia.

## Decisiones pendientes sin resolver
Ninguna.

## Roadmap de Mejora Priorizado
1. Mantener controles.`;

const buildFixture = (options = {}) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-validator-'));
  const resources = path.join(root, 'resources');
  const generated = new Set(options.generatedIds ?? ['devops-environments', 'iac-environments', 'iac-structure', 'ci-cd', 'monitoring', 'alerting', 'runbooks']);
  const write = (relative, content) => {
    const file = path.join(root, relative);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, content);
  };
  const read = relative => fs.readFileSync(path.join(root, relative), 'utf8');
  const replace = (relative, search, replacement) => write(relative, read(relative).replace(search, replacement));

  const lines = [
    'schema_version: 1', 'project: "Test"', 'updated_at: "2026-07-14"',
    `resources_root: "${options.resourcesRoot ?? 'resources'}"`,
    'baseline: { cloud_providers: [azure] }', 'constraints: {}', 'decisions: {}', 'assumptions: []',
    'intentional_omissions: []', 'validation:', '  last_run: "2026-07-14"',
    '  errors: 0', '  warnings: 0', 'files:'
  ];
  for (const id of logicalIds) {
    const isGenerated = generated.has(id);
    lines.push(`  ${id}:`, `    path: "${paths[id]}"`, `    status: ${isGenerated ? 'generated' : 'omitted'}`, `    mode: ${isGenerated ? 'as-is' : 'null'}`);
    if (!isGenerated) lines.push('    reason: "No aplica al fixture"');
    else lines.push('    sources: [fixture]', '    owner: platform', '    validated_at: "2026-07-14"', '    summary: "Fixture válido"');
  }
  lines.push('pending_decisions:', '  - id: PD-001', '    owner: platform', '    exit_criteria: "Confirmar proveedor"');
  write('resources/.vulcano/manifest.yaml', `${lines.join('\n')}\n`);

  if (generated.has('monitoring')) write(`resources/${paths.monitoring}`, document(doraBody()));
  if (generated.has('ci-cd')) write(`resources/${paths['ci-cd']}`, document(inspectionBody()));
  if (generated.has('alerting')) write(`resources/${paths.alerting}`, document('| ID | Alerta | Severidad |\n|---|---|---|\n| ALT-001 | Error budget | Alta |'));
  if (generated.has('runbooks')) write(`resources/${paths.runbooks}`, document('## Error budget\n**ID:** ALT-001'));
  if (generated.has('iac-structure')) write(`resources/${paths['iac-structure']}`, document('# Estructura Pulumi'));
  if (generated.has('devops-environments')) write(`resources/${paths['devops-environments']}`, document(environmentBody(false)));
  if (generated.has('iac-environments')) write(`resources/${paths['iac-environments']}`, document(environmentBody(true)));

  const links = [...generated].map(id => `- [${id}](${paths[id]})`).join('\n');
  write('resources/01-devops-index.md', `# Índice DevOps\n\n${links}\n`);
  write('resources/02-madurez-devsecops.md', maturityBody);
  return { root, resources, write, read, replace };
};

const run = (root, extra = []) => spawnSync(process.execPath, [validator, '--root', root, '--strict-completeness', ...extra], { encoding: 'utf8' });
const runPartial = root => spawnSync(process.execPath, [validator, '--root', root], { encoding: 'utf8' });
const output = result => `${result.stderr}${result.stdout}`;
const fixtures = [];
let checks = 0;
const check = fn => { fn(); checks += 1; };

try {
  check(() => {
    for (const [logicalId, outputPath] of Object.entries(paths)) {
      const templatePath = logicalId === 'iac-structure'
        ? outputPath.replace('pulumi-structure', 'terraform-structure')
        : outputPath;
      assert.ok(manifestTemplate.includes(`path: ${templatePath}`), `${logicalId}: ruta numerada ausente en manifest.template.yaml`);
    }
  });

  const ok = buildFixture(); fixtures.push(ok.root);
  check(() => {
    const result = run(ok.root);
    assert.equal(result.status, 0, output(result));
  });

  const terraformProfileMissing = buildFixture(); fixtures.push(terraformProfileMissing.root);
  check(() => {
    terraformProfileMissing.replace('resources/.vulcano/manifest.yaml', 'decisions: {}', [
      'decisions:',
      '  iac: terraform',
      '  devops_platform: azure_devops'
    ].join('\n'));
    const result = run(terraformProfileMissing.root);
    assert.equal(result.status, 1);
    assert.match(output(result), /decisions\.terraform.*perfil Terraform/);
  });

  const terraformProfileValid = buildFixture(); fixtures.push(terraformProfileValid.root);
  check(() => {
    terraformProfileValid.replace('resources/.vulcano/manifest.yaml', 'decisions: {}', [
      'decisions:',
      '  iac: terraform',
      '  devops_platform: azure_devops',
      '  terraform:',
      '    required_version: ">= 1.9, < 2.0"',
      '    provider_constraints: { azurerm: "~> 4.0" }',
      '    module_standard: internal',
      '    execution_backend: azure_devops',
      '    test_strategy: plan_mock',
      '    registry_source: public',
      '    registry_mcp: read_only',
      '    adoption_mode: none'
    ].join('\n'));
    const result = run(terraformProfileValid.root);
    assert.equal(result.status, 0, output(result));
  });

  const awsGithubProfileValid = buildFixture(); fixtures.push(awsGithubProfileValid.root);
  check(() => {
    awsGithubProfileValid.replace('resources/.vulcano/manifest.yaml',
      'baseline: { cloud_providers: [azure] }', 'baseline: { cloud_providers: [aws] }');
    awsGithubProfileValid.replace('resources/.vulcano/manifest.yaml', 'decisions: {}', [
      'decisions:',
      '  cloud_provider: aws',
      '  iac: terraform',
      '  devops_platform: github',
      '  terraform:',
      '    required_version: ">= 1.9, < 2.0"',
      '    provider_constraints: { aws: "~> 6.0" }',
      '    module_standard: internal',
      '    execution_backend: github_actions',
      '    test_strategy: plan_mock',
      '    registry_source: public',
      '    registry_mcp: read_only',
      '    adoption_mode: none'
    ].join('\n'));
    const result = run(awsGithubProfileValid.root);
    assert.equal(result.status, 0, output(result));
  });

  const awsProviderMismatch = buildFixture(); fixtures.push(awsProviderMismatch.root);
  check(() => {
    awsProviderMismatch.replace('resources/.vulcano/manifest.yaml',
      'baseline: { cloud_providers: [azure] }', 'baseline: { cloud_providers: [aws] }');
    awsProviderMismatch.replace('resources/.vulcano/manifest.yaml', 'decisions: {}', [
      'decisions:',
      '  cloud_provider: aws',
      '  iac: terraform',
      '  devops_platform: github',
      '  terraform:',
      '    required_version: ">= 1.9, < 2.0"',
      '    provider_constraints: { azurerm: "~> 4.0" }',
      '    module_standard: internal',
      '    execution_backend: github_actions',
      '    test_strategy: plan_mock',
      '    registry_source: public',
      '    registry_mcp: read_only',
      '    adoption_mode: none'
    ].join('\n'));
    const result = run(awsProviderMismatch.root);
    assert.equal(result.status, 1);
    assert.match(output(result), /cloud_provider aws requiere constraint para aws/);
  });

  const gitlabProfileValid = buildFixture(); fixtures.push(gitlabProfileValid.root);
  check(() => {
    gitlabProfileValid.replace('resources/.vulcano/manifest.yaml', 'decisions: {}', [
      'decisions:',
      '  cloud_provider: azure',
      '  iac: terraform',
      '  devops_platform: gitlab',
      '  terraform:',
      '    required_version: ">= 1.9, < 2.0"',
      '    provider_constraints: { azurerm: "~> 4.0" }',
      '    module_standard: internal',
      '    execution_backend: gitlab_ci',
      '    test_strategy: plan_mock',
      '    registry_source: public',
      '    registry_mcp: read_only',
      '    adoption_mode: none'
    ].join('\n'));
    const result = run(gitlabProfileValid.root);
    assert.equal(result.status, 0, output(result));
  });

  check(() => {
    ok.replace('resources/observability/01-monitoring.md', doraBody(), `${doraBody()}\n\n- [ ] Criterio real\n- [x] Criterio cumplido\n\`array[0]\``);
    const result = run(ok.root);
    assert.equal(result.status, 0, output(result));
  });

  const mermaid = buildFixture(); fixtures.push(mermaid.root);
  check(() => {
    mermaid.replace('resources/observability/01-monitoring.md', doraBody(), `${doraBody()}\n\n\`\`\`mermaid\nflowchart TD\n A[Reporte] --> B[Triage]\n\`\`\``);
    const result = run(mermaid.root);
    assert.equal(result.status, 0, output(result));
  });

  const placeholder = buildFixture(); fixtures.push(placeholder.root);
  check(() => {
    placeholder.replace('resources/infrastructure-as-code/04-pulumi-structure.md', '# Estructura Pulumi', '# Estructura Pulumi\n\nRTO: [RTO]');
    const result = run(placeholder.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /placeholder de plantilla sin completar: \[RTO\]/i);
  });

  const envMismatch = buildFixture(); fixtures.push(envMismatch.root);
  check(() => {
    envMismatch.write('resources/infrastructure-as-code/02-environments.md', document(environmentBody(true, ['dev', 'staging'])));
    const result = run(envMismatch.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /orden de promoción inconsistentes/i);
  });

  const barePending = buildFixture(); fixtures.push(barePending.root);
  check(() => {
    barePending.replace('resources/infrastructure-as-code/04-pulumi-structure.md', '# Estructura Pulumi', '# Estructura Pulumi\n\n[PENDIENTE DE DEFINIR]');
    const result = run(barePending.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /pendiente sin ID registrado/i);
  });

  const absent = buildFixture(); fixtures.push(absent.root);
  check(() => {
    fs.rmSync(path.join(absent.root, 'resources/observability/07-runbooks.md'));
    const result = run(absent.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /archivo no existe|falta observability\/(?:07-)?runbooks/i);
  });

  const omittedRunbooks = buildFixture({ generatedIds: ['devops-environments', 'iac-environments', 'iac-structure', 'monitoring', 'alerting'] }); fixtures.push(omittedRunbooks.root);
  check(() => {
    const result = run(omittedRunbooks.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /faltan? observability\/(?:07-)?runbooks|falta observability\/(?:07-)?runbooks/i);
  });

  const noRunbookId = buildFixture(); fixtures.push(noRunbookId.root);
  check(() => {
    noRunbookId.write('resources/observability/07-runbooks.md', document('## Sin correspondencia\n**ID:** ALT-999'));
    const result = run(noRunbookId.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /ALT-001/);
  });

  const invalidManifest = buildFixture(); fixtures.push(invalidManifest.root);
  check(() => {
    invalidManifest.write('resources/.vulcano/manifest.yaml', 'schema_version: [\n');
    const result = run(invalidManifest.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /YAML inválido/i);
  });

  const secret = buildFixture(); fixtures.push(secret.root);
  check(() => {
    secret.replace('resources/infrastructure-as-code/04-pulumi-structure.md', '# Estructura Pulumi', '# Estructura Pulumi\n\napi_key: "abcdefghijklmnop123456"');
    const result = run(secret.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /posible secreto/i);
  });

  const noFrontmatter = buildFixture(); fixtures.push(noFrontmatter.root);
  check(() => {
    noFrontmatter.write('resources/infrastructure-as-code/04-pulumi-structure.md', '# Sin frontmatter');
    const result = run(noFrontmatter.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /falta frontmatter/i);
  });

  const invalidFrontmatter = buildFixture(); fixtures.push(invalidFrontmatter.root);
  check(() => {
    invalidFrontmatter.write('resources/infrastructure-as-code/04-pulumi-structure.md', '---\nproyecto: [\nfecha: 2026-07-14\nfuente: fixture\nmodo: as-is\n---\n# Inválido');
    const result = run(invalidFrontmatter.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /frontmatter YAML inválido/i);
  });

  const modeMismatch = buildFixture(); fixtures.push(modeMismatch.root);
  check(() => {
    modeMismatch.write('resources/infrastructure-as-code/04-pulumi-structure.md', document('# Estructura Pulumi', { mode: 'greenfield' }));
    const result = run(modeMismatch.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /no coincide con manifest/i);
  });

  const badMetadata = buildFixture(); fixtures.push(badMetadata.root);
  check(() => {
    badMetadata.write('resources/infrastructure-as-code/04-pulumi-structure.md', document('# Estructura Pulumi', { project: 'Otro', date: '"2026-02-31"', source: '""' }));
    const result = run(badMetadata.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /proyecto no coincide/i);
    assert.match(result.stderr, /fecha debe ser una fecha real/i);
    assert.match(result.stderr, /fuente debe ser texto/i);
  });

  const missingManifest = buildFixture(); fixtures.push(missingManifest.root);
  check(() => {
    fs.rmSync(path.join(missingManifest.root, 'resources/.vulcano/manifest.yaml'));
    const result = run(missingManifest.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /No existe .*manifest\.yaml/i);
    const partial = runPartial(missingManifest.root);
    assert.equal(partial.status, 0, output(partial));
  });

  const wrongRoot = buildFixture({ resourcesRoot: 'services/otro/resources' }); fixtures.push(wrongRoot.root);
  check(() => {
    const result = run(wrongRoot.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /resources_root apunta/i);
  });

  const traversal = buildFixture(); fixtures.push(traversal.root);
  check(() => {
    traversal.replace('resources/.vulcano/manifest.yaml', 'path: "infrastructure-as-code/04-pulumi-structure.md"', 'path: "../../escape.md"');
    const result = run(traversal.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /path sale de resources_root/i);
  });

  const unnumbered = buildFixture(); fixtures.push(unnumbered.root);
  check(() => {
    unnumbered.replace('resources/.vulcano/manifest.yaml', 'path: "infrastructure-as-code/04-pulumi-structure.md"', 'path: "infrastructure-as-code/pulumi-structure.md"');
    const result = run(unnumbered.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /prefijo canónico 04-/i);
  });

  const wrongFolder = buildFixture(); fixtures.push(wrongFolder.root);
  check(() => {
    wrongFolder.replace('resources/.vulcano/manifest.yaml', 'path: "infrastructure-as-code/04-pulumi-structure.md"', 'path: "observability/04-pulumi-structure.md"');
    const result = run(wrongFolder.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /path debe estar en infrastructure-as-code\//i);
  });

  const alternateRoot = buildFixture(); fixtures.push(alternateRoot.root);
  check(() => {
    const customResources = path.join(alternateRoot.root, 'services', 'auth', 'resources');
    fs.mkdirSync(path.dirname(customResources), { recursive: true });
    fs.renameSync(alternateRoot.resources, customResources);
    const customManifest = path.join(customResources, '.vulcano', 'manifest.yaml');
    fs.writeFileSync(customManifest, fs.readFileSync(customManifest, 'utf8').replace('resources_root: "resources"', 'resources_root: "services/auth/resources"'));
    const result = run(alternateRoot.root, ['--resources-dir', customResources]);
    assert.equal(result.status, 0, output(result));
  });

  const missingIndex = buildFixture(); fixtures.push(missingIndex.root);
  check(() => {
    fs.rmSync(path.join(missingIndex.root, 'resources/01-devops-index.md'));
    const result = run(missingIndex.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /01-devops-index\.md/i);
  });

  const incompleteIndex = buildFixture(); fixtures.push(incompleteIndex.root);
  check(() => {
    incompleteIndex.replace('resources/01-devops-index.md', '- [iac-structure](infrastructure-as-code/04-pulumi-structure.md)\n', '');
    const result = run(incompleteIndex.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /no enlaza infrastructure-as-code\/04-pulumi-structure\.md/i);
  });

  const missingMaturity = buildFixture(); fixtures.push(missingMaturity.root);
  check(() => {
    fs.rmSync(path.join(missingMaturity.root, 'resources/02-madurez-devsecops.md'));
    const result = run(missingMaturity.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /02-madurez-devsecops\.md/i);
  });

  const incompleteMaturity = buildFixture(); fixtures.push(incompleteMaturity.root);
  check(() => {
    incompleteMaturity.write('resources/02-madurez-devsecops.md', '# Evaluación vacía');
    const result = run(incompleteMaturity.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /falta sección/i);
  });

  const incompleteDora = buildFixture(); fixtures.push(incompleteDora.root);
  check(() => {
    incompleteDora.replace('resources/observability/01-monitoring.md', '| API | Deployment frequency', '| | Deployment frequency');
    const result = run(incompleteDora.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /deployment frequency requiere aplicación\/servicio/i);
  });

  const missingInspection = buildFixture(); fixtures.push(missingInspection.root);
  check(() => {
    missingInspection.write('resources/devops-strategy/06-ci-cd.md', document('# CI/CD sin inspección'));
    const result = run(missingInspection.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /falta sección Inspección Continua/i);
  });

  const incompleteInspection = buildFixture(); fixtures.push(incompleteInspection.root);
  check(() => {
    incompleteInspection.replace('resources/devops-strategy/06-ci-cd.md', '| Duplicación | Bloques duplicados / código nuevo | 4% | 3% | Ratchet por baseline | Bloquea merge | Analizador | Desarrollo |', '| Duplicación | | 4% | 3% | Ratchet por baseline | Bloquea merge | Analizador | Desarrollo |');
    const result = run(incompleteInspection.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /duplicación requiere definición/i);
  });

  const missingDebtPolicy = buildFixture(); fixtures.push(missingDebtPolicy.root);
  check(() => {
    missingDebtPolicy.replace('resources/devops-strategy/06-ci-cd.md', '- **Priorización / SLA:** Por impacto, revisión mensual', '- Revisión mensual');
    const result = run(missingDebtPolicy.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /política de deuda técnica sin Priorización \/ SLA/i);
  });

  const staleValidation = buildFixture(); fixtures.push(staleValidation.root);
  check(() => {
    staleValidation.replace('resources/.vulcano/manifest.yaml', 'last_run: "2026-07-14"', 'last_run: null');
    const result = run(staleValidation.root);
    assert.equal(result.status, 1);
    assert.match(result.stderr, /validation\.last_run/i);
  });

  check(() => {
    const result = spawnSync(process.execPath, [validator, '--resources-dir'], { encoding: 'utf8' });
    assert.equal(result.status, 1);
    assert.match(result.stderr, /--resources-dir requiere una ruta/i);
  });

  console.log(`Vulcano validator fixtures: ${checks}/${checks} passed.`);
} finally {
  for (const fixture of fixtures) fs.rmSync(fixture, { recursive: true, force: true });
}
