import assert from 'node:assert/strict';
import test from 'node:test';
import { computeDoraMetrics, parseComponents } from '../assets/dora-collect.template.mjs';

test('sin deployments en la ventana, ninguna métrica se infiere', () => {
  const result = computeDoraMetrics([]);
  assert.equal(result.sample_size, 0);
  assert.equal(result.deployment_frequency_per_day, null);
  assert.equal(result.change_lead_time_hours, null);
  assert.equal(result.failed_deployment_recovery_time_hours, null);
  assert.equal(result.change_fail_rate, null);
  assert.equal(result.deployment_rework_rate, null);
});

test('calcula las cinco métricas sobre una serie mixta de éxitos y fallos', () => {
  const events = [
    { status: 'success', started_at: '2026-07-01T10:00:00Z', completed_at: '2026-07-01T10:10:00Z' },
    { status: 'success', started_at: '2026-07-03T10:00:00Z', completed_at: '2026-07-03T10:10:00Z' },
    { status: 'failure', started_at: '2026-07-05T10:00:00Z', completed_at: '2026-07-05T10:05:00Z' },
    { status: 'success', started_at: '2026-07-05T14:00:00Z', completed_at: '2026-07-05T14:05:00Z' },
    { status: 'success', started_at: '2026-07-10T10:00:00Z', completed_at: '2026-07-10T10:10:00Z' }
  ];
  const result = computeDoraMetrics(events);
  assert.equal(result.sample_size, 5);
  assert.equal(result.change_fail_rate, 0.2);
  assert.equal(result.failed_deployment_recovery_time_hours, 4);
  assert.equal(result.deployment_rework_rate, 0);
  assert.ok(Math.abs(result.deployment_frequency_per_day - 4 / 9) < 1e-9);
  assert.ok(Math.abs(result.change_lead_time_hours - 0.14583333333333331) < 1e-9);
});

test('despliegues exitosos consecutivos dentro de la ventana de rework cuentan como rework', () => {
  const events = [
    { status: 'success', started_at: '2026-07-01T10:00:00Z', completed_at: '2026-07-01T10:00:00Z' },
    { status: 'success', started_at: '2026-07-01T14:00:00Z', completed_at: '2026-07-01T14:00:00Z' },
    { status: 'success', started_at: '2026-07-08T10:00:00Z', completed_at: '2026-07-08T10:00:00Z' }
  ];
  const result = computeDoraMetrics(events, { reworkWindowHours: 24 });
  assert.equal(result.deployment_rework_rate, 0.5);
});

test('un solo deployment no produce division por cero en rework rate', () => {
  const result = computeDoraMetrics([
    { status: 'success', started_at: '2026-07-01T10:00:00Z', completed_at: '2026-07-01T10:10:00Z' }
  ]);
  assert.equal(result.deployment_rework_rate, null);
  assert.equal(result.change_fail_rate, 0);
});

test('no ejecuta main() al importar el módulo desde un test', () => {
  // Regresión: el guard de entrypoint debe evitar detectPlatform()/fetch al hacer import()
  // en un test — si esto lanzara, el propio import de arriba ya habría fallado.
  assert.ok(typeof computeDoraMetrics === 'function');
});

test('parseComponents: sin DORA_COMPONENTS, devuelve el componente único "app" (compatibilidad hacia atrás)', () => {
  assert.deepEqual(parseComponents(undefined), ['app']);
  assert.deepEqual(parseComponents(''), ['app']);
  assert.deepEqual(parseComponents('   '), ['app']);
});

test('parseComponents: separa, recorta y valida una lista por componente', () => {
  assert.deepEqual(parseComponents('backend, frontend'), ['backend', 'frontend']);
  assert.deepEqual(parseComponents('backend,frontend,'), ['backend', 'frontend']);
});

test('parseComponents: rechaza nombres inválidos o duplicados', () => {
  assert.throws(() => parseComponents('Backend'), /nombre de componente inválido/);
  assert.throws(() => parseComponents('backend,backend'), /componente duplicado/);
});
