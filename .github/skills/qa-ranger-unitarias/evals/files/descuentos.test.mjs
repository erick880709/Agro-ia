// Pruebas existentes del equipo. Fixture de evaluación: no modificar.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { calcularTotal, porcentajePorVolumen } from './descuentos.mjs';

test('UT-01 [high] [RF-01] cliente estándar sin volumen paga el subtotal', () => {
  const resultado = calcularTotal([{ sku: 'A', precio: 10, cantidad: 2 }], 'estandar');
  assert.deepEqual(resultado, { subtotal: 20, descuento: 0, total: 20 });
});

test('UT-02 [high] [RF-02] 10 unidades aplican 5% por volumen', () => {
  assert.equal(porcentajePorVolumen(10), 0.05);
  assert.equal(porcentajePorVolumen(9), 0);
});

test('UT-03 [high] [RF-03] cliente oro suma 10%', () => {
  const resultado = calcularTotal([{ sku: 'A', precio: 100, cantidad: 1 }], 'oro');
  assert.deepEqual(resultado, { subtotal: 100, descuento: 10, total: 90 });
});
