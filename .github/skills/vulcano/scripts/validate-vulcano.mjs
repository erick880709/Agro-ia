#!/usr/bin/env node

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const args = process.argv.slice(2);
const errors = [];
const warnings = [];
const strict = args.includes('--strict-completeness');
const normalize = value => value.replaceAll('\\', '/');

const argValue = flag => {
  const index = args.indexOf(flag);
  if (index < 0) return null;
  const value = args[index + 1];
  if (!value || value.startsWith('--')) {
    errors.push(`${flag} requiere una ruta.`);
    return null;
  }
  return value;
};

const rootValue = argValue('--root');
const resourcesValue = argValue('--resources-dir');
const root = path.resolve(rootValue ?? process.cwd());
const resources = resourcesValue ? path.resolve(resourcesValue) : path.join(root, 'resources');
const manifestPath = path.join(resources, '.vulcano', 'manifest.yaml');

const logicalFiles = [
  'devops-overview', 'repository-management', 'task-management', 'branching-strategy',
  'devops-environments', 'iac-architecture', 'iac-environments', 'naming-conventions',
  'iac-structure', 'state-management', 'modules', 'networking', 'secrets-management',
  'ci-cd', 'continuous-testing', 'security', 'release-management', 'incident-management',
  'disaster-recovery', 'monitoring', 'logging', 'tracing', 'slis-slos', 'dashboards',
  'alerting', 'runbooks'
];
const expectedPrefixByLogicalId = new Map([
  ['devops-overview', '01'], ['repository-management', '02'], ['task-management', '03'],
  ['branching-strategy', '04'], ['devops-environments', '05'], ['ci-cd', '06'],
  ['continuous-testing', '07'], ['security', '08'], ['release-management', '09'],
  ['incident-management', '10'], ['disaster-recovery', '11'],
  ['iac-architecture', '01'], ['iac-environments', '02'], ['naming-conventions', '03'],
  ['iac-structure', '04'], ['state-management', '05'], ['modules', '06'],
  ['networking', '07'], ['secrets-management', '08'],
  ['monitoring', '01'], ['logging', '02'], ['tracing', '03'], ['slis-slos', '04'],
  ['dashboards', '05'], ['alerting', '06'], ['runbooks', '07']
]);
const expectedDirectoryByLogicalId = new Map(logicalFiles.map(logicalId => {
  if (logicalId.startsWith('iac-') || ['naming-conventions', 'state-management', 'modules', 'networking', 'secrets-management'].includes(logicalId)) {
    return [logicalId, 'infrastructure-as-code'];
  }
  if (['monitoring', 'logging', 'tracing', 'slis-slos', 'dashboards', 'alerting', 'runbooks'].includes(logicalId)) {
    return [logicalId, 'observability'];
  }
  return [logicalId, 'devops-strategy'];
}));
const allowedStatuses = new Set(['pending', 'generated', 'existing', 'omitted']);
const allowedModes = new Set(['greenfield', 'as-is', 'as-is+to-be']);
const isIsoDate = value => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value ?? '')) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.valueOf()) && date.toISOString().slice(0, 10) === value;
};
const isInside = (parent, child) => {
  const relative = path.relative(parent, child);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
};

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

const parseYamlText = text => {
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', yamlCode], { input: text, encoding: 'utf8' });
    if (!result.error && result.status === 0) {
      try { return JSON.parse(result.stdout); } catch { /* probar siguiente runtime */ }
    }
  }
  return { __error__: 'No se pudo ejecutar Python con PyYAML.' };
};

const walkMarkdown = dir => {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory() && entry.name !== '.vulcano') return walkMarkdown(full);
    return entry.isFile() && entry.name.endsWith('.md') ? [full] : [];
  });
};

let manifest = null;
let fileEntries = {};
const pendingIds = new Set();
const manifestFilesByPath = new Map();
const generatedRecords = [];

