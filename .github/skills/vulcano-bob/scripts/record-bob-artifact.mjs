#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const args = process.argv.slice(2);

function value(flag, required = false) {
  const index = args.indexOf(flag);
  if (index < 0) {
    if (required) throw new Error(`${flag} es obligatorio.`);
    return null;
  }
  const result = args[index + 1];
  if (!result || result.startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return result;
}

function yaml(mode, input) {
  const code = mode === 'load'
    ? 'import json,sys,yaml; print(json.dumps(yaml.safe_load(sys.stdin.read()), ensure_ascii=False))'
    : 'import json,sys,yaml; print(yaml.safe_dump(json.load(sys.stdin), sort_keys=False, allow_unicode=True), end="")';
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code], { input, encoding: 'utf8' });
    if (!result.error && result.status === 0) return result.stdout;
  }
  throw new Error('Se requiere Python con PyYAML.');
}

try {
  const root = path.resolve(value('--root') ?? process.cwd());
  const resources = path.resolve(value('--resources-dir') ?? path.join(root, 'resources'));
  const logicalId = value('--logical-id', true);
  const status = value('--status', true);
  const reason = value('--reason');
  if (!['pending', 'conflict', 'omitted'].includes(status)) {
    throw new Error('Este comando solo registra pending/conflict/omitted; para generated usar validate-and-record-bob-artifact.mjs.');
  }
  if (['conflict', 'omitted'].includes(status) && !reason) throw new Error(`${status} requiere --reason.`);
  const manifestPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  if (!fs.existsSync(manifestPath)) throw new Error('No existe bob-manifest.yaml.');
  const manifest = JSON.parse(yaml('load', fs.readFileSync(manifestPath, 'utf8')));
  const artifact = manifest.artifacts?.[logicalId];
  if (!artifact) throw new Error(`logical_id desconocido: ${logicalId}.`);
  artifact.status = status;
  artifact.source_hashes = {};
  artifact.validated = {
    format: null, validate: null, lint: null, security: null, syntax: null, last_run: null, evidence: {}
  };
  if (reason) artifact.reason = reason;
  else delete artifact.reason;
  manifest.updated_at = new Date().toISOString().slice(0, 10);
  fs.writeFileSync(manifestPath, yaml('dump', JSON.stringify(manifest)), 'utf8');
  console.log(`Actualizado ${logicalId}: ${status}.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
