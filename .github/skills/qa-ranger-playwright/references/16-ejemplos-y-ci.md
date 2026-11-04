# Ejemplos E2E, regresión visual y CI con Playwright

Ejemplos de implementación y pipeline, adaptables al proyecto. Para configuración completa, autenticación y reportes consulta [CI y reportes](09-ci-cd-y-reportes.md). Los jobs unitarios y de integración ilustran las etapas previas del pipeline; pertenecen a sus runners. Los casos deben conservar el ID y la prioridad acordados.

## Índice

- [Integración con CI/CD](#integración-con-cicd)

### Testing End-to-End

**Propósito:** Verificar que los flujos completos de usuario funcionen en un entorno de navegador real.

**Qué Probar a Nivel E2E:**
- Flujos de negocio críticos (checkout, registro, login)
- Secuencias de navegación entre páginas
- Flujos de autenticación
- Integraciones con terceros
- Procesamiento de pagos
- Asistentes de formularios (wizards)

**Ejemplo: Testear el Flujo de Checkout**

```typescript
// e2e/checkout.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Checkout Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('completes purchase successfully', async ({ page }) => {
    // Agregar producto al carrito
    await page.goto('/products/widget-pro');
    await page.getByRole('button', { name: 'Add to Cart' }).click();

    // Verificar que el carrito se haya actualizado
    await expect(page.getByTestId('cart-count')).toHaveText('1');

    // Ir al checkout
    await page.getByRole('link', { name: 'Checkout' }).click();

    // Completar información de envío
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Address').fill('123 Test St');
    await page.getByLabel('City').fill('Test City');
    await page.getByLabel('Zip').fill('12345');

    // Completar información de pago (tarjeta de prueba)
    await page.getByLabel('Card Number').fill('4242424242424242');
    await page.getByLabel('Expiry').fill('12/25');
    await page.getByLabel('CVC').fill('123');

    // Enviar el pedido
    await page.getByRole('button', { name: 'Place Order' }).click();

    // Verificar la confirmación
    await expect(page).toHaveURL(/\/orders\/\w+/);
    await expect(page.getByText('Order Confirmed')).toBeVisible();
  });

  test('shows validation errors for invalid input', async ({ page }) => {
    await page.goto('/checkout');
    await page.getByRole('button', { name: 'Place Order' }).click();

    await expect(page.getByText('Email is required')).toBeVisible();
    await expect(page.getByText('Address is required')).toBeVisible();
  });
});
```

### Testing de Regresión Visual

**Propósito:** Detectar cambios visuales no intencionados en los componentes de la UI.

**Herramientas:** Comparaciones visuales de Playwright, Percy, Chromatic

**Ejemplo: Test de Snapshot Visual**

```typescript
// e2e/visual/components.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
  test('button variants render correctly', async ({ page }) => {
    await page.goto('/storybook/button');
    await expect(page).toHaveScreenshot('button-variants.png');
  });

  test('responsive header', async ({ page }) => {
    // Escritorio
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');
    await expect(page.locator('header')).toHaveScreenshot('header-desktop.png');

    // Móvil
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('header')).toHaveScreenshot('header-mobile.png');
  });
});
```

## Integración con CI/CD

### Etapas del Pipeline

```yaml
# .github/workflows/test.yml
name: Test Pipeline

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  unit:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run test:unit -- --coverage
      - uses: codecov/codecov-action@v4
        with:
          files: coverage/lcov.info
          fail_ci_if_error: true

  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run test:integration

  e2e:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: integration
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npx playwright test
        env:
          QA_RUN_ID: ${{ github.run_id }}-${{ github.run_attempt }}
      # Gate real: no basarse en el exit code de `playwright test` solo (eso
      # ya falla si un test individual falla), sino en el veredicto agregado
      # que calculan las reglas QA del paquete de contratos a partir del CTRF del runner
      # — considera severidad (`[critical]`) y bloqueados, no solo pass/fail.
      - run: node .claude/contracts/output/generate-execution-report.mjs --ctrf resources/qa/reports/${{ github.run_id }}-${{ github.run_attempt }}/ctrf.json --expected resources/qa/plans/casos.json --out resources/qa/reports/${{ github.run_id }}-${{ github.run_attempt }}/execution-report.md --fail-on-no-go
        if: always()
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: qa-evidence-${{ github.run_id }}-${{ github.run_attempt }}
          path: resources/qa/*/${{ github.run_id }}-${{ github.run_attempt }}
          retention-days: 30
```

El paso de `generate-execution-report.mjs` corre con `if: always()` para que el
reporte y la evidencia se generen y suban aunque `playwright test` haya
fallado — pero `--fail-on-no-go` igual tumba el job si el veredicto agregado
es `NO-GO`. Ver `../../ranger/SKILL.md` Paso 5 y `13-evidencia-video.md`.

### División de Tests para Mayor Velocidad

```yaml
# Ejecutar pruebas E2E en paralelo en múltiples máquinas
e2e:
  strategy:
    matrix:
      shard: [1, 2, 3, 4]
  steps:
    - run: npx playwright test --shard=${{ matrix.shard }}/4
```
