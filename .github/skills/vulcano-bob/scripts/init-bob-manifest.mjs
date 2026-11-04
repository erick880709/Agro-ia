#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { getAdapterDescriptor, resolveAdapters } from './adapter-registry.mjs';

const args = process.argv.slice(2);
const normalize = value => value.replaceAll('\\', '/');

function argValue(flag) {
  const index = args.indexOf(flag);
  if (index < 0) return null;
  const value = args[index + 1];
  if (!value || value.startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return value;
}

function pythonYaml(mode, input) {
  const code = mode === 'load'
    ? 'import json,sys,yaml; print(json.dumps(yaml.safe_load(sys.stdin.read()), ensure_ascii=False))'
    : 'import json,sys,yaml; print(yaml.safe_dump(json.load(sys.stdin), sort_keys=False, allow_unicode=True), end="")';
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code], { input, encoding: 'utf8' });
    if (!result.error && result.status === 0) return result.stdout;
  }
  throw new Error('Se requiere Python con PyYAML para administrar bob-manifest.yaml.');
}

function validateTerraformProfile(profile) {
  if (!profile || typeof profile !== 'object' || Array.isArray(profile)) {
    throw new Error('definition_incomplete: falta decisions.terraform en manifest.yaml.');
  }
  if (typeof profile.required_version !== 'string' || !profile.required_version.trim()) {
    throw new Error('definition_incomplete: decisions.terraform.required_version es obligatorio.');
  }
  if (!profile.provider_constraints || typeof profile.provider_constraints !== 'object' ||
      Array.isArray(profile.provider_constraints) || Object.keys(profile.provider_constraints).length === 0) {
    throw new Error('definition_incomplete: decisions.terraform.provider_constraints es obligatorio.');
  }
  const allowed = {
    module_standard: ['internal', 'avm'],
    execution_backend: ['azure_devops', 'github_actions', 'gitlab_ci', 'hcp_terraform'],
    test_strategy: ['plan_mock', 'plan_mock_and_integration'],
    registry_source: ['public', 'private', 'mixed', 'none'],
    registry_mcp: ['read_only', 'disabled'],
    adoption_mode: ['none', 'moved_import']
  };
  for (const [key, values] of Object.entries(allowed)) {
    if (!values.includes(profile[key])) {
      throw new Error(`unsupported_adapter: decisions.terraform.${key} debe ser ${values.join(' o ')}.`);
    }
  }
  if (profile.module_standard === 'avm' && !['azurerm', 'azapi'].some(key => profile.provider_constraints[key])) {
    throw new Error('definition_incomplete: AVM requiere constraint para azurerm o azapi.');
  }
}

function applyAdapterOverrides(manifest, adapterSelection) {
  const descriptors = [
    getAdapterDescriptor('cloud', adapterSelection.cloud),
    getAdapterDescriptor('pipeline', adapterSelection.pipeline)
  ];
  const pipeline = descriptors[1];
  if (Array.isArray(pipeline.pipeline_files)) {
    manifest.target_repo.pipeline_files = [...pipeline.pipeline_files];
  }
  for (const descriptor of descriptors) {
    for (const [logicalId, override] of Object.entries(descriptor.artifact_overrides ?? {})) {
      const artifact = manifest.artifacts?.[logicalId];
      if (!artifact) throw new Error(`invalid_adapter: ${descriptor.kind}/${descriptor.id} modifica artefacto inexistente ${logicalId}.`);
      if (override.path) artifact.path = override.path;
      if (override.contract) artifact.contract = JSON.parse(JSON.stringify(override.contract));
    }
  }
}

try {
  const root = path.resolve(argValue('--root') ?? process.cwd());
  const resources = path.resolve(argValue('--resources-dir') ?? path.join(root, 'resources'));
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  const bobPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  const templatePath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'assets', 'bob-manifest.template.yaml');

  if (!fs.existsSync(vulcanoPath)) throw new Error(`No existe ${normalize(path.relative(root, vulcanoPath))}.`);
  const migrateAdapters = args.includes('--migrate-adapters') || args.includes('--migrate-profile');
  if (migrateAdapters && !fs.existsSync(bobPath)) throw new Error('--migrate-adapters requiere un bob-manifest.yaml existente.');
  if (fs.existsSync(bobPath) && !args.includes('--force') && !migrateAdapters) {
    throw new Error(`${normalize(path.relative(root, bobPath))} ya existe; no se sobrescribió.`);
  }

  const vulcano = JSON.parse(pythonYaml('load', fs.readFileSync(vulcanoPath, 'utf8')));
  const adapterSelection = resolveAdapters(vulcano);
  validateTerraformProfile(vulcano.decisions.terraform);
  const manifest = migrateAdapters && fs.existsSync(bobPath)
    ? JSON.parse(pythonYaml('load', fs.readFileSync(bobPath, 'utf8')))
    : JSON.parse(pythonYaml('load', fs.readFileSync(templatePath, 'utf8')));
  if (migrateAdapters && ![3, 4].includes(manifest.schema_version)) {
    throw new Error('unsupported_schema: --migrate-adapters solo admite bob-manifest schema_version 3 o 4.');
  }
  manifest.schema_version = 4;
  manifest.project = vulcano.project;
  manifest.updated_at = new Date().toISOString().slice(0, 10);
  manifest.resources_root = vulcano.resources_root;
  manifest.source_manifest = normalize(path.relative(root, vulcanoPath));
  manifest.source_snapshot = {
    manifest_updated_at: vulcano.updated_at,
    cloud_provider: adapterSelection.cloud,
    iac: vulcano.decisions.iac,
    devops_platform: vulcano.decisions.devops_platform
  };
  manifest.adapter_selection = adapterSelection;
  manifest.terraform_profile = JSON.parse(JSON.stringify(vulcano.decisions.terraform));
  applyAdapterOverrides(manifest, adapterSelection);
  manifest.preflight.capabilities = {
    terraform_registry_mcp: manifest.terraform_profile.registry_mcp === 'read_only' ? 'unknown' : 'disabled',
    terraform_style_guide: 'unknown',
    terraform_test: 'unknown',
    azure_verified_modules: manifest.terraform_profile.module_standard === 'avm' ? 'unknown' : 'not_required',
    refactor_module: manifest.terraform_profile.adoption_mode === 'moved_import' ? 'unknown' : 'not_required',
    terraform_search_import: 'disabled'
  };
  if (migrateAdapters) {
    manifest.preflight.status = 'pending';
    manifest.preflight.checked_at = null;
  }

  fs.mkdirSync(path.dirname(bobPath), { recursive: true });
  fs.writeFileSync(bobPath, pythonYaml('dump', JSON.stringify(manifest)), 'utf8');
  console.log(`${migrateAdapters ? 'Migrado' : 'Creado'} ${normalize(path.relative(root, bobPath))} con schema_version 4.`);
  if (migrateAdapters) process.exit(0);
  const modulesPath = path.join(resources, 'infrastructure-as-code', '06-modules.md');
  if (fs.existsSync(modulesPath)) {
    const compiler = path.join(path.dirname(fileURLToPath(import.meta.url)), 'compile-bob-contract.mjs');
    const result = spawnSync(process.execPath, [compiler, '--root', root, '--resources-dir', resources], {
      encoding: 'utf8'
    });
    if (result.status !== 0) throw new Error(`No se pudo compilar el contrato de módulos:\n${result.stderr.trim()}`);
    process.stdout.write(result.stdout);
  }
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
