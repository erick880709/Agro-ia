# Patrones de automatización con Playwright

Ejemplos de POM, fixtures, asincronía, pasos y escenarios avanzados. Adapta localizadores al DOM real y conserva ID y prioridad del runbook. Las reglas de [revisión](11-revision-y-antipatrones.md) y las APIs de la versión instalada gobiernan estos ejemplos.

## Índice

- [Page Objects](#page-objects)
- [Fixtures](#fixtures)
- [Asincronía y pasos de evidencia](#asincronía-y-pasos-de-evidencia)
- [Patrones Avanzados de Playwright](#patrones-avanzados-de-playwright)
- [Depuración](#depuración)

## Page Objects

### Page Objects de Playwright

```typescript
// e2e/pages/LoginPage.ts
import { Page, Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign in' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectRedirectToDashboard() {
    await expect(this.page).toHaveURL('/dashboard');
  }
}
```

**Uso en las pruebas:**

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';

test.describe('Authentication', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('successful login redirects to dashboard', async () => {
    await loginPage.login('user@example.com', 'password123');
    await loginPage.expectRedirectToDashboard();
  });

  test('invalid credentials show error', async () => {
    await loginPage.login('user@example.com', 'wrongpassword');
    await loginPage.expectError('Invalid credentials');
  });
});
```

### Cuándo usar POM

| Escenario | ¿Usar POM? |
|----------|----------|
| Páginas complejas con muchas interacciones | Sí |
| Componentes reutilizables probados en varias suites | Sí |
| Pruebas simples de un solo uso | No (excesivo) |
| Pruebas E2E con flujos compartidos | Sí |

---

## Fixtures

### Fixtures de Playwright

```typescript
// e2e/fixtures/auth.ts
import { test as base, Page } from '@playwright/test';
import { createUser } from '../factories/userFactory';

interface AuthFixtures {
  authenticatedPage: Page;
  adminPage: Page;
  testUser: ReturnType<typeof createUser>;
}

export const test = base.extend<AuthFixtures>({
  testUser: async ({}, use) => {
    const user = createUser();
    await use(user);
  },

  authenticatedPage: async ({ page, testUser }, use) => {
    // Iniciar sesión vía API para omitir la UI
    await page.request.post('/api/auth/login', {
      data: {
        email: testUser.email,
        password: 'testpassword',
      },
    });

    // Obtener la cookie de sesión
    const cookies = await page.context().cookies();
    await page.context().addCookies(cookies);

    await use(page);
  },

  adminPage: async ({ page }, use) => {
    const admin = createUser({ role: 'admin' });

    await page.request.post('/api/auth/login', {
      data: {
        email: admin.email,
        password: 'adminpassword',
      },
    });

    await use(page);
  },
});

export { expect } from '@playwright/test';
```

**Uso de fixtures personalizados:**

```typescript
// e2e/dashboard.spec.ts
import { test, expect } from './fixtures/auth';

test('dashboard shows user name', async ({ authenticatedPage, testUser }) => {
  await authenticatedPage.goto('/dashboard');
  await expect(authenticatedPage.getByText(testUser.name)).toBeVisible();
});

test('admin sees admin panel', async ({ adminPage }) => {
  await adminPage.goto('/dashboard');
  await expect(adminPage.getByText('Admin Panel')).toBeVisible();
});
```

## Asincronía y pasos de evidencia

### Patrones asíncronos de Playwright

```typescript
// e2e/async-patterns.spec.ts
import { test, expect } from '@playwright/test';

test('waits for API response', async ({ page }) => {
  // Esperar una respuesta específica
  const responsePromise = page.waitForResponse('/api/data');
  await page.click('button.load-data');
  const response = await responsePromise;
  expect(response.status()).toBe(200);
});

test('waits for navigation', async ({ page }) => {
  await page.goto('/');
  await Promise.all([
    page.waitForURL('/dashboard'),
    page.click('a.dashboard-link'),
  ]);
});

test('waits for page readiness', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});

test('retries assertion until pass', async ({ page }) => {
  // Aserción con reintento automático
  await expect(page.locator('.counter')).toHaveText('10', { timeout: 5000 });
});
```

### Pasos nombrados con test.step() para evidencia legible

Cuando un spec E2E queda ligado a un caso del runbook y se graba como
evidencia (ver `13-evidencia-video.md`), envolver cada
paso lógico en `test.step()` hace que el reporte HTML y el trace viewer
muestren puntos de referencia nombrados, en vez de un video/trace corrido
sin marcas:

```typescript
// e2e/login-TC-01.spec.ts
import { test, expect } from '@playwright/test';

test('TC-01 [critical] - Login con credenciales válidas', async ({ page }) => {
  await test.step('Abrir la página de login', async () => {
    await page.goto('/login');
  });

  await test.step('Completar credenciales', async () => {
    await page.getByLabel('Email').fill(process.env.QA_USER_EMAIL!);
    await page.getByLabel('Password').fill(process.env.QA_USER_PASSWORD!);
  });

  await test.step('Enviar y verificar redirección', async () => {
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL('/dashboard');
  });
});
```

Nombrá cada paso por su intención ("Completar credenciales"), no por la
acción cruda ("fill inputs"). Combinado con `QA_SLOWMO_MS` en
`playwright.config.ts`, esto es lo que hace que un video de evidencia sea
revisable por una persona en vez de solo "técnicamente correcto".

---

## Patrones Avanzados de Playwright

Escenarios que van más allá de un flujo single-page single-user —
necesarios en apps con múltiples roles, tiempo real, contenido embebido o
comportamiento dependiente del reloj.

### Multi-Contexto y Multi-Usuario

Cada `BrowserContext` es una sesión aislada (cookies, storage, cache
propios) — usalo para simular dos usuarios interactuando con el mismo
recurso en paralelo, sin los workarounds que hacen falta en Cypress:

```typescript
test('dos usuarios ven el mismo documento colaborativo en tiempo real', async ({ browser }) => {
  const contextA = await browser.newContext({ storageState: 'auth/userA.json' });
  const contextB = await browser.newContext({ storageState: 'auth/userB.json' });
  const pageA = await contextA.newPage();
  const pageB = await contextB.newPage();

  await pageA.goto('/docs/123');
  await pageB.goto('/docs/123');

  await pageA.getByRole('textbox').fill('Hola desde A');
  await expect(pageB.getByText('Hola desde A')).toBeVisible();

  await contextA.close();
  await contextB.close();
});
```

Para popups/nuevas pestañas dentro del mismo contexto (no un usuario
distinto, solo una ventana nueva):

```typescript
const [popup] = await Promise.all([
  page.waitForEvent('popup'),
  page.getByRole('link', { name: 'Abrir en nueva pestaña' }).click(),
]);
await expect(popup).toHaveURL(/\/preview/);
```

### WebSockets y Tiempo Real

Interceptar y aserear sobre mensajes WebSocket sin depender de que la UI
los refleje visualmente a tiempo (evita sleeps duros esperando una
actualización en pantalla):

```typescript
test('recibe notificación en tiempo real', async ({ page }) => {
  const wsMessages: string[] = [];
  page.on('websocket', (ws) => {
    ws.on('framereceived', (frame) => wsMessages.push(frame.payload as string));
  });

  await page.goto('/dashboard');
  await triggerServerEvent(); // helper que dispara el evento del lado servidor

  await expect.poll(() => wsMessages.some((m) => m.includes('order.created'))).toBe(true);
  await expect(page.getByText('Nueva orden recibida')).toBeVisible();
});
```

### Iframes y Shadow DOM

```typescript
// Iframe: localizar el frame primero, después el elemento dentro
const frame = page.frameLocator('iframe[title="Checkout de pago"]');
await frame.getByLabel('Número de tarjeta').fill('4242424242424242');

// Shadow DOM: Playwright lo atraviesa automáticamente con locators normales,
// sin sintaxis especial — a diferencia de Selenium/Cypress clásico
await page.getByRole('button', { name: 'Confirmar' }).click(); // funciona aunque el botón esté en shadow DOM
```

Cuando un iframe es de un tercero (ej. un widget de pago embebido), no
intentar interactuar con su contenido interno en pruebas propias más allá
de lo estrictamente necesario para completar el flujo — el resto de ese
iframe está fuera del alcance de lo que este proyecto puede/debe verificar.

### Mocking de Reloj (`page.clock`)

Para lógica dependiente del tiempo (expiración de sesión, countdown,
"hace 5 minutos") sin esperas reales:

```typescript
test('sesión expira tras 30 minutos de inactividad', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-01-01T10:00:00Z') });
  await page.goto('/dashboard');

  await page.clock.fastForward('30:01'); // 30 minutos y 1 segundo
  await expect(page.getByText('Tu sesión expiró')).toBeVisible();
});
```

Preferir `page.clock` sobre mockear `Date`/`setTimeout` manualmente en el
código de la app — Playwright controla el reloj del navegador de forma
consistente con lo que la app realmente ve, sin tocar el código de
producción para hacerlo testeable.

### Análisis de Trace por CLI (Debug Sin Abrir el Visor Gráfico)

Útil para depurar un fallo de CI sin GUI disponible:

```bash
npx playwright show-trace resources/qa/TC-01/<runId>/trace.zip   # visor gráfico, si hay display
npx playwright show-trace --trace resources/qa/TC-01/<runId>/trace.zip --list  # metadata en texto
```

Si no hay entorno gráfico disponible (típico en un contenedor de CI), un
`trace.zip` es igual un archivo ZIP inspeccionable manualmente: contiene
`trace.trace` (eventos en JSONL) y capturas de red/consola — extraerlo y
buscar el evento de error (`"type":"error"` o la acción justo antes del
fallo) es más rápido que reproducir el fallo localmente cuando la causa no
es obvia por el mensaje de error solo.

### Cuarentena de Flaky Dirigida por Datos

Complementa `../../ranger/references/qa_best_practices.md#estrategia-de-cuarentena`: compara corridas
independientes con una herramienta del proyecto y conserva IDs, proyectos,
reintentos y resultados originales. Este paquete no incluye un script de tendencias.

---

## Depuración

### Depuración con Playwright

```bash
# Modo debug - abre el navegador con el inspector
npx playwright test --debug

# Modo UI - ejecutor de tests visual
npx playwright test --ui

# Modo headed - ver el navegador
npx playwright test --headed

# Visor de trazas después de un fallo
npx playwright show-trace trace.zip
```

**Pausar dentro de un test:**
```typescript
test('debug this', async ({ page }) => {
  await page.goto('/');
  await page.pause(); // Abre el inspector
  await page.click('button');
});
```
