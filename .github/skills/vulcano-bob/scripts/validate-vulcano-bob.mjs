#!/usr/bin/env node

import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { inspectTerraformTests } from './terraform-test-policy.mjs';
import { resolveAdapters } from './adapter-registry.mjs';

const args = process.argv.slice(2);
const errors = [];
const warnings = [];
const strict = args.includes('--strict-completeness');
const skipTools = args.includes('--skip-tools');
if (strict && skipTools) errors.push('--skip-tools no está permitido con --strict-completeness.');
const normalize = value => value.replaceAll('\\', '/');

function argValue(flag) {
  const index = args.indexOf(flag);
  if (index < 0) return null;
  const value = args[index + 1];
  if (!value || value.startsWith('--')) {
    errors.push(`${flag} requiere una ruta.`);
    return null;
  }
  return value;
}

const root = path.resolve(argValue('--root') ?? process.cwd());
const resources = path.resolve(argValue('--resources-dir') ?? path.join(root, 'resources'));
const bobManifestPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
const vulcanoManifestPath = path.join(resources, '.vulcano', 'manifest.yaml');
// pipeline-app se desdobla en pipeline-app-<componente> cuando decisions.pipeline_topology es
// per_component (ver references/adapters.md §Ubicación de los pipelines de aplicación) — el
// nombre exacto de cada componente no está fijo aquí, se resuelve más abajo con el manifiesto
// de Vulcano ya cargado.
const baseExpectedLogicalIds = [
  'bootstrap-backend',
  'env-dev',
  'env-qa',
  'env-prod',
  'pipeline-iac',
  'pipeline-drift'
];
const allowedStatuses = new Set(['pending', 'generated', 'conflict', 'omitted']);

const yamlCode = [
  'import json, sys',
  'try:',
  ' import yaml',
  'except Exception as exc:',
  ' print(json.dumps({"__error__": "PyYAML no disponible: " + str(exc)})); sys.exit(0)',
  'try:',
  ' data = yaml.safe_load(sys.stdin.read())',
  ' print(json.dumps(data, ensure_ascii=False, default=str))',
  'except Exception as exc:',
  ' print(json.dumps({"__error__": str(exc)}, ensure_ascii=False))'
].join('\n');

function parseYamlText(text) {
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', yamlCode], { input: text, encoding: 'utf8' });
    if (!result.error && result.status === 0) {
      try {
        return JSON.parse(result.stdout);
      } catch {
        // Probar el siguiente runtime.
      }
    }
  }
  return { __error__: 'No se pudo ejecutar Python con PyYAML.' };
}

// Una entrada de "stages" puede venir envuelta en una expresión de plantilla evaluada en tiempo
// de compilación (p.ej. "${{ if eq(parameters.deployQa, true) }}:") en vez de tener stage/jobs
// directos — expandir esos bloques antes de analizar el grafo de stages real.
function flattenStages(entries) {
  const result = [];
  for (const entry of entries ?? []) {
    if (!entry || typeof entry !== 'object') continue;
    if ('stage' in entry) result.push(entry);
    else {
      for (const [key, value] of Object.entries(entry)) {
        if (key.startsWith('${{') && Array.isArray(value)) result.push(...flattenStages(value));
      }
    }
  }
  return result;
}

// dependsOn puede contener el mismo tipo de envoltorio condicional que las stages (p.ej. para
// que ApplyProd dependa de ApplyQa solo si esa stage se compiló, o de ApplyDev si no) — resolver
// esos bloques a la lista plana de nombres de stage referenciados.
function flattenDependencies(dependsOn) {
  if (dependsOn === undefined) return [];
  const items = Array.isArray(dependsOn) ? dependsOn : [dependsOn];
  const result = [];
  for (const item of items) {
    if (typeof item === 'string') result.push(item);
    else if (item && typeof item === 'object') {
      for (const [key, value] of Object.entries(item)) {
        if (key.startsWith('${{') && Array.isArray(value)) result.push(...flattenDependencies(value));
      }
    }
  }
  return result;
}

function dumpYaml(value) {
  const code = 'import json,sys,yaml; print(yaml.safe_dump(json.load(sys.stdin), sort_keys=False, allow_unicode=True), end="")';
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code], { input: JSON.stringify(value), encoding: 'utf8' });
    if (!result.error && result.status === 0) return result.stdout;
  }
  throw new Error('No se pudo serializar bob-manifest.yaml con PyYAML.');
}

function readYaml(file, label) {
  if (!fs.existsSync(file)) {
    errors.push(`No existe ${label}: ${normalize(path.relative(root, file))}.`);
    return null;
  }
  const parsed = parseYamlText(fs.readFileSync(file, 'utf8'));
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed) || parsed.__error__) {
    errors.push(`${label} inválido: ${parsed?.__error__ ?? 'debe ser un objeto YAML'}.`);
    return null;
  }
  return parsed;
}

function validateManifestSchema(data) {
  const schemaPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'assets', 'bob-manifest.schema.json');
  const code = [
    'import json,sys',
    'try:',
    ' import jsonschema',
    'except Exception as exc:',
    ' print(json.dumps({"unavailable": str(exc)})); sys.exit(0)',
    'payload=json.load(sys.stdin)',
    'try:',
    ' jsonschema.Draft202012Validator(payload["schema"]).validate(payload["data"])',
    ' print(json.dumps({"ok": True}))',
    'except Exception as exc:',
    ' print(json.dumps({"error": str(exc)}))'
  ].join('\n');
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code], {
      input: JSON.stringify({ schema: JSON.parse(fs.readFileSync(schemaPath, 'utf8')), data }),
      encoding: 'utf8'
    });
    if (!result.error && result.status === 0) {
      const parsed = JSON.parse(result.stdout);
      if (parsed.unavailable) warnings.push(`jsonschema no disponible; se aplicaron solo validaciones internas: ${parsed.unavailable}.`);
      else if (parsed.error) errors.push(`bob-manifest.yaml no cumple bob-manifest.schema.json: ${parsed.error}`);
      return;
    }
  }
  warnings.push('No se pudo ejecutar JSON Schema; se aplicaron solo validaciones internas.');
}

