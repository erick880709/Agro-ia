#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { resolveAdapters } from './adapter-registry.mjs';

const args = process.argv.slice(2);

function value(flag) {
  const index = args.indexOf(flag);
  if (index < 0) return null;
  const result = args[index + 1];
  if (!result || result.startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return result;
}

function loadYaml(text) {
  const code = 'import json,sys,yaml; print(json.dumps(yaml.safe_load(sys.stdin.read()), ensure_ascii=False))';
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code], { input: text, encoding: 'utf8' });
    if (!result.error && result.status === 0) return JSON.parse(result.stdout);
  }
  throw new Error('Se requiere Python con PyYAML.');
}

try {
  const root = path.resolve(value('--root') ?? process.cwd());
  const resources = path.resolve(value('--resources-dir') ?? path.join(root, 'resources'));
  const manifestPath = path.join(resources, '.vulcano', 'manifest.yaml');
  if (!fs.existsSync(manifestPath)) throw new Error(`No existe ${path.relative(root, manifestPath)}.`);
  const selection = resolveAdapters(loadYaml(fs.readFileSync(manifestPath, 'utf8')), {
    allowPlanned: args.includes('--allow-planned')
  });
  process.stdout.write(`${JSON.stringify(selection, null, 2)}\n`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
