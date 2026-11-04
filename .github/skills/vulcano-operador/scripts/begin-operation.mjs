#!/usr/bin/env node

import path from 'node:path';
import { argValue, assertBobUnchanged, loadContext, updateDate, writeYaml } from './operations-lib.mjs';

const args = process.argv.slice(2);

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const resources = path.resolve(argValue(args, '--resources-dir') ?? path.join(root, 'resources'));
  const context = loadContext(root, resources);
  assertBobUnchanged(context);
  const id = argValue(args, '--id', true);
  const action = context.operations.actions?.[id];
  if (!action || action.status !== 'authorized') throw new Error(`${id} no está authorized.`);
  if (Date.now() >= Date.parse(action.authorization?.expires_at ?? '')) throw new Error('La autorización expiró.');
  if (action.authorization.scope_hash !== action.scope_hash) throw new Error('La autorización no corresponde al alcance actual.');
  const observedAt = Date.parse(context.operations.reconciliation.observed_at ?? '');
  if (!Number.isFinite(observedAt) || Date.now() - observedAt > 30 * 60 * 1000) {
    throw new Error('La reconciliación tiene más de 30 minutos; no iniciar la mutación.');
  }
  action.status = 'running';
  context.operations.mode = 'operate';
  updateDate(context.operations);
  writeYaml(context.operationsPath, context.operations);
  console.log(JSON.stringify({
    id, platform: context.operations.operator_selection.platform, type: action.type,
    target_ref: action.target_ref, logical_id: action.logical_id,
    desired_sha256: action.desired_sha256, scope_hash: action.scope_hash
  }));
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
