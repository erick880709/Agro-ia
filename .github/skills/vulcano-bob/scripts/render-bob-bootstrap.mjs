#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { getAdapterDescriptor, resolveAdapters } from './adapter-registry.mjs';

const args = process.argv.slice(2);
const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function argValue(flag) {
  const index = args.indexOf(flag);
  if (index < 0) return null;
  const result = args[index + 1];
  if (!result || result.startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return result;
}

function loadYaml(file) {
  const code = 'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding="utf-8")), ensure_ascii=False))';
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code, file], { encoding: 'utf8' });
    if (!result.error && result.status === 0) return JSON.parse(result.stdout);
  }
  throw new Error('Se requiere Python con PyYAML para renderizar el bootstrap.');
}

function contained(base, candidate, label) {
  const resolved = path.resolve(base, candidate);
  const relative = path.relative(base, resolved);
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error(`${label} sale del directorio permitido.`);
  return resolved;
}

try {
  const root = path.resolve(argValue('--root') ?? process.cwd());
  const resources = path.resolve(argValue('--resources-dir') ?? path.join(root, 'resources'));
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  const bobPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  if (!fs.existsSync(vulcanoPath) || !fs.existsSync(bobPath)) throw new Error('Se requieren manifest.yaml y bob-manifest.yaml inicializados.');
  const selection = resolveAdapters(loadYaml(vulcanoPath));
  const cloud = getAdapterDescriptor('cloud', selection.cloud);
  if (!cloud.bootstrap_template) throw new Error(`cloud/${cloud.id} no declara bootstrap_template; generar según ${cloud.reference}.`);
  const bob = loadYaml(bobPath);
  if (bob.adapter_selection?.cloud !== cloud.id) throw new Error('bob-manifest.yaml no coincide con la selección cloud fuente.');
  const source = contained(skillRoot, cloud.bootstrap_template, 'bootstrap_template');
  if (!fs.existsSync(source)) throw new Error(`bootstrap_template inexistente para cloud/${cloud.id}.`);
  const destination = bob.artifacts?.['bootstrap-backend']?.path;
  if (!destination) throw new Error('bob-manifest.yaml no declara artifacts.bootstrap-backend.path.');
  const target = contained(root, destination, 'bootstrap-backend.path');
  if (fs.existsSync(target) && !args.includes('--force')) {
    throw new Error(`${destination} ya existe; usar --force solo después de reconciliarlo.`);
  }
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(source, target);
  fs.chmodSync(target, 0o755);
  console.log(`Renderizado ${destination} para cloud/${cloud.id}.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
