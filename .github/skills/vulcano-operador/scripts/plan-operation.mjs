#!/usr/bin/env node

import path from 'node:path';
import { resolveOperatorAdapters } from './adapter-registry.mjs';
import { argValue, assertBobUnchanged, assertSanitized, loadContext, readJsonFile, scopeFor, updateDate, writeYaml } from './operations-lib.mjs';

const args = process.argv.slice(2);

// Tipos que promueven un despliegue hacia adelante — requieren progresión dev -> qa -> prod.
// rollback_deployment, cancel_pipeline_run y las acciones "configure" (register_pipeline,
// create_environment, update_variable_group, configure_branch_policy, tag_release) quedan fuera
// a propósito: no promueven nada, o son correctivas/de configuración sin orden de ambiente.
const PROGRESSIVE_DEPLOY_TYPES = new Set(['queue_pipeline', 'approve_deployment', 'promote_release']);
const ENVIRONMENT_ORDER = ['dev', 'qa', 'prod'];

/**
 * Exige que, para promover `logicalId` a `environment`, ya exista una acción `verified` (con
 * `verification.result === 'succeeded'`) del mismo `logicalId` en el ambiente inmediatamente
 * anterior — nunca saltar de dev directo a prod, ni de qa a prod sin que dev/qa hayan pasado por
 * verificación real. No aplica al primer ambiente de la secuencia (no tiene predecesor).
 * @param {Record<string, object>} actions - `context.operations.actions` actual.
 * @param {string} logicalId - `logical_id` de Bob que se está promoviendo.
 * @param {string} environment - Ambiente objetivo de esta acción (`dev`/`qa`/`prod`).
 * @throws {Error} Si el ambiente anterior no tiene una acción verificada con éxito.
 */
function assertEnvironmentProgression(actions, logicalId, environment) {
  const index = ENVIRONMENT_ORDER.indexOf(environment);
  if (index <= 0) return;
  const priorEnvironment = ENVIRONMENT_ORDER[index - 1];
  const priorVerified = Object.values(actions ?? {}).some(action =>
    action.logical_id === logicalId &&
    action.environment === priorEnvironment &&
    action.status === 'verified' &&
    action.verification?.result === 'succeeded'
  );
  if (!priorVerified) {
    throw new Error(
      `Progresión bloqueada: no hay una acción verified con éxito para "${logicalId}" en ` +
      `"${priorEnvironment}" — no se puede promover directo a "${environment}" sin pasar primero ` +
      `por ${priorEnvironment}.`
    );
  }
}

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const resources = path.resolve(argValue(args, '--resources-dir') ?? path.join(root, 'resources'));
  const context = loadContext(root, resources);
  assertBobUnchanged(context);
  const resolved = resolveOperatorAdapters(context.bob);
  if (context.operations.operator_selection?.platform !== resolved.selection.platform ||
      context.operations.operator_selection?.cloud !== resolved.selection.cloud) {
    throw new Error('operator_selection no coincide con Bob.');
  }
  if (context.operations.gate.status !== 'ready' || context.operations.capabilities.platform_mcp !== 'available') {
    throw new Error(`Se requiere reconciliación lista con ${resolved.platform.mcp_capability} disponible.`);
  }
  const observedAt = Date.parse(context.operations.reconciliation.observed_at ?? '');
  if (!Number.isFinite(observedAt) || Date.now() - observedAt > 30 * 60 * 1000) throw new Error('La reconciliación tiene más de 30 minutos; repetirla.');
  const id = argValue(args, '--id', true);
  if (!/^OP-ACT-\d{3}$/.test(id)) throw new Error('--id debe usar OP-ACT-NNN.');
  if (context.operations.actions?.[id]) throw new Error(`${id} ya existe.`);
  const type = argValue(args, '--type', true);
  const risk = resolved.platform.allowed_actions?.[type];
  if (!risk) throw new Error(`Tipo no permitido por platform/${resolved.platform.id}: ${type}.`);
  const mcpUnsupportedReason = resolved.platform.mcp_unsupported_actions?.[type];
  if (mcpUnsupportedReason) {
    throw new Error(`missing_capability: ${type} no tiene herramienta MCP en platform/${resolved.platform.id}. ${mcpUnsupportedReason}`);
  }
  const logicalId = argValue(args, '--logical-id', true);
  if (!context.bob.artifacts?.[logicalId]) throw new Error(`logical_id no existe en Bob: ${logicalId}.`);
  const environment = argValue(args, '--environment');
  if (PROGRESSIVE_DEPLOY_TYPES.has(type)) {
    if (!environment) {
      throw new Error(`--environment (dev, qa o prod) es obligatorio para ${type} — exige progresión dev -> qa -> prod.`);
    }
    if (!ENVIRONMENT_ORDER.includes(environment)) throw new Error('--environment debe ser dev, qa o prod.');
    assertEnvironmentProgression(context.operations.actions, logicalId, environment);
  } else if (environment && !ENVIRONMENT_ORDER.includes(environment)) {
    throw new Error('--environment debe ser dev, qa o prod.');
  }
  const desired = readJsonFile(root, argValue(args, '--desired-file', true), 'desired');
  const observedArg = argValue(args, '--observed-file');
  const observed = observedArg ? readJsonFile(root, observedArg, 'observed') : null;
  const summaries = [];
  for (let index = 0; index < args.length; index += 1) {
    if (args[index] === '--summary' && args[index + 1]) summaries.push(args[index + 1]);
  }
  if (summaries.length === 0) throw new Error('Se requiere al menos un --summary.');
  const targetRef = argValue(args, '--target-ref', true);
  assertSanitized({ target_ref: targetRef, summaries }, 'alcance');
  const action = {
    type, risk, logical_id: logicalId, target_ref: targetRef, environment: environment ?? null,
    desired_sha256: desired.sha256, observed_sha256: observed?.sha256 ?? null,
    diff_summary: summaries, scope_hash: '', status: 'proposed',
    proposed_at: new Date().toISOString(), authorization: null, execution: null, verification: null
  };
  action.scope_hash = scopeFor(action);
  context.operations.actions[id] = action;
  context.operations.mode = 'authorize';
  updateDate(context.operations);
  writeYaml(context.operationsPath, context.operations);
  console.log(`${id} propuesto en ${resolved.platform.id} (${action.risk}); scope_hash=${action.scope_hash}.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