function resolveContained(base, candidate, label) {
  if (typeof candidate !== 'string' || candidate.trim() === '') {
    errors.push(`${label}: ruta vacía o inválida.`);
    return null;
  }
  if (path.isAbsolute(candidate)) {
    errors.push(`${label}: la ruta debe ser relativa: ${normalize(candidate)}.`);
    return null;
  }
  const resolved = path.resolve(base, candidate);
  const relative = path.relative(base, resolved);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    errors.push(`${label}: la ruta sale del directorio permitido: ${normalize(candidate)}.`);
    return null;
  }
  return resolved;
}

function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

const TOOL_VERSION_TIMEOUT_MS = 15_000;
const TOOL_RUN_TIMEOUT_MS = 180_000;

function toolAvailable(command) {
  const result = spawnSync(command, ['--version'], { encoding: 'utf8', timeout: TOOL_VERSION_TIMEOUT_MS });
  return !result.error && result.status === 0;
}

function runTool(command, toolArgs, cwd, label) {
  const result = spawnSync(command, toolArgs, { cwd, encoding: 'utf8', timeout: TOOL_RUN_TIMEOUT_MS });
  if (result.error || result.status !== 0) {
    const output = `${result.stdout ?? ''}${result.stderr ?? ''}`.trim();
    const timedOut = result.signal === 'SIGTERM' || result.error?.code === 'ETIMEDOUT';
    const reason = timedOut ? ` (timeout tras ${TOOL_RUN_TIMEOUT_MS / 1000}s; posible falta de red o registro Terraform inalcanzable)` : '';
    errors.push(`${label} falló${reason}${output ? `:\n${output}` : '.'}`);
    return false;
  }
  return true;
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
}

function validateTerraformProfile(profile, label) {
  if (!profile || typeof profile !== 'object' || Array.isArray(profile)) {
    errors.push(`${label}: falta el perfil Terraform.`);
    return false;
  }
  if (typeof profile.required_version !== 'string' || !profile.required_version.trim()) {
    errors.push(`${label}: required_version es obligatorio.`);
  }
  if (!profile.provider_constraints || typeof profile.provider_constraints !== 'object' ||
      Array.isArray(profile.provider_constraints) || Object.keys(profile.provider_constraints).length === 0) {
    errors.push(`${label}: provider_constraints debe ser un mapa no vacío.`);
  } else {
    for (const [provider, constraint] of Object.entries(profile.provider_constraints)) {
      if (!/^[a-z0-9_-]+$/i.test(provider) || typeof constraint !== 'string' || !constraint.trim()) {
        errors.push(`${label}: constraint inválido para provider ${provider}.`);
      }
    }
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
    if (!values.includes(profile[key])) errors.push(`${label}: ${key} debe ser ${values.join(' o ')}.`);
  }
  if (profile.module_standard === 'avm' && !['azurerm', 'azapi'].some(key => profile.provider_constraints?.[key])) {
    errors.push(`${label}: AVM requiere constraint para azurerm o azapi.`);
  }
  return true;
}

function validateTerraformCopy(sourceDir, logicalId, profile, iacRoot) {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-tf-'));
  // env-* referencia modulos propios por path local relativo (../../modules/<nombre>, ver
  // 04-terraform-structure.md) — copiar solo la carpeta del ambiente rompe esa referencia.
  const isEnvWithinIacRoot = logicalId.startsWith('env-') && iacRoot &&
    (sourceDir === iacRoot || sourceDir.startsWith(iacRoot + path.sep));
  const tempModule = isEnvWithinIacRoot
    ? path.join(tempRoot, 'iac_root', path.relative(iacRoot, sourceDir))
    : path.join(tempRoot, 'module');
  try {
    if (isEnvWithinIacRoot) {
      fs.cpSync(iacRoot, path.join(tempRoot, 'iac_root'), {
        recursive: true,
        filter: source => !['.terraform', '.git'].includes(path.basename(source))
      });
    } else {
      fs.cpSync(sourceDir, tempModule, {
        recursive: true,
        filter: source => !['.terraform', '.git'].includes(path.basename(source))
      });
    }
    if (!runTool('terraform', ['init', '-backend=false', '-input=false'], tempModule, `terraform init en ${logicalId}`)) return false;
    if (!runTool('terraform', ['validate'], tempModule, `terraform validate en ${logicalId}`)) return false;
    const inspection = inspectTerraformTests(tempModule);
    if (logicalId.startsWith('module-') && ['plan_mock', 'plan_mock_and_integration'].includes(profile?.test_strategy) && inspection.files.length === 0) {
      errors.push(`${logicalId} requiere al menos un tests/*.tftest.hcl.`);
      return false;
    }
    if (inspection.errors.length > 0) {
      for (const error of inspection.errors) errors.push(`${logicalId}: ${error}`);
      return false;
    }
    if (inspection.files.length > 0) return runTool('terraform', ['test', '-no-color'], tempModule, `terraform test plan/mock en ${logicalId}`);
    return true;
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function walkFiles(target) {
  if (!fs.existsSync(target)) return [];
  if (fs.statSync(target).isFile()) return [target];
  const files = [];
  const stack = [target];
  while (stack.length) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      if (['.terraform', '.git', 'node_modules'].includes(entry.name)) continue;
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) stack.push(full);
      else files.push(full);
    }
  }
  return files;
}

