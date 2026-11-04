import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

export const normalize = value => value.replaceAll('\\', '/');
export const manifestRelative = 'resources/.vulcano/operations-manifest.yaml';

export function argValue(args, flag, required = false) {
  const index = args.indexOf(flag);
  if (index < 0) {
    if (required) throw new Error(`${flag} es obligatorio.`);
    return null;
  }
  const result = args[index + 1];
  if (!result || result.startsWith('--')) throw new Error(`${flag} requiere un valor.`);
  return result;
}

export function yaml(mode, input) {
  const code = mode === 'load'
    ? 'import json,sys,yaml; print(json.dumps(yaml.safe_load(sys.stdin.read()), ensure_ascii=False))'
    : 'import json,sys,yaml; print(yaml.safe_dump(json.load(sys.stdin), sort_keys=False, allow_unicode=True), end="")';
  for (const command of ['python', 'python3']) {
    const result = spawnSync(command, ['-c', code], { input, encoding: 'utf8' });
    if (!result.error && result.status === 0) return result.stdout;
  }
  throw new Error('Se requiere Python con PyYAML.');
}

export function readYaml(file) {
  if (!fs.existsSync(file)) throw new Error(`No existe ${normalize(file)}.`);
  const parsed = JSON.parse(yaml('load', fs.readFileSync(file, 'utf8')));
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error(`${normalize(file)} debe ser un objeto YAML.`);
  return parsed;
}

export function writeYaml(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, yaml('dump', JSON.stringify(value)), 'utf8');
}

export function sha256Content(content) {
  return crypto.createHash('sha256').update(content).digest('hex');
}

export function sha256File(file) {
  return sha256Content(fs.readFileSync(file));
}

export function contained(base, candidate, label) {
  const resolved = path.resolve(base, candidate);
  const relative = path.relative(base, resolved);
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error(`${label} sale del workspace.`);
  return resolved;
}

export function stable(value) {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(key => [key, stable(value[key])]));
  }
  return value;
}

export function hashObject(value) {
  return sha256Content(JSON.stringify(stable(value)));
}

export function assertSanitized(value, label = 'contenido') {
  const forbiddenKey = /(^|_)(password|passwd|secret|token|pat|client_secret|connection_string|api_key|access_key|private_key|session_key|credential)($|_)/i;
  const forbiddenValue = /(-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._-]{12,}|[?&](sig|se|sp|sv)=)/i;
  const visit = (item, trail) => {
    if (Array.isArray(item)) return item.forEach((child, index) => visit(child, `${trail}[${index}]`));
    if (item && typeof item === 'object') {
      for (const [key, child] of Object.entries(item)) {
        if (forbiddenKey.test(key)) throw new Error(`${label} contiene una clave sensible en ${trail}.${key}.`);
        visit(child, `${trail}.${key}`);
      }
    } else if (typeof item === 'string' && forbiddenValue.test(item)) {
      throw new Error(`${label} contiene un posible secreto en ${trail}.`);
    }
  };
  visit(value, '$');
}

export function loadContext(root, resourcesDir = path.join(root, 'resources')) {
  const resources = path.resolve(resourcesDir);
  const operationsPath = path.join(resources, '.vulcano', 'operations-manifest.yaml');
  const operations = readYaml(operationsPath);
  const bobPath = contained(root, operations.source.bob_manifest, 'source.bob_manifest');
  const bob = readYaml(bobPath);
  return { root, resources, operationsPath, operations, bobPath, bob };
}

export function assertBobUnchanged(context) {
  if (sha256File(context.bobPath) !== context.operations.source.bob_sha256) {
    throw new Error('Cambió bob-manifest.yaml después del gate; reconciliar e inicializar de nuevo.');
  }
}

export function updateDate(manifest) {
  manifest.updated_at = new Date().toISOString().slice(0, 10);
}

export function scopeFor(action) {
  return hashObject({
    type: action.type,
    risk: action.risk,
    logical_id: action.logical_id,
    target_ref: action.target_ref,
    desired_sha256: action.desired_sha256,
    observed_sha256: action.observed_sha256,
    diff_summary: action.diff_summary
  });
}

export function readJsonFile(root, candidate, label) {
  const file = contained(root, candidate, label);
  if (!fs.existsSync(file)) throw new Error(`No existe ${candidate}.`);
  const parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
  assertSanitized(parsed, label);
  return { file, parsed, sha256: sha256File(file) };
}

export function gitCommit(root) {
  const result = spawnSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' });
  return !result.error && result.status === 0 ? result.stdout.trim() : null;
}
