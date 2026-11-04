#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { replaceMarkerLine, validateDeploymentModel, validateDeploymentStrategy, validateNotificationChannel, validatePipelineTopology, validatePolicyEngine } from './renderer-lib.mjs';

const args = process.argv.slice(2);
const normalize = value => value.replaceAll('\\', '/');

function policyAsCodeStep(engine, environment, indent = 10) {
  if (engine === 'none') return null;
  const pad = ' '.repeat(indent);
  return [
    `${pad}- bash: POLICY_ENGINE=${engine} ./scripts/ci-policy-check.sh infra/environments/${environment}/tfplan`,
    `${pad}  displayName: Policy as code check`
  ].join('\n');
}

// El agente Microsoft-hosted ubuntu-24.04 no trae Terraform (ni tflint/trivy) preinstalados —
// confirmado en runner-images/Ubuntu2404-Readme.md — así que cada job que invoca `terraform`
// necesita instalarlo primero. Solo el job de Validate corre tflint/trivy; los jobs de
// plan/apply por ambiente solo necesitan la CLI de Terraform.
function terraformInstallStep(version, indent, { withLintTools = false } = {}) {
  const pad = ' '.repeat(indent);
  const lines = [
    `${pad}- bash: |`,
    `${pad}    set -euo pipefail`,
    `${pad}    mkdir -p "$(Agent.TempDirectory)/bin"`,
    `${pad}    curl -fsSL -o "$(Agent.TempDirectory)/terraform.zip" "https://releases.hashicorp.com/terraform/${version}/terraform_${version}_linux_amd64.zip"`,
    `${pad}    unzip -o "$(Agent.TempDirectory)/terraform.zip" -d "$(Agent.TempDirectory)/bin"`
  ];
  if (withLintTools) {
    lines.push(
      `${pad}    curl -fsSL https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | TFLINT_INSTALL_PATH="$(Agent.TempDirectory)/bin" bash`,
      `${pad}    curl -fsSL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b "$(Agent.TempDirectory)/bin"`
    );
  }
  lines.push(
    `${pad}    echo "##vso[task.prependpath]$(Agent.TempDirectory)/bin"`,
    `${pad}  displayName: Install Terraform ${version}${withLintTools ? ', tflint and trivy' : ''}`
  );
  return lines.join('\n');
}

function notificationStage(channel) {
  if (channel === 'none') return null;
  // Dos steps condicionados a succeeded()/failed() en vez de que ci-notify.sh intente adivinar
  // el resultado agregado de DeployDev/DeployQa/DeployProd — succeeded()/failed() sin argumentos
  // ya reflejan el estado de las dependencias del stage aunque este tenga condition: always().
  return [
    '  - stage: NotifyResult',
    '    dependsOn: [DeployDev, DeployQa, DeployProd]',
    '    condition: always()',
    '    jobs:',
    '      - job: NotifyPipelineResult',
    '        steps:',
    `          - bash: NOTIFICATION_CHANNEL=${channel} PIPELINE_STATUS=success ./scripts/ci-notify.sh`,
    '            displayName: Notify deployment result (success)',
    '            condition: succeeded()',
    '            env:',
    '              NOTIFICATION_WEBHOOK_URL: $(notificationWebhookUrl)',
    `          - bash: NOTIFICATION_CHANNEL=${channel} PIPELINE_STATUS=failure ./scripts/ci-notify.sh`,
    '            displayName: Notify deployment result (failure)',
    '            condition: failed()',
    '            env:',
    '              NOTIFICATION_WEBHOOK_URL: $(notificationWebhookUrl)'
  ].join('\n');
}

function progressiveAnalysisStep(strategy) {
  if (strategy === 'rolling') return null;
  return [
    '                - bash: curl --fail --retry 6 --retry-delay 10 "$(analysisMetricsSource)"',
    `                  displayName: Analyze rollout (${strategy})`,
    '                  env:',
    '                    ANALYSIS_METRICS_SOURCE: $(analysisMetricsSource)'
  ].join('\n');
}

function progressiveRequiredVar(strategy) {
  if (strategy === 'rolling') return null;
  return '                ANALYSIS_METRICS_SOURCE';
}

function progressiveEnvVar(strategy) {
  if (strategy === 'rolling') return null;
  return '              ANALYSIS_METRICS_SOURCE: $(analysisMetricsSource)';
}