function terraformDeclarations(target) {
  const text = walkFiles(target)
    .filter(file => /\.tf$/i.test(file))
    .map(file => fs.readFileSync(file, 'utf8'))
    .join('\n');
  return {
    inputs: new Set([...text.matchAll(/\bvariable\s+"([^"]+)"\s*\{/g)].map(match => match[1])),
    outputs: new Set([...text.matchAll(/\boutput\s+"([^"]+)"\s*\{/g)].map(match => match[1]))
  };
}

const vulcano = readYaml(vulcanoManifestPath, 'manifest.yaml de Vulcano');
const bob = readYaml(bobManifestPath, 'bob-manifest.yaml');
let resolvedAdapterSelection = null;
const artifacts = new Map();
const generatedPaths = new Map();
const vulcanoFilesByPath = new Map();

if (vulcano) {
  for (const entry of Object.values(vulcano.files ?? {})) {
    if (entry?.path) vulcanoFilesByPath.set(normalize(entry.path), entry);
  }
  try {
    resolvedAdapterSelection = resolveAdapters(vulcano);
    validateTerraformProfile(vulcano.decisions.terraform, 'manifest.yaml decisions.terraform');
  } catch (error) {
    errors.push(error.message);
  }

  const modulesPath = path.join(resources, 'infrastructure-as-code', '06-modules.md');
  if (fs.existsSync(modulesPath)) {
    const text = fs.readFileSync(modulesPath, 'utf8');
    if (/dependencia circular/i.test(text) && /depends_on/i.test(text)) {
      errors.push('source_conflict: 06-modules.md declara una dependencia circular y propone depends_on; Bob no puede implementarla como dependencia de datos.');
    }
  }

  const structurePath = path.join(resources, 'infrastructure-as-code', '04-terraform-structure.md');
  if (fs.existsSync(structurePath)) {
    const text = fs.readFileSync(structurePath, 'utf8');
    // Revisar solo el primer bloque de árbol de carpetas (fenced code block), no la prosa —
    // una explicación en texto de por qué NO debe estar en la raíz no debe disparar el conflicto.
    const treeBlock = text.match(/```\r?\n(infra\/[\s\S]*?)```/);
    const rootLevelVersionsTf = treeBlock ? /^ {2}versions\.tf\b/m.test(treeBlock[1]) : false;
    if (rootLevelVersionsTf && /directorios de trabajo independientes/i.test(text)) {
      errors.push('source_conflict: 04-terraform-structure.md ubica versions.tf en la raíz de infra/ (fuera de cada root module de ambiente); Terraform no hereda ese archivo entre directorios.');
    }
  }

  const observabilityRequired = ['observability/01-monitoring.md', 'observability/02-logging.md', 'observability/06-alerting.md']
    .some(source => vulcanoFilesByPath.get(source)?.status === 'generated');
  const modulesPathForObservability = path.join(resources, 'infrastructure-as-code', '06-modules.md');
  if (observabilityRequired && fs.existsSync(modulesPathForObservability)) {
    const text = fs.readFileSync(modulesPathForObservability, 'utf8');
    if (!/observability|application insights|log analytics/i.test(text)) {
      errors.push('source_conflict: la definición exige observabilidad, pero 06-modules.md no declara módulos/contratos para implementarla.');
    }
  }

  const networkPath = path.join(resources, 'infrastructure-as-code', '07-networking.md');
  if (fs.existsSync(networkPath)) {
    const text = fs.readFileSync(networkPath, 'utf8');
    if (/Private Endpoint o Service Endpoint/i.test(text)) {
      errors.push('source_conflict: 07-networking.md no decide entre Private Endpoint y Service Endpoint para Key Vault.');
    }
    if (/VNet Integration saliente/i.test(text) && /snet-app[^\n]*entrada 443 desde Internet/i.test(text)) {
      errors.push('source_conflict: 07-networking.md modela tráfico entrante de App Service sobre una subnet documentada como integración saliente.');
    }
  }

  const ciPath = path.join(resources, 'devops-strategy', '06-ci-cd.md');
  const modulesPathForRuntime = path.join(resources, 'infrastructure-as-code', '06-modules.md');
  if (fs.existsSync(ciPath) && fs.existsSync(modulesPathForRuntime)) {
    const combined = `${fs.readFileSync(ciPath, 'utf8')}\n${fs.readFileSync(modulesPathForRuntime, 'utf8')}`;
    if (/Angular/i.test(combined) && /App Service/i.test(combined) &&
        !/startup command|startup_command|pm2\s+serve|serve\s+-s|WEBSITE_RUN_FROM_PACKAGE/i.test(combined)) {
      errors.push('source_conflict: se despliega una SPA Angular a Linux App Service, pero la definición no declara cómo servir los archivos estáticos ni su startup command.');
    }
  }
}

if (bob) {
  validateManifestSchema(bob);
  if (bob.schema_version !== 4) errors.push('bob-manifest.yaml: schema_version debe ser 4.');
  if (typeof bob.project !== 'string' || !bob.project.trim()) errors.push('bob-manifest.yaml: project es obligatorio.');
  if (typeof bob.resources_root !== 'string' || !bob.resources_root.trim()) errors.push('bob-manifest.yaml: resources_root es obligatorio.');
  if (typeof bob.source_manifest !== 'string' || !bob.source_manifest.trim()) errors.push('bob-manifest.yaml: source_manifest es obligatorio.');
  validateTerraformProfile(bob.terraform_profile, 'bob-manifest.yaml terraform_profile');

  if (vulcano) {
    if (bob.project !== vulcano.project) errors.push('bob-manifest.yaml: project no coincide con manifest.yaml de Vulcano.');
    if (bob.resources_root !== vulcano.resources_root) errors.push('bob-manifest.yaml: resources_root no coincide con manifest.yaml de Vulcano.');
    if (bob.source_snapshot?.iac !== vulcano.decisions?.iac) errors.push('bob-manifest.yaml: source_snapshot.iac no coincide con Vulcano.');
    if (bob.source_snapshot?.devops_platform !== vulcano.decisions?.devops_platform) errors.push('bob-manifest.yaml: source_snapshot.devops_platform no coincide con Vulcano.');
    if (resolvedAdapterSelection && bob.source_snapshot?.cloud_provider !== resolvedAdapterSelection.cloud) {
      errors.push('bob-manifest.yaml: source_snapshot.cloud_provider no coincide con Vulcano.');
    }
    if (bob.source_snapshot?.manifest_updated_at !== vulcano.updated_at) warnings.push('El snapshot del manifiesto de Vulcano está desactualizado; repetir preflight.');
    if (JSON.stringify(canonical(bob.terraform_profile)) !== JSON.stringify(canonical(vulcano.decisions?.terraform))) {
      errors.push('bob-manifest.yaml: terraform_profile no coincide con decisions.terraform de Vulcano.');
    }
    if (resolvedAdapterSelection &&
        JSON.stringify(canonical(bob.adapter_selection)) !== JSON.stringify(canonical(resolvedAdapterSelection))) {
      errors.push('bob-manifest.yaml: adapter_selection no coincide con los adaptadores resueltos desde Vulcano.');
    }
  }

  const sourceManifestResolved = resolveContained(root, bob.source_manifest, 'bob-manifest.yaml source_manifest');
  if (sourceManifestResolved && path.resolve(sourceManifestResolved) !== path.resolve(vulcanoManifestPath)) {
    errors.push('bob-manifest.yaml: source_manifest no apunta al manifiesto de Vulcano cargado.');
  }

  const preflightStatus = bob.preflight?.status;
  if (!['pending', 'ready', 'blocked'].includes(preflightStatus)) {
    errors.push(`bob-manifest.yaml: preflight.status inválido: ${preflightStatus ?? 'ausente'}.`);
  }
  const conflicts = Array.isArray(bob.preflight?.conflicts) ? bob.preflight.conflicts : [];
  if (preflightStatus === 'blocked' || conflicts.length > 0) {
    errors.push(`Preflight bloqueado: ${conflicts.length} conflicto(s) registrado(s).`);
  } else if (strict && preflightStatus !== 'ready') {
    errors.push('Cierre estricto requiere preflight.status: ready.');
  }
  const capabilities = bob.preflight?.capabilities ?? {};
  const capabilityStatus = (name, required = false) => {
    const status = capabilities[name];
    if (status === 'unknown' || status === undefined) {
      (strict ? errors : warnings).push(`Capacidad ${name} no fue comprobada durante preflight.`);
    } else if (status === 'missing') {
      (required ? errors : warnings).push(`missing_capability: ${name}.`);
    }
    return status;
  };
  if (bob.terraform_profile?.registry_mcp === 'read_only') {
    capabilityStatus('terraform_registry_mcp', ['private', 'mixed'].includes(bob.terraform_profile?.registry_source));
  }
  else if (capabilities.terraform_registry_mcp !== 'disabled') errors.push('terraform_registry_mcp debe estar disabled cuando registry_mcp está deshabilitado.');
  capabilityStatus('terraform_style_guide');
  capabilityStatus('terraform_test');
  if (bob.terraform_profile?.module_standard === 'avm') capabilityStatus('azure_verified_modules', true);
  else if (capabilities.azure_verified_modules !== 'not_required') errors.push('azure_verified_modules debe estar not_required para module_standard internal.');
  if (bob.terraform_profile?.adoption_mode === 'moved_import') capabilityStatus('refactor_module');
  else if (capabilities.refactor_module !== 'not_required') errors.push('refactor_module debe estar not_required cuando no hay adopción.');
  if (capabilities.terraform_search_import !== 'disabled') {
    errors.push('terraform_search_import debe permanecer disabled dentro de Bob; su ejecución requiere un flujo remoto autorizado.');
  }

  const artifactObject = bob.artifacts && typeof bob.artifacts === 'object' && !Array.isArray(bob.artifacts)
    ? bob.artifacts
    : null;
  if (!artifactObject) errors.push('bob-manifest.yaml: artifacts debe ser un mapa.');

  for (const [logicalId, entry] of Object.entries(artifactObject ?? {})) {
    artifacts.set(logicalId, entry);
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) {
      errors.push(`bob-manifest.yaml: ${logicalId} debe ser un objeto.`);
      continue;
    }
    if (!allowedStatuses.has(entry.status)) {
      errors.push(`bob-manifest.yaml: status inválido en ${logicalId}: ${entry.status ?? 'ausente'}.`);
      continue;
    }
    if (!Array.isArray(entry.depends_on)) errors.push(`bob-manifest.yaml: ${logicalId} requiere depends_on.`);
    if (!entry.contract || !Array.isArray(entry.contract.inputs) || !Array.isArray(entry.contract.outputs)) {
      errors.push(`bob-manifest.yaml: ${logicalId} requiere contract.inputs y contract.outputs.`);
    } else {
      if (new Set(entry.contract.inputs).size !== entry.contract.inputs.length) errors.push(`${logicalId} tiene inputs duplicados.`);
      if (new Set(entry.contract.outputs).size !== entry.contract.outputs.length) errors.push(`${logicalId} tiene outputs duplicados.`);
    }
    if (entry.status === 'conflict') errors.push(`Artefacto en conflict: ${logicalId}${entry.reason ? ` (${entry.reason})` : ''}.`);
    if (entry.status === 'omitted' && !entry.reason) errors.push(`bob-manifest.yaml: ${logicalId} está omitted sin reason.`);
    if (strict && entry.status === 'pending') errors.push(`Cierre incompleto: ${logicalId} sigue pending.`);

    const artifactPath = resolveContained(root, entry.path, `bob-manifest.yaml ${logicalId}.path`);
    if (!artifactPath) continue;
    const normalizedPath = normalize(path.relative(root, artifactPath)).toLowerCase();
    if (generatedPaths.has(normalizedPath)) {
      errors.push(`Rutas duplicadas: ${logicalId} y ${generatedPaths.get(normalizedPath)} apuntan a ${normalize(entry.path)}.`);
    } else {
      generatedPaths.set(normalizedPath, logicalId);
    }

    if (!Array.isArray(entry.source_docs) || entry.source_docs.length === 0) {
      errors.push(`bob-manifest.yaml: ${logicalId} no declara source_docs.`);
    }
    for (const sourceDoc of entry.source_docs ?? []) {
      const cleanSource = String(sourceDoc).split('#')[0];
      const sourcePath = resolveContained(resources, cleanSource, `${logicalId}.source_docs`);
      if (!sourcePath || !fs.existsSync(sourcePath)) {
        if (sourcePath) errors.push(`Fuente inexistente para ${logicalId}: ${normalize(cleanSource)}.`);
        continue;
      }
      const sourceContract = vulcanoFilesByPath.get(normalize(cleanSource));
      if (!sourceContract) {
        errors.push(`Fuente de ${logicalId} no registrada en manifest.yaml de Vulcano: ${normalize(cleanSource)}.`);
      } else if (sourceContract.status !== 'generated') {
        errors.push(`Fuente no generada para ${logicalId}: ${normalize(cleanSource)} está ${sourceContract.status ?? 'sin estado'}.`);
      }
      if (entry.status === 'generated') {
        const recorded = entry.source_hashes?.[sourceDoc];
        if (!/^[a-f0-9]{64}$/i.test(recorded ?? '')) {
          errors.push(`bob-manifest.yaml: ${logicalId} no tiene SHA-256 válido para ${sourceDoc}.`);
        } else if (recorded.toLowerCase() !== sha256(sourcePath)) {
          errors.push(`Drift de fuente en ${logicalId}: cambió ${sourceDoc}.`);
        }
      }
    }

    if (entry.status === 'generated') {
      if (!fs.existsSync(artifactPath)) errors.push(`${logicalId} está generated pero no existe ${normalize(entry.path)}.`);
      if (!entry.validated || typeof entry.validated !== 'object') {
        errors.push(`bob-manifest.yaml: ${logicalId} generated no tiene bloque validated.`);
      } else if (strict && !entry.validated.last_run) {
        errors.push(`bob-manifest.yaml: ${logicalId} generated no registra validated.last_run.`);
      } else if (strict) {
        if (logicalId === 'bootstrap-backend' && entry.validated.syntax !== true) {
          errors.push(`bob-manifest.yaml: ${logicalId} requiere validated.syntax: true.`);
        }
        if (logicalId.startsWith('pipeline-') && entry.validated.syntax !== true) {
          errors.push(`bob-manifest.yaml: ${logicalId} requiere validated.syntax: true.`);
        }
        if ((logicalId.startsWith('module-') || logicalId.startsWith('env-')) &&
            (entry.validated.format !== true || entry.validated.validate !== true)) {
          errors.push(`bob-manifest.yaml: ${logicalId} requiere format y validate en true.`);
        }
        if (logicalId.startsWith('module-') &&
            ['plan_mock', 'plan_mock_and_integration'].includes(bob.terraform_profile?.test_strategy) &&
            entry.validated.test !== true) {
          errors.push(`bob-manifest.yaml: ${logicalId} requiere validated.test: true.`);
        }
        const evidence = entry.validated.evidence ?? {};
        const requiredEvidence = logicalId.startsWith('pipeline-') || logicalId === 'bootstrap-backend'
          ? ['syntax']
          : logicalId.startsWith('module-') ? ['format', 'validate', 'test']
            : logicalId.startsWith('env-') ? ['format', 'validate'] : [];
        for (const check of requiredEvidence) {
          if (evidence[check]?.status !== 'passed' || !evidence[check]?.output_sha256) {
            errors.push(`bob-manifest.yaml: ${logicalId} no tiene evidencia ejecutada para ${check}.`);
          }
        }
      }
    }
  }

  for (const logicalId of baseExpectedLogicalIds) {
    if (!artifacts.has(logicalId)) errors.push(`Falta logical_id obligatorio: ${logicalId}.`);
  }
  if (vulcano?.decisions?.pipeline_topology === 'per_component') {
    const componentPipelines = [...artifacts.keys()].filter(id => /^pipeline-app-/.test(id));
    if (componentPipelines.length < 2) {
      errors.push('decisions.pipeline_topology es per_component pero no hay al menos dos logical_id pipeline-app-<componente>.');
    }
  } else if (!artifacts.has('pipeline-app')) {
    errors.push('Falta logical_id obligatorio: pipeline-app.');
  }
  if (![...artifacts.keys()].some(id => id.startsWith('module-'))) {
    errors.push('Falta al menos un módulo compilado desde infrastructure-as-code/06-modules.md.');
  }

  for (const [logicalId, entry] of artifacts) {
    for (const dependency of entry?.depends_on ?? []) {
      if (!artifacts.has(dependency)) errors.push(`${logicalId} depende de logical_id desconocido: ${dependency}.`);
      if (dependency === logicalId) errors.push(`${logicalId} no puede depender de sí mismo.`);
      if (entry.status === 'generated' && !['generated', 'omitted'].includes(artifacts.get(dependency)?.status)) {
        errors.push(`${logicalId} está generated pero su dependencia ${dependency} no está cerrada.`);
      }
    }
  }

  const visiting = new Set();
  const visited = new Set();
  function visit(logicalId, trail = []) {
    if (visiting.has(logicalId)) {
      errors.push(`Ciclo en depends_on: ${[...trail, logicalId].join(' -> ')}.`);
      return;
    }
    if (visited.has(logicalId) || !artifacts.has(logicalId)) return;
    visiting.add(logicalId);
    for (const dependency of artifacts.get(logicalId)?.depends_on ?? []) visit(dependency, [...trail, logicalId]);
    visiting.delete(logicalId);
    visited.add(logicalId);
  }
  for (const logicalId of artifacts.keys()) visit(logicalId);

  const operationalIds = new Set();
  for (const pending of bob.operational_pending ?? []) {
    if (!pending || !/^OP-\d{3}$/.test(pending.id ?? '')) errors.push('operational_pending contiene un ID inválido; usar OP-NNN.');
    else if (operationalIds.has(pending.id)) errors.push(`operational_pending duplica ${pending.id}.`);
    else operationalIds.add(pending.id);
    if (!pending?.description || !pending?.owner) errors.push(`${pending?.id ?? 'OP desconocido'} requiere description y owner.`);
  }

  if (strict) {
    const indexPath = resolveContained(root, bob.closure_index, 'bob-manifest.yaml closure_index');
    if (indexPath && !fs.existsSync(indexPath)) errors.push(`Falta índice de cierre: ${normalize(bob.closure_index)}.`);
    for (const [logicalId, entry] of artifacts) {
      if (!logicalId.startsWith('env-') || entry.status !== 'generated') continue;
      const envPath = resolveContained(root, entry.path, `${logicalId}.lockfile`);
      if (envPath && !fs.existsSync(path.join(envPath, '.terraform.lock.hcl'))) {
        errors.push(`${logicalId} no contiene .terraform.lock.hcl versionado.`);
      }
    }
  }
}

const secretPatterns = [
  /password\s*=\s*"[^"$]{4,}"/i,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
  /(AKIA|ASIA)[0-9A-Z]{16}/,
  /xox[baprs]-[0-9A-Za-z-]{10,}/,
  /(client_secret|access_token|api_key)\s*[:=]\s*["'][^"']{8,}["']/i
];
const codeExtensions = /\.(tf|tfvars|ya?ml|sh|ps1)$/i;