if (!fs.existsSync(manifestPath)) {
  const message = `No existe ${normalize(path.relative(root, manifestPath) || manifestPath)}; créalo al iniciar una sesión Vulcano.`;
  (strict ? errors : warnings).push(message);
} else {
  const manifestText = fs.readFileSync(manifestPath, 'utf8');
  manifest = parseYamlText(manifestText);
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)) {
    errors.push('Manifest debe ser un objeto YAML.');
  } else if (manifest.__error__) {
    errors.push(`Manifest YAML inválido: ${manifest.__error__}`);
  } else {
    if (manifest.schema_version !== 1) errors.push('Manifest schema_version debe ser 1.');
    if (typeof manifest.project !== 'string' || !manifest.project.trim()) errors.push('Manifest project es requerido.');
    if (!isIsoDate(manifest.updated_at)) errors.push('Manifest updated_at debe ser una fecha real YYYY-MM-DD.');
    if (typeof manifest.resources_root !== 'string' || !manifest.resources_root.trim()) {
      errors.push('Manifest resources_root es requerido.');
    } else {
      const declaredRoot = path.resolve(root, manifest.resources_root);
      if (declaredRoot !== resources) {
        errors.push(`Manifest resources_root apunta a ${normalize(declaredRoot)}, pero se valida ${normalize(resources)}.`);
      }
    }
    for (const key of ['baseline', 'constraints', 'decisions', 'validation']) {
      if (!manifest[key] || typeof manifest[key] !== 'object' || Array.isArray(manifest[key])) errors.push(`Manifest ${key} debe ser un mapa.`);
    }
    const selectedCloud = manifest.decisions?.cloud_provider ??
      (Array.isArray(manifest.baseline?.cloud_providers) && manifest.baseline.cloud_providers.length === 1
        ? manifest.baseline.cloud_providers[0]
        : null);
    if (typeof selectedCloud !== 'string' || !selectedCloud.trim()) {
      (strict ? errors : warnings).push(
        'Manifest decisions.cloud_provider es obligatorio cuando baseline.cloud_providers no contiene exactamente una nube.'
      );
    } else if (Array.isArray(manifest.baseline?.cloud_providers) &&
               manifest.baseline.cloud_providers.length > 0 &&
               !manifest.baseline.cloud_providers.includes(selectedCloud)) {
      errors.push(`Manifest decisions.cloud_provider ${selectedCloud} no aparece en baseline.cloud_providers.`);
    }
    if (manifest.decisions?.iac === 'terraform') {
      const profile = manifest.decisions.terraform;
      const reportProfile = message => (strict ? errors : warnings).push(`Manifest decisions.terraform: ${message}`);
      if (!profile || typeof profile !== 'object' || Array.isArray(profile)) {
        reportProfile('se requiere el perfil Terraform cuando decisions.iac es terraform.');
      } else {
        const requiredText = ['required_version'];
        const allowed = {
          module_standard: new Set(['internal', 'avm']),
          execution_backend: new Set(['azure_devops', 'github_actions', 'gitlab_ci', 'hcp_terraform']),
          test_strategy: new Set(['plan_mock', 'plan_mock_and_integration']),
          registry_source: new Set(['public', 'private', 'mixed', 'none']),
          registry_mcp: new Set(['read_only', 'disabled']),
          adoption_mode: new Set(['none', 'moved_import'])
        };
        for (const key of requiredText) {
          if (typeof profile[key] !== 'string' || !profile[key].trim()) reportProfile(`${key} es obligatorio.`);
        }
        for (const [key, values] of Object.entries(allowed)) {
          if (!values.has(profile[key])) reportProfile(`${key} debe ser uno de: ${[...values].join(', ')}.`);
        }
        if (!profile.provider_constraints || typeof profile.provider_constraints !== 'object' ||
            Array.isArray(profile.provider_constraints) || Object.keys(profile.provider_constraints).length === 0) {
          reportProfile('provider_constraints debe declarar al menos un provider y su constraint aprobado.');
        } else {
          for (const [provider, constraint] of Object.entries(profile.provider_constraints)) {
            if (!/^[a-z0-9_-]+$/i.test(provider) || typeof constraint !== 'string' || !constraint.trim()) {
              reportProfile(`constraint inválido para provider ${provider}.`);
            }
          }
        }
        if (profile.module_standard === 'avm' &&
            !['azurerm', 'azapi'].some(provider => typeof profile.provider_constraints?.[provider] === 'string')) {
          reportProfile('module_standard avm requiere constraint para azurerm o azapi.');
        }
        const requiredCloudProviders = {
          azure: ['azurerm', 'azapi'],
          aws: ['aws']
        };
        if (requiredCloudProviders[selectedCloud] &&
            !requiredCloudProviders[selectedCloud].some(provider => typeof profile.provider_constraints?.[provider] === 'string')) {
          reportProfile(`cloud_provider ${selectedCloud} requiere constraint para ${requiredCloudProviders[selectedCloud].join(' o ')}.`);
        }
        if (profile.execution_backend === 'azure_devops' && manifest.decisions.devops_platform !== 'azure_devops') {
          reportProfile('execution_backend azure_devops requiere decisions.devops_platform: azure_devops.');
        }
        if (profile.execution_backend === 'github_actions' && !['github', 'github_actions'].includes(manifest.decisions.devops_platform)) {
          reportProfile('execution_backend github_actions requiere decisions.devops_platform: github o github_actions.');
        }
        if (profile.execution_backend === 'gitlab_ci' && manifest.decisions.devops_platform !== 'gitlab') {
          reportProfile('execution_backend gitlab_ci requiere decisions.devops_platform: gitlab.');
        }
      }
    }
    for (const key of ['assumptions', 'intentional_omissions']) {
      if (!Array.isArray(manifest[key])) errors.push(`Manifest ${key} debe ser una lista.`);
    }
    if (strict && manifest.validation && typeof manifest.validation === 'object') {
      if (!isIsoDate(manifest.validation.last_run)) errors.push('Manifest validation.last_run debe registrar una fecha YYYY-MM-DD en el cierre.');
      if (!Number.isInteger(manifest.validation.errors) || manifest.validation.errors < 0) errors.push('Manifest validation.errors debe ser un entero no negativo.');
      if (!Number.isInteger(manifest.validation.warnings) || manifest.validation.warnings < 0) errors.push('Manifest validation.warnings debe ser un entero no negativo.');
    }
    if (!manifest.files || typeof manifest.files !== 'object' || Array.isArray(manifest.files)) errors.push('Manifest files debe ser un mapa.');
    else fileEntries = manifest.files;
    if (!Array.isArray(manifest.pending_decisions)) errors.push('Manifest pending_decisions debe ser una lista.');
    else {
      const seenPending = new Set();
      for (const item of manifest.pending_decisions) {
        if (!item || typeof item !== 'object' || !/^PD-\d{3,}$/.test(item.id ?? '')) errors.push('Cada pending_decision requiere ID PD-NNN.');
        else {
          if (seenPending.has(item.id)) errors.push(`${item.id}: ID de pendiente duplicado.`);
          seenPending.add(item.id);
          pendingIds.add(item.id);
          if (!item.owner || !item.exit_criteria) errors.push(`${item.id}: requiere owner y exit_criteria.`);
        }
      }
    }
    const probableSecret = /(?:api[_-]?key|client[_-]?secret|password|token)\s*[:=]\s*["']?[A-Za-z0-9_\-\/.+=]{16,}/i;
    if (probableSecret.test(manifestText)) errors.push('Manifest contiene un posible secreto.');
  }
}

