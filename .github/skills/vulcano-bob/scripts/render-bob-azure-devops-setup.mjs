#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { argValue, replaceMarkerLine, validatePipelineTopology } from './renderers/renderer-lib.mjs';

const args = process.argv.slice(2);
const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const normalize = value => value.replaceAll('\\', '/');

function loadYaml(file) {
  const code = 'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding="utf-8")), ensure_ascii=False))';
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code, file], { encoding: 'utf8' });
    if (!result.error && result.status === 0) return JSON.parse(result.stdout);
  }
  throw new Error('Se requiere Python con PyYAML para renderizar el script de setup de Azure DevOps.');
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
  fs.chmodSync(target, 0o755);
  console.log(`Renderizado ${normalize(destination)}.`);
}

function shellVarName(environmentName) {
  return `ENV_ID_${environmentName.toUpperCase().replaceAll('-', '_')}`;
}

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

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const resources = path.resolve(argValue(args, '--resources-dir') ?? path.join(root, 'resources'));
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  if (!fs.existsSync(vulcanoPath)) throw new Error('No existe resources/.vulcano/manifest.yaml.');
  const vulcano = loadYaml(vulcanoPath);
  if (vulcano.decisions?.devops_platform !== 'azure_devops') {
    throw new Error('decisions.devops_platform no es "azure_devops"; este renderer es específico de Azure DevOps.');
  }

  const terraformGroup = argValue(args, '--terraform-variable-group', true);
  const applicationGroup = argValue(args, '--application-variable-group', true);
  for (const [label, group] of [['terraform', terraformGroup], ['application', applicationGroup]]) {
    if (!/^[A-Za-z0-9._ -]+$/.test(group)) throw new Error(`Variable group ${label} inválido.`);
  }

  const pipelineTopology = argValue(args, '--pipeline-topology', true);
  validatePipelineTopology(pipelineTopology);
  const componentsRaw = argValue(args, '--components');
  if (pipelineTopology === 'per_component' && !componentsRaw) {
    throw new Error('--components es obligatorio con --pipeline-topology per_component (mismos nombres que --components de render-bob-dora.mjs).');
  }
  if (pipelineTopology === 'single' && componentsRaw) {
    throw new Error('--components no aplica con --pipeline-topology single.');
  }
  const components = componentsRaw ? validateComponents(componentsRaw) : null;

  const minReviewersRaw = argValue(args, '--min-reviewers', true);
  const minReviewers = Number(minReviewersRaw);
  if (!Number.isInteger(minReviewers) || minReviewers <= 0) {
    throw new Error(`--min-reviewers debe ser un entero positivo (recibido "${minReviewersRaw}").`);
  }

  const force = args.includes('--force');
  const assets = path.resolve(skillRoot, 'assets');

  // Un nombre de environment por componente (o uno solo si la topología es single) — nunca
  // "dev"/"qa"/"prod" compartido entre componentes: eso mezclaría sus deployment records en el
  // mismo objeto de Azure DevOps y rompería cualquier lectura de DORA por componente.
  const environments = components
    ? components.flatMap(component => [
        { name: `dev-${component}`, description: `Deploy ${component} a dev` },
        { name: `qa-${component}`, description: `Deploy ${component} a qa` },
        { name: `prod-${component}`, description: `Deploy ${component} a prod (blue-green/canary si aplica)` }
      ])
    : [
        { name: 'dev', description: 'Deploy a dev' },
        { name: 'qa', description: 'Deploy a qa' },
        { name: 'prod', description: 'Deploy a prod (blue-green/canary si aplica)' }
      ];

  const creationCalls = environments
    .map(({ name, description }) => `${shellVarName(name)}="$(create_environment "${name}" "${description}")"`)
    .join('\n');
  const idSummary = environments
    .map(({ name }) => `echo "${name} -> \${${shellVarName(name)}}"`)
    .join('\n');

  let content = fs.readFileSync(contained(assets, 'azure-devops-setup.template.sh', 'azure-devops-setup.template.sh'), 'utf8');
  content = content
    .replaceAll('__TERRAFORM_VARIABLE_GROUP__', terraformGroup)
    .replaceAll('__APPLICATION_VARIABLE_GROUP__', applicationGroup)
    .replaceAll('__MIN_REVIEWERS__', String(minReviewers));
  content = replaceMarkerLine(content, '# __ENVIRONMENT_CREATION_CALLS__', creationCalls);
  content = replaceMarkerLine(content, '# __ENVIRONMENT_ID_SUMMARY__', idSummary);

  writeFile(root, 'infra/bootstrap/setup-azure-devops.sh', content, force);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
