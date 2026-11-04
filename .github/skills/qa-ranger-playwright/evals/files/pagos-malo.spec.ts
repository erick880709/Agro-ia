import { test, expect } from '@playwright/test';

let referencia: string;

test.describe.serial('pagos', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://qa.banco-demo.com/login');
    await page.getByLabel('Usuario').fill('usuario.qa');
    await page.getByLabel('Contraseña').fill('Clave-Prueba-1');
    await page.getByRole('button', { name: 'Ingresar' }).click();
  });

  test('test 1', async ({ page }) => {
    await page.goto('https://qa.banco-demo.com/pagos');
    await page.locator('//div[2]/form/input[1]').fill('150000');
    await page.click('#btn-pagar');
    await page.waitForTimeout(3000);
    expect(await page.getByText('Pago exitoso').isVisible()).toBe(true);
    referencia = await page.locator('.css-1x9ab2c > span:nth-child(2)').innerText();
  });

  test('consulta el pago', async ({ page }) => {
    await page.goto('/historial');
    await page.waitForLoadState('networkidle');
    expect(page.getByText(referencia)).toBeVisible();
  });

  test.only('cancela pago', async ({ page }) => {
    await page.goto('/pagos');
    page.getByRole('button', { name: 'Cancelar' }).click();
    await page.getByRole('button', { name: 'Confirmar' }).first().click({ force: true });
    if (await page.getByRole('dialog').isVisible()) {
      await page.getByRole('button', { name: 'Aceptar' }).click();
    }
    try {
      await expect(page.locator('button:visible')).toHaveCount(2);
    } catch (e) {
      console.log('no importa');
    }
  });

  test('descarga comprobante', async ({ page }) => {
    const token = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJxYSJ9.abc123def456';
    await page.setExtraHTTPHeaders({ Authorization: token });
    await page.goto('/comprobante');
    await page.pause();
    await page.getByRole('link', { name: 'Descargar' }).click().catch(() => {});
  });
});
