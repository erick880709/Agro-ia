import assert from 'node:assert/strict';
import test from 'node:test';
import { resolveAdapters } from './adapter-registry.mjs';

function manifest(overrides = {}) {
  return {
    baseline: { cloud_providers: ['azure'] },
    decisions: {
      cloud_provider: 'azure',
      iac: 'terraform',
      devops_platform: 'azure_devops',
      terraform: {
        provider_constraints: { azurerm: '~> 4.0' },
        execution_backend: 'azure_devops'
      },
      ...overrides
    }
  };
}

test('resuelve Azure, Terraform y Azure DevOps sin una skill por combinación', () => {
  assert.deepEqual(resolveAdapters(manifest()), {
    cloud: 'azure',
    iac: 'terraform',
    pipeline: 'azure_devops',
    remote_operator: 'vulcano-operador',
    status: 'implemented'
  });
});

test('normaliza GitHub a github_actions implementado', () => {
  const input = manifest({
    devops_platform: 'github',
    terraform: {
      provider_constraints: { azurerm: '~> 4.0' },
      execution_backend: 'github_actions'
    }
  });
  assert.deepEqual(resolveAdapters(input), {
    cloud: 'azure',
    iac: 'terraform',
    pipeline: 'github_actions',
    remote_operator: 'vulcano-operador',
    status: 'implemented'
  });
});

test('AWS y GitHub se seleccionan como dimensiones independientes', () => {
  const input = manifest({
    cloud_provider: 'aws',
    devops_platform: 'github_actions',
    terraform: {
      provider_constraints: { aws: '~> 6.0' },
      execution_backend: 'github_actions'
    }
  });
  const selection = resolveAdapters(input);
  assert.equal(selection.cloud, 'aws');
  assert.equal(selection.pipeline, 'github_actions');
  assert.equal(selection.iac, 'terraform');
  assert.equal(selection.status, 'implemented');
});

test('GitLab se resuelve con backend gitlab_ci', () => {
  const input = manifest({
    devops_platform: 'gitlab',
    terraform: {
      provider_constraints: { azurerm: '~> 4.0' },
      execution_backend: 'gitlab_ci'
    }
  });
  assert.equal(resolveAdapters(input).pipeline, 'gitlab');
  assert.equal(resolveAdapters(input).status, 'implemented');
});

test('GCP resuelve como cloud implementado con provider google', () => {
  const input = manifest({
    cloud_provider: 'gcp',
    terraform: {
      provider_constraints: { google: '~> 6.0' },
      execution_backend: 'azure_devops'
    }
  });
  const selection = resolveAdapters(input);
  assert.equal(selection.cloud, 'gcp');
  assert.equal(selection.status, 'implemented');
});

test('rechaza un provider incompatible con la nube seleccionada', () => {
  assert.throws(
    () => resolveAdapters(manifest({ cloud_provider: 'aws' }), { allowPlanned: true }),
    /cloud\/aws requiere al menos uno de los providers aws/
  );
});
