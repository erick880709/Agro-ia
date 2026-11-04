import { type Locator, type Page, test } from '@playwright/test';

// TODO(verificar-locator): ajusta las etiquetas y los nombres a la pantalla real.
// Explora sus elementos con playwright-cli o codegen.
export class LoginPage {
  readonly usuario: Locator;
  readonly clave: Locator;
  readonly ingresar: Locator;
  readonly error: Locator;

  constructor(private readonly page: Page) {
    this.usuario = page.getByLabel('{{LABEL_USUARIO}}');
    this.clave = page.getByLabel('{{LABEL_CLAVE}}');
    this.ingresar = page.getByRole('button', { name: '{{BOTON_INGRESAR}}' });
    this.error = page.getByRole('alert');
  }

  async abrir() {
    await this.page.goto('{{RUTA_LOGIN}}');
  }

  async ingresarCon(usuario: string, clave: string) {
    await test.step(`iniciar sesión como ${usuario}`, async () => {
      await this.usuario.fill(usuario);
      await this.clave.fill(clave);
      await this.ingresar.click();
    });
  }
}
