# BDD/Gherkin con Playwright

Para decidir cuándo usar BDD y definir escenarios consulta la [guía común](../../ranger/references/tools/bdd_gherkin_patterns.md). Integra los ejemplos en la versión instalada y verifica la configuración de generación con el proyecto; conserva fixtures, reportes y evidencia de Playwright.

## Índice

- [BDD sobre Playwright (`playwright-bdd`)](#bdd-sobre-playwright-playwright-bdd)
- [Evidencia y trazabilidad](#evidencia-y-trazabilidad)

## BDD sobre Playwright (`playwright-bdd`)

```bash
npm install -D playwright-bdd @cucumber/cucumber
```

```typescript
// playwright-bdd.config.ts
import { defineBddConfig } from 'playwright-bdd';

export default defineBddConfig({
  features: 'features/**/*.feature',
  steps: 'steps/**/*.ts',
});
```

```typescript
// steps/login.steps.ts
import { createBdd } from 'playwright-bdd';

const { Given, When, Then } = createBdd();

Given('el usuario está en la página de login', async ({ page }) => {
  await page.goto('/login');
});

When('ingresa un email y password válidos', async ({ page }) => {
  await page.getByLabel('Email').fill(process.env.QA_USER_EMAIL!);
  await page.getByLabel('Password').fill(process.env.QA_USER_PASSWORD!);
});

Then('es redirigido al dashboard', async ({ page }) => {
  await expect(page).toHaveURL(/dashboard/);
});
```

`playwright-bdd` genera specs de Playwright reales a partir de los
`.feature`, así que hereda toda la config de evidencia (video/trace/
screenshot) de `playwright.config.ts` sin cambios adicionales.

## Evidencia y trazabilidad

Usa la [guía de evidencia](13-evidencia-video.md). Propaga los tags de caso y prioridad al título, tags o anotaciones de cada test generado y verifica su presencia en el CTRF. No supongas que el adaptador BDD los exporta automáticamente.
