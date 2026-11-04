#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const args = process.argv.slice(2);
const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const normalize = value => value.replaceAll('\\', '/');
const ENVIRONMENTS = ['dev', 'qa', 'prod'];

function argValue(flag, required = false) {
  const index = args.indexOf(flag);
  if (index < 0) {
    if (required) throw new Error(`${flag} es obligatorio.`);
    return null;
  }
  const result = args[index + 1];
  if (!result || result.startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return result;
}

function positiveInt(flag) {
  const raw = argValue(flag, true);
  const value = Number(raw);
  if (!Number.isInteger(value) || value <= 0) throw new Error(`${flag} debe ser un entero positivo (recibido "${raw}").`);
  return value;
}

function loadYaml(file) {
  const code = 'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding="utf-8")), ensure_ascii=False))';
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code, file], { encoding: 'utf8' });
    if (!result.error && result.status === 0) return JSON.parse(result.stdout);
  }
  throw new Error('Se requiere Python con PyYAML para renderizar los manifiestos GitOps.');
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

function readTemplate(assets, name) {
  return fs.readFileSync(contained(assets, path.join('gitops', name), name), 'utf8');
}

try {
  const root = path.resolve(argValue('--root') ?? process.cwd());
  const resources = path.resolve(argValue('--resources-dir') ?? path.join(root, 'resources'));
  const vulcanoPath = path.join(resources, '.vulcano', 'manifest.yaml');
  if (!fs.existsSync(vulcanoPath)) throw new Error('No existe resources/.vulcano/manifest.yaml.');
  const vulcano = loadYaml(vulcanoPath);
  if (vulcano.decisions?.deployment_model !== 'gitops') {
    throw new Error('decisions.deployment_model no es "gitops"; nada que renderizar. Ver references/preguntas-por-archivo.md (ci-cd.md) en vulcano.');
  }

  const appName = argValue('--app-name', true);
  if (!/^[a-z][a-z0-9-]*$/.test(appName)) throw new Error('--app-name debe ser un nombre DNS-safe en minúsculas (ej. "checkout-api").');
  const containerPort = positiveInt('--container-port');
  const imageRepository = argValue('--image-repository', true);
  const manifestsRepoUrl = argValue('--manifests-repo-url', true);
  const initialImageTag = argValue('--initial-image-tag', true);
  const replicas = {
    dev: positiveInt('--replicas-dev'),
    qa: positiveInt('--replicas-qa'),
    prod: positiveInt('--replicas-prod')
  };
  const force = args.includes('--force');
  const assets = path.resolve(skillRoot, 'assets');

  const substitute = text => text
    .replaceAll('__APP_NAME__', appName)
    .replaceAll('__CONTAINER_PORT__', String(containerPort))
    .replaceAll('__IMAGE_REPOSITORY__', imageRepository)
    .replaceAll('__MANIFESTS_REPO_URL__', manifestsRepoUrl)
    .replaceAll('__INITIAL_IMAGE_TAG__', initialImageTag);

  const basePairs = [
    ['base.deployment.template.yaml', 'infra/gitops/base/deployment.yaml'],
    ['base.service.template.yaml', 'infra/gitops/base/service.yaml'],
    ['base.configmap.template.yaml', 'infra/gitops/base/configmap.yaml'],
    ['base.kustomization.template.yaml', 'infra/gitops/base/kustomization.yaml']
  ];
  for (const [template, destination] of basePairs) {
    writeFile(root, destination, substitute(readTemplate(assets, template)), force);
  }

  for (const environment of ENVIRONMENTS) {
    const overlayContent = substitute(readTemplate(assets, 'overlay.kustomization.template.yaml'))
      .replaceAll('__ENVIRONMENT__', environment)
      .replaceAll('__REPLICA_COUNT__', String(replicas[environment]));
    writeFile(root, `infra/gitops/overlays/${environment}/kustomization.yaml`, overlayContent, force);

    const applicationContent = substitute(readTemplate(assets, 'argocd.application.template.yaml'))
      .replaceAll('__ENVIRONMENT__', environment);
    writeFile(root, `infra/gitops/argocd/application-${environment}.yaml`, applicationContent, force);
  }
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
