# Patrones de Cypress

Reference específico de Cypress, paralelo a `../test_automation_patterns.md`
(Playwright). Usar este archivo cuando el Paso 0.1 de `../../SKILL.md`
detectó `cypress.config.*`/carpeta `cypress/` en el proyecto, o el usuario
pidió Cypress explícitamente. Las Reglas de Oro del `SKILL.md` aplican
igual acá — este archivo solo traduce el "cómo" a la sintaxis de Cypress.

---

## Índice

- [Diferencias Clave vs Playwright](#diferencias-clave-vs-playwright)
- [Configuración Base](#configuración-base)
- [Locators y Aserciones](#locators-y-aserciones)
- [Comandos Custom](#comandos-custom)
- [Interceptación de Red (`cy.intercept`)](#interceptación-de-red-cyintercept)
- [Page Object Model en Cypress](#page-object-model-en-cypress)
- [Component Testing](#component-testing)
- [Evidencia](#evidencia)
- [CI](#ci)
- [Convención de Id de Caso](#convención-de-id-de-caso)

---

## Diferencias Clave vs Playwright

| Aspecto | Playwright | Cypress |
|---|---|---|
| Multi-pestaña/multi-contexto | Nativo (`context.newPage()`) | No soportado directamente — requiere workarounds o `cy.origin()` para cross-origin |
| Ejecución | Node.js fuera del navegador | Dentro del navegador (afecta cómo interactúa con el DOM) |
| Reintentos | Auto-retry en aserciones web-first | Auto-retry en la mayoría de comandos y aserciones por defecto |
| Multi-navegador | Chromium, Firefox, WebKit | Chromium-based, Firefox — sin WebKit |
| API de red | `page.route()` / fixture `request` | `cy.intercept()` |
| Trace/debug | `trace.zip` con timeline completo | Time-travel debugger en el Cypress Runner, sin trace portable equivalente |

Si el proyecto necesita multi-pestaña, WebKit real, o trace portable para
CI headless, señalarlo como limitación conocida de Cypress en el plan de
pruebas — no es una razón automática para migrar (ver
`./tool_migration_guide.md`), pero sí algo que el usuario debe saber.

## Configuración Base

```typescript
// cypress.config.ts
import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: process.env.QA_BASE_URL || 'http://localhost:3000',
    video: true,
    screenshotOnRunFailure: true,
    videosFolder: 'resources/qa/cypress-results/videos',
    screenshotsFolder: 'resources/qa/cypress-results/screenshots',
    setupNodeEvents(on, config) {
      // registrar plugins/tasks acá
    },
  },
  env: {
    QA_USER_EMAIL: process.env.QA_USER_EMAIL,
  },
});
```

Igual que con Playwright: si el proyecto ya tiene `cypress.config.ts`, no
sobrescribirlo — fusionar solo `video`/`screenshotOnRunFailure`/las
carpetas de salida bajo `resources/qa/`.

## Locators y Aserciones

Mismo orden de prioridad que Playwright (ver Reglas de Oro): rol/label/
texto antes que CSS/XPath.

```typescript
// Preferido
cy.findByRole('button', { name: 'Ingresar' }).click();
cy.findByLabelText('Email').type('${QA_USER_EMAIL}');

// Fallback cuando no hay semántica clara
cy.get('[data-testid="submit-button"]').click();
```

`findByRole`/`findByLabelText` requieren `@testing-library/cypress`
(instalable con `--with-unit` en `ensure-qa-dependencies.mjs` si el
proyecto también usa React Testing Library). Sin esa dependencia, usar
`cy.get('[role=button]')` como alternativa más verbosa.

Cypress reintenta aserciones automáticamente — no hace falta `waitFor`
manual como en RTL, pero sí evitar `cy.wait(<ms>)` con un número fijo (ver
Reglas de Oro): usar `cy.wait('@aliasDeIntercept')` para esperar una
request específica en vez de un tiempo arbitrario.

## Comandos Custom

Encapsular flujos repetidos como comandos custom en vez de helpers sueltos:

```typescript
// cypress/support/commands.ts
Cypress.Commands.add('loginAsUser', () => {
  cy.session('user-session', () => {
    cy.visit('/login');
    cy.findByLabelText('Email').type(Cypress.env('QA_USER_EMAIL'));
    cy.findByLabelText('Password').type(Cypress.env('QA_USER_PASSWORD'), { log: false });
    cy.findByRole('button', { name: 'Ingresar' }).click();
    cy.url().should('include', '/dashboard');
  });
});
```

`cy.session()` cachea la sesión entre tests del mismo archivo — evita
repetir el login completo en cada caso, similar al `storageState` de
Playwright.

## Interceptación de Red (`cy.intercept`)

```typescript
cy.intercept('POST', '/api/orders', { fixture: 'order-success.json' }).as('createOrder');
cy.findByRole('button', { name: 'Confirmar' }).click();
cy.wait('@createOrder');
cy.findByText('Orden creada').should('be.visible');
```

Igual que con MSW en Playwright/Jest: mockear solo servicios externos o
dependencias no disponibles en el entorno de prueba, nunca la propia app
bajo prueba (Regla de Oro 5).

## Page Object Model en Cypress

```typescript
// cypress/support/pages/LoginPage.ts
export class LoginPage {
  visit() {
    cy.visit('/login');
    return this;
  }
  login(email: string, password: string) {
    cy.findByLabelText('Email').type(email);
    cy.findByLabelText('Password').type(password, { log: false });
    cy.findByRole('button', { name: 'Ingresar' }).click();
    return this;
  }
}
```

## Component Testing

Para componentes React/Vue aislados (equivalente a RTL pero corriendo en
un navegador real):

```typescript
// cypress.config.ts
export default defineConfig({
  component: {
    devServer: { framework: 'next', bundler: 'webpack' },
  },
});
```

```typescript
import { LoginForm } from '../../src/components/LoginForm';

it('muestra error con credenciales inválidas', () => {
  cy.mount(<LoginForm />);
  cy.findByRole('button', { name: 'Ingresar' }).click();
  cy.findByText('Email requerido').should('be.visible');
});
```

Usar component testing para lógica de UI aislada; reservar `e2e` para
flujos completos entre páginas.

## Evidencia

A diferencia de Playwright, Cypress no produce un `trace.zip` portable.
La evidencia por defecto:

- **Video**: uno por archivo de spec (no por test individual),
  `videosFolder` configurado arriba.
- **Screenshot**: automático en cada fallo (`screenshotOnRunFailure`), más
  cualquier `cy.screenshot()` manual en pasos clave.
- Sin trace — para debug post-mortem, apoyarse en el video + logs de
  consola/red que Cypress adjunta al reporte si se usa un reporter como
  `mochawesome`.

Este paquete no incluye un organizador Cypress. Integra el reporter real del
proyecto con casos, corrida, intentos y rutas de evidencia. No uses el organizador
Playwright para leer resultados Cypress. La ausencia de trace requiere una
excepción explícita del encargo. Video por spec y screenshots solo en fallo no
satisfacen por sí solos la política de evidencia por caso.

## CI

```yaml
# .github/workflows/cypress.yml (fragmento relevante)
- uses: cypress-io/github-action@v6
  with:
    browser: chrome
    record: false
  env:
    QA_BASE_URL: ${{ secrets.QA_BASE_URL }}
    QA_USER_EMAIL: ${{ secrets.QA_USER_EMAIL }}
    QA_USER_PASSWORD: ${{ secrets.QA_USER_PASSWORD }}
```

## Convención de Id de Caso

Igual que Playwright: prefijo en el título del `it()`/`describe()`, ej.
`it('TC-01 [critical] - Login con credenciales válidas', () => {...})`.
Conserva IDs y prioridades en el reporter del proyecto. La organización automática requiere su propio adaptador Cypress.
