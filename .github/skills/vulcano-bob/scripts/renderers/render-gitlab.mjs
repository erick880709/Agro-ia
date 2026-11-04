#!/usr/bin/env node

import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  argValue, renderFiles, replaceMarkerLine, replaceOnce,
  validateCron, validateDeploymentModel, validateDeploymentStrategy, validateNotificationChannel, validatePolicyEngine
} from './renderer-lib.mjs';

const args = process.argv.slice(2);

const PUSH_DEPLOY_SCRIPT_LINE = '    - ./scripts/ci-deploy.sh';
const GITOPS_DEPLOY_SCRIPT_LINE = '    - IMAGE_TAG="$CI_COMMIT_SHA" ./scripts/ci-update-gitops-manifests.sh';

function progressiveAnalysisScriptLine(strategy) {
  if (strategy === 'rolling') return null;
  return '    - ANALYSIS_METRICS_SOURCE="$ANALYSIS_METRICS_SOURCE" ./scripts/ci-analyze-rollout.sh';
}

function progressiveRollbackJob(strategy) {
  if (strategy === 'rolling') return null;
  return [
    'application_rollback:',
    '  stage: deploy',
    '  image: $DEPLOY_IMAGE',
    '  needs: [application_deploy]',
    '  parallel:',
    '    matrix:',
    '      - DEPLOY_ENVIRONMENT: [dev, qa, prod]',
    '  environment: $DEPLOY_ENVIRONMENT',
    '  script:',
    '    - ./scripts/ci-rollback.sh',
    '  rules:',
    "    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'",
    '      when: on_failure'
  ].join('\n');
}

function policyAsCodeScriptLine(engine) {
  if (engine === 'none') return null;
  return `    - POLICY_ENGINE=${engine} ./scripts/ci-policy-check.sh tfplan`;
}

function notificationJob(channel) {
  if (channel === 'none') return null;
  // Dos jobs (on_success/on_failure) en vez de uno con when: always — GitLab no expone un
  // resultado agregado legible dentro del script sin correlacionar jobs manualmente, así que cada
  // job fija su propio PIPELINE_STATUS según la regla que lo dispara.
  return [
    'application_notify_success:',
    '  stage: deploy',
    '  image: $DEPLOY_IMAGE',
    '  needs: [application_deploy]',
    '  parallel:',
    '    matrix:',
    '      - DEPLOY_ENVIRONMENT: [dev, qa, prod]',
    '  environment: $DEPLOY_ENVIRONMENT',
    '  variables:',
    `    NOTIFICATION_CHANNEL: ${channel}`,
    '    PIPELINE_STATUS: success',
    '  script:',
    '    - ./scripts/ci-notify.sh',
    '  rules:',
    "    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'",
    '      when: on_success',
    '',
    'application_notify_failure:',
    '  stage: deploy',
    '  image: $DEPLOY_IMAGE',
    '  needs: [application_deploy]',
    '  parallel:',
    '    matrix:',
    '      - DEPLOY_ENVIRONMENT: [dev, qa, prod]',
    '  environment: $DEPLOY_ENVIRONMENT',
    '  variables:',
    `    NOTIFICATION_CHANNEL: ${channel}`,
    '    PIPELINE_STATUS: failure',
    '  script:',
    '    - ./scripts/ci-notify.sh',
    '  rules:',
    "    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'",
    '      when: on_failure'
  ].join('\n');
}

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const cloud = argValue(args, '--adapter-cloud', true);
  if (!['azure', 'aws'].includes(cloud)) throw new Error(`Cloud no soportada por GitLab CI: ${cloud}.`);
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
  // GitLab busca `.gitlab-ci.yml` en la raíz salvo que el proyecto reconfigure el "CI/CD
  // configuration file" en su configuración (un ajuste de plataforma, no un parámetro de este
  // renderer) — a diferencia de Azure DevOps, mover el archivo aquí sin ese ajuste produce un
  // pipeline que GitLab no encuentra. Los includes (`iac.yml`, `drift.yml`) sí ya viven en
  // `.gitlab/ci/`, organizados aparte del entrypoint.
  const assets = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'assets');
  const replace = text => text.replaceAll('__CLOUD__', cloud)
    .replaceAll('__TERRAFORM_VERSION__', terraformVersion)
    .replace('__DRIFT_CRON__', driftCron);
  const replaceIac = text => replaceMarkerLine(replace(text), '# __POLICY_AS_CODE__', policyAsCodeScriptLine(policyEngine));
  const replaceApplication = text => {
    const rendered = replace(text);
    const withDeploy = deploymentModel === 'gitops'
      ? replaceOnce(rendered, PUSH_DEPLOY_SCRIPT_LINE, GITOPS_DEPLOY_SCRIPT_LINE, 'el script de deploy push-based')
      : rendered;
    const withAnalysis = replaceMarkerLine(withDeploy, '# __PROGRESSIVE_DELIVERY_ANALYSIS__', progressiveAnalysisScriptLine(deploymentStrategy));
    const withRollback = replaceMarkerLine(withAnalysis, '# __PROGRESSIVE_DELIVERY_ROLLBACK_JOB__', progressiveRollbackJob(deploymentStrategy));
    return replaceMarkerLine(withRollback, '# __NOTIFICATION_JOB__', notificationJob(notificationChannel));
  };
  const definitions = [
    ['gitlab.terraform.template.yml', '.gitlab/ci/iac.yml', replaceIac],
    ['gitlab.terraform-drift.template.yml', '.gitlab/ci/drift.yml', replace],
    ['gitlab.application.template.yml', '.gitlab-ci.yml', replaceApplication]
  ];
  if (notificationChannel !== 'none') {
    definitions.push(['ci-notify.template.sh', 'scripts/ci-notify.sh', text => text]);
  }
  renderFiles(root, assets, definitions, args.includes('--force'));
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
