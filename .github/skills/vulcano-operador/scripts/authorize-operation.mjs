#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { argValue, assertBobUnchanged, assertSanitized, contained, loadContext, sha256File, updateDate, writeYaml } from './operations-lib.mjs';

const args = process.argv.slice(2);

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const resources = path.resolve(argValue(args, '--resources-dir') ?? path.join(root, 'resources'));
  const context = loadContext(root, resources);
  assertBobUnchanged(context);
  const id = argValue(args, '--id', true);
  const action = context.operations.actions?.[id];
  if (!action || action.status !== 'proposed') throw new Error(`${id} no está proposed.`);
  const observedAt = Date.parse(context.operations.reconciliation.observed_at ?? '');
  if (!Number.isFinite(observedAt) || Date.now() - observedAt > 30 * 60 * 1000) {
    throw new Error('La reconciliación tiene más de 30 minutos; repetirla antes de autorizar.');
  }
  const confirmationPath = contained(root, argValue(args, '--confirmation-file', true), 'confirmation-file');
  const confirmation = fs.readFileSync(confirmationPath, 'utf8').trim();
  assertSanitized(confirmation, 'confirmación');
  if (!confirmation.includes(id) && !confirmation.includes(action.target_ref)) {
    throw new Error('La confirmación debe nombrar el ID o target exacto.');
  }
  const requestedMinutes = Number(argValue(args, '--expires-in-minutes') ?? (action.risk === 'execute' ? 30 : 1440));
  const maximum = action.risk === 'execute' ? 30 : 1440;
  if (!Number.isInteger(requestedMinutes) || requestedMinutes < 1 || requestedMinutes > maximum) {
    throw new Error(`Expiración inválida; máximo ${maximum} minutos para ${action.risk}.`);
  }
  const now = new Date();
  action.authorization = {
    authorized_by: argValue(args, '--authorized-by', true),
    authorized_at: now.toISOString(),
    expires_at: new Date(now.getTime() + requestedMinutes * 60 * 1000).toISOString(),
    scope_hash: action.scope_hash,
    confirmation_sha256: sha256File(confirmationPath)
  };
  action.status = 'authorized';
  context.operations.mode = 'operate';
  updateDate(context.operations);
  writeYaml(context.operationsPath, context.operations);
  console.log(`${id} autorizado hasta ${action.authorization.expires_at}; el alcance no puede ampliarse.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
