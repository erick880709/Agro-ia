#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { getAdapterDescriptor, resolveAdapters } from './adapter-registry.mjs';
import { validateCron, replaceMarkerLine } from './renderers/renderer-lib.mjs';

const args = process.argv.slice(2);
const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const normalize = value => value.replaceAll('\\', '/');

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
  throw new Error('Se requiere Python con PyYAML para renderizar el colector DORA.');
}

/**
 * Valida `--components` (decisions.pipeline_topology: per_component en Vulcano): lista separada
 * por comas de nombres de componente, en minúsculas, sin duplicados. Refleja las mismas reglas
 * que `parseComponents` en `dora-collect.template.mjs`, para que el renderer y el colector nunca
 * diverjan sobre qué es un nombre válido.
 * @param {string} raw - Valor crudo recibido en `--components`.
 * @returns {string[]} Nombres de componente validados, en el orden dado.
 * @throws {Error} Si la lista está vacía, tiene un nombre inválido o un nombre repetido.
 */
function validateComponents(raw) {
  const names = raw.split(',').map(name => name.trim()).filter(Boolean);
  if (names.length === 0) throw new Error('--components no puede estar vacío.');
  const seen = new Set();
  for (const name of names) {
    if (!/^[a-z0-9-]+$/.test(name)) throw new Error(`--components: nombre inválido "${name}" (usar minúsculas, dígitos y guiones).`);
    if (seen.has(name)) throw new Error(`--components: componente duplicado "${name}".`);
    seen.add(name);
  }
  return names;
}

function componentEnvSuffix(name) {
  return name.toUpperCase().replaceAll('-', '_');
}

function componentPascalCase(name) {
  return name.split('-').map(part => part.charAt(0).toUpperCase() + part.slice(1)).join('');
}

/**
 * Construye el reemplazo del marcador `__DORA_ENVIRONMENT_VARS__` para la plataforma de pipeline
 * seleccionada. Sin `components` (topología `single`), preserva exactamente el comportamiento
 * previo a esta capacidad — para Azure DevOps, la única variable `DORA_ENVIRONMENT_ID` que ya
 * existía; para GitHub Actions/GitLab, ninguna variable adicional (el colector asume el
 * componente único `app`).
 * @param {string} platformId - `adapter_selection.pipeline` resuelto (`azure_devops`,
 *   `github_actions`, `gitlab`).
 * @param {string[]|null} components - Lista validada de `--components`, o `null` si no se pasó.
 * @returns {string|null} Línea(s) de reemplazo para el marcador, o `null` para eliminarlo.
 */
function environmentVarsReplacement(platformId, components) {
  if (platformId === 'azure_devops') {
    if (!components) return '      DORA_ENVIRONMENT_ID: $(prodEnvironmentId)';
    const lines = [`      DORA_COMPONENTS: ${components.join(',')}`];
    for (const name of components) {
      lines.push(`      DORA_ENVIRONMENT_ID_${componentEnvSuffix(name)}: $(prodEnvironmentId${componentPascalCase(name)})`);
    }
    return lines.join('\n');
  }
  if (platformId === 'github_actions') {
    return components ? `          DORA_COMPONENTS: ${components.join(',')}` : null;
  }
  if (platformId === 'gitlab') {
    return components ? `    DORA_COMPONENTS: ${components.join(',')}` : null;
  }
  throw new Error(`unsupported_adapter: pipeline/${platformId} no declara soporte de componentes DORA.`);
}

function contained(base, candidate, label) {
  const resolved = path.resolve(base, candidate);
  const relative = path.relative(base, resolved);
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error(`${label} sale del directorio permitido.`);
  return resolved;
}

function writeFile(root, destination, content, force) {
  const target = contained(root, destination, destination);
  if (fs.existsSync(target) && !force) {
    throw new Error(`${normalize(destination)} ya existe; usar --force solo después de reconciliarlo.`);
  }
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, content, 'utf8');
  console.log(`Renderizado ${normalize(destination)}.`);
}

try {
  const root = path.resolve(argValue('--root') ?? process.cwd());
  const resources = path.resolve(argValue('--resources-dir') ?? path.join(root, 'resources'));
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  if (!fs.existsSync(vulcanoPath)) throw new Error('No existe resources/.vulcano/manifest.yaml.');
  const vulcano = loadYaml(vulcanoPath);
  if (vulcano.decisions?.dora_collection_method !== 'automated') {
    throw new Error('decisions.dora_collection_method no es "automated"; nada que renderizar. Ver references/preguntas-por-archivo.md (monitoring.md) en vulcano.');
  }
  const selection = resolveAdapters(vulcano);
  const pipeline = getAdapterDescriptor('pipeline', selection.pipeline);
  if (!pipeline.dora_pipeline || !pipeline.dora_collector_script) {
    throw new Error(`unsupported_adapter: pipeline/${selection.pipeline} no declara soporte de colector DORA.`);
  }

  const assets = path.resolve(skillRoot, 'assets');
  const force = args.includes('--force');

  // decisions.pipeline_topology (vulcano, 06-ci-cd.md §Integración Continua): con per_component,
  // --components debe listar los mismos nombres que ya identifican cada pipeline de aplicación
  // (ver render-*-app.mjs), para que el colector mida cada uno por separado en vez de un
  // dataset combinado que ocultaría cuál componente realmente cambia una métrica.
  const componentsRaw = argValue('--components');
  const components = componentsRaw ? validateComponents(componentsRaw) : null;

  const { cron_placeholder: cronPlaceholder, template, path: destination } = pipeline.dora_pipeline;
  let content = fs.readFileSync(contained(assets, template, 'dora_pipeline.template'), 'utf8');
  if (cronPlaceholder) {
    const cron = argValue('--dora-cron');
    if (!cron) throw new Error(`--dora-cron es obligatorio para pipeline/${selection.pipeline}.`);
    validateCron(cron);
    if (!content.includes(cronPlaceholder)) throw new Error(`La plantilla ya no contiene ${cronPlaceholder}; revisar el renderer.`);
    content = content.replaceAll(cronPlaceholder, cron);
  }
  content = replaceMarkerLine(content, '# __DORA_ENVIRONMENT_VARS__', environmentVarsReplacement(selection.pipeline, components));

  const applicationGroup = argValue('--application-variable-group');
  if (applicationGroup) {
    if (!/^[A-Za-z0-9._ -]+$/.test(applicationGroup)) throw new Error('Variable group de aplicación inválido.');
    if (!content.includes('vulcano-application-deploy')) {
      throw new Error(`--application-variable-group no aplica a pipeline/${selection.pipeline} (no referencia vulcano-application-deploy).`);
    }
    content = content.replaceAll('vulcano-application-deploy', applicationGroup);
  }

  const scriptSource = contained(assets, pipeline.dora_collector_script.template, 'dora_collector_script.template');
  writeFile(root, pipeline.dora_collector_script.path, fs.readFileSync(scriptSource, 'utf8'), force);
  writeFile(root, destination, content, force);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
