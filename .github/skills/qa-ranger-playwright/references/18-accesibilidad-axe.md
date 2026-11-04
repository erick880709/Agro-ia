# Accesibilidad automatizada con Playwright

Consulta los [criterios comunes y checklists manuales](../../ranger/references/accessibility_testing_guide.md) y la [guía visual y de accesibilidad](07-visual-y-accesibilidad.md). Estos ejemplos cubren regresiones automatizadas; conserva video, trace y screenshot de los casos de navegador según la política compartida.

## Automatizado: axe en Playwright

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('A11Y-01 [high] - Página de login sin violaciones críticas/serias de axe', async ({ page }) => {
  await page.goto('/login');
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze();

  const blocking = results.violations.filter((v) => ['critical', 'serious'].includes(v.impact ?? ''));
  expect(blocking, JSON.stringify(blocking, null, 2)).toEqual([]);
});
```

Correr esto en cada flujo crítico del plan de pruebas, no solo en una
página "de accesibilidad" aparte — cada página nueva que entra al smoke
suite es candidata a sumar su caso `A11Y-xxx`.
