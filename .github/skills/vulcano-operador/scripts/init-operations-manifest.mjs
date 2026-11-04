#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolveOperatorAdapters } from './adapter-registry.mjs';
import { argValue, gitCommit, normalize, readYaml, sha256File, updateDate, writeYaml } from './operations-lib.mjs';

const args = process.argv.slice(2);

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const resources = path.resolve(argValue(args, '--resources-dir') ?? path.join(root, 'resources'));
  const bobPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  const operationsPath = path.join(resources, '.vulcano', 'operations-manifest.yaml');
  if (!fs.existsSync(bobPath)) throw new Error('No existe bob-manifest.yaml; completar primero Vulcano Bob.');
  const migrate = args.includes('--migrate');
  if (migrate && !fs.existsSync(operationsPath)) throw new Error('--migrate requiere operations-manifest.yaml existente.');
  if (fs.existsSync(operationsPath) && !args.includes('--force') && !migrate) {
    throw new Error('operations-manifest.yaml ya existe; no se sobrescribió.');
  }

  const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
  const bobValidator = path.resolve(scriptsDir, '..', '..', 'vulcano-bob', 'scripts', 'validate-vulcano-bob.mjs');
  const validation = spawnSync(process.execPath, [bobValidator, '--root', root, '--resources-dir', resources, '--strict-completeness', '--write-summary'], {
    encoding: 'utf8'
  });
  if (validation.status !== 0) throw new Error(`Bob no supera el cierre estricto:\n${validation.stdout}${validation.stderr}`);

  const bob = readYaml(bobPath);
  const resolved = resolveOperatorAdapters(bob);
  let manifest;
  if (migrate) {
    manifest = readYaml(operationsPath);
    if (![1, 2].includes(manifest.schema_version)) throw new Error('unsupported_schema: migración admite schema v1 o v2.');
    const previousCapabilities = manifest.capabilities ?? {};
    manifest.capabilities = {
      platform_mcp: previousCapabilities.platform_mcp ?? previousCapabilities.azure_devops_mcp ?? 'unknown',
      cloud_mcp: previousCapabilities.cloud_mcp ?? previousCapabilities.azure_mcp ?? 'unknown'
    };
    for (const action of Object.values(manifest.actions ?? {})) {
      if (action.status === 'authorized') {
        action.status = 'proposed';
        action.authorization = null;
      }
      // Acciones de antes del guardrail de progresión dev -> qa -> prod (plan-operation.mjs) no
      // tienen `environment` — backfill a null (no bloquea nada, solo deja de aplicar el
      // guardrail retroactivamente a acciones ya propuestas antes de esta capacidad).
      action.environment ??= null;
    }
    manifest.gate = { status: 'pending', checked_at: null, blockers: [] };
    manifest.mode = 'reconcile';
    manifest.reconciliation = { observed_at: null, tool: null, snapshot_sha256: null };
  } else {
    manifest = readYaml(path.resolve(scriptsDir, '..', 'assets', 'operations-manifest.template.yaml'));
  }

  manifest.schema_version = 2;
  manifest.project = bob.project;
  manifest.operator_selection = resolved.selection;
  manifest.source = {
    bob_manifest: normalize(path.relative(root, bobPath)),
    bob_sha256: sha256File(bobPath),
    git_commit: gitCommit(root)
  };
  manifest.target ??= { organization: null, project: null, repository: null, branch: null };
  for (const [field, flag] of Object.entries({
    organization: '--organization', project: '--project', repository: '--repository', branch: '--branch'
  })) {
    const provided = argValue(args, flag);
    if (provided !== null) manifest.target[field] = provided;
  }
  updateDate(manifest);
  writeYaml(operationsPath, manifest);
  console.log(`${migrate ? 'Migrado' : 'Creado'} ${normalize(path.relative(root, operationsPath))}; ` +
    `${resolved.selection.platform} + ${resolved.selection.cloud}, modo reconcile, sin mutaciones autorizadas.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
