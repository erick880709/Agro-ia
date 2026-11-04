# Ejemplos y organización de pruebas JavaScript

Ejemplos unitarios y de integración de componentes, organización de archivos y cobertura Jest. Mantén el alcance solicitado: los ejemplos de integración no convierten una ejecución unitaria en una validación de API. La meta QA predeterminada es 95% por métrica soportada; una meta diferente requiere targetOverride explícito. Ajusta las exclusiones al alcance acordado.

## Índice

- [Cobertura de Jest](#cobertura-de-jest)
- [Patrones de Organización de Tests](#patrones-de-organización-de-tests)

### Testing Unitario

**Propósito:** Verificar que unidades individuales de código funcionen correctamente de forma aislada.

**Qué Probar a Nivel Unitario:**
- Funciones utilitarias puras
- Hooks personalizados (con renderHook)
- Renderizado de componentes individuales
- Reducers de estado
- Lógica de validación
- Transformadores de datos

**Ejemplo: Testear una Función Pura**

```typescript
// utils/formatPrice.ts
export function formatPrice(cents: number, currency = 'USD'): string {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  });
  return formatter.format(cents / 100);
}

// utils/formatPrice.test.ts
describe('formatPrice', () => {
  it('formats cents to USD by default', () => {
    expect(formatPrice(1999)).toBe('$19.99');
  });

  it('handles zero', () => {
    expect(formatPrice(0)).toBe('$0.00');
  });

  it('supports different currencies', () => {
    expect(formatPrice(1999, 'EUR')).toContain('€');
  });

  it('handles large numbers', () => {
    expect(formatPrice(100000000)).toBe('$1,000,000.00');
  });
});
```

**Ejemplo: Testear un Hook Personalizado**

```typescript
// hooks/useCounter.ts
export function useCounter(initial = 0) {
  const [count, setCount] = useState(initial);
  const increment = () => setCount(c => c + 1);
  const decrement = () => setCount(c => c - 1);
  const reset = () => setCount(initial);
  return { count, increment, decrement, reset };
}

// hooks/useCounter.test.ts
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('starts with initial value', () => {
    const { result } = renderHook(() => useCounter(5));
    expect(result.current.count).toBe(5);
  });

  it('increments count', () => {
    const { result } = renderHook(() => useCounter(0));
    act(() => result.current.increment());
    expect(result.current.count).toBe(1);
  });

  it('decrements count', () => {
    const { result } = renderHook(() => useCounter(5));
    act(() => result.current.decrement());
    expect(result.current.count).toBe(4);
  });

  it('resets to initial value', () => {
    const { result } = renderHook(() => useCounter(10));
    act(() => result.current.increment());
    act(() => result.current.reset());
    expect(result.current.count).toBe(10);
  });
});
```

### Testing de Integración

**Propósito:** Verificar que múltiples unidades funcionen correctamente en conjunto.

**Qué Probar a Nivel de Integración:**
- Árboles de componentes con múltiples hijos
- Componentes con proveedores de contexto
- Flujos de envío de formularios
- Manejo de llamadas a API y sus respuestas
- Interacciones de manejo de estado
- Componentes dependientes del router

**Ejemplo: Testear un Componente con Llamada a API**

```typescript
// components/UserProfile.tsx
export function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => setUser(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  return <div>{user?.name}</div>;
}

// components/UserProfile.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { UserProfile } from './UserProfile';

const server = setupServer(
  rest.get('/api/users/:id', (req, res, ctx) => {
    return res(ctx.json({ id: req.params.id, name: 'John Doe' }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('UserProfile', () => {
  it('shows loading state initially', () => {
    render(<UserProfile userId="123" />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays user name after loading', async () => {
    render(<UserProfile userId="123" />);
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });
  });

  it('displays error on API failure', async () => {
    server.use(
      rest.get('/api/users/:id', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );
    render(<UserProfile userId="123" />);
    await waitFor(() => {
      expect(screen.getByText(/Error/)).toBeInTheDocument();
    });
  });
});
```

## Cobertura de Jest

### Configuración de Cobertura de Jest

```javascript
// jest.config.js
module.exports = {
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{ts,tsx}',
    '!src/**/index.{ts,tsx}', // archivos barrel
    '!src/types/**',
  ],
  coverageThreshold: {
    global: {
      statements: 95,
      branches: 95,
      functions: 95,
      lines: 95,
    },
    // Umbrales más altos para rutas críticas
    './src/services/payment/': {
      statements: 95,
      branches: 95,
      functions: 95,
      lines: 95,
    },
    './src/services/auth/': {
      statements: 95,
      branches: 85,
      functions: 95,
      lines: 95,
    },
  },
  coverageReporters: ['text', 'lcov', 'html', 'json'],
};
```

---

## Patrones de Organización de Tests

### Tests Co-ubicados (Recomendado para React)

```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx      # Pruebas unitarias
│   │   ├── Button.stories.tsx   # Storybook
│   │   └── index.ts
│   └── Form/
│       ├── Form.tsx
│       ├── Form.test.tsx
│       └── Form.integration.test.tsx  # Pruebas de integración
├── hooks/
│   ├── useAuth.ts
│   └── useAuth.test.ts
└── utils/
    ├── formatters.ts
    └── formatters.test.ts
```

### Directorio de Tests Separado

```
src/
├── components/
├── hooks/
└── utils/

__tests__/
├── unit/
│   ├── components/
│   ├── hooks/
│   └── utils/
├── integration/
│   └── flows/
└── fixtures/
    ├── users.json
    └── products.json

e2e/
├── specs/
│   ├── auth.spec.ts
│   └── checkout.spec.ts
├── fixtures/
│   └── auth.ts
└── pages/      # Modelos de Objetos de Página (Page Object Models)
    ├── LoginPage.ts
    └── CheckoutPage.ts
```

### Convenciones de Nombrado de Archivos de Test

| Patrón | Caso de Uso |
|---------|----------|
| `*.test.ts` | Pruebas unitarias |
| `*.spec.ts` | Pruebas de integración/E2E |
| `*.integration.test.ts` | Pruebas de integración explícitas |
| `*.e2e.spec.ts` | Pruebas E2E explícitas |
| `*.a11y.test.ts` | Pruebas de accesibilidad |
| `*.visual.spec.ts` | Pruebas de regresión visual |

---
