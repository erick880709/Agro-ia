import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { inspectTerraformTests } from './terraform-test-policy.mjs';

const scripts = path.dirname(fileURLToPath(import.meta.url));

function fixture(testBody) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-tf-policy-'));
  fs.mkdirSync(path.join(root, 'tests'), { recursive: true });
  fs.writeFileSync(path.join(root, 'versions.tf'), `terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
  }
}\n`);
  fs.writeFileSync(path.join(root, 'tests', 'module.tftest.hcl'), testBody);
  return root;
}

test('acepta terraform test local con plan explícito y provider mockeado', t => {
  const root = fixture(`mock_provider "azurerm" {}\nrun "defaults" {\n  command = plan\n}\n`);
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const result = inspectTerraformTests(root);
  assert.equal(result.files.length, 1);
  assert.equal(result.runCount, 1);
  assert.deepEqual(result.errors, []);
});

test('rechaza default apply y provider real en pruebas locales', t => {
  const root = fixture(`run "unsafe_default" {\n  assert { condition = true error_message = "x" }\n}\n`);
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const result = inspectTerraformTests(root);
  assert(result.errors.some(error => error.includes('command = plan')));
  assert(result.errors.some(error => error.includes('mock_provider "azurerm"')));
});

test('record-bob-capability persiste solo estados permitidos', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'vulcano-capability-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const directory = path.join(root, 'resources', '.vulcano');
  fs.mkdirSync(directory, { recursive: true });
  fs.writeFileSync(path.join(directory, 'bob-manifest.yaml'), JSON.stringify({
    updated_at: '2026-07-16',
    preflight: { status: 'pending', checked_at: null, conflicts: [], capabilities: { terraform_test: 'unknown' } }
  }));
  const script = path.join(scripts, 'record-bob-capability.mjs');
  const ok = spawnSync(process.execPath, [script, '--root', root, '--capability', 'terraform_test', '--status', 'available'], { encoding: 'utf8' });
  assert.equal(ok.status, 0, ok.stderr);
  const text = fs.readFileSync(path.join(directory, 'bob-manifest.yaml'), 'utf8');
  assert.match(text, /terraform_test: available/);
  const rejected = spawnSync(process.execPath, [script, '--root', root, '--capability', 'terraform_search_import', '--status', 'available'], { encoding: 'utf8' });
  assert.equal(rejected.status, 1);
});
