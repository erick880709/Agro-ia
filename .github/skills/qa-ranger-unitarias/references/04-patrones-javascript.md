# Patrones de pruebas con Jest, RTL y MSW

Consulta esta guía para componentes React, factories, fixtures, mocks, asincronía y snapshots. Usa el runner y las versiones del proyecto; los ejemplos Jest se adaptan a Vitest cuando corresponda. Para diseño y cobertura del stack consulta [runners y cobertura](01-runners-y-cobertura.md).

## Índice

- [Factories de Datos de Prueba](#factories-de-datos-de-prueba)
- [Fixtures de Jest y datos compartidos](#fixtures-de-jest-y-datos-compartidos)
- [Estrategias de Mocking](#estrategias-de-mocking)
- [Utilidades de Prueba Personalizadas](#utilidades-de-prueba-personalizadas)
- [Patrones de Pruebas Asíncronas](#patrones-de-pruebas-asíncronas)
- [Guía de Snapshot Testing](#guía-de-snapshot-testing)

### Component Object Model (React Testing Library)

```typescript
// __tests__/objects/LoginFormObject.ts
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

export class LoginFormObject {
  get emailInput() {
    return screen.getByLabelText(/email/i);
  }

  get passwordInput() {
    return screen.getByLabelText(/password/i);
  }

  get submitButton() {
    return screen.getByRole('button', { name: /sign in/i });
  }

  get errorMessage() {
    return screen.queryByRole('alert');
  }

  async fillEmail(email: string) {
    await userEvent.type(this.emailInput, email);
  }

  async fillPassword(password: string) {
    await userEvent.type(this.passwordInput, password);
  }

  async submit() {
    await userEvent.click(this.submitButton);
  }

  async login(email: string, password: string) {
    await this.fillEmail(email);
    await this.fillPassword(password);
    await this.submit();
  }

  async expectError(message: string) {
    await waitFor(() => {
      expect(this.errorMessage).toHaveTextContent(message);
    });
  }
}
```

## Factories de Datos de Prueba

Las factories crean datos de prueba con valores por defecto razonables, reduciendo el código repetitivo y mejorando la mantenibilidad.

### Patrón de Factory Básico

```typescript
// __tests__/factories/userFactory.ts
interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'guest';
  createdAt: Date;
  preferences: {
    theme: 'light' | 'dark';
    notifications: boolean;
  };
}

let idCounter = 0;

export function createUser(overrides: Partial<User> = {}): User {
  return {
    id: `user-${++idCounter}`,
    email: `user${idCounter}@example.com`,
    name: `Test User ${idCounter}`,
    role: 'user',
    createdAt: new Date('2024-01-01'),
    preferences: {
      theme: 'light',
      notifications: true,
    },
    ...overrides,
    // Combinar en profundidad (deep merge) las preferencias si se proporcionan
    preferences: {
      theme: 'light',
      notifications: true,
      ...overrides.preferences,
    },
  };
}

// Builders especializados
export function createAdmin(overrides: Partial<User> = {}): User {
  return createUser({ role: 'admin', ...overrides });
}

export function createGuest(overrides: Partial<User> = {}): User {
  return createUser({
    role: 'guest',
    name: 'Guest',
    email: '',
    ...overrides,
  });
}
```

### Builder Pattern para objetos complejos

```typescript
// __tests__/factories/orderBuilder.ts
interface OrderItem {
  productId: string;
  quantity: number;
  price: number;
}

interface Order {
  id: string;
  userId: string;
  items: OrderItem[];
  status: 'pending' | 'processing' | 'shipped' | 'delivered';
  total: number;
  shippingAddress: Address;
  createdAt: Date;
}

export class OrderBuilder {
  private order: Partial<Order> = {};
  private items: OrderItem[] = [];

  withId(id: string): this {
    this.order.id = id;
    return this;
  }

  forUser(userId: string): this {
    this.order.userId = userId;
    return this;
  }

  withItem(productId: string, quantity: number, price: number): this {
    this.items.push({ productId, quantity, price });
    return this;
  }

  withStatus(status: Order['status']): this {
    this.order.status = status;
    return this;
  }

  shippedTo(address: Address): this {
    this.order.shippingAddress = address;
    return this;
  }

  build(): Order {
    const total = this.items.reduce(
      (sum, item) => sum + item.price * item.quantity,
      0
    );

    return {
      id: this.order.id || `order-${Date.now()}`,
      userId: this.order.userId || 'user-1',
      items: this.items,
      status: this.order.status || 'pending',
      total,
      shippingAddress: this.order.shippingAddress || createAddress(),
      createdAt: new Date(),
    };
  }
}

// Uso
const order = new OrderBuilder()
  .forUser('user-123')
  .withItem('product-1', 2, 29.99)
  .withItem('product-2', 1, 49.99)
  .withStatus('processing')
  .build();
```

### Factory con Faker

```typescript
// __tests__/factories/productFactory.ts
import { faker } from '@faker-js/faker';

interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  inStock: boolean;
  imageUrl: string;
}

export function createProduct(overrides: Partial<Product> = {}): Product {
  return {
    id: faker.string.uuid(),
    name: faker.commerce.productName(),
    description: faker.commerce.productDescription(),
    price: parseFloat(faker.commerce.price({ min: 10, max: 500 })),
    category: faker.commerce.department(),
    inStock: faker.datatype.boolean({ probability: 0.8 }),
    imageUrl: faker.image.url(),
    ...overrides,
  };
}

export function createProducts(count: number): Product[] {
  return Array.from({ length: count }, () => createProduct());
}
```

---

## Fixtures de Jest y datos compartidos

### Configuración de pruebas de Jest

```typescript
// jest.setup.ts
import '@testing-library/jest-dom';
import { server } from './__tests__/mocks/server';

// Iniciar el servidor de MSW antes de todas las pruebas
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));

// Restablecer los handlers después de cada prueba
afterEach(() => server.resetHandlers());

// Limpiar después de todas las pruebas
afterAll(() => server.close());

// Mock de window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock de IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};
```

### Archivos de datos de prueba compartidos

```typescript
// __tests__/fixtures/products.json
{
  "products": [
    {
      "id": "prod-1",
      "name": "Widget Pro",
      "price": 29.99,
      "category": "Electronics"
    },
    {
      "id": "prod-2",
      "name": "Gadget Plus",
      "price": 49.99,
      "category": "Electronics"
    }
  ]
}

// __tests__/fixtures/index.ts
import productsData from './products.json';
import usersData from './users.json';

export const fixtures = {
  products: productsData.products,
  users: usersData.users,
};
```

---

## Estrategias de Mocking

### MSW (Mock Service Worker) para mocking de API

MSW intercepta las solicitudes de red a nivel de service worker, funcionando tanto en el navegador como en Node.

**Configuración de handlers:**

```typescript
// __tests__/mocks/handlers.ts
import { rest } from 'msw';
import { createUser } from '../factories/userFactory';
import { createProduct } from '../factories/productFactory';

export const handlers = [
  // GET /api/users/:id
  rest.get('/api/users/:id', (req, res, ctx) => {
    const { id } = req.params;
    const user = createUser({ id: id as string });
    return res(ctx.json(user));
  }),

  // GET /api/products
  rest.get('/api/products', (req, res, ctx) => {
    const category = req.url.searchParams.get('category');
    const products = Array.from({ length: 10 }, () => createProduct());
    const filtered = category
      ? products.filter(p => p.category === category)
      : products;
    return res(ctx.json(filtered));
  }),

  // POST /api/orders
  rest.post('/api/orders', async (req, res, ctx) => {
    const body = await req.json();
    return res(
      ctx.status(201),
      ctx.json({
        id: `order-${Date.now()}`,
        ...body,
        status: 'pending',
      })
    );
  }),

  // Simulación de error
  rest.get('/api/error', (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({ error: 'Internal Server Error' })
    );
  }),
];
```

**Configuración del servidor:**

```typescript
// __tests__/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

**Sobrescribiendo handlers en las pruebas:**

```typescript
// __tests__/components/ProductList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { server } from '../mocks/server';
import { ProductList } from '../../src/components/ProductList';

describe('ProductList', () => {
  it('shows loading state', () => {
    render(<ProductList />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders products', async () => {
    render(<ProductList />);
    await waitFor(() => {
      expect(screen.getAllByTestId('product-card')).toHaveLength(10);
    });
  });

  it('shows error state on API failure', async () => {
    server.use(
      rest.get('/api/products', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    render(<ProductList />);
    await waitFor(() => {
      expect(screen.getByText(/error loading products/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no products', async () => {
    server.use(
      rest.get('/api/products', (req, res, ctx) => {
        return res(ctx.json([]));
      })
    );

    render(<ProductList />);
    await waitFor(() => {
      expect(screen.getByText('No products found')).toBeInTheDocument();
    });
  });
});
```

### Mocking de módulos con Jest

```typescript
// Mockear un módulo
jest.mock('../../src/services/analytics', () => ({
  trackEvent: jest.fn(),
  trackPageView: jest.fn(),
  setUser: jest.fn(),
}));

// Mockear con implementación
jest.mock('next/router', () => ({
  useRouter: jest.fn().mockReturnValue({
    pathname: '/test',
    push: jest.fn(),
    replace: jest.fn(),
    query: {},
  }),
}));

// Mock parcial (conserva algunas implementaciones reales)
jest.mock('../../src/utils/helpers', () => ({
  ...jest.requireActual('../../src/utils/helpers'),
  sendEmail: jest.fn().mockResolvedValue({ success: true }),
}));
```

### Mocking de hooks

```typescript
// __tests__/hooks/useAuth.test.tsx
import { renderHook, act } from '@testing-library/react';
import { useAuth } from '../../src/hooks/useAuth';
import * as authService from '../../src/services/auth';

jest.mock('../../src/services/auth');

const mockAuthService = authService as jest.Mocked<typeof authService>;

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('logs in user successfully', async () => {
    const mockUser = { id: '1', email: 'test@example.com' };
    mockAuthService.login.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('handles login error', async () => {
    mockAuthService.login.mockRejectedValue(new Error('Invalid credentials'));

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      try {
        await result.current.login('test@example.com', 'wrong');
      } catch (e) {
        // Esperado
      }
    });

    expect(result.current.user).toBeNull();
    expect(result.current.error).toBe('Invalid credentials');
  });
});
```

---

## Utilidades de Prueba Personalizadas

### Render con Providers

```typescript
// __tests__/utils/renderWithProviders.tsx
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '../../src/contexts/ThemeContext';
import { AuthProvider } from '../../src/contexts/AuthContext';

interface ExtendedRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialUser?: User | null;
  theme?: 'light' | 'dark';
}

export function renderWithProviders(
  ui: ReactElement,
  {
    initialUser = null,
    theme = 'light',
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Deshabilitar reintentos en las pruebas
      },
    },
  });

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <AuthProvider initialUser={initialUser}>
          <ThemeProvider initialTheme={theme}>
            {children}
          </ThemeProvider>
        </AuthProvider>
      </QueryClientProvider>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

// Reexportar todo desde RTL
export * from '@testing-library/react';
export { renderWithProviders as render };
```

**Uso:**

```typescript
// __tests__/components/Dashboard.test.tsx
import { render, screen } from '../utils/renderWithProviders';
import { Dashboard } from '../../src/components/Dashboard';
import { createUser } from '../factories/userFactory';

describe('Dashboard', () => {
  it('shows user greeting when authenticated', () => {
    const user = createUser({ name: 'John Doe' });
    render(<Dashboard />, { initialUser: user });
    expect(screen.getByText('Hello, John Doe')).toBeInTheDocument();
  });

  it('shows login prompt when not authenticated', () => {
    render(<Dashboard />, { initialUser: null });
    expect(screen.getByText('Please log in')).toBeInTheDocument();
  });

  it('applies dark theme', () => {
    render(<Dashboard />, { theme: 'dark' });
    expect(document.body).toHaveClass('dark');
  });
});
```

### Matchers personalizados

```typescript
// __tests__/utils/customMatchers.ts
import { expect } from '@playwright/test';

expect.extend({
  async toHaveLoadedSuccessfully(page) {
    const hasNoErrors = await page.evaluate(() => {
      return !document.querySelector('[data-error]');
    });
    const isLoaded = await page.evaluate(() => {
      return document.readyState === 'complete';
    });

    return {
      pass: hasNoErrors && isLoaded,
      message: () =>
        hasNoErrors
          ? 'Page loaded with errors'
          : 'Page did not finish loading',
    };
  },

  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling;
    return {
      pass,
      message: () =>
        `expected ${received} ${pass ? 'not ' : ''}to be within range ${floor} - ${ceiling}`,
    };
  },
});

// Declaraciones de tipos
declare global {
  namespace PlaywrightTest {
    interface Matchers<R> {
      toHaveLoadedSuccessfully(): Promise<R>;
    }
  }
}
```

---

## Patrones de Pruebas Asíncronas

### Esperar elementos

```typescript
// Preferido: usar findBy* (espera automáticamente)
const element = await screen.findByText('Loaded');

// Esperar a que aparezca un elemento
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});

// Esperar a que un elemento desaparezca
await waitForElementToBeRemoved(() => screen.queryByText('Loading...'));

// Esperar con timeout personalizado
await waitFor(
  () => {
    expect(mockFn).toHaveBeenCalled();
  },
  { timeout: 5000 }
);
```

### Prueba de cambios de estado asíncronos

```typescript
// __tests__/components/AsyncButton.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AsyncButton } from '../../src/components/AsyncButton';

describe('AsyncButton', () => {
  it('shows loading state during async operation', async () => {
    const user = userEvent.setup();
    const onClickMock = jest.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(<AsyncButton onClick={onClickMock}>Submit</AsyncButton>);

    // Estado inicial
    expect(screen.getByRole('button')).toHaveTextContent('Submit');
    expect(screen.getByRole('button')).not.toBeDisabled();

    // Clic y verificación del estado de carga
    await user.click(screen.getByRole('button'));
    expect(screen.getByRole('button')).toHaveTextContent('Loading...');
    expect(screen.getByRole('button')).toBeDisabled();

    // Esperar a que finalice
    await waitFor(() => {
      expect(screen.getByRole('button')).toHaveTextContent('Submit');
      expect(screen.getByRole('button')).not.toBeDisabled();
    });
  });
});
```

### Prueba de funciones con debounce/throttle

```typescript
// __tests__/components/SearchInput.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchInput } from '../../src/components/SearchInput';

// Usar temporizadores simulados (fake timers) para probar el debounce
jest.useFakeTimers();

describe('SearchInput', () => {
  it('debounces search calls', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    const onSearchMock = jest.fn();

    render(<SearchInput onSearch={onSearchMock} debounceMs={300} />);

    // Escribir rápidamente
    await user.type(screen.getByRole('textbox'), 'test');

    // Todavía no hay llamadas (debounce en curso)
    expect(onSearchMock).not.toHaveBeenCalled();

    // Avanzar los temporizadores más allá del umbral de debounce
    jest.advanceTimersByTime(300);

    // Ahora debería haberse llamado una vez con el valor final
    expect(onSearchMock).toHaveBeenCalledTimes(1);
    expect(onSearchMock).toHaveBeenCalledWith('test');
  });
});
```

## Guía de Snapshot Testing

### Cuándo usar snapshots

| Buenos casos de uso | Malos casos de uso |
|----------------|---------------|
| Componentes de UI estáticos | Contenido dinámico |
| Mensajes de error | Timestamps/IDs |
| Objetos de configuración | Árboles de componentes grandes |
| Datos serializables | Componentes interactivos |

### Snapshots de componentes

```typescript
// __tests__/components/Button.test.tsx
import { render } from '@testing-library/react';
import { Button } from '../../src/components/Button';

describe('Button snapshots', () => {
  it('renders primary variant', () => {
    const { container } = render(
      <Button variant="primary">Click me</Button>
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders secondary variant', () => {
    const { container } = render(
      <Button variant="secondary">Click me</Button>
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders disabled state', () => {
    const { container } = render(
      <Button disabled>Click me</Button>
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
```

### Snapshots inline

```typescript
// Adecuado para salidas pequeñas y estables
it('formats date correctly', () => {
  const result = formatDate(new Date('2024-01-15'));
  expect(result).toMatchInlineSnapshot(`"January 15, 2024"`);
});

it('generates expected error message', () => {
  const error = new ValidationError('email', 'Invalid format');
  expect(error.message).toMatchInlineSnapshot(
    `"Validation failed for 'email': Invalid format"`
  );
});
```

### Buenas prácticas de snapshots

1. **Mantené los snapshots pequeños**: capturá elementos específicos, no páginas completas
2. **Usá snapshots inline para salidas pequeñas**: son más fáciles de revisar en el código
3. **Revisá con atención los cambios de snapshot**: no los actualices a ciegas
4. **Evitá snapshots para contenido dinámico**: filtrá timestamps e IDs
5. **Combiná con otras aserciones**: los snapshots complementan, no reemplazan

```typescript
// Filtrar contenido dinámico de los snapshots
it('renders user card', () => {
  const { container } = render(<UserCard user={mockUser} />);

  // Eliminar elementos dinámicos antes del snapshot
  const card = container.firstChild;
  const timestamp = card.querySelector('.timestamp');
  timestamp?.remove();

  expect(card).toMatchSnapshot();
});
```

---