for (const [logicalId, entry] of Object.entries(fileEntries)) {
  if (!logicalFiles.includes(logicalId)) warnings.push(`Manifest contiene logical_id no estándar: ${logicalId}.`);
  if (!entry || typeof entry !== 'object') { errors.push(`${logicalId}: entrada files inválida.`); continue; }
  if (!allowedStatuses.has(entry.status)) errors.push(`${logicalId}: status inválido.`);
  if (!entry.path || typeof entry.path !== 'string') { errors.push(`${logicalId}: path requerido.`); continue; }
  const expectedPrefix = expectedPrefixByLogicalId.get(logicalId);
  const normalizedEntryPath = normalize(entry.path);
  const outputName = path.posix.basename(normalizedEntryPath);
  if (expectedPrefix && !outputName.startsWith(`${expectedPrefix}-`)) {
    errors.push(`${logicalId}: path debe usar el prefijo canónico ${expectedPrefix}-: ${entry.path}`);
  }
  const expectedDirectory = expectedDirectoryByLogicalId.get(logicalId);
  if (expectedDirectory && path.posix.dirname(normalizedEntryPath) !== expectedDirectory) {
    errors.push(`${logicalId}: path debe estar en ${expectedDirectory}/: ${entry.path}`);
  }
  if (path.isAbsolute(entry.path)) errors.push(`${logicalId}: path debe ser relativo a resources_root.`);
  const resolvedPath = path.resolve(resources, entry.path);
  if (!isInside(resources, resolvedPath)) errors.push(`${logicalId}: path sale de resources_root: ${entry.path}`);
  else {
    if (manifestFilesByPath.has(resolvedPath)) errors.push(`${logicalId}: path duplicado con ${manifestFilesByPath.get(resolvedPath).logicalId}: ${entry.path}`);
    manifestFilesByPath.set(resolvedPath, { logicalId, entry });
  }
  if (['generated', 'existing'].includes(entry.status) && !allowedModes.has(entry.mode)) errors.push(`${logicalId}: mode requerido o inválido.`);
  else if (entry.mode != null && !allowedModes.has(entry.mode)) errors.push(`${logicalId}: mode inválido.`);
  if (['generated', 'existing'].includes(entry.status) && isInside(resources, resolvedPath) && !fs.existsSync(resolvedPath)) {
    errors.push(`${logicalId}: status ${entry.status} pero el archivo no existe: ${entry.path}`);
  }
  if (['generated', 'existing'].includes(entry.status)) {
    if (!Array.isArray(entry.sources) || !entry.sources.length || entry.sources.some(source => typeof source !== 'string' || !source.trim())) errors.push(`${logicalId}: sources debe ser una lista no vacía de textos.`);
    if (typeof entry.owner !== 'string' || !entry.owner.trim()) errors.push(`${logicalId}: owner requerido.`);
    if (!isIsoDate(entry.validated_at)) errors.push(`${logicalId}: validated_at debe ser una fecha real YYYY-MM-DD.`);
    if (typeof entry.summary !== 'string' || !entry.summary.trim()) errors.push(`${logicalId}: summary requerido.`);
    generatedRecords.push({ logicalId, entry, resolvedPath });
  }
  if (entry.status === 'omitted' && !entry.reason) errors.push(`${logicalId}: omitted requiere reason.`);
}