for (const [logicalId, entry] of artifacts) {
  if (entry?.status !== 'generated') continue;
  const artifactPath = resolveContained(root, entry.path, `${logicalId}.path scan`);
  if (!artifactPath || !fs.existsSync(artifactPath)) continue;
  for (const file of walkFiles(artifactPath).filter(item => codeExtensions.test(item))) {
    const text = fs.readFileSync(file, 'utf8');
    if (/<[^>\r\n]{2,}>/.test(text)) errors.push(`Placeholder sin resolver en ${normalize(path.relative(root, file))}.`);
    for (const line of text.split(/\r?\n/)) {
      // Case-sensitive y con límite de palabra: "TODO" es la convención real de marcador de
      // pendiente en comentarios de código; en minúsculas es simplemente la palabra española
      // "todo" ("todo el sistema", "por ahora"), altísimamente frecuente en un kit que genera
      // todo su contenido en español — un chequeo case-insensitive aquí producía falsos positivos
      // en cualquier comentario que la usara con su sentido normal, no como marcador.
      if (/\bTODO\b/.test(line) && !/\bTODO\b.*(?:PD|OP)-\d{3}/.test(line)) {
        errors.push(`TODO sin PD-NNN/OP-NNN en ${normalize(path.relative(root, file))}.`);
        break;
      }
    }
    if (secretPatterns.some(pattern => pattern.test(text))) {
      errors.push(`Posible secreto en texto plano: ${normalize(path.relative(root, file))}.`);
    }
  }
}

