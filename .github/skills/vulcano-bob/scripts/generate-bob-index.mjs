#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const args = process.argv.slice(2);
const normalize = value => value.replaceAll('\\', '/');

function argValue(flag) {
  const index = args.indexOf(flag);
  if (index < 0) return null;
  const value = args[index + 1];
  if (!value || value.startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return value;
}

function loadYaml(text) {
  const code = 'import json,sys,yaml; print(json.dumps(yaml.safe_load(sys.stdin.read()), ensure_ascii=False))';
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code], { input: text, encoding: 'utf8' });
    if (!result.error && result.status === 0) return JSON.parse(result.stdout);
  }
  throw new Error('Se requiere Python con PyYAML para leer bob-manifest.yaml.');
}

function escapeCell(value) {
  return String(value ?? '').replaceAll('|', '\\|').replaceAll('\n', ' ');
}

try {
  const root = path.resolve(argValue('--root') ?? process.cwd());
  const resources = path.resolve(argValue('--resources-dir') ?? path.join(root, 'resources'));
  const manifestPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  if (!fs.existsSync(manifestPath)) throw new Error(`No existe ${normalize(path.relative(root, manifestPath))}.`);
  const manifest = loadYaml(fs.readFileSync(manifestPath, 'utf8'));
  if (manifest.schema_version !== 4) throw new Error('bob-manifest.yaml debe usar schema_version 4.');
  const indexPath = path.resolve(root, manifest.closure_index);
  const relativeIndex = path.relative(root, indexPath);
  if (relativeIndex.startsWith('..') || path.isAbsolute(relativeIndex)) throw new Error('closure_index sale del workspace.');

  const groups = [
    ['Bootstrap', ([id]) => id === 'bootstrap-backend'],
    ['Módulos Terraform', ([id]) => id.startsWith('module-')],
    ['Ambientes Terraform', ([id]) => id.startsWith('env-')],
    ['Pipelines', ([id]) => id.startsWith('pipeline-')]
  ];
  const lines = [
    `# Índice de IaC y pipelines — ${manifest.project}`,
    '',
    `Generado desde \`resources/.vulcano/bob-manifest.yaml\` (schema v${manifest.schema_version}).`,
    `Última actualización del manifiesto: ${manifest.updated_at}.`,
    ''
  ];

  const entries = Object.entries(manifest.artifacts ?? {});
  for (const [title, predicate] of groups) {
    lines.push(`## ${title}`, '', '| Artefacto | Estado | Ruta | Fuentes | Última validación |', '|---|---|---|---|---|');
    for (const [logicalId, artifact] of entries.filter(predicate)) {
      const target = path.resolve(root, artifact.path);
      const link = normalize(path.relative(path.dirname(indexPath), target));
      const sources = (artifact.source_docs ?? []).map(source => `[${source}](${source})`).join('<br>');
      lines.push(
        `| \`${escapeCell(logicalId)}\` | ${escapeCell(artifact.status)} | ` +
        `[${escapeCell(artifact.path)}](${link}) | ${sources} | ${escapeCell(artifact.validated?.last_run ?? 'pendiente')} |`
      );
    }
    lines.push('');
  }

  const conflicts = entries.filter(([, artifact]) => artifact.status === 'conflict');
  const pending = entries.filter(([, artifact]) => artifact.status === 'pending');
  lines.push('## Resumen', '');
  lines.push(`- Generados: ${entries.filter(([, artifact]) => artifact.status === 'generated').length}`);
  lines.push(`- Pendientes: ${pending.length}`);
  lines.push(`- Conflictos: ${conflicts.length}`);
  lines.push(`- Omitidos: ${entries.filter(([, artifact]) => artifact.status === 'omitted').length}`);
  lines.push('');

  fs.mkdirSync(path.dirname(indexPath), { recursive: true });
  fs.writeFileSync(indexPath, `${lines.join('\n')}\n`, 'utf8');
  console.log(`Generado ${normalize(path.relative(root, indexPath))}.`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
