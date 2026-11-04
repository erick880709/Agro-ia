import fs from 'node:fs';
import path from 'node:path';

export const normalize = value => value.replaceAll('\\', '/');

export function argValue(args, flag, required = false) {
  const index = args.indexOf(flag);
  if (index < 0) {
    if (required) throw new Error(`${flag} es obligatorio.`);
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
    if (step !== undefined && Number(step) === 0) throw new Error(`--drift-cron: paso 0 en campo ${label}.`);
    if (range === '*') continue;
    const bounds = range.split('-').map(Number);
    if (bounds.some(bound => bound < min || bound > max)) {
      throw new Error(`--drift-cron: campo ${label} fuera de rango [${min}-${max}].`);
    }
    if (bounds.length === 2 && bounds[0] > bounds[1]) throw new Error(`--drift-cron: rango invertido en campo ${label}.`);
  }
}

export function validateCron(expression) {
  const fields = expression.trim().split(/\s+/);
  if (fields.length !== 5) throw new Error('--drift-cron debe ser una expresión cron UTC de cinco campos.');
  const ranges = [[0, 59, 'minuto'], [0, 23, 'hora'], [1, 31, 'día'], [1, 12, 'mes'], [0, 7, 'día de semana']];
  fields.forEach((field, index) => validateCronField(field, ...ranges[index]));
}

export const DEPLOYMENT_STRATEGIES = ['rolling', 'canary', 'blue_green'];

/**
 * Valida que la estrategia de despliegue solicitada sea una de las soportadas por los renderers.
 * @param {string} strategy - Valor recibido de `--deployment-strategy`.
 * @throws {Error} Si `strategy` no es rolling, canary o blue_green.
 */
export function validateDeploymentStrategy(strategy) {
  if (!DEPLOYMENT_STRATEGIES.includes(strategy)) {
    throw new Error(`--deployment-strategy debe ser rolling, canary o blue_green (recibido "${strategy}").`);
  }
}

export const POLICY_ENGINES = ['none', 'opa', 'conftest'];

/**
 * Valida el motor de policy as code solicitado para el gate de `plan` en el pipeline de IaC.
 * @param {string} engine - Valor recibido de `--policy-engine`.
 * @throws {Error} Si `engine` no es none, opa o conftest.
 */
export function validatePolicyEngine(engine) {
  if (!POLICY_ENGINES.includes(engine)) {
    throw new Error(`--policy-engine debe ser none, opa o conftest (recibido "${engine}").`);
  }
}

export const NOTIFICATION_CHANNELS = ['none', 'slack', 'teams'];

/**
 * Valida el canal de notificación solicitado para el job/stage final del pipeline de aplicación.
 * @param {string} channel - Valor recibido de `--notification-channel`.
 * @throws {Error} Si `channel` no es none, slack o teams.
 */
export function validateNotificationChannel(channel) {
  if (!NOTIFICATION_CHANNELS.includes(channel)) {
    throw new Error(`--notification-channel debe ser none, slack o teams (recibido "${channel}").`);
  }
}

export const DEPLOYMENT_MODELS = ['push_pipeline', 'gitops'];

/**
 * Valida el modelo de despliegue solicitado (push directo desde el pipeline vs. GitOps).
 * @param {string} model - Valor recibido de `--deployment-model`.
 * @throws {Error} Si `model` no es push_pipeline o gitops.
 */
export function validateDeploymentModel(model) {
  if (!DEPLOYMENT_MODELS.includes(model)) {
    throw new Error(`--deployment-model debe ser push_pipeline o gitops (recibido "${model}").`);
  }
}

export const PIPELINE_TOPOLOGIES = ['single', 'per_component'];

/**
 * Valida la topología de pipeline de aplicación solicitada — un pipeline combinado vs. uno por
 * componente desplegable (ver decisions.pipeline_topology en el manifiesto de Vulcano).
 * @param {string} topology - Valor recibido de `--pipeline-topology`.
 * @throws {Error} Si `topology` no es single o per_component.
 */