for (const [logicalId, entry] of artifacts) {
  if (!(logicalId.startsWith('module-') || logicalId.startsWith('env-')) || entry?.status !== 'generated') continue;
  const target = resolveContained(root, entry.path, `${logicalId}.contract`);
  if (!target || !fs.existsSync(target)) continue;
  const testInspection = inspectTerraformTests(target);
  if (logicalId.startsWith('module-') && ['plan_mock', 'plan_mock_and_integration'].includes(bob?.terraform_profile?.test_strategy) && testInspection.files.length === 0) {
    errors.push(`${logicalId}: falta tests/*.tftest.hcl requerido por ${bob.terraform_profile.test_strategy}.`);
  }
  for (const error of testInspection.errors) errors.push(`${logicalId}: ${error}`);
  if (!logicalId.startsWith('module-')) continue;
  const declarations = terraformDeclarations(target);
  for (const input of entry.contract?.inputs ?? []) {
    if (!declarations.inputs.has(input)) errors.push(`${logicalId}: input documentado sin variable HCL: ${input}.`);
  }
  for (const output of entry.contract?.outputs ?? []) {
    if (!declarations.outputs.has(output)) errors.push(`${logicalId}: output documentado sin output HCL: ${output}.`);
  }
  for (const input of declarations.inputs) {
    if (!(entry.contract?.inputs ?? []).includes(input)) errors.push(`${logicalId}: variable HCL no declarada en el contrato fuente: ${input}.`);
  }
  for (const output of declarations.outputs) {
    if (!(entry.contract?.outputs ?? []).includes(output)) errors.push(`${logicalId}: output HCL no declarado en el contrato fuente: ${output}.`);
  }
}

