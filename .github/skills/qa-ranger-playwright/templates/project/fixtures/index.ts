import { test as base, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

type Fixtures = {
  loginPage: LoginPage;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  // Configura page solo cuando la prueba usa esa página. Una prueba API no abre un navegador.
  page: async ({ page }, use) => {
      const errores: string[] = [];
      page.on('pageerror', (e) => errores.push(e.message));
      await use(page);
      expect(errores, 'errores JavaScript no controlados en la página').toEqual([]);
  },
});

export { expect };
