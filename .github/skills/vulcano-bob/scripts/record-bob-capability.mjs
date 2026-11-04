#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const args = process.argv.slice(2);
const value = flag => {
  const index = args.indexOf(flag);
  if (index < 0 || !args[index + 1] || args[index + 1].startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return args[index + 1];
};

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

const allowed = {
  terraform_registry_mcp: ['available', 'missing', 'disabled'],
  terraform_style_guide: ['available', 'missing'],
  terraform_test: ['available', 'missing'],
  azure_verified_modules: ['available', 'missing', 'not_required'],
  refactor_module: ['available', 'missing', 'not_required'],
  terraform_search_import: ['disabled']
};

try {
  const root = path.resolve(args.includes('--root') ? value('--root') : process.cwd());
  const resources = path.resolve(args.includes('--resources-dir') ? value('--resources-dir') : path.join(root, 'resources'));
  const capability = value('--capability');
  const status = value('--status');
  if (!allowed[capability]) throw new Error(`Capacidad desconocida: ${capability}.`);
  if (!allowed[capability].includes(status)) throw new Error(`${capability} no admite status ${status}.`);
  const manifestPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  if (!fs.existsSync(manifestPath)) throw new Error('No existe bob-manifest.yaml.');
  const manifest = JSON.parse(yaml('load', fs.readFileSync(manifestPath, 'utf8')));
  manifest.preflight ??= { status: 'pending', checked_at: null, conflicts: [], capabilities: {} };
  manifest.preflight.capabilities ??= {};
  manifest.preflight.capabilities[capability] = status;
  manifest.preflight.checked_at = new Date().toISOString();
  manifest.updated_at = new Date().toISOString().slice(0, 10);
  fs.writeFileSync(manifestPath, yaml('dump', JSON.stringify(manifest)), 'utf8');
  console.log(`Registrado ${capability}: ${status}.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
