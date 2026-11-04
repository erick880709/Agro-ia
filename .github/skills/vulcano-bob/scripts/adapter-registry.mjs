import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const adaptersRoot = path.join(skillRoot, 'adapters');

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

export function loadAdapterRegistry() {
  const registry = readJson(path.join(adaptersRoot, 'registry.json'));
  if (registry.schema_version !== 1) throw new Error('unsupported_adapter_registry: schema_version debe ser 1.');
  return registry;
}

function selectedCloud(vulcano) {
  const explicit = vulcano.decisions?.cloud_provider;
  if (explicit) return explicit;
  const baseline = vulcano.baseline?.cloud_providers;
  if (Array.isArray(baseline) && baseline.length === 1) return baseline[0];
  throw new Error('definition_incomplete: decisions.cloud_provider es obligatorio cuando baseline.cloud_providers no contiene exactamente una nube.');
}

export function getAdapterDescriptor(kind, requested) {
  const registry = loadAdapterRegistry();
  const canonical = registry.aliases?.[kind]?.[requested] ?? requested;
  const relative = registry.adapters?.[kind]?.[canonical];
  if (!relative) throw new Error(`unsupported_adapter: no existe adaptador ${kind} para ${requested}.`);
  const adapter = readJson(path.join(adaptersRoot, relative));
  if (adapter.id !== canonical || adapter.kind !== kind) {
    throw new Error(`invalid_adapter: ${relative} no coincide con ${kind}/${canonical}.`);
  }
  return adapter;
}

export function resolveAdapters(vulcano, { allowPlanned = false } = {}) {
  const requested = {
    cloud: selectedCloud(vulcano),
    iac: vulcano.decisions?.iac,
    pipeline: vulcano.decisions?.devops_platform
  };
  for (const [kind, value] of Object.entries(requested)) {
    if (typeof value !== 'string' || !value.trim()) throw new Error(`definition_incomplete: falta decisions.${kind}.`);
  }

  const resolved = Object.fromEntries(
    Object.entries(requested).map(([kind, value]) => [kind, getAdapterDescriptor(kind, value)])
  );
  const unavailable = Object.entries(resolved).filter(([, adapter]) => adapter.status !== 'implemented');
  if (unavailable.length > 0 && !allowPlanned) {
    const detail = unavailable.map(([kind, adapter]) => `${kind}/${adapter.id} (${adapter.status})`).join(', ');
    throw new Error(`unsupported_adapter: adaptador no implementado: ${detail}.`);
  }

  const profile = vulcano.decisions?.[resolved.iac.profile_key];
  if (!profile || typeof profile !== 'object' || Array.isArray(profile)) {
    throw new Error(`definition_incomplete: falta decisions.${resolved.iac.profile_key}.`);
  }
  const providers = Object.keys(profile.provider_constraints ?? {});
  if (resolved.cloud.required_provider_any?.length > 0 &&
      !resolved.cloud.required_provider_any.some(provider => providers.includes(provider))) {
    throw new Error(
      `incompatible_adapter: cloud/${resolved.cloud.id} requiere al menos uno de los providers ` +
      `${resolved.cloud.required_provider_any.join(', ')}.`
    );
  }
  if (resolved.pipeline.supported_execution_backends?.length > 0 &&
      !resolved.pipeline.supported_execution_backends.includes(profile.execution_backend)) {
    throw new Error(
      `incompatible_adapter: pipeline/${resolved.pipeline.id} no soporta execution_backend ` +
      `${profile.execution_backend ?? 'ausente'}.`
    );
  }

  return {
    cloud: resolved.cloud.id,
    iac: resolved.iac.id,
    pipeline: resolved.pipeline.id,
    remote_operator: resolved.pipeline.remote_operator ?? null,
    status: unavailable.length === 0 ? 'implemented' : 'planned'
  };
}
