#!/usr/bin/env node

import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { inspectTerraformTests } from './terraform-test-policy.mjs';

const args = process.argv.slice(2);
const normalize = value => value.replaceAll('\\', '/');

function value(flag, required = false) {
  const index = args.indexOf(flag);
  if (index < 0) {
    if (required) throw new Error(`${flag} es obligatorio.`);
    return null;
  }
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

function contained(base, candidate, label) {
  if (path.isAbsolute(candidate)) throw new Error(`${label} debe ser relativa.`);
  const resolved = path.resolve(base, candidate);
  const relative = path.relative(base, resolved);
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error(`${label} sale del workspace.`);
  return resolved;
}

const TOOL_VERSION_TIMEOUT_MS = 15_000;
const TOOL_RUN_TIMEOUT_MS = 180_000;

function commandVersion(command) {
  const result = spawnSync(command, ['--version'], { encoding: 'utf8', timeout: TOOL_VERSION_TIMEOUT_MS });
  return !result.error && result.status === 0
    ? `${result.stdout}${result.stderr}`.trim().split(/\r?\n/)[0]
    : null;
}

function execute(command, toolArgs, cwd, label) {
  const startedAt = new Date().toISOString();
  const result = spawnSync(command, toolArgs, { cwd, encoding: 'utf8', timeout: TOOL_RUN_TIMEOUT_MS });
  const output = `${result.stdout ?? ''}${result.stderr ?? ''}`;
  const timedOut = result.signal === 'SIGTERM' || result.error?.code === 'ETIMEDOUT';
  const evidence = {
    status: !result.error && result.status === 0 ? 'passed' : 'failed',
    tool: command,
    tool_version: commandVersion(command),
    command: [command, ...toolArgs].join(' '),
    exit_code: result.status,
    output_sha256: crypto.createHash('sha256').update(output).digest('hex'),
    run_at: startedAt
  };
  if (evidence.status !== 'passed') {
    const reason = timedOut ? ` (timeout tras ${TOOL_RUN_TIMEOUT_MS / 1000}s; posible falta de red o registro Terraform inalcanzable)` : '';
    throw new Error(`${label} falló${reason}:\n${output.trim() || result.error?.message}`);
  }
  return evidence;
}

const skipped = (tool, reason) => ({ status: 'skipped', tool, reason, run_at: new Date().toISOString() });

function pipelineEvidence(file) {
  const code = [
    'import sys,yaml',
    'd=yaml.safe_load(open(sys.argv[1], encoding="utf-8"))',
    'has_stages=isinstance(d.get("stages"),list)',
    'has_jobs=isinstance(d.get("jobs"),list)',
    // Azure Pipelines admite un pipeline de un solo job como steps: de nivel raiz (sin stages/jobs
    // envolventes) — forma usada por el colector DORA programado (dora.yml).
    'has_bare_steps=isinstance(d.get("steps"),list) and not has_stages and not has_jobs',
    'assert isinstance(d,dict) and (has_stages or has_jobs or has_bare_steps)',
    'if has_bare_steps:',
    ' assert d["steps"]',
    // Una entrada de stages puede venir envuelta en una expresión de plantilla evaluada en
    // tiempo de compilación (p.ej. "${{ if eq(parameters.deployQa, true) }}:") en vez de tener
    // stage/jobs directos — expandir esos bloques antes de validar cada stage real.
    'def expand_stages(entries):',
    ' for e in entries:',
    '  if not isinstance(e, dict): continue',
    '  if "stage" in e: yield e',
    '  else:',
    '   for k, v in e.items():',
    '    if k.startswith("${{") and isinstance(v, list):',
    '     yield from expand_stages(v)',
    'for s in expand_stages(d.get("stages",[]) or []):',
    ' assert s.get("stage") and isinstance(s.get("jobs"),list)',
    ' for j in s.get("jobs",[]):',
    '  steps=j.get("steps") if "job" in j else j.get("strategy",{}).get("runOnce",{}).get("deploy",{}).get("steps")',
    '  assert isinstance(steps,list) and steps',
    'for j in (d.get("jobs") or []):',
    ' steps=j.get("steps") if "job" in j else j.get("strategy",{}).get("runOnce",{}).get("deploy",{}).get("steps")',
    ' assert isinstance(steps,list) and steps'
  ].join('\n');
  for (const python of ['python', 'python3']) {
    if (commandVersion(python)) return execute(python, ['-c', code, file], path.dirname(file), 'Validación YAML/semántica');
  }
  throw new Error('Se requiere Python con PyYAML para validar pipelines.');
}

try {
  const root = path.resolve(value('--root') ?? process.cwd());
  const resources = path.resolve(value('--resources-dir') ?? path.join(root, 'resources'));
  const logicalId = value('--logical-id', true);
  const manifestPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  if (!fs.existsSync(manifestPath)) throw new Error('No existe bob-manifest.yaml.');
  const manifest = JSON.parse(yaml('load', fs.readFileSync(manifestPath, 'utf8')));
  const artifact = manifest.artifacts?.[logicalId];
  if (!artifact) throw new Error(`logical_id desconocido: ${logicalId}.`);
  for (const dependency of artifact.depends_on ?? []) {
    if (!['generated', 'omitted'].includes(manifest.artifacts?.[dependency]?.status)) {
      throw new Error(`${logicalId} depende de ${dependency}, que no está cerrado.`);
    }
  }
  const artifactPath = contained(root, artifact.path, `${logicalId}.path`);
  if (!fs.existsSync(artifactPath)) throw new Error(`No existe ${normalize(artifact.path)}.`);
  const validated = {
    format: null, validate: null, test: null, lint: null, security: null, syntax: null,
    last_run: new Date().toISOString(), evidence: {}
  };

  if (logicalId.startsWith('module-') || logicalId.startsWith('env-')) {
    if (!commandVersion('terraform')) throw new Error('terraform es obligatorio para marcar IaC como generated.');
    validated.evidence.format = execute('terraform', ['fmt', '-check', '-recursive', artifactPath], root, 'terraform fmt');
    validated.format = true;
    const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-bob-record-'));
    // env-* root modules referencian modulos propios por path local relativo
    // (../../modules/<nombre>, ver 04-terraform-structure.md) — copiar solo la carpeta del
    // ambiente rompe esa referencia. Para env-*, replicar el arbol completo de iac_root
    // preservando la posicion relativa; module-* si se valida aislado (harness minimo).
    const iacRoot = manifest.target_repo?.iac_root ? path.resolve(root, manifest.target_repo.iac_root) : null;
    const isEnvWithinIacRoot = logicalId.startsWith('env-') && iacRoot &&
      (artifactPath === iacRoot || artifactPath.startsWith(iacRoot + path.sep));
    let temp;
    if (isEnvWithinIacRoot) {
      const relativeInsideIacRoot = path.relative(iacRoot, artifactPath);
      fs.cpSync(iacRoot, path.join(tempRoot, 'iac_root'), { recursive: true, filter: source => path.basename(source) !== '.terraform' });
      temp = path.join(tempRoot, 'iac_root', relativeInsideIacRoot);
    } else {
      temp = path.join(tempRoot, 'artifact');
      fs.cpSync(artifactPath, temp, { recursive: true, filter: source => path.basename(source) !== '.terraform' });
    }
    try {
      validated.evidence.init = execute('terraform', ['init', '-backend=false', '-input=false'], temp, 'terraform init');
      validated.evidence.validate = execute('terraform', ['validate'], temp, 'terraform validate');
      validated.validate = true;
      const inspection = inspectTerraformTests(temp);
      const testsRequired = logicalId.startsWith('module-') &&
        ['plan_mock', 'plan_mock_and_integration'].includes(manifest.terraform_profile?.test_strategy);
      if (testsRequired && inspection.files.length === 0) {
        throw new Error(`${logicalId} requiere al menos un tests/*.tftest.hcl por test_strategy ${manifest.terraform_profile.test_strategy}.`);
      }
      if (inspection.errors.length > 0) throw new Error(`Política de terraform test inválida en ${logicalId}:\n${inspection.errors.join('\n')}`);
      if (inspection.files.length > 0) {
        validated.evidence.test = execute('terraform', ['test', '-no-color'], temp, 'terraform test plan/mock');
        validated.test = true;
      } else {
        validated.evidence.test = skipped('terraform test', 'No hay tests locales para este root module');
        validated.test = 'skipped';
      }
    } finally {
      fs.rmSync(tempRoot, { recursive: true, force: true });
    }
    if (commandVersion('tflint')) {
      validated.evidence.lint = execute('tflint', [`--chdir=${artifactPath}`], root, 'tflint');
      validated.lint = true;
    } else {
      validated.evidence.lint = skipped('tflint', 'Herramienta no instalada');
      validated.lint = 'skipped';
    }
    if (commandVersion('trivy')) {
      validated.evidence.security = execute('trivy', ['config', artifactPath], root, 'trivy config');
      validated.security = true;
    } else if (commandVersion('tfsec')) {
      validated.evidence.security = execute('tfsec', [artifactPath], root, 'tfsec');
      validated.security = true;
    } else if (commandVersion('checkov')) {
      validated.evidence.security = execute('checkov', ['-d', artifactPath], root, 'checkov');
      validated.security = true;
    } else {
      validated.evidence.security = skipped('trivy/tfsec/checkov', 'Herramienta no instalada');
      validated.security = 'skipped';
    }
  } else if (logicalId.startsWith('pipeline-')) {
    validated.evidence.syntax = pipelineEvidence(artifactPath);
    validated.syntax = true;
  } else if (logicalId === 'bootstrap-backend') {
    if (!commandVersion('bash')) throw new Error('bash es obligatorio para validar el bootstrap.');
    validated.evidence.syntax = execute('bash', ['-n', artifactPath], root, 'bash -n');
    validated.syntax = true;
    if (commandVersion('shellcheck')) {
      validated.evidence.lint = execute('shellcheck', [artifactPath], root, 'shellcheck');
      validated.lint = true;
    } else {
      validated.evidence.lint = skipped('shellcheck', 'Herramienta no instalada');
      validated.lint = 'skipped';
    }
  } else {
    throw new Error(`No existe adaptador de validación para ${logicalId}.`);
  }

  artifact.source_hashes = {};
  for (const sourceDoc of artifact.source_docs ?? []) {
    const source = contained(resources, String(sourceDoc).split('#')[0], `${logicalId}.source_docs`);
    if (!fs.existsSync(source)) throw new Error(`Fuente inexistente: ${sourceDoc}.`);
    artifact.source_hashes[sourceDoc] = crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex');
  }
  artifact.validated = validated;
  artifact.status = 'generated';
  delete artifact.reason;
  manifest.updated_at = new Date().toISOString().slice(0, 10);
  fs.writeFileSync(manifestPath, yaml('dump', JSON.stringify(manifest)), 'utf8');
  console.log(`Validado y registrado ${logicalId}: generated (${Object.keys(validated.evidence).join(', ')}).`);
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
