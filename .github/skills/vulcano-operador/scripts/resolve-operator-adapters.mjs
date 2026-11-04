#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { argValue, readYaml } from './operations-lib.mjs';
import { resolveOperatorAdapters } from './adapter-registry.mjs';

const args = process.argv.slice(2);

try {
  const root = path.resolve(argValue(args, '--root') ?? process.cwd());
  const resources = path.resolve(argValue(args, '--resources-dir') ?? path.join(root, 'resources'));
  const bobPath = path.join(resources, '.vulcano', 'bob-manifest.yaml');
  if (!fs.existsSync(bobPath)) throw new Error('No existe bob-manifest.yaml; completar primero Vulcano Bob.');
  const resolved = resolveOperatorAdapters(readYaml(bobPath), { allowPlanned: args.includes('--allow-planned') });
  console.log(JSON.stringify({
    ...resolved.selection,
    platform_mcp: resolved.platform.mcp_capability,
    cloud_mcp: resolved.cloud.mcp_capability,
    required_target_fields: resolved.platform.required_target_fields,
    allowed_actions: resolved.platform.allowed_actions
  }, null, 2));
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exit(1);
}
