#!/usr/bin/env node
// Colector de métricas DORA: deployment frequency, change lead time, failed deployment
// recovery time, change fail rate y deployment rework rate. Lee el historial de deployments
// desde la API nativa de la plataforma CI usando el token ya disponible en el runtime — no
// requiere un secreto adicional. Ver references/dora-collector.md para el detalle de cada
// endpoint y su nivel de certeza documentado por plataforma.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REWORK_WINDOW_HOURS = Number(process.env.DORA_REWORK_WINDOW_HOURS ?? 24);
const WINDOW_DAYS = Number(process.env.DORA_WINDOW_DAYS ?? 30);

function detectPlatform() {
  if (process.env.GITHUB_ACTIONS === 'true') return 'github_actions';
  if (process.env.GITLAB_CI === 'true') return 'gitlab';
  if (process.env.TF_BUILD === 'True') return 'azure_devops';
  throw new Error('No se detectó una plataforma CI soportada (GITHUB_ACTIONS, GITLAB_CI, TF_BUILD).');
}

/**
 * Resuelve la lista de componentes a medir por separado desde `DORA_COMPONENTS`
 * (`decisions.pipeline_topology: per_component` en Vulcano). Sin la variable (o vacía), devuelve
 * el componente único implícito `app` — comportamiento idéntico al colector previo a esta
 * capacidad, para no romper ningún proyecto ya generado con topología `single`.
 * @param {string|undefined} raw - Valor crudo de `DORA_COMPONENTS` (lista separada por comas).
 * @returns {string[]} Nombres de componente, en minúsculas, sin duplicados.
 * @throws {Error} Si algún nombre no es `[a-z0-9-]+` o hay un nombre repetido.
 */
export function parseComponents(raw) {
  if (!raw || !raw.trim()) return ['app'];
  const names = raw.split(',').map(name => name.trim()).filter(Boolean);
  if (names.length === 0) return ['app'];
  const seen = new Set();
  for (const name of names) {
    if (!/^[a-z0-9-]+$/.test(name)) {
      throw new Error(`DORA_COMPONENTS: nombre de componente inválido "${name}" (usar minúsculas, dígitos y guiones).`);
    }
    if (seen.has(name)) throw new Error(`DORA_COMPONENTS: componente duplicado "${name}".`);
    seen.add(name);
  }
  return names;
}

function isSingleComponent(components) {
  return components.length === 1 && components[0] === 'app';
}

function componentEnvSuffix(component) {
  return component.toUpperCase().replaceAll('-', '_');
}

function environmentNameFor(component, components) {
  return isSingleComponent(components) ? 'prod' : `prod-${component}`;
}

async function fetchJson(url, headers) {
  const response = await fetch(url, { headers });
  if (!response.ok) throw new Error(`${url} respondió ${response.status}: ${await response.text()}`);
  return response.json();
}

// --- Fetchers: cada uno normaliza a [{ environment, status, started_at, completed_at, sha }] ---

