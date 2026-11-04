# Accesibilidad de componentes con Jest y RTL

Usa jest-axe con componentes en memoria y el runner del proyecto. Consulta los [criterios comunes y checklists manuales](../../ranger/references/accessibility_testing_guide.md); la prueba de un componente aislado no acredita el flujo completo. Conserva el reporte del runner según la política unit.

## Automatizado: axe en Componentes (jest-axe)

Para componentes aislados con React Testing Library:

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);
import { LoginForm } from './LoginForm';

test('LoginForm no tiene violaciones de accesibilidad', async () => {
  const { container } = render(<LoginForm />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

Útil para detectar regresiones a nivel de componente antes de que lleguen
a integración/E2E — más rápido de ejecutar, pero no reemplaza el chequeo
de página completa (un componente accesible en aislamiento puede quedar
mal ensamblado en contexto).
