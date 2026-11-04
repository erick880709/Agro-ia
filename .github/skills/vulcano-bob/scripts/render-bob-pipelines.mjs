#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { getAdapterDescriptor, resolveAdapters } from './adapter-registry.mjs';

const args = process.argv.slice(2);
const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

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
  throw new Error('Se requiere Python con PyYAML para resolver el adaptador de pipeline.');
}

try {
  const root = path.resolve(value('--root') ?? process.cwd());
  const resources = path.resolve(value('--resources-dir') ?? path.join(root, 'resources'));
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  if (!fs.existsSync(vulcanoPath)) throw new Error('No existe resources/.vulcano/manifest.yaml.');
  const selection = resolveAdapters(loadYaml(fs.readFileSync(vulcanoPath, 'utf8')));
  const adapter = getAdapterDescriptor('pipeline', selection.pipeline);
  if (!adapter.renderer) throw new Error(`unsupported_adapter: pipeline/${selection.pipeline} no declara renderer.`);
  const renderer = path.resolve(skillRoot, adapter.renderer);
  const relative = path.relative(skillRoot, renderer);
  if (relative.startsWith('..') || path.isAbsolute(relative) || !fs.existsSync(renderer)) {
    throw new Error(`invalid_adapter: renderer fuera del skill o inexistente para pipeline/${selection.pipeline}.`);
  }
  const result = spawnSync(process.execPath, [renderer, ...args, '--adapter-cloud', selection.cloud], { encoding: 'utf8' });
  process.stdout.write(result.stdout ?? '');
  process.stderr.write(result.stderr ?? '');
  process.exit(result.status ?? 1);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