if (manifest) {
  const missingLogical = logicalFiles.filter(id => !(id in fileEntries));
  if (missingLogical.length) (strict ? errors : warnings).push(`Manifest sin ${missingLogical.length} logical_id(s): ${missingLogical.join(', ')}.`);
}

const vulcanoDocs = walkMarkdown(resources).filter(file =>
  /^(devops-strategy|infrastructure-as-code|observability)\//.test(normalize(path.relative(resources, file)))
);
const probableSecret = /(?:api[_-]?key|client[_-]?secret|password|token)\s*[:=]\s*["']?[A-Za-z0-9_\-\/.+=]{16,}/i;
const pendingPattern = /\[PENDIENTE DE DEFINIR(?::\s*([^\]]+))?\]/gi;
const mermaidFence = /```mermaid\s*\r?\n[\s\S]*?```/gi;
const mermaidBlocks = [];
const placeholderHint = /^(?:TBD|TODO|RTO|RPO|ALT-NNN|YYYY-MM-DD|N|%|\.\.\.|proyecto|nombre|herramienta|qui[eé]n|qu[eé]|c[oó]mo|cu[aá]ndo|d[oó]nde|lista|tabla|árbol|baseline|fecha|por qu[eé]|si\b|sí\/no|alta\/crítica|bajo\/medio\/alto|greenfield\b|acci[oó]n|criterio|ej\.|ver\b|URL\b|ALM\b)/i;

