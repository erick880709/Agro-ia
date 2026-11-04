import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const adaptersRoot = path.join(skillRoot, 'adapters');

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

export function loadRegistry() {
  const registry = readJson(path.join(adaptersRoot, 'registry.json'));
  if (registry.schema_version !== 1) throw new Error('unsupported_adapter_registry: schema_version debe ser 1.');
  return registry;
}

export function getAdapter(kind, requested) {
  const registry = loadRegistry();
  const canonical = registry.aliases?.[kind]?.[requested] ?? requested;
  const relative = registry.adapters?.[kind]?.[canonical];
  if (!relative) throw new Error(`unsupported_adapter: no existe ${kind}/${requested}.`);
  const adapter = readJson(path.join(adaptersRoot, relative));
  if (adapter.id !== canonical || adapter.kind !== kind) {
    throw new Error(`invalid_adapter: ${relative} no coincide con ${kind}/${canonical}.`);
  }
  return adapter;
}

export function resolveOperatorAdapters(bob, { allowPlanned = false } = {}) {
  const platformId = bob.adapter_selection?.pipeline;
  const cloudId = bob.adapter_selection?.cloud;
  if (!platformId || !cloudId) throw new Error('definition_incomplete: Bob requiere adapter_selection.pipeline y adapter_selection.cloud.');
  const platform = getAdapter('platform', platformId);
  const cloud = getAdapter('cloud', cloudId);
  const unavailable = [platform, cloud].filter(adapter => adapter.status !== 'implemented');
  if (unavailable.length > 0 && !allowPlanned) {
    throw new Error(`unsupported_adapter: ${unavailable.map(item => `${item.kind}/${item.id} (${item.status})`).join(', ')}.`);
  }
  const declaredOperator = bob.adapter_selection?.remote_operator;
  if (declaredOperator && declaredOperator !== 'vulcano-operador') {
    throw new Error(`incompatible_operator: Bob delega a ${declaredOperator}, no a vulcano-operador.`);
  }
  return {
    selection: {
      platform: platform.id,
      cloud: cloud.id,
      status: unavailable.length === 0 ? 'implemented' : 'planned'
    },
    platform,
    cloud
  };
}