if (bob) {
  for (const pipelinePath of bob.target_repo?.pipeline_files ?? []) {
    const full = resolveContained(root, pipelinePath, 'target_repo.pipeline_files');
    if (!full || !fs.existsSync(full)) {
      if (strict) errors.push(`Pipeline declarado pero inexistente: ${normalize(pipelinePath)}.`);
      continue;
    }
    const pipelineText = fs.readFileSync(full, 'utf8');
    const parsed = parseYamlText(pipelineText);
    if (!parsed || typeof parsed !== 'object' || parsed.__error__) {
      errors.push(`Pipeline YAML inválido en ${normalize(pipelinePath)}: ${parsed?.__error__ ?? 'estructura inválida'}.`);
      continue;
    }
    if (bob.adapter_selection?.pipeline === 'github_actions') {
      if (!parsed.jobs || typeof parsed.jobs !== 'object' || Array.isArray(parsed.jobs) || Object.keys(parsed.jobs).length === 0) {
        errors.push(`Workflow ${normalize(pipelinePath)} debe declarar jobs como mapa no vacío.`);
      }
      if (/\bpull_request_target\s*:/i.test(pipelineText)) {
        errors.push(`Workflow ${normalize(pipelinePath)} no puede usar pull_request_target con despliegues.`);
      }
      if (!/permissions:\s*[\s\S]*?contents:\s*read/i.test(pipelineText) ||
          !/permissions:\s*[\s\S]*?id-token:\s*write/i.test(pipelineText)) {
        errors.push(`Workflow ${normalize(pipelinePath)} debe limitar contents: read y habilitar id-token: write para OIDC.`);
      }
      for (const [jobName, job] of Object.entries(parsed.jobs ?? {})) {
        if (!Array.isArray(job?.steps) || job.steps.length === 0) {
          errors.push(`Job ${jobName} en ${normalize(pipelinePath)} no tiene steps.`);
        }
      }
      if (/terraform\s+apply/i.test(pipelineText)) {
        if (!/actions\/upload-artifact@v4/i.test(pipelineText) || !/actions\/download-artifact@v4/i.test(pipelineText) ||
            !/terraform\s+apply[^\n]*\btfplan\b/i.test(pipelineText)) {
          errors.push(`Workflow ${normalize(pipelinePath)} debe aplicar exactamente el tfplan publicado y descargado.`);
        }
        if (!/environment:\s*\$\{\{\s*matrix\.environment\s*\}\}/i.test(pipelineText)) {
          errors.push(`Workflow ${normalize(pipelinePath)} aplica Terraform sin environment protegido por entorno.`);
        }
      }
      if (/drift/i.test(path.basename(pipelinePath)) && /terraform\s+apply/i.test(pipelineText)) {
        errors.push(`Workflow de drift ${normalize(pipelinePath)} no puede ejecutar terraform apply.`);
      }
      if (/Analyze rollout/i.test(pipelineText) && !/Abort and rollback/i.test(pipelineText)) {
        errors.push(`Workflow ${normalize(pipelinePath)} analiza el rollout sin step de abort/rollback.`);
      }
      continue;
    }
    if (bob.adapter_selection?.pipeline === 'gitlab') {
      const reserved = new Set(['include', 'stages', 'variables', 'workflow', 'default', 'image', 'services', 'before_script', 'after_script', 'cache']);
      const jobs = Object.entries(parsed).filter(([name, entry]) =>
        !reserved.has(name) && !name.startsWith('.') && entry && typeof entry === 'object' && !Array.isArray(entry)
      );
      if (jobs.length === 0) errors.push(`Pipeline GitLab ${normalize(pipelinePath)} no declara jobs ejecutables.`);
      for (const [jobName, job] of jobs) {
        if (!job.script && !job.extends && !job.trigger) {
          errors.push(`Job GitLab ${jobName} en ${normalize(pipelinePath)} no declara script, extends o trigger.`);
        }
      }
      if (/terraform\s+apply/i.test(pipelineText)) {
        if (!/artifacts:/i.test(pipelineText) || !/terraform\s+apply[^\n]*\btfplan\b/i.test(pipelineText)) {
          errors.push(`Pipeline GitLab ${normalize(pipelinePath)} debe aplicar el tfplan conservado como artifact.`);
        }
        if (!/environment:/i.test(pipelineText)) {
          errors.push(`Pipeline GitLab ${normalize(pipelinePath)} aplica Terraform sin environment protegido.`);
        }
      }
      if (/drift/i.test(path.basename(pipelinePath)) && /terraform\s+apply/i.test(pipelineText)) {
        errors.push(`Pipeline de drift ${normalize(pipelinePath)} no puede ejecutar terraform apply.`);
      }
      if (/ci-analyze-rollout\.sh/i.test(pipelineText) && !/application_rollback/i.test(pipelineText)) {
        errors.push(`Pipeline GitLab ${normalize(pipelinePath)} analiza el rollout sin job application_rollback.`);
      }
      continue;
    }
    // Azure Pipelines admite un pipeline de un solo job como steps: de nivel raiz (sin stages/jobs
    // envolventes) — forma usada por el colector DORA programado (dora.yml).
    const hasBareSteps = Array.isArray(parsed.steps) && !Array.isArray(parsed.stages) && !Array.isArray(parsed.jobs);
    if (!Array.isArray(parsed.stages) && !Array.isArray(parsed.jobs) && !hasBareSteps) {
      errors.push(`Pipeline ${normalize(pipelinePath)} debe declarar stages o jobs.`);
    }
    if (hasBareSteps && parsed.steps.length === 0) {
      errors.push(`Pipeline ${normalize(pipelinePath)} declara steps vacio.`);
    }
    const stages = flattenStages(parsed.stages);
    const stageNames = new Set();
    const publishedArtifacts = new Set();
    const downloadedArtifacts = [];

    const inspectSteps = steps => {
      for (const step of steps ?? []) {
        if (step?.publish && step.artifact) publishedArtifacts.add(String(step.artifact));
        if (step?.download === 'current' && step.artifact) downloadedArtifacts.push(String(step.artifact));
      }
    };

    for (const stage of stages) {
      const stageName = stage?.stage;
      if (!stageName) errors.push(`Pipeline ${normalize(pipelinePath)} contiene un stage sin nombre.`);
      else if (stageNames.has(stageName)) errors.push(`Stage duplicado en ${normalize(pipelinePath)}: ${stageName}.`);
      else stageNames.add(stageName);
    }
    for (const stage of stages) {
      const dependencies = flattenDependencies(stage?.dependsOn);
      for (const dependency of dependencies) {
        if (!stageNames.has(dependency)) errors.push(`Stage ${stage.stage ?? 'sin nombre'} depende de stage desconocido: ${dependency}.`);
      }
      const jobNames = new Set();
      for (const job of stage.jobs ?? []) {
        const jobName = job?.job ?? job?.deployment;
        if (!jobName) errors.push(`Stage ${stage.stage ?? 'sin nombre'} contiene un job sin nombre.`);
        else if (jobNames.has(jobName)) errors.push(`Job duplicado en stage ${stage.stage}: ${jobName}.`);
        else jobNames.add(jobName);

        if (job?.deployment) {
          const steps = job.strategy?.runOnce?.deploy?.steps;
          if (!Array.isArray(steps) || steps.length === 0) {
            errors.push(`Deployment job ${job.deployment} en ${normalize(pipelinePath)} no tiene strategy.runOnce.deploy.steps.`);
          } else {
            inspectSteps(steps);
            const serialized = JSON.stringify(steps);
            if (/terraform[^"']*\bapply\b/i.test(serialized) &&
                !steps.some(step => step?.checkout === 'self')) {
              errors.push(`Deployment job ${job.deployment} en ${normalize(pipelinePath)} ejecuta Terraform sin checkout: self.`);
            }
          }
        } else if (!Array.isArray(job?.steps) || job.steps.length === 0) {
          errors.push(`Job ${jobName ?? 'sin nombre'} en ${normalize(pipelinePath)} no tiene steps.`);
        } else inspectSteps(job.steps);
      }
    }
    for (const artifact of downloadedArtifacts) {
      if (!publishedArtifacts.has(artifact)) errors.push(`Pipeline ${normalize(pipelinePath)} descarga ${artifact}, pero no lo publica.`);
    }
    // Con pipeline_topology: per_component, cada pipeline de aplicación cubre un solo componente
    // — exigir "Rollback backend" y "Rollback frontend" a la vez en el mismo archivo asumiría la
    // forma del pipeline combinado. Con esa topología basta con al menos un rollback nombrado
    // (Rollback <componente>) presente en el archivo; con single (o sin decidir) se conserva el
    // chequeo estricto original de ambos nombres literales.
    const perComponentTopology = vulcano?.decisions?.pipeline_topology === 'per_component';
    const hasNamedRollback = /Rollback \S+/i.test(pipelineText);
    const hasBothRollbacks = /Rollback backend/i.test(pipelineText) && /Rollback frontend/i.test(pipelineText);
    if (/Swap Slots/i.test(pipelineText)) {
      if (!/Health check posterior al swap/i.test(pipelineText)) {
        errors.push(`Pipeline ${normalize(pipelinePath)} hace slot swap sin health check posterior.`);
      }
      const rollbackOk = perComponentTopology ? hasNamedRollback : hasBothRollbacks;
      if (!rollbackOk) {
        errors.push(`Pipeline ${normalize(pipelinePath)} hace slot swap sin rollback coordinado.`);
      }
    }
    if (/Analyze rollout/i.test(pipelineText)) {
      const rollbackOk = perComponentTopology ? hasNamedRollback : hasBothRollbacks;
      if (!rollbackOk) errors.push(`Pipeline ${normalize(pipelinePath)} analiza el rollout sin rollback coordinado.`);
    }

    const operationalDescriptions = (bob.operational_pending ?? [])
      .map(item => `${item.id ?? ''} ${item.description ?? ''}`.toLowerCase())
      .join('\n');
    for (const parameter of parsed.parameters ?? []) {
      if (parameter?.default !== '') continue;
      const name = String(parameter.name ?? '');
      if (name && pipelineText.includes(`parameters.${name}`) && !operationalDescriptions.includes(name.toLowerCase())) {
        errors.push(`Parámetro operativo vacío sin OP-NNN registrado en ${normalize(pipelinePath)}: ${name}.`);
      }
    }
  }
}

const generatedTerraform = [...artifacts.entries()].filter(([id, entry]) =>
  entry?.status === 'generated' && (id.startsWith('module-') || id.startsWith('env-'))
);

if (skipTools) {
  warnings.push('--skip-tools activo: no se ejecutaron validadores externos.');
} else if (generatedTerraform.length > 0 && bob) {
  const iacRoot = resolveContained(root, bob.target_repo?.iac_root ?? 'infra', 'target_repo.iac_root');
  if (iacRoot && fs.existsSync(iacRoot)) {
    if (!toolAvailable('terraform')) {
      warnings.push('terraform no está instalado; se omitieron fmt/init/validate.');
    } else {
      runTool('terraform', ['fmt', '-check', '-recursive'], iacRoot, `terraform fmt en ${normalize(path.relative(root, iacRoot))}`);
      for (const [logicalId, entry] of generatedTerraform) {
        const terraformPath = resolveContained(root, entry.path, `${logicalId}.path tools`);
        if (!terraformPath || !fs.existsSync(terraformPath)) continue;
        validateTerraformCopy(terraformPath, logicalId, bob.terraform_profile, iacRoot);
      }
    }

    if (toolAvailable('tflint')) runTool('tflint', ['--chdir', iacRoot, '--recursive'], root, 'tflint');
    else warnings.push('tflint no está instalado; se omitió lint.');

    if (toolAvailable('trivy')) runTool('trivy', ['config', iacRoot], root, 'trivy config');
    else if (toolAvailable('tfsec')) runTool('tfsec', [iacRoot], root, 'tfsec');
    else if (toolAvailable('checkov')) runTool('checkov', ['-d', iacRoot], root, 'checkov');
    else warnings.push('Ni trivy, tfsec ni checkov están instalados; se omitió security scan.');
  }
}

const bootstrap = artifacts.get('bootstrap-backend');
if (!skipTools && bootstrap?.status === 'generated') {
  const script = resolveContained(root, bootstrap.path, 'bootstrap-backend.path tools');
  if (script && fs.existsSync(script)) {
    if (toolAvailable('bash')) runTool('bash', ['-n', script], root, 'bash -n del bootstrap');
    else warnings.push('bash no está instalado; se omitió la validación sintáctica del bootstrap.');
    if (toolAvailable('shellcheck')) runTool('shellcheck', [script], root, 'shellcheck del bootstrap');
    else warnings.push('shellcheck no está instalado; se omitió lint del bootstrap.');
  }
}

if (!skipTools && [...artifacts.values()].some(entry => entry?.status === 'generated')) {
  if (toolAvailable('gitleaks')) {
    // gitleaks no autodescubre .gitleaks.toml cuando se invoca con --no-git --source <ruta
    // absoluta fuera de cwd> — pasarlo explícito si el proyecto define uno (permite un allowlist
    // de falsos positivos, ej. fixtures *.tftest.hcl, sin tocar el ruleset por defecto).
    const projectGitleaksConfig = path.join(root, '.gitleaks.toml');
    const gitleaksConfigArgs = fs.existsSync(projectGitleaksConfig) ? ['--config', projectGitleaksConfig] : [];
    const scanned = new Set();
    for (const [logicalId, entry] of artifacts) {
      if (entry?.status !== 'generated') continue;
      const target = resolveContained(root, entry.path, `${logicalId}.path gitleaks`);
      if (!target || !fs.existsSync(target)) continue;
      const source = fs.statSync(target).isDirectory() ? target : path.dirname(target);
      if (scanned.has(source)) continue;
      scanned.add(source);
      runTool('gitleaks', ['detect', '--no-git', '--source', source, '--redact', ...gitleaksConfigArgs], root, `gitleaks en ${logicalId}`);
    }
  } else {
    warnings.push('gitleaks no está instalado; se omitió secret scanning especializado.');
  }
}

if (bob && args.includes('--write-summary')) {
  // Releer el archivo fresco en vez de reusar el objeto `bob` cargado al inicio de esta corrida:
  // una validación real tarda minutos (terraform validate/test + tflint/trivy por módulo), tiempo
  // suficiente para que una edición manual concurrente al manifiesto quede pisada si escribimos de
  // vuelta la copia en memoria más vieja. Solo el resumen de validación depende de esta corrida;
  // el resto del contenido debe ser el que esté en disco en este momento.
  const currentOnDisk = readYaml(bobManifestPath, 'bob-manifest.yaml') ?? bob;
  currentOnDisk.validation = {
    last_run: new Date().toISOString(),
    errors: errors.length,
    warnings: warnings.length
  };
  currentOnDisk.updated_at = new Date().toISOString().slice(0, 10);
  fs.writeFileSync(bobManifestPath, dumpYaml(currentOnDisk), 'utf8');
}

for (const warning of warnings) console.warn(`WARN: ${warning}`);
for (const error of errors) console.error(`ERROR: ${error}`);
console.log(`Vulcano-bob validation: ${errors.length} error(es), ${warnings.length} warning(s).`);
process.exit(errors.length > 0 ? 1 : 0);