const findTemplatePlaceholder = text => {
  const pattern = /\[([^\[\]\n]{1,200})\](?!\()/g;
  for (const match of text.matchAll(pattern)) {
    const value = match[1].trim();
    const before = text[match.index - 1];
    const after = text[match.index + match[0].length];
    if (!value || /^(?:x|X|\d+)$/.test(value) || value.startsWith('PENDIENTE DE DEFINIR')) continue;
    if (before === '!' || after === '[') continue;
    if (placeholderHint.test(value)) return match[0];
  }
  return null;
};

for (const file of vulcanoDocs) {
  const relative = normalize(path.relative(resources, file));
  const text = fs.readFileSync(file, 'utf8');
  const frontmatter = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  let metadata = null;
  if (!frontmatter) errors.push(`${relative}: falta frontmatter.`);
  else {
    metadata = parseYamlText(frontmatter[1]);
    if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata) || metadata.__error__) {
      errors.push(`${relative}: frontmatter YAML inválido${metadata?.__error__ ? `: ${metadata.__error__}` : '.'}`);
      metadata = null;
    } else {
      if (typeof metadata.proyecto !== 'string' || !metadata.proyecto.trim()) errors.push(`${relative}: proyecto requerido en frontmatter.`);
      else if (manifest?.project && metadata.proyecto !== manifest.project) errors.push(`${relative}: proyecto no coincide con manifest.project.`);
      if (!isIsoDate(metadata.fecha)) errors.push(`${relative}: fecha debe ser una fecha real YYYY-MM-DD.`);
      const validSource = (typeof metadata.fuente === 'string' && metadata.fuente.trim()) ||
        (Array.isArray(metadata.fuente) && metadata.fuente.length && metadata.fuente.every(source => typeof source === 'string' && source.trim()));
      if (!validSource) errors.push(`${relative}: fuente debe ser texto o lista no vacía.`);
      if (!allowedModes.has(metadata.modo)) errors.push(`${relative}: modo inválido o ausente.`);
    }
  }
  if (manifest) {
    const record = manifestFilesByPath.get(path.resolve(file));
    if (!record) errors.push(`${relative}: archivo no registrado en el manifiesto.`);
    else {
      if (!['generated', 'existing'].includes(record.entry.status)) errors.push(`${relative}: existe, pero su status en el manifiesto es ${record.entry.status}.`);
      if (metadata?.modo && record.entry.mode !== metadata.modo) errors.push(`${relative}: modo ${metadata.modo} no coincide con manifest (${record.entry.mode}).`);
    }
  }
  const textOutsideMermaid = text.replace(mermaidFence, '');
  const placeholder = findTemplatePlaceholder(textOutsideMermaid);
  if (placeholder) errors.push(`${relative}: contiene placeholder de plantilla sin completar: ${placeholder}`);
  for (const match of text.matchAll(pendingPattern)) {
    const id = match[1]?.trim();
    if (!id || !pendingIds.has(id)) errors.push(`${relative}: pendiente sin ID registrado: ${match[0]}`);
  }
  if (probableSecret.test(text)) errors.push(`${relative}: contiene un posible secreto.`);
  for (const match of text.matchAll(/\[[^\]]+\]\((?!https?:|mailto:|#)([^)]+)\)/g)) {
    const target = match[1].split('#')[0].replace(/^<|>$/g, '');
    if (target && !fs.existsSync(path.resolve(path.dirname(file), target))) warnings.push(`${relative}: enlace local posiblemente roto: ${target}`);
  }
  for (const match of text.matchAll(/```mermaid\s*\r?\n([\s\S]*?)```/gi)) mermaidBlocks.push({ relative, source: match[1] });
}

const splitTableRow = line => line.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim());
const sectionAfter = (text, heading) => {
  const match = text.match(heading);
  if (!match || match.index == null) return '';
  const start = match.index + match[0].length;
  const rest = text.slice(start);
  const next = rest.search(/^##\s/m);
  return next >= 0 ? rest.slice(0, next) : rest;
};
const subsectionAfter = (text, heading) => {
  const match = text.match(heading);
  if (!match || match.index == null) return '';
  const start = match.index + match[0].length;
  const rest = text.slice(start);
  const next = rest.search(/^###\s/m);
  return next >= 0 ? rest.slice(0, next) : rest;
};
const normalizedText = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

const architectureRoots = [...new Set([
  path.join(resources, 'architecture'),
  path.join(root, 'resources', 'architecture'),
].map(value => path.resolve(value)))];
let archiSecurityDocs = architectureRoots
  .flatMap(walkMarkdown)
  .filter(file => /^19\.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_.+\.md$/i.test(path.basename(file)));
archiSecurityDocs = [...new Set(archiSecurityDocs.map(file => path.resolve(file)))];

if (archiSecurityDocs.length > 1) {
  const baselineSources = Array.isArray(manifest?.baseline?.sources) ? manifest.baseline.sources : [];
  const declaredSources = baselineSources.filter(source => typeof source === 'string').join('\n');
  const selected = archiSecurityDocs.filter(file => {
    const relativeToRoot = normalize(path.relative(root, file));
    const relativeToResources = normalize(path.relative(resources, file));
    return declaredSources.includes(relativeToRoot) || declaredSources.includes(relativeToResources);
  });
  if (selected.length === 1) archiSecurityDocs = selected;
  else {
    const message = 'Hay varios 19.1 de Archi y baseline.sources no identifica uno de forma unívoca.';
    (strict ? errors : warnings).push(message);
    archiSecurityDocs = [];
  }
}

if (archiSecurityDocs.length === 1) {
  const archiSecurityText = fs.readFileSync(archiSecurityDocs[0], 'utf8');
  const secIds = new Set([...archiSecurityText.matchAll(/\bSEC-\d{3,}\b/gi)].map(match => match[0].toUpperCase()));
  const securityPath = path.join(resources, 'devops-strategy', '08-security.md');
  if (!secIds.size) {
    const message = `${normalize(path.relative(root, archiSecurityDocs[0]))}: no contiene requisitos SEC-xxx materializables.`;
    (strict ? errors : warnings).push(message);
  } else if (!fs.existsSync(securityPath)) {
    const message = `Existe 19.1 de Archi con ${secIds.size} requisito(s) SEC-xxx, pero falta devops-strategy/08-security.md.`;
    (strict ? errors : warnings).push(message);
  } else {
    const securityText = fs.readFileSync(securityPath, 'utf8');
    if (!/^##\s*Matriz de operacionalizaci[oó]n de requisitos Archi\s*$/im.test(securityText)) {
      errors.push('08-security.md: falta sección Matriz de operacionalización de requisitos Archi.');
    }
    const mappedIds = new Set([...securityText.matchAll(/\bSEC-\d{3,}\b/gi)].map(match => match[0].toUpperCase()));
    for (const secId of secIds) {
      if (!mappedIds.has(secId)) {
        const message = `08-security.md: falta operacionalizar o disponer ${secId} de Archi.`;
        (strict ? errors : warnings).push(message);
      }
    }
  }
}

const ciCd = path.join(resources, 'devops-strategy', '06-ci-cd.md');
if (fs.existsSync(ciCd)) {
  const ciCdText = fs.readFileSync(ciCd, 'utf8');
  const inspection = sectionAfter(ciCdText, /^##\s*Inspecci[oó]n Continua y Deuda T[eé]cnica\s*$/im);
  if (!inspection) errors.push('06-ci-cd.md: falta sección Inspección Continua y Deuda Técnica.');
  else {
    const requiredSubsections = [
      'Métricas y gates de calidad',
      'Integración y feedback en PR',
      'Política de deuda técnica',
      'Excepciones temporales'
    ];
    for (const heading of requiredSubsections) {
      const pattern = new RegExp(`^###\\s*${heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*$`, 'im');
      if (!pattern.test(inspection)) errors.push(`06-ci-cd.md: falta subsección ${heading}.`);
    }

    const metricsSection = subsectionAfter(inspection, /^###\s*M[eé]tricas y gates de calidad\s*$/im);
    const metricRows = metricsSection.split(/\r?\n/)
      .filter(line => line.trim().startsWith('|'))
      .map(splitTableRow)
      .filter(row => row.length && row[0] && !/^[-:]+$/.test(row[0]) && normalizedText(row[0]) !== 'dimension');
    const requiredDimensions = [
      ['cobertura de código nuevo', /cobertura de codigo nuevo/],
      ['duplicación', /duplicacion/],
      ['complejidad', /complejidad/],
      ['mantenibilidad/confiabilidad', /mantenibilidad.*confiabilidad/],
      ['issues bloqueantes', /issues? bloqueantes?/]
    ];
    for (const [label, pattern] of requiredDimensions) {
      const row = metricRows.find(candidate => pattern.test(normalizedText(candidate[0] || '')));
      if (!row) errors.push(`06-ci-cd.md: falta evaluación de ${label} en inspección continua.`);
      else if (row.length < 8 || row.slice(0, 8).some(cell => !cell)) {
        errors.push(`06-ci-cd.md: ${label} requiere definición, baseline, umbral en código nuevo, tratamiento del legado, consecuencia, fuente y owner.`);
      }
    }

    const debtSection = subsectionAfter(inspection, /^###\s*Pol[ií]tica de deuda t[eé]cnica\s*$/im);
    for (const field of ['Baseline y ratchet', 'Regla para código nuevo', 'Tratamiento del legado', 'Registro y owner', 'Priorización / SLA']) {
      if (!normalizedText(debtSection).includes(normalizedText(field))) errors.push(`06-ci-cd.md: política de deuda técnica sin ${field}.`);
    }

    const prSection = subsectionAfter(inspection, /^###\s*Integraci[oó]n y feedback en PR\s*$/im);
    for (const field of ['Herramienta/capacidad', 'Etapa y alcance', 'Feedback', 'Enforcement']) {
      if (!normalizedText(prSection).includes(normalizedText(field))) errors.push(`06-ci-cd.md: feedback en PR sin ${field}.`);
    }

    const exceptionSection = subsectionAfter(inspection, /^###\s*Excepciones temporales\s*$/im);
    const exceptionRows = exceptionSection.split(/\r?\n/)
      .filter(line => line.trim().startsWith('|'))
      .map(splitTableRow)
      .filter(row => row.length && row[0] && !/^[-:]+$/.test(row[0]) && normalizedText(row[0]) !== 'id');
    if (!exceptionRows.length || exceptionRows.some(row => row.length < 6 || row.slice(0, 6).some(cell => !cell))) {
      errors.push('06-ci-cd.md: excepciones temporales requiere una fila completa o declarar explícitamente que no hay ninguna vigente.');
    }
  }
}

const monitoring = path.join(resources, 'observability', '01-monitoring.md');
if (fs.existsSync(monitoring)) {
  const section = sectionAfter(fs.readFileSync(monitoring, 'utf8'), /^##\s*Métricas DORA\s*$/im);
  const metrics = ['deployment frequency', 'change lead time', 'failed deployment recovery time', 'change fail rate', 'deployment rework rate'];
  const rows = section.split(/\r?\n/).filter(line => line.trim().startsWith('|')).map(splitTableRow);
  for (const metric of metrics) {
    const metricRows = rows.filter(row => row.some(cell => cell.toLowerCase() === metric));
    if (!metricRows.length) errors.push(`01-monitoring.md: falta métrica DORA: ${metric}`);
    for (const row of metricRows) {
      if (row.length < 7 || row.slice(0, 7).some(cell => !cell)) errors.push(`01-monitoring.md: ${metric} requiere aplicación/servicio, definición, fuente/ventana, baseline/calidad, meta y equipo accountable/participantes.`);
    }
  }
}

const firstTableColumn = (text, heading) => {
  const match = text.match(heading);
  if (!match || match.index == null) return null;
  const afterHeading = text.slice(match.index + match[0].length);
  const table = afterHeading.match(/\|.*\|\r?\n\|[-:\s|]+\|\r?\n((?:\|.*\|\r?\n?)+)/);
  if (!table) return null;
  return table[1].split(/\r?\n/)
    .filter(row => row.trim())
    .map(row => splitTableRow(row)[0]?.replace(/[*_`]/g, '').trim().toLowerCase())
    .filter(Boolean);
};
const devopsEnvironments = path.join(resources, 'devops-strategy', '05-environments.md');
const iacEnvironments = path.join(resources, 'infrastructure-as-code', '02-environments.md');
if (fs.existsSync(devopsEnvironments) && fs.existsSync(iacEnvironments)) {
  const devopsNames = firstTableColumn(fs.readFileSync(devopsEnvironments, 'utf8'), /##\s*Ambientes existentes/i);
  const iacNames = firstTableColumn(fs.readFileSync(iacEnvironments, 'utf8'), /##\s*Materializaci[oó]n por ambiente/i);
  if (!devopsNames || !iacNames) errors.push('No se pudo leer la tabla ordenada de ambientes en DevOps 05-environments.md o IaC 02-environments.md.');
  else if (devopsNames.join(',') !== iacNames.join(',')) {
    errors.push(`Ambientes u orden de promoción inconsistentes entre devops-strategy/05-environments.md [${devopsNames.join(', ')}] e infrastructure-as-code/02-environments.md [${iacNames.join(', ')}].`);
  }
}

const alerting = path.join(resources, 'observability', '06-alerting.md');
const runbooks = path.join(resources, 'observability', '07-runbooks.md');
if (fs.existsSync(alerting)) {
  const alertText = fs.readFileSync(alerting, 'utf8');
  const alertIds = [...alertText.matchAll(/\b(ALT-\d{3,})\b[^\n]*(?:crítica|critica|alta)/gi)].map(match => match[1].toUpperCase());
  if (alertIds.length && !fs.existsSync(runbooks)) errors.push('Existen alertas altas/críticas, pero falta observability/07-runbooks.md.');
  else if (alertIds.length) {
    const runbookText = fs.readFileSync(runbooks, 'utf8');
    const runbookIds = new Set([...runbookText.matchAll(/\*\*ID:\*\*\s*(ALT-\d{3,})/gi)].map(match => match[1].toUpperCase()));
    for (const id of new Set(alertIds)) if (!runbookIds.has(id)) errors.push(`Falta runbook con ID para alerta alta/crítica: ${id}`);
  }
}

if (strict && manifest) {
  const indexPath = path.join(resources, '01-devops-index.md');
  const maturityPath = path.join(resources, '02-madurez-devsecops.md');
  if (!fs.existsSync(indexPath)) errors.push('Falta resources_root/01-devops-index.md en el cierre.');
  else {
    const indexText = fs.readFileSync(indexPath, 'utf8');
    const linked = new Set([...indexText.matchAll(/\[[^\]]+\]\((?!https?:|mailto:|#)([^)]+)\)/g)].map(match => {
      const target = match[1].split('#')[0].replace(/^<|>$/g, '');
      return path.resolve(path.dirname(indexPath), target);
    }));
    for (const record of generatedRecords) if (!linked.has(record.resolvedPath)) errors.push(`01-devops-index.md no enlaza ${record.entry.path}.`);
  }
  if (!fs.existsSync(maturityPath)) errors.push('Falta resources_root/02-madurez-devsecops.md en el cierre.');
  else {
    const maturity = fs.readFileSync(maturityPath, 'utf8');
    for (const heading of ['Estándar(es) de Referencia', 'Completitud Documental', 'Madurez por Pilar', 'Decisiones pendientes sin resolver', 'Roadmap de Mejora Priorizado']) {
      if (!maturity.toLowerCase().includes(heading.toLowerCase())) errors.push(`02-madurez-devsecops.md: falta sección ${heading}.`);
    }
  }
}

if (mermaidBlocks.length) {
  const probe = spawnSync('npx', ['--no-install', 'mmdc', '--version'], { encoding: 'utf8', shell: os.platform() === 'win32' });
  if (probe.status !== 0) warnings.push('Hay diagramas Mermaid, pero @mermaid-js/mermaid-cli no está instalado; sintaxis no compilada.');
  else {
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-mermaid-'));
    try {
      for (let i = 0; i < mermaidBlocks.length; i++) {
        const input = path.join(temp, `${i}.mmd`); const output = path.join(temp, `${i}.svg`);
        fs.writeFileSync(input, mermaidBlocks[i].source);
        const result = spawnSync('npx', ['--no-install', 'mmdc', '-i', input, '-o', output], { encoding: 'utf8', shell: os.platform() === 'win32' });
        if (result.status !== 0) errors.push(`${mermaidBlocks[i].relative}: Mermaid inválido: ${(result.stderr || result.stdout).trim()}`);
      }
    } finally { fs.rmSync(temp, { recursive: true, force: true }); }
  }
}

const uniqueWarnings = [...new Set(warnings)];
const uniqueErrors = [...new Set(errors)];
for (const warning of uniqueWarnings) console.warn(`WARN: ${warning}`);
for (const error of uniqueErrors) console.error(`ERROR: ${error}`);
console.log(`Vulcano validation: ${uniqueErrors.length} error(es), ${uniqueWarnings.length} warning(s).`);
process.exitCode = uniqueErrors.length ? 1 : 0;
