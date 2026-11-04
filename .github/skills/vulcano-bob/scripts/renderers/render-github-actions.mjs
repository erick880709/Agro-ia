#!/usr/bin/env node

import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  argValue, cloudAuth, renderFiles, replaceMarkerLine, replaceOnce,
  validateCron, validateDeploymentModel, validateDeploymentStrategy, validateNotificationChannel, validatePolicyEngine
} from './renderer-lib.mjs';

const args = process.argv.slice(2);

const PUSH_DEPLOY_STEP = [
  '      - name: Deploy and verify health',
  '        env:',
  '          DEPLOY_ENVIRONMENT: ${{ matrix.environment }}',
  '        run: ./scripts/ci-deploy.sh'
].join('\n');

const GITOPS_DEPLOY_STEP = [
  '      - name: Update GitOps manifests',
  '        env:',
  '          DEPLOY_ENVIRONMENT: ${{ matrix.environment }}',
  '          IMAGE_TAG: ${{ github.sha }}',
  '        run: ./scripts/ci-update-gitops-manifests.sh'
].join('\n');

function policyAsCodeStep(engine, indent) {
  if (engine === 'none') return null;
  const pad = ' '.repeat(indent);
  return [
    `${pad}- name: Policy as code check`,
    `${pad}  working-directory: infra/environments/\${{ matrix.environment }}`,
    `${pad}  env:`,
    `${pad}    POLICY_ENGINE: ${engine}`,
    `${pad}  run: ./scripts/ci-policy-check.sh tfplan`
  ].join('\n');
}

function notificationJob(channel, indent) {
  if (channel === 'none') return null;
  const pad = ' '.repeat(indent);
  // Dos steps con if: success()/failure() en vez de que ci-notify.sh adivine el resultado —
  // ambos evalúan el estado agregado del job `deploy` del que este job depende, aunque el job
  // en sí tenga if: always().
  return [
    `${pad}notify:`,
    `${pad}  if: always()`,
    `${pad}  needs: deploy`,
    `${pad}  runs-on: ubuntu-latest`,
    `${pad}  steps:`,
    `${pad}    - name: Notify deployment result (success)`,
    `${pad}      if: success()`,
    `${pad}      env:`,
    `${pad}        NOTIFICATION_CHANNEL: ${channel}`,
    `${pad}        PIPELINE_STATUS: success`,
    `${pad}        NOTIFICATION_WEBHOOK_URL: \${{ secrets.NOTIFICATION_WEBHOOK_URL }}`,
    `${pad}      run: ./scripts/ci-notify.sh`,
    `${pad}    - name: Notify deployment result (failure)`,
    `${pad}      if: failure()`,
    `${pad}      env:`,
    `${pad}        NOTIFICATION_CHANNEL: ${channel}`,
    `${pad}        PIPELINE_STATUS: failure`,
    `${pad}        NOTIFICATION_WEBHOOK_URL: \${{ secrets.NOTIFICATION_WEBHOOK_URL }}`,
    `${pad}      run: ./scripts/ci-notify.sh`
  ].join('\n');
}

function progressiveAnalysisStep(strategy, indent) {
  if (strategy === 'rolling') return null;
  const pad = ' '.repeat(indent);
  return [
    `${pad}- name: Analyze rollout (${strategy})`,
    `${pad}  env:`,
    `${pad}    DEPLOY_ENVIRONMENT: \${{ matrix.environment }}`,
    `${pad}    ANALYSIS_METRICS_SOURCE: \${{ vars.ANALYSIS_METRICS_SOURCE }}`,
    `${pad}  run: ./scripts/ci-analyze-rollout.sh`
  ].join('\n');
}

function progressiveRollbackStep(strategy, indent) {
  if (strategy === 'rolling') return null;
  const pad = ' '.repeat(indent);
  return [
    `${pad}- name: Abort and rollback (${strategy})`,
    `${pad}  if: failure()`,
    `${pad}  env:`,
    `${pad}    DEPLOY_ENVIRONMENT: \${{ matrix.environment }}`,
    `${pad}  run: ./scripts/ci-rollback.sh`
  ].join('\n');
}

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const cloud = argValue(args, '--adapter-cloud', true);
  const driftCron = argValue(args, '--drift-cron', true);
  const terraformVersion = argValue(args, '--terraform-version', true);
  if (!/^\d+\.\d+\.\d+$/.test(terraformVersion)) throw new Error('--terraform-version debe ser una versión exacta x.y.z aprobada.');
  const deploymentStrategy = argValue(args, '--deployment-strategy') ?? 'rolling';
  validateDeploymentStrategy(deploymentStrategy);
  const deploymentModel = argValue(args, '--deployment-model') ?? 'push_pipeline';
  validateDeploymentModel(deploymentModel);
  const policyEngine = argValue(args, '--policy-engine') ?? 'none';
  validatePolicyEngine(policyEngine);
  const notificationChannel = argValue(args, '--notification-channel') ?? 'none';
  validateNotificationChannel(notificationChannel);
  validateCron(driftCron);
  // A diferencia de Azure DevOps, GitHub Actions solo ejecuta workflows ubicados literalmente en
  // `.github/workflows/` — no hay una carpeta de destino que parametrizar aquí sin producir un
  // workflow que GitHub ignora en silencio. La única variable real es el nombre del archivo
  // dentro de esa carpeta, ya cubierto por el segundo elemento de cada definición de abajo.
  const assets = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'assets');
  const replace = text => text
    .replaceAll('__TERRAFORM_VERSION__', terraformVersion)
    .replaceAll('      # __CLOUD_AUTH__', cloudAuth(cloud, 6));
  const replaceIac = text => replaceMarkerLine(replace(text), '# __POLICY_AS_CODE__', policyAsCodeStep(policyEngine, 6));
  const replaceApplication = text => {
    const rendered = replace(text);
    const withDeploy = deploymentModel === 'gitops'
      ? replaceOnce(rendered, PUSH_DEPLOY_STEP, GITOPS_DEPLOY_STEP, 'el step de deploy push-based')
      : rendered;
    const withAnalysis = replaceMarkerLine(withDeploy, '# __PROGRESSIVE_DELIVERY_ANALYSIS__', progressiveAnalysisStep(deploymentStrategy, 6));
    const withRollback = replaceMarkerLine(withAnalysis, '# __PROGRESSIVE_DELIVERY_ROLLBACK__', progressiveRollbackStep(deploymentStrategy, 6));
    return replaceMarkerLine(withRollback, '# __NOTIFICATION_JOB__', notificationJob(notificationChannel, 2));
  };
  const definitions = [
    ['github-actions.terraform.template.yml', '.github/workflows/iac.yml', replaceIac],
    ['github-actions.terraform-drift.template.yml', '.github/workflows/drift.yml', text =>
      replace(text).replace("cron: '0 5 * * *'", `cron: '${driftCron}'`)],
    ['github-actions.application.template.yml', '.github/workflows/application.yml', replaceApplication]
  ];
  if (notificationChannel !== 'none') {
    definitions.push(['ci-notify.template.sh', 'scripts/ci-notify.sh', text => text]);
  }
  renderFiles(root, assets, definitions, args.includes('--force'));
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
