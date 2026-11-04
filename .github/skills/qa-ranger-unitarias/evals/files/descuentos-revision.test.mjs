// Pruebas enviadas a revisión. Fixture de evaluación: no modificar.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as descuentos from './descuentos.mjs';

let pedido = [{ sku: 'A', precio: 10, cantidad: 10 }];

test('funciona', () => {
  descuentos.calcularTotal(pedido, 'oro');
});

test('volumen', async () => {
  pedido.push({ sku: 'B', precio: 5, cantidad: 40 });
  await new Promise((resolve) => setTimeout(resolve, 500));
  assert.ok(descuentos.porcentajePorVolumen(50) > 0);
});

test('total con volumen', () => {
  // Depende de que la prueba anterior haya agregado el ítem B.
  const resultado = descuentos.calcularTotal(pedido, 'estandar');
  assert.equal(resultado.total, resultado.subtotal - resultado.descuento);
});

test('cupón', () => {
  const hoy = new Date().toISOString().slice(0, 10);
  const resultado = descuentos.calcularTotal(pedido, 'plata', { porcentaje: 0.05, vence: '2099-12-31', hoy });
  assert.ok(resultado.descuento);
});

test('tope', () => {
  try {
    descuentos.calcularTotal([{ sku: 'A', precio: 100, cantidad: 100 }], 'oro', { porcentaje: 0.5, vence: '2099-12-31', hoy: '2026-01-01' });
  } catch (error) {
    assert.fail('no debería fallar');
  }
});

test.skip('cliente desconocido', () => {
  assert.throws(() => descuentos.porcentajePorCliente('bronce'));
});