function value(flag, required = false) {
  const index = args.indexOf(flag);
  if (index < 0) {
    if (required) throw new Error(`${flag} es obligatorio y debe corresponder a un OP-NNN resuelto.`);
    return null;
  }
  const result = args[index + 1];
  if (!result || result.startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return result;
}

function validateCronField(part, min, max, label) {
  for (const item of part.split(',')) {
    const match = item.match(/^(\*|\d+(?:-\d+)?)(?:\/(\d+))?$/);
    if (!match) throw new Error(`--drift-cron: campo ${label} inválido: "${item}".`);
    const [, range, step] = match;
    if (step !== undefined && Number(step) === 0) throw new Error(`--drift-cron: paso 0 en campo ${label}: "${item}".`);
    if (range !== '*') {
      const bounds = range.split('-').map(Number);
      for (const bound of bounds) {
        if (bound < min || bound > max) throw new Error(`--drift-cron: campo ${label} fuera de rango [${min}-${max}]: "${item}".`);
      }
      if (bounds.length === 2 && bounds[0] > bounds[1]) throw new Error(`--drift-cron: rango invertido en campo ${label}: "${item}".`);
    }
  }
}

function validateCron(expression) {
  const fields = expression.trim().split(/\s+/);
  if (fields.length !== 5) throw new Error('--drift-cron debe ser una expresión cron UTC de cinco campos.');
  const [minute, hour, dayOfMonth, month, dayOfWeek] = fields;
  validateCronField(minute, 0, 59, 'minuto');
  validateCronField(hour, 0, 23, 'hora');
  validateCronField(dayOfMonth, 1, 31, 'día del mes');
  validateCronField(month, 1, 12, 'mes');
  validateCronField(dayOfWeek, 0, 7, 'día de la semana');
}

function replaceOnce(text, expected, replacement, label) {
  const occurrences = text.split(expected).length - 1;
  if (occurrences === 0) throw new Error(`La plantilla ya no contiene ${label}; revisar el renderer.`);
  if (occurrences > 1) throw new Error(`La plantilla contiene ${occurrences} ocurrencias de ${label}, no una sola; revisar el renderer antes de reemplazar a ciegas.`);
  return text.replace(expected, replacement);
}

try {
  const root = path.resolve(value('--root') ?? process.cwd());
  const terraformGroup = value('--terraform-variable-group', true);
  const applicationGroup = value('--application-variable-group', true);
  const driftCron = value('--drift-cron', true);
  validateCron(driftCron);
  const deploymentStrategy = value('--deployment-strategy') ?? 'rolling';
  validateDeploymentStrategy(deploymentStrategy);
  const deploymentModel = value('--deployment-model') ?? 'push_pipeline';
  validateDeploymentModel(deploymentModel);
  if (deploymentModel === 'gitops') {
    throw new Error(
      'unsupported_adapter: las plantillas node-*-app de Azure DevOps despliegan a Azure Web ' +
      'App slots, no a Kubernetes — no están wireadas para deployment_model: gitops. Los manifiestos ' +
      'Kustomize/ArgoCD (render-bob-gitops.mjs) se generan igual; conectarlos requiere un pipeline ' +
      'de aplicación distinto a estas plantillas de referencia. Usar pipeline/github_actions o ' +
      'pipeline/gitlab si se necesita el paso de deploy de GitOps generado automáticamente.'
    );
  }
  const policyEngine = value('--policy-engine') ?? 'none';
  validatePolicyEngine(policyEngine);
  const notificationChannel = value('--notification-channel') ?? 'none';
  validateNotificationChannel(notificationChannel);
  // decisions.pipeline_topology (vulcano, 06-ci-cd.md §Integración Continua): single = un solo
  // pipeline de aplicación combinado (default, compatibilidad hacia atrás); per_component = un
  // pipeline por unidad desplegable (backend/frontend), cada uno con su propio trigger por path.
  const pipelineTopology = value('--pipeline-topology') ?? 'single';
  validatePipelineTopology(pipelineTopology);
  // Carpeta de destino de los pipelines de aplicación — decisión del arquitecto en 06-ci-cd.md,
  // no un default asumido. Vacío conserva el comportamiento histórico (raíz del repo).
  const appPipelineDirRaw = value('--app-pipeline-dir') ?? '';
  if (appPipelineDirRaw && (path.isAbsolute(appPipelineDirRaw) || appPipelineDirRaw.split(/[\\/]/).includes('..'))) {
    throw new Error('--app-pipeline-dir debe ser una ruta relativa dentro del repo, sin "..".');
  }
  const appPipelineDir = appPipelineDirRaw.replace(/[\\/]+$/, '');
  const appPipelinePath = filename => appPipelineDir ? `${appPipelineDir}/${filename}` : filename;
  for (const [label, group] of [['terraform', terraformGroup], ['application', applicationGroup]]) {
    if (!/^[A-Za-z0-9._ -]+$/.test(group)) throw new Error(`Variable group ${label} inválido.`);
  }
  const terraformVersion = value('--terraform-version', true);
  if (!/^\d+\.\d+\.\d+$/.test(terraformVersion)) throw new Error('--terraform-version debe ser una versión exacta x.y.z aprobada.');

  const assets = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'assets');
  const definitions = [
    ['azure-pipelines.terraform.template.yml', 'infra/pipelines/iac.yml', text => {
      let rendered = replaceOnce(text, 'vulcano-terraform-operations', terraformGroup, 'variable group Terraform');
      rendered = replaceMarkerLine(rendered, '# __POLICY_AS_CODE_DEV__', policyAsCodeStep(policyEngine, 'dev'));
      rendered = replaceMarkerLine(rendered, '# __POLICY_AS_CODE_QA__', policyAsCodeStep(policyEngine, 'qa', 12));
      rendered = replaceMarkerLine(rendered, '# __POLICY_AS_CODE_PROD__', policyAsCodeStep(policyEngine, 'prod', 12));
      rendered = replaceMarkerLine(rendered, '# __INSTALL_TERRAFORM_VALIDATE__', terraformInstallStep(terraformVersion, 10, { withLintTools: true }));
      rendered = replaceMarkerLine(rendered, '# __INSTALL_TERRAFORM_PLAN_DEV__', terraformInstallStep(terraformVersion, 10));
      rendered = replaceMarkerLine(rendered, '# __INSTALL_TERRAFORM_APPLY_DEV__', terraformInstallStep(terraformVersion, 16));
      rendered = replaceMarkerLine(rendered, '# __INSTALL_TERRAFORM_PLAN_QA__', terraformInstallStep(terraformVersion, 12));
      rendered = replaceMarkerLine(rendered, '# __INSTALL_TERRAFORM_APPLY_QA__', terraformInstallStep(terraformVersion, 18));
      rendered = replaceMarkerLine(rendered, '# __INSTALL_TERRAFORM_PLAN_PROD__', terraformInstallStep(terraformVersion, 12));
      rendered = replaceMarkerLine(rendered, '# __INSTALL_TERRAFORM_APPLY_PROD__', terraformInstallStep(terraformVersion, 18));
      return rendered;
    }],
    ['azure-pipelines.terraform-drift.template.yml', 'infra/pipelines/drift.yml', text => {
      let rendered = replaceOnce(text, 'vulcano-terraform-operations', terraformGroup, 'variable group Terraform');
      rendered = replaceOnce(rendered, 'cron: "0 5 * * *"', `cron: "${driftCron}"`, 'cron de drift');
      return rendered;
    }],
    ...applicationPipelineDefinitions()
  ];
  if (notificationChannel !== 'none') {
    definitions.push(['ci-notify.template.sh', 'scripts/ci-notify.sh', text => text]);
  }

  function applicationTransform(text) {
    let rendered = replaceOnce(text, 'vulcano-application-deploy', applicationGroup, 'variable group de aplicación');
    rendered = replaceMarkerLine(rendered, '# __PROGRESSIVE_DELIVERY_REQUIRED_VAR__', progressiveRequiredVar(deploymentStrategy));
    rendered = replaceMarkerLine(rendered, '# __PROGRESSIVE_DELIVERY_ENV__', progressiveEnvVar(deploymentStrategy));
    rendered = replaceMarkerLine(rendered, '# __PROGRESSIVE_DELIVERY_ANALYSIS__', progressiveAnalysisStep(deploymentStrategy));
    rendered = replaceMarkerLine(rendered, '# __NOTIFICATION_STAGE__', notificationStage(notificationChannel));
    return rendered;
  }

  function applicationPipelineDefinitions() {
    if (pipelineTopology === 'single') {
      return [['azure-pipelines.node-angular-app.template.yml', appPipelinePath('azure-pipelines.yml'), applicationTransform]];
    }
    return [
      ['azure-pipelines.node-backend-app.template.yml', appPipelinePath('backend.yml'), applicationTransform],
      ['azure-pipelines.node-frontend-app.template.yml', appPipelinePath('frontend.yml'), applicationTransform]
    ];
  }

  for (const [asset, destination, render] of definitions) {
    const target = path.join(root, destination);
    if (fs.existsSync(target) && !args.includes('--force')) {
      throw new Error(`${normalize(destination)} ya existe; usar --force solo después de reconciliarlo.`);
    }
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, render(fs.readFileSync(path.join(assets, asset), 'utf8')), 'utf8');
    console.log(`Renderizado ${normalize(destination)}.`);
  }
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
