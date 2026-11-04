// Prueba con un error intencional para capturar un trace real, el registro de la ejecución.
// No copies esta prueba al proyecto.
import { test, expect } from '@playwright/test';

test('TC-FLAKY-01 [critical] confirma una transferencia', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Usuario').fill(process.env.E2E_USER!);
  await page.getByLabel('Contraseña').fill(process.env.E2E_PASSWORD!);
  await page.getByRole('button', { name: 'Ingresar' }).click();
  await page.getByRole('heading', { name: 'Inicio' }).waitFor();
  await page.goto('/transferencias/nueva');
  await page.getByLabel('Cuenta destino').fill('12345678901');
  await page.getByLabel('Monto').fill('1000');
  await page.getByRole('button', { name: 'Continuar' }).click();
  await page.getByRole('button', { name: 'Confirmar transferencia' }).click();
  await page.waitForTimeout(100);
  expect(await page.getByRole('alert').textContent()).toContain('Transferencia exitosa');
});
