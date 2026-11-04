# 04 — Autenticación y sesiones

## Contenido
1. Patrón base: proyecto `setup` + `storageState`
2. Login por API (más rápido y estable)
3. Varios roles
4. Una cuenta por worker
5. Varios usuarios en un mismo test
6. OTP, MFA, SSO, passkeys
7. Session storage, expiración y logout
8. Consideraciones de seguridad

---

## 1. Patrón base

```ts
// tests/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const archivo = 'playwright/.auth/user.json';

setup('autenticar usuario estándar', async ({ page }) => {
  const usuario = process.env.E2E_USER, clave = process.env.E2E_PASSWORD;
  if (!usuario || !clave) throw new Error('Definir E2E_USER y E2E_PASSWORD');
  await page.goto('/login');
  await page.getByLabel('Usuario').fill(usuario);
  await page.getByLabel('Contraseña').fill(clave);
  await page.getByRole('button', { name: 'Ingresar' }).click();
  await expect(page.getByRole('heading', { name: 'Inicio' })).toBeVisible();   // sesión realmente establecida
  await page.context().storageState({ path: archivo });
});
```
En `playwright.config.ts`, proyecto `setup` + `dependencies: ['setup']` + `use.storageState` (ver 01 §2). Así el login ocurre **una vez por ejecución** y cada test arranca autenticado en un contexto aislado.

Tests que deben empezar sin sesión (el propio login, páginas públicas):
```ts
test.use({ storageState: { cookies: [], origins: [] } });
```

## 2. Login por API

Si el login es por formulario pero existe un endpoint, o la app usa tokens:
```ts
setup('autenticar por API', async ({ request }) => {
  const r = await request.post('/api/auth/login', {
    data: { usuario: process.env.E2E_USER, clave: process.env.E2E_PASSWORD },
  });
  expect(r.ok(), await r.text()).toBeTruthy();
  await request.storageState({ path: 'playwright/.auth/user.json' });   // guarda cookies de la respuesta
});
```
Apps SPA que guardan el token en `localStorage`: `storageState` también persiste `localStorage` por origen (y en 1.63+ OPFS con la opción `opfs`). Si el token vive en `sessionStorage`, ver §7.

Mantén al menos **un test de UI del login** (`@smoke`) aunque el resto use el atajo por API.

## 3. Varios roles

```ts
// auth.setup.ts
setup('admin', async ({ page }) => { /* login admin */ await page.context().storageState({ path: 'playwright/.auth/admin.json' }); });
setup('cliente', async ({ page }) => { /* login cliente */ await page.context().storageState({ path: 'playwright/.auth/cliente.json' }); });

// spec
test.describe('backoffice', () => {
  test.use({ storageState: 'playwright/.auth/admin.json' });
  test('aprueba solicitudes', async ({ page }) => { /* ... */ });
});
```
O un proyecto por rol en la config.

## 4. Una cuenta por worker

Cuando los tests modifican el estado de la cuenta (preferencias, saldo), cada worker debe usar la suya:
```ts
export const test = base.extend<{}, { cuentaWorker: string }>({
  storageState: ({ cuentaWorker }, use) => use(cuentaWorker),
  cuentaWorker: [async ({ browser }, use) => {
    const id = test.info().parallelIndex;
    const archivo = path.resolve(test.info().project.outputDir, `.auth/${id}.json`);
    if (!fs.existsSync(archivo)) {
      const page = await browser.newPage({ storageState: undefined });
      // login con la cuenta id (p. ej. E2E_USER_0, E2E_USER_1, ...)
      await page.context().storageState({ path: archivo });
      await page.close();
    }
    await use(archivo);
  }, { scope: 'worker' }],
});
```
Requiere un pool de cuentas de prueba ≥ número de workers.

## 5. Varios usuarios en un test

Flujos maker-checker (uno crea, otro aprueba) o chats:
```ts
test('el aprobador ve la solicitud creada por el analista', async ({ browser }) => {
  const analista = await browser.newContext({ storageState: 'playwright/.auth/analista.json' });
  const aprobador = await browser.newContext({ storageState: 'playwright/.auth/aprobador.json' });
  const pA = await analista.newPage(), pB = await aprobador.newPage();
  // ... analista crea; aprobador valida
  await analista.close(); await aprobador.close();
});
```
Mejor aún: fixtures `paginaAnalista` / `paginaAprobador` que creen y cierren los contextos.

## 6. OTP, MFA, SSO, passkeys

| Mecanismo | Estrategia en pruebas |
|---|---|
| OTP por SMS/correo | En ambiente de pruebas: OTP fijo para usuarios de prueba, endpoint de prueba que expone el último OTP, o bandeja de correo de pruebas consultada por API (Mailpit/MailHog) |
| TOTP (app autenticadora) | Generar el código desde el secreto del usuario de prueba con una librería TOTP (`otpauth`); secreto en el vault |
| SSO corporativo (Azure AD/Entra, Okta) | Autenticar una vez en `setup` y reutilizar `storageState`; o client credentials / ROPC habilitado solo en pruebas para obtener token. Evitar automatizar la UI del IdP en cada ejecución |
| CAPTCHA | Desactivado o con clave de prueba (p. ej. claves de prueba de reCAPTCHA) **en ambientes de prueba**. Nunca intentar resolverlo/evadirlo |
| Passkeys / WebAuthn | 1.61+: autenticador virtual `context.credentials`; 1.62+: `storageState({ credentials: true })` persiste las passkeys |

Ninguno de estos atajos debe existir en producción: coordínalo con desarrollo y seguridad como configuración exclusiva de ambientes bajos.

## 7. Session storage, expiración y logout

- `sessionStorage` no se guarda en `storageState`: guárdalo aparte (`page.evaluate(() => JSON.stringify(sessionStorage))`) y restáuralo con `context.addInitScript`, o usa en 1.61+ `page.sessionStorage`.
- Sesiones que expiran en suites largas: regenerar el estado en cada ejecución (el `setup` corre siempre) y mantener la suite por debajo del tiempo de expiración, o refrescar por API.
- Prueba explícitamente: expiración por inactividad (con `page.clock`, ver 06), cierre de sesión que invalida el token (volver atrás no muestra datos), sesión concurrente si el negocio la restringe.

## 8. Seguridad

- `playwright/.auth/*.json` contiene sesiones válidas: **siempre en `.gitignore`**, nunca como artefacto público del pipeline.
- Credenciales de prueba con privilegios mínimos, rotadas, en el vault del pipeline (Azure Key Vault / variable groups secretos / GitHub secrets).
- Los traces incluyen requests con headers: si se publican, filtrar o restringir el acceso al artefacto.
