#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

function walk(target) {
  if (!fs.existsSync(target)) return [];
  const result = [];
  const stack = [target];
  while (stack.length) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      if (['.terraform', '.git', 'node_modules'].includes(entry.name)) continue;
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) stack.push(full);
      else result.push(full);
    }
  }
  return result;
}

function withoutComments(text) {
  let result = '';
  let quote = false;
  let blockComment = false;
  for (let index = 0; index < text.length; index += 1) {
    const current = text[index];
    const next = text[index + 1];
    if (blockComment) {
      if (current === '*' && next === '/') { blockComment = false; result += '  '; index += 1; }
      else result += current === '\n' ? '\n' : ' ';
      continue;
    }
    if (!quote && current === '/' && next === '*') { blockComment = true; result += '  '; index += 1; continue; }
    if (!quote && current === '/' && next === '/') {
      while (index < text.length && text[index] !== '\n') { result += ' '; index += 1; }
      result += '\n';
      continue;
    }
    if (!quote && current === '#') {
      while (index < text.length && text[index] !== '\n') { result += ' '; index += 1; }
      result += '\n';
      continue;
    }
    if (current === '"' && text[index - 1] !== '\\') quote = !quote;
    result += current;
  }
  return result;
}

function matchingBrace(text, openIndex) {
  let depth = 0;
  let quote = false;
  for (let index = openIndex; index < text.length; index += 1) {
    const current = text[index];
    if (current === '"' && text[index - 1] !== '\\') quote = !quote;
    if (quote) continue;
    if (current === '{') depth += 1;
    if (current === '}') depth -= 1;
    if (depth === 0) return index;
  }
  return -1;
}

function blocks(text, pattern) {
  const result = [];
  for (const match of text.matchAll(pattern)) {
    const open = text.indexOf('{', match.index);
    const close = matchingBrace(text, open);
    if (close < 0) result.push({ name: match[1] ?? null, body: '', malformed: true });
    else result.push({ name: match[1] ?? null, body: text.slice(open + 1, close), malformed: false });
  }
  return result;
}

function requiredProviders(moduleRoot) {
  const providers = new Set();
  const terraform = walk(moduleRoot)
    .filter(file => file.endsWith('.tf') && !file.includes(`${path.sep}tests${path.sep}`))
    .map(file => withoutComments(fs.readFileSync(file, 'utf8')))
    .join('\n');
  for (const block of blocks(terraform, /\brequired_providers\s*\{/g)) {
    for (const match of block.body.matchAll(/\bsource\s*=\s*"[^"]+\/([A-Za-z0-9_-]+)"/g)) providers.add(match[1]);
  }
  return providers;
}

export function inspectTerraformTests(moduleRoot) {
  const testRoot = path.join(moduleRoot, 'tests');
  const files = walk(testRoot).filter(file => file.endsWith('.tftest.hcl'));
  const errors = [];
  const mockedProviders = new Set();
  let runCount = 0;

  for (const file of files) {
    const text = withoutComments(fs.readFileSync(file, 'utf8'));
    for (const match of text.matchAll(/\bmock_provider\s+"([^"]+)"\s*\{/g)) mockedProviders.add(match[1]);
    const runBlocks = blocks(text, /\brun\s+"([^"]+)"\s*\{/g);
    if (runBlocks.length === 0) errors.push(`${path.relative(moduleRoot, file)} no contiene bloques run.`);
    for (const run of runBlocks) {
      runCount += 1;
      if (run.malformed) errors.push(`${path.relative(moduleRoot, file)}: run ${run.name} tiene llaves desbalanceadas.`);
      else if (!/\bcommand\s*=\s*plan\b/.test(run.body)) {
        errors.push(`${path.relative(moduleRoot, file)}: run ${run.name} debe declarar command = plan; apply y el default apply no son locales seguros.`);
      }
    }
  }

  // Sin archivos de test no hay nada que mockear todavia — exigir mock_provider aqui produciria
  // un falso bloqueante en artefactos (ej. env-*) donde test_strategy no exige tests propios.
  const providers = requiredProviders(moduleRoot);
  if (files.length > 0) {
    for (const provider of providers) {
      if (!mockedProviders.has(provider)) errors.push(`tests/ debe declarar mock_provider "${provider}" para impedir acceso real del provider.`);
    }
  }

  return {
    files,
    runCount,
    providers: [...providers].sort(),
    mockedProviders: [...mockedProviders].sort(),
    errors
  };
}

if (path.resolve(process.argv[1] ?? '') === fileURLToPath(import.meta.url)) {
  const root = path.resolve(process.argv[2] ?? process.cwd());
  const result = inspectTerraformTests(root);
  console.log(JSON.stringify({ ...result, files: result.files.map(file => path.relative(root, file).replaceAll('\\', '/')) }, null, 2));
  process.exit(result.errors.length > 0 ? 1 : 0);
}