async function fetchGitHubDeployments({ token, repository, apiUrl, environment, since }) {
  const headers = { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' };
  const deployments = await fetchJson(
    `${apiUrl}/repos/${repository}/deployments?environment=${encodeURIComponent(environment)}&per_page=100`, headers
  );
  const events = [];
  for (const deployment of deployments) {
    if (new Date(deployment.created_at) < since) continue;
    const statuses = await fetchJson(`${apiUrl}/repos/${repository}/deployments/${deployment.id}/statuses?per_page=10`, headers);
    const finalStatus = statuses.find(status => ['success', 'failure', 'error'].includes(status.state));
    events.push({
      environment: deployment.environment,
      status: finalStatus?.state === 'success' ? 'success' : 'failure',
      started_at: deployment.created_at,
      completed_at: finalStatus?.created_at ?? deployment.created_at,
      sha: deployment.sha
    });
  }
  return events;
}

async function fetchGitLabDeployments({ token, apiUrl, projectId, environment, since }) {
  const headers = { 'PRIVATE-TOKEN': token };
  const deployments = await fetchJson(
    `${apiUrl}/projects/${projectId}/deployments?environment=${encodeURIComponent(environment)}&order_by=created_at&sort=desc&per_page=100`,
    headers
  );
  return deployments
    .filter(deployment => new Date(deployment.created_at) >= since)
    .map(deployment => ({
      environment: deployment.environment?.name ?? environment,
      status: deployment.status === 'success' ? 'success' : 'failure',
      started_at: deployment.created_at,
      completed_at: deployment.updated_at ?? deployment.created_at,
      sha: deployment.sha
    }));
}

async function fetchAzureDevOpsDeployments({ token, collectionUri, project, environmentId, since }) {
  // NOTA: la API de deployment records de Environments (`_apis/pipelines/environments/
  // {environmentId}/environmentdeploymentrecords`) es relativamente reciente y su contrato/
  // versión ha cambiado entre releases de Azure DevOps — verificar contra la documentación
  // vigente antes de depender de este dato en producción (mismo criterio que
  // references/estandares-operativos.md aplica al resto del kit).
  const headers = { Authorization: `Basic ${Buffer.from(`:${token}`).toString('base64')}` };
  const url = `${collectionUri}${project}/_apis/pipelines/environments/${environmentId}/environmentdeploymentrecords?api-version=7.1-preview.1`;
  const result = await fetchJson(url, headers);
  return (result.value ?? [])
    .filter(record => new Date(record.startTime) >= since)
    .map(record => ({
      environment: 'prod',
      status: record.result === 'succeeded' ? 'success' : 'failure',
      started_at: record.startTime,
      completed_at: record.finishTime ?? record.startTime,
      sha: record.definition?.id ?? null
    }));
}

async function fetchComponentEvents(platform, component, components, since) {
  if (platform === 'github_actions') {
    return fetchGitHubDeployments({
      token: process.env.GITHUB_TOKEN,
      repository: process.env.GITHUB_REPOSITORY,
      apiUrl: process.env.GITHUB_API_URL ?? 'https://api.github.com',
      environment: environmentNameFor(component, components),
      since
    });
  }
  if (platform === 'gitlab') {
    return fetchGitLabDeployments({
      token: process.env.CI_JOB_TOKEN,
      apiUrl: process.env.CI_API_V4_URL,
      projectId: process.env.CI_PROJECT_ID,
      environment: environmentNameFor(component, components),
      since
    });
  }
  const environmentIdVar = isSingleComponent(components) ? 'DORA_ENVIRONMENT_ID' : `DORA_ENVIRONMENT_ID_${componentEnvSuffix(component)}`;
  const environmentId = process.env[environmentIdVar];
  if (!environmentId) throw new Error(`${environmentIdVar} no está definido (requerido para el componente "${component}").`);
  return fetchAzureDevOpsDeployments({
    token: process.env.SYSTEM_ACCESSTOKEN,
    collectionUri: process.env.SYSTEM_COLLECTIONURI,
    project: process.env.SYSTEM_TEAMPROJECT,
    environmentId,
    since
  });
}

// --- Cálculo de métricas: función pura, testable sin red ---

/**
 * Calcula las cinco métricas DORA vigentes a partir de una lista normalizada de eventos de
 * deployment. Función pura, sin acceso a red — testable de forma aislada.
 * @param {Array<{status: 'success'|'failure', started_at: string, completed_at: string}>} events
 *   Eventos de deployment ya normalizados (ver `fetchGitHubDeployments`/`fetchGitLabDeployments`/
 *   `fetchAzureDevOpsDeployments`).
 * @param {{reworkWindowHours?: number}} [options] - Ventana en horas para considerar dos
 *   despliegues exitosos consecutivos como "rework" (default: `DORA_REWORK_WINDOW_HOURS`).
 * @returns {{
 *   deployment_frequency_per_day: number|null,
 *   change_lead_time_hours: number|null,
 *   failed_deployment_recovery_time_hours: number|null,
 *   change_fail_rate: number|null,
 *   deployment_rework_rate: number|null,
 *   sample_size: number,
 *   note: string
 * }} Dataset de métricas, con `null` en cualquier campo sin datos suficientes para calcularlo.
 */
export function computeDoraMetrics(events, { reworkWindowHours = REWORK_WINDOW_HOURS } = {}) {
  const sorted = [...events].sort((a, b) => new Date(a.completed_at) - new Date(b.completed_at));
  const total = sorted.length;
  if (total === 0) {
    return {
      deployment_frequency_per_day: null,
      change_lead_time_hours: null,
      failed_deployment_recovery_time_hours: null,
      change_fail_rate: null,
      deployment_rework_rate: null,
      sample_size: 0,
      note: 'Sin deployments en la ventana consultada; no se infiere una métrica.'
    };
  }

  const successes = sorted.filter(event => event.status === 'success');
  const failures = sorted.filter(event => event.status === 'failure');

  const windowStart = new Date(sorted[0].completed_at);
  const windowEnd = new Date(sorted[sorted.length - 1].completed_at);
  const windowDays = Math.max((windowEnd - windowStart) / (1000 * 60 * 60 * 24), 1);
  const deploymentFrequencyPerDay = successes.length / windowDays;

  const leadTimes = successes
    .map(event => (new Date(event.completed_at) - new Date(event.started_at)) / (1000 * 60 * 60))
    .filter(hours => Number.isFinite(hours) && hours >= 0);
  const changeLeadTimeHours = leadTimes.length > 0
    ? leadTimes.reduce((sum, hours) => sum + hours, 0) / leadTimes.length
    : null;

  const recoveryTimes = [];
  for (let index = 0; index < sorted.length; index += 1) {
    if (sorted[index].status !== 'failure') continue;
    const nextSuccess = sorted.slice(index + 1).find(event => event.status === 'success');
    if (nextSuccess) {
      recoveryTimes.push((new Date(nextSuccess.completed_at) - new Date(sorted[index].completed_at)) / (1000 * 60 * 60));
    }
  }
  const failedDeploymentRecoveryTimeHours = recoveryTimes.length > 0
    ? recoveryTimes.reduce((sum, hours) => sum + hours, 0) / recoveryTimes.length
    : null;

  const changeFailRate = failures.length / total;

  let reworked = 0;
  for (let index = 0; index < successes.length - 1; index += 1) {
    const gapHours = (new Date(successes[index + 1].completed_at) - new Date(successes[index].completed_at)) / (1000 * 60 * 60);
    if (gapHours <= reworkWindowHours) reworked += 1;
  }
  const deploymentReworkRate = successes.length > 1 ? reworked / (successes.length - 1) : null;

  return {
    deployment_frequency_per_day: deploymentFrequencyPerDay,
    change_lead_time_hours: changeLeadTimeHours,
    failed_deployment_recovery_time_hours: failedDeploymentRecoveryTimeHours,
    change_fail_rate: changeFailRate,
    deployment_rework_rate: deploymentReworkRate,
    sample_size: total,
    note: 'change_lead_time_hours aproxima desde el inicio del deployment, no desde el commit ' +
      'original; deployment_rework_rate aproxima "rework" como despliegues exitosos consecutivos ' +
      `separados por ${reworkWindowHours}h o menos. Ambas son aproximaciones declaradas, no una ` +
      'medición exacta del DORA Quick Check oficial.'
  };
}

async function main() {
  const platform = detectPlatform();
  const since = new Date(Date.now() - WINDOW_DAYS * 24 * 60 * 60 * 1000);
  const components = parseComponents(process.env.DORA_COMPONENTS);

  const perComponent = {};
  for (const component of components) {
    perComponent[component] = computeDoraMetrics(await fetchComponentEvents(platform, component, components, since));
  }

  const dataset = isSingleComponent(components)
    ? { generated_at: new Date().toISOString(), platform, window_days: WINDOW_DAYS, metrics: perComponent.app }
    : { generated_at: new Date().toISOString(), platform, window_days: WINDOW_DAYS, components: perComponent };

  const outputPath = process.env.DORA_OUTPUT_PATH ?? 'dora-metrics.json';
  fs.mkdirSync(path.dirname(path.resolve(outputPath)), { recursive: true });
  fs.writeFileSync(outputPath, `${JSON.stringify(dataset, null, 2)}\n`, 'utf8');

  const summary = isSingleComponent(components)
    ? `${perComponent.app.sample_size} deployments`
    : components.map(name => `${name}: ${perComponent[name].sample_size} deployments`).join(', ');
  console.log(`DORA dataset escrito en ${outputPath} (${summary}, plataforma ${platform}).`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  main().catch(error => {
    console.error(`ERROR: ${error.message}`);
    process.exit(1);
  });
}