export function validatePipelineTopology(topology) {
  if (!PIPELINE_TOPOLOGIES.includes(topology)) {
    throw new Error(`--pipeline-topology debe ser single o per_component (recibido "${topology}").`);
  }
}

/**
 * Reemplaza una única ocurrencia exacta de `expected` en `text`, sin reemplazos a ciegas cuando
 * hay cero o más de una coincidencia.
 * @param {string} text - Contenido de la plantilla ya renderizada.
 * @param {string} expected - Bloque literal que debe existir exactamente una vez.
 * @param {string} replacement - Contenido con el que se reemplaza `expected`.
 * @param {string} label - Descripción usada en el mensaje de error.
 * @returns {string} El texto con el reemplazo aplicado.
 * @throws {Error} Si `expected` no aparece, o aparece más de una vez.
 */
export function replaceOnce(text, expected, replacement, label) {
  const occurrences = text.split(expected).length - 1;
  if (occurrences === 0) throw new Error(`La plantilla ya no contiene ${label}; revisar el renderer.`);
  if (occurrences > 1) throw new Error(`La plantilla contiene ${occurrences} ocurrencias de ${label}, no una sola; revisar el renderer antes de reemplazar a ciegas.`);
  return text.replace(expected, replacement);
}

/**
 * Reemplaza (o elimina) todas las líneas cuyo contenido, sin espacios, coincida con `marker`.
 * @param {string} text - Contenido de la plantilla ya renderizada.
 * @param {string} marker - Línea marcadora a ubicar (comparada con `trim()`).
 * @param {string|null} replacement - Línea de reemplazo, o `null` para eliminar el marcador.
 * @returns {string} El texto con el marcador reemplazado o eliminado.
 * @throws {Error} Si el marcador no existe en `text`.
 */
export function replaceMarkerLine(text, marker, replacement) {
  const lines = text.split('\n');
  const indices = [];
  lines.forEach((line, index) => { if (line.trim() === marker.trim()) indices.push(index); });
  if (indices.length === 0) throw new Error(`La plantilla ya no contiene el marcador "${marker.trim()}"; revisar el renderer.`);
  for (const index of [...indices].reverse()) {
    if (replacement === null) lines.splice(index, 1);
    else lines[index] = replacement;
  }
  return lines.join('\n');
}

export function renderFiles(root, assets, definitions, force = false) {
  for (const [asset, destination, transform = text => text] of definitions) {
    const target = path.resolve(root, destination);
    const relative = path.relative(root, target);
    if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error(`Destino fuera del workspace: ${destination}.`);
    if (fs.existsSync(target) && !force) throw new Error(`${normalize(destination)} ya existe; usar --force solo despues de reconciliarlo.`);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, transform(fs.readFileSync(path.join(assets, asset), 'utf8')), 'utf8');
    console.log(`Renderizado ${normalize(destination)}.`);
  }
}

export function cloudAuth(cloud, indent) {
  const pad = ' '.repeat(indent);
  if (cloud === 'aws') {
    return [
      `${pad}- name: Authenticate to AWS with OIDC`,
      `${pad}  uses: aws-actions/configure-aws-credentials@v5`,
      `${pad}  with:`,
      `${pad}    role-to-assume: \${{ vars.AWS_ROLE_TO_ASSUME }}`,
      `${pad}    aws-region: \${{ vars.AWS_REGION }}`
    ].join('\n');
  }
  if (cloud === 'azure') {
    return [
      `${pad}- name: Authenticate to Azure with OIDC`,
      `${pad}  uses: azure/login@v2`,
      `${pad}  with:`,
      `${pad}    client-id: \${{ vars.AZURE_CLIENT_ID }}`,
      `${pad}    tenant-id: \${{ vars.AZURE_TENANT_ID }}`,
      `${pad}    subscription-id: \${{ vars.AZURE_SUBSCRIPTION_ID }}`
    ].join('\n');
  }
  throw new Error(`Cloud no soportada por el renderer: ${cloud}.`);
}
