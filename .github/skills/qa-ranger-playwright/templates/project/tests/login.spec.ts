import { test, expect } from '../fixtures';
import { requerida } from '../config/env';

// Estas pruebas comprueban el inicio de sesión. Cada una empieza sin una sesión autenticada.
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Inicio de sesión', { tag: '@login' }, () => {
  test.beforeEach(async ({ loginPage }) => {
    await loginPage.abrir();
  });

  test('TC-LOGIN-01 [critical] ingresa con credenciales válidas', { tag: '@smoke' }, async ({ page, loginPage }) => {
    await loginPage.ingresarCon(requerida('E2E_USER'), requerida('E2E_PASSWORD'));
    await expect(page.getByRole('heading', { name: '{{HEADING_INICIO}}' })).toBeVisible();
  });

  test('TC-LOGIN-02 [high] rechaza una contraseña incorrecta', async ({ loginPage }) => {
    await loginPage.ingresarCon(requerida('E2E_USER'), `incorrecta-${Date.now()}`);
    await expect(loginPage.error).toBeVisible();
    await expect(loginPage.ingresar).toBeVisible();
  });
});
