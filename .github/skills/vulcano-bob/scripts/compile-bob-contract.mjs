#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const args = process.argv.slice(2);
const normalize = value => value.replaceAll('\\', '/');

function value(flag) {
  const index = args.indexOf(flag);
  if (index < 0) return null;
  const result = args[index + 1];
  if (!result || result.startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return result;
}

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

const emptyValidation = () => ({
  format: null, validate: null, test: null, lint: null, security: null, syntax: null, last_run: null, evidence: {}
});

function parseModules(markdown) {
  const headings = [...markdown.matchAll(/^## `([^`]+)`\s*$/gm)];
  return headings.map((match, index) => {
    const name = match[1];
    const body = markdown.slice(match.index + match[0].length, headings[index + 1]?.index ?? markdown.length);
    const inputBlock = body.match(/- \*\*Inputs:\*\*([\s\S]*?)(?=\n- \*\*Outputs:\*\*)/)?.[1] ?? '';
    const inputRows = [...inputBlock.matchAll(/^\s*\|\s*`([^`]+)`\s*\|([^|]*)\|([^|]*)\|([^|]*)\|/gm)];
    const inputs = inputRows.map(item => item[1]);
    const outputText = body.match(/- \*\*Outputs:\*\*([\s\S]*?)(?=\n- \*\*(?:Depende de|Origen):\*\*)/)?.[1] ?? '';
    const outputTextWithoutAsides = outputText.replaceAll(/\([^)]*\)/g, '');
    const isTerminalModule = /\bninguno\b/i.test(outputText);
    const outputs = isTerminalModule ? [] : [...outputTextWithoutAsides.matchAll(/`([^`]+)`/g)].map(item => item[1]);
    const dependsBlock = body.match(/- \*\*Depende de:\*\*([\s\S]*?)(?=\n- \*\*Origen:\*\*)/)?.[1] ?? '';
    const explicitDependencies = /\bninguno\b/i.test(dependsBlock)
      ? []
      : [...dependsBlock.matchAll(/`([^`]+)`/g)].map(item => item[1]);
    const origin = body.match(/- \*\*Origen:\*\*[\s\S]*?`(infra\/modules\/[^`]+)`/)?.[1] ?? `infra/modules/${name}`;
    if (inputs.length === 0 || (outputs.length === 0 && !isTerminalModule)) {
      throw new Error(`El módulo ${name} no declara una tabla de Inputs y una lista de Outputs analizables.`);
    }
    return { name, body, inputs: [...new Set(inputs)], outputs: [...new Set(outputs)], explicitDependencies: [...new Set(explicitDependencies)], path: origin };
  });
}

try {
  const root = path.resolve(value('--root') ?? process.cwd());
  const resources = path.resolve(value('--resources-dir') ?? path.join(root, 'resources'));
  const manifestPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  const modulesPath = path.join(resources, 'infrastructure-as-code', '06-modules.md');
  if (!fs.existsSync(manifestPath)) throw new Error('Primero ejecutar init-bob-manifest.mjs.');
  if (!fs.existsSync(modulesPath)) throw new Error('No existe infrastructure-as-code/06-modules.md.');

  const manifest = JSON.parse(yaml('load', fs.readFileSync(manifestPath, 'utf8')));
  const modules = parseModules(fs.readFileSync(modulesPath, 'utf8'));
  if (modules.length === 0) throw new Error('06-modules.md no contiene módulos con encabezado ## `nombre`.');
  const outputProducers = new Map();
  for (const module of modules) for (const output of module.outputs) outputProducers.set(output, module.name);

  const previous = manifest.artifacts ?? {};
  const compiled = {};
  for (const module of modules) {
    const logicalId = `module-${module.name}`;
    const dependencies = new Set();
    for (const input of module.inputs) {
      const producer = outputProducers.get(input);
      if (producer && producer !== module.name) dependencies.add(`module-${producer}`);
    }
    for (const dependencyName of module.explicitDependencies) {
      if (dependencyName === module.name) {
        throw new Error(`El módulo ${module.name} declara \`Depende de\` sobre sí mismo.`);
      }
      if (!modules.some(candidate => candidate.name === dependencyName)) {
        throw new Error(`El módulo ${module.name} declara \`Depende de: ${dependencyName}\`, que no existe en el catálogo de 06-modules.md.`);
      }
      dependencies.add(`module-${dependencyName}`);
    }
    const prior = previous[logicalId];
    const contract = { inputs: module.inputs, outputs: module.outputs };
    const compatible = prior && prior.path === module.path && JSON.stringify(prior.contract) === JSON.stringify(contract);
    compiled[logicalId] = {
      path: module.path,
      status: compatible ? prior.status : 'pending',
      depends_on: [...dependencies],
      contract,
      source_docs: ['infrastructure-as-code/06-modules.md'],
      source_hashes: compatible ? prior.source_hashes : {},
      validated: compatible ? prior.validated : emptyValidation()
    };
    if (compatible && prior.reason) compiled[logicalId].reason = prior.reason;
  }

  const staticArtifacts = Object.fromEntries(Object.entries(previous).filter(([id]) => !id.startsWith('module-')));
  const moduleIds = Object.keys(compiled);
  for (const [id, artifact] of Object.entries(staticArtifacts)) {
    if (id.startsWith('env-')) artifact.depends_on = moduleIds;
  }
  manifest.artifacts = { ...staticArtifacts, ...compiled };
  manifest.updated_at = new Date().toISOString().slice(0, 10);
  fs.writeFileSync(manifestPath, yaml('dump', JSON.stringify(manifest)), 'utf8');
  console.log(`Contrato compilado: ${modules.length} módulo(s) derivados de 06-modules.md.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
