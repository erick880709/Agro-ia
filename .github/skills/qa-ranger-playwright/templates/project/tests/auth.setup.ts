import { test as setup, expect } from '@playwright/test';
import { requerida } from '../config/env';
import { LoginPage } from '../pages/login.page';

const STORAGE_STATE = 'playwright/.auth/user.json';

setup('autenticar usuario de pruebas', async ({ page }) => {
  const login = new LoginPage(page);
  await login.abrir();
  await login.ingresarCon(requerida('E2E_USER'), requerida('E2E_PASSWORD'));
  // TODO(verificar-locator): usa un elemento que confirme el inicio de sesión.
  await expect(page.getByRole('heading', { name: '{{HEADING_INICIO}}' })).toBeVisible();
  await page.context().storageState({ path: STORAGE_STATE });
});
