#!/usr/bin/env node

import path from 'node:path';
import { argValue, assertBobUnchanged, loadContext, readJsonFile, updateDate, writeYaml } from './operations-lib.mjs';

const args = process.argv.slice(2);

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const resources = path.resolve(argValue(args, '--resources-dir') ?? path.join(root, 'resources'));
  const context = loadContext(root, resources);
  assertBobUnchanged(context);
  const id = argValue(args, '--id', true);
  const phase = argValue(args, '--phase', true);
  const action = context.operations.actions?.[id];
  if (!action) throw new Error(`${id} no existe.`);
  const evidence = readJsonFile(root, argValue(args, '--evidence-file', true), 'evidence').parsed;
  const allowed = new Set(['tool', 'result', 'scope_hash', 'request_sha256', 'response_sha256', 'external_id']);
  if (Object.keys(evidence).some(key => !allowed.has(key))) throw new Error('La evidencia contiene campos no permitidos.');
  if (!evidence.tool || !['succeeded', 'failed'].includes(evidence.result)) throw new Error('Evidencia requiere tool y result válido.');
  for (const key of ['scope_hash', 'request_sha256', 'response_sha256']) {
    if (!/^[a-f0-9]{64}$/.test(evidence[key] ?? '')) throw new Error(`Evidencia requiere ${key} SHA-256.`);
  }
  if (evidence.scope_hash !== action.scope_hash) throw new Error('El scope_hash de la evidencia no coincide.');
  const recorded = { ...evidence, external_id: evidence.external_id ?? null, recorded_at: new Date().toISOString() };

  if (phase === 'execution') {
    if (action.status !== 'running') throw new Error(`${id} no está running; ejecutar begin-operation.mjs antes del MCP.`);
    if (Date.now() >= Date.parse(action.authorization?.expires_at ?? '')) throw new Error('La autorización expiró.');
    if (action.authorization.scope_hash !== action.scope_hash) throw new Error('La autorización no corresponde al alcance actual.');
    action.execution = recorded;
    action.status = evidence.result === 'succeeded' ? 'succeeded' : 'failed';
    context.operations.mode = evidence.result === 'succeeded' ? 'verify' : 'reconcile';
  } else if (phase === 'verification') {
    if (action.status !== 'succeeded' || action.execution?.result !== 'succeeded') throw new Error(`${id} no tiene ejecución exitosa para verificar.`);
    action.verification = recorded;
    action.status = evidence.result === 'succeeded' ? 'verified' : 'failed';
    context.operations.mode = 'reconcile';
  } else {
    throw new Error('--phase debe ser execution o verification.');
  }
  updateDate(context.operations);
  writeYaml(context.operationsPath, context.operations);
  console.log(`${id}: ${phase} ${evidence.result}; estado ${action.status}.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
