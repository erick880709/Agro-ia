#!/usr/bin/env node

import path from 'node:path';
import { resolveOperatorAdapters } from './adapter-registry.mjs';
import { argValue, assertBobUnchanged, loadContext, readJsonFile, updateDate, writeYaml } from './operations-lib.mjs';

const args = process.argv.slice(2);

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const resources = path.resolve(argValue(args, '--resources-dir') ?? path.join(root, 'resources'));
  const context = loadContext(root, resources);
  assertBobUnchanged(context);
  const resolved = resolveOperatorAdapters(context.bob);
  if (context.operations.operator_selection?.platform !== resolved.selection.platform ||
      context.operations.operator_selection?.cloud !== resolved.selection.cloud ||
      context.operations.operator_selection?.status !== resolved.selection.status) {
    throw new Error('operator_selection no coincide con Bob; migrar o reinicializar.');
  }
  const platform = argValue(args, '--platform-mcp') ?? argValue(args, '--azure-devops-mcp');
  const cloud = argValue(args, '--cloud-mcp') ?? argValue(args, '--azure-mcp');
  if (!platform || !cloud) throw new Error('--platform-mcp y --cloud-mcp son obligatorios.');
  if (!['available', 'missing'].includes(platform) || !['available', 'missing'].includes(cloud)) {
    throw new Error('Las capacidades deben ser available o missing.');
  }
  const snapshot = readJsonFile(root, argValue(args, '--snapshot-file', true), 'snapshot');
  context.operations.capabilities = { platform_mcp: platform, cloud_mcp: cloud };
  context.operations.reconciliation = {
    observed_at: new Date().toISOString(),
    tool: argValue(args, '--tool', true),
    snapshot_sha256: snapshot.sha256
  };
  for (const action of Object.values(context.operations.actions ?? {})) {
    if (action.status === 'authorized') {
      action.status = 'proposed';
      action.authorization = null;
    }
  }
  context.operations.mode = 'plan';
  context.operations.gate.status = platform === 'available' ? 'ready' : 'blocked';
  context.operations.gate.checked_at = new Date().toISOString();
  context.operations.gate.blockers = platform === 'available'
    ? []
    : [`missing_capability: ${resolved.platform.mcp_capability}`];
  updateDate(context.operations);
  writeYaml(context.operationsPath, context.operations);
  console.log(`Reconciliación registrada: ${resolved.platform.mcp_capability} ${platform}, ${resolved.cloud.mcp_capability} ${cloud}.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
