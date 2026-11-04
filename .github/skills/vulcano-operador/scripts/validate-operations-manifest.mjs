#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolveOperatorAdapters } from './adapter-registry.mjs';
import { argValue, assertSanitized, loadContext, scopeFor, sha256File, updateDate, writeYaml } from './operations-lib.mjs';

const args = process.argv.slice(2);
const errors = [];
const warnings = [];
const strict = args.includes('--strict');

function validateSchema(manifest) {
  const schemaPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'assets', 'operations-manifest.schema.json');
  const code = [
    'import json,sys',
    'try:', ' import jsonschema',
    'except Exception as exc:', ' print(json.dumps({"unavailable": str(exc)})); sys.exit(0)',
    'p=json.load(sys.stdin)', 'issues=[]',
    'for e in jsonschema.Draft202012Validator(p["schema"]).iter_errors(p["data"]):',
    ' issues.append({"path": ".".join(str(x) for x in e.path), "message": e.message})',
    'print(json.dumps({"issues": issues}))'
  ].join('\n');
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code], {
      input: JSON.stringify({ schema: JSON.parse(fs.readFileSync(schemaPath, 'utf8')), data: manifest }), encoding: 'utf8'
    });
    if (!result.error && result.status === 0) {
      const parsed = JSON.parse(result.stdout);
      if (parsed.unavailable) warnings.push(`jsonschema no disponible: ${parsed.unavailable}.`);
      for (const issue of parsed.issues ?? []) errors.push(`schema ${issue.path || '$'}: ${issue.message}`);
      return;
    }
  }
  errors.push('No se pudo ejecutar JSON Schema.');
}

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const resources = path.resolve(argValue(args, '--resources-dir') ?? path.join(root, 'resources'));
  const context = loadContext(root, resources);
  validateSchema(context.operations);
  try { assertSanitized(context.operations, 'operations-manifest.yaml'); } catch (error) { errors.push(error.message); }
  if (sha256File(context.bobPath) !== context.operations.source.bob_sha256) errors.push('Drift: bob-manifest.yaml cambió después del gate operacional.');
  if (context.operations.project !== context.bob.project) errors.push('El proyecto operacional no coincide con Bob.');

  let resolved = null;
  try {
    resolved = resolveOperatorAdapters(context.bob);
    if (context.operations.operator_selection?.platform !== resolved.selection.platform ||
        context.operations.operator_selection?.cloud !== resolved.selection.cloud ||
        context.operations.operator_selection?.status !== resolved.selection.status) {
      errors.push('operator_selection no coincide con Bob.');
    }
  } catch (error) {
    errors.push(error.message);
  }

  if (strict && context.operations.gate.status !== 'ready') errors.push('Cierre estricto requiere gate.status ready.');
  if (strict && context.operations.capabilities.platform_mcp !== 'available') {
    errors.push(`Cierre estricto requiere ${resolved?.platform.mcp_capability ?? 'platform MCP'} disponible.`);
  }
  if (strict && resolved) {
    for (const field of resolved.platform.required_target_fields ?? []) {
      if (!context.operations.target[field]) errors.push(`Cierre estricto requiere target.${field}.`);
    }
    if (!context.operations.reconciliation.observed_at || !context.operations.reconciliation.snapshot_sha256) {
      errors.push('Cierre estricto requiere reconciliación registrada.');
    }
  }

  for (const [id, action] of Object.entries(context.operations.actions ?? {})) {
    if (!/^OP-ACT-\d{3}$/.test(id)) errors.push(`ID de acción inválido: ${id}.`);
    if (!context.bob.artifacts?.[action.logical_id]) errors.push(`${id}: logical_id desconocido ${action.logical_id}.`);
    const expectedRisk = resolved?.platform.allowed_actions?.[action.type];
    if (!expectedRisk) errors.push(`${id}: acción ${action.type} no permitida por el adaptador.`);
    else if (expectedRisk !== action.risk) errors.push(`${id}: riesgo ${action.risk} no coincide con ${expectedRisk}.`);
    if (scopeFor(action) !== action.scope_hash) errors.push(`${id}: scope_hash no coincide con el alcance.`);
    if (['authorized', 'running'].includes(action.status)) {
      if (!action.authorization) errors.push(`${id}: ${action.status} sin autorización.`);
      else {
        if (action.authorization.scope_hash !== action.scope_hash) errors.push(`${id}: autorización para otro alcance.`);
        if (Date.now() >= Date.parse(action.authorization.expires_at)) errors.push(`${id}: autorización expirada.`);
      }
    }
    if (['succeeded', 'verified'].includes(action.status) && action.execution?.result !== 'succeeded') errors.push(`${id}: ${action.status} sin ejecución exitosa.`);
    if (action.status === 'verified' && action.verification?.result !== 'succeeded') errors.push(`${id}: verified sin verificación exitosa.`);
    if (action.risk === 'execute' && /prod/i.test(action.target_ref) && action.status === 'authorized') {
      warnings.push(`${id}: ejecutar producción no autoriza ni responde approvals.`);
    }
  }

  context.operations.validation = { last_run: new Date().toISOString(), errors: errors.length, warnings: warnings.length };
  updateDate(context.operations);
  writeYaml(context.operationsPath, context.operations);
} catch (error) {
  errors.push(error.message);
}

for (const warning of warnings) console.warn(`WARN: ${warning}`);
for (const error of errors) console.error(`ERROR: ${error}`);
console.log(`Vulcano Operador validation: ${errors.length} error(es), ${warnings.length} warning(s).`);
process.exit(errors.length > 0 ? 1 : 0);
