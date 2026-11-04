# 03 — Arquitectura de suite

## Contenido
1. Estructura de carpetas
2. Page objects: cuándo y cómo
3. Fixtures (`test.extend`)
4. Datos de prueba
5. Organización de tests: describe, steps, tags, anotaciones
6. Paralelismo, locks y modo serial
7. Convenciones de código

---

## 1. Estructura

```
e2e/
├── playwright.config.ts
├── package.json / tsconfig.json / eslint.config.mjs
├── .env.example                    # variables requeridas, sin valores reales
├── Linea_Base_<Proyecto>.md
├── config/env.ts                   # URLs por ambiente
├── fixtures/
│   ├── index.ts                    # export const test = base.extend<...>(...)
│   └── data.ts                     # builders/fábricas de datos
├── pages/                          # page objects (uno por página o componente grande)
│   ├── login.page.ts
│   └── transferencias.page.ts
├── api/                            # clientes API para setup/limpieza
│   └── pagos.client.ts
├── tests/
│   ├── auth.setup.ts
│   ├── transferencias/
│   │   ├── crear-transferencia.spec.ts
│   │   └── historial.spec.ts
│   └── api/
│       └── pagos.api.spec.ts
└── playwright/.auth/               # storageState (gitignored)
```
Specs por **capacidad de negocio**, no por sprint ni por página técnica. Nombres en kebab-case: `crear-transferencia.spec.ts`.

## 2. Page objects

Úsalos cuando una página se usa en 3 o más specs o sus locators son no triviales. Reglas:
- Locators como propiedades `readonly` declaradas en el constructor (son perezosos: no tocan el DOM al crearse).
- Métodos = **intenciones del usuario** (`transferir(datos)`), no micro-acciones (`clickBotonTransferir()`).
- Sin aserciones de negocio dentro del page object; puede exponer locators para que el test asierte. Excepción aceptada: un método `esperarCargada()` que asegura un estado estable.
- Sin herencia profunda; composición (componentes reutilizables como `TablaMovimientos`).
- `test.step` dentro de los métodos para un reporte legible.

```ts
// pages/transferencias.page.ts
import { type Page, type Locator, test } from '@playwright/test';

export type DatosTransferencia = { cuentaDestino: string; monto: number; descripcion?: string };

export class TransferenciasPage {
  readonly cuentaDestino: Locator;
  readonly monto: Locator;
  readonly descripcion: Locator;
  readonly continuar: Locator;
  readonly confirmar: Locator;
  readonly mensaje: Locator;

  constructor(private readonly page: Page) {
    this.cuentaDestino = page.getByLabel('Cuenta destino');
    this.monto = page.getByLabel('Monto');
    this.descripcion = page.getByLabel('Descripción');
    this.continuar = page.getByRole('button', { name: 'Continuar' });
    this.confirmar = page.getByRole('button', { name: 'Confirmar transferencia' });
    this.mensaje = page.getByRole('alert');
  }

  async abrir() {
    await this.page.goto('/transferencias/nueva');
  }

  async transferir({ cuentaDestino, monto, descripcion }: DatosTransferencia) {
    await test.step(`transferir ${monto} a ${cuentaDestino}`, async () => {
      await this.cuentaDestino.fill(cuentaDestino);
      await this.monto.fill(String(monto));
      if (descripcion) await this.descripcion.fill(descripcion);
      await this.continuar.click();
      await this.confirmar.click();
    });
  }
}
```

**POM vs fixture vs helper**: page object para la UI de una página; fixture para *proveer* objetos y estado a los tests (con setup/teardown); función helper pura para lógica sin estado (formatear montos, generar documentos).

## 3. Fixtures

```ts
// fixtures/index.ts
import { test as base, expect } from '@playwright/test';
import { TransferenciasPage } from '../pages/transferencias.page';
import { PagosClient } from '../api/pagos.client';

type Fixtures = {
  transferencias: TransferenciasPage;
  pagosApi: PagosClient;
  cuentaConSaldo: { numero: string };
};

export const test = base.extend<Fixtures>({
  transferencias: async ({ page }, use) => {
    await use(new TransferenciasPage(page));
  },
  pagosApi: async ({ request }, use) => {
    await use(new PagosClient(request));
  },
  // dato creado por test y eliminado al terminar, aunque el test falle
  cuentaConSaldo: async ({ pagosApi }, use) => {
    const cuenta = await pagosApi.crearCuentaPrueba({ saldo: 1_000_000 });
    await use(cuenta);
    await pagosApi.eliminarCuenta(cuenta.numero);
  },
});
export { expect };
```
Los tests importan `test` y `expect` desde `fixtures`, no desde `@playwright/test`.

- Fixtures **de worker** (`{ scope: 'worker' }`) para recursos costosos compartidos por un worker (una cuenta por worker, una conexión).
- `{ auto: true }` para fixtures que deben correr siempre (p. ej. adjuntar logs de consola al fallar).
- Opciones configurables por proyecto: `[valorPorDefecto, { option: true }]` + `test.use({ ... })`.
- `mergeTests(a, b)` para combinar fixtures de varios módulos.

Fixture automática útil — falla el test si hubo errores JS no controlados en la página:
```ts
erroresPagina: [async ({ page }, use) => {
  const errores: string[] = [];
  page.on('pageerror', e => errores.push(e.message));
  await use(errores);
  expect(errores, 'errores JavaScript no controlados en la página').toEqual([]);
}, { auto: true }],
```

## 4. Datos de prueba

| Estrategia | Uso |
|---|---|
| Crear por API en una fixture, limpiar al final | Por defecto |
| Datos únicos (`${Date.now()}-${testInfo.workerIndex}`, `crypto.randomUUID()`, faker) | Campos con unicidad (correo, documento, referencia) |
| Una cuenta por worker (`testInfo.parallelIndex`) | Cuando el estado de la cuenta se modifica |
| Datos semilla de solo lectura | Catálogos, parametrías |
| Mock de red | Estados imposibles o costosos de producir (ver 06) |

Nunca: datos reales de clientes, IDs fijos que alguien puede borrar, dependencias de que otro test haya creado algo.

Data-driven:
```ts
const casos = [
  { monto: 0, error: 'El monto debe ser mayor a cero' },
  { monto: -100, error: 'El monto debe ser mayor a cero' },
  { monto: 10_000_001, error: 'Supera el tope diario' },
] as const;
for (const { monto, error } of casos) {
  test(`[HU-245][CA-2] rechaza monto ${monto}`, async ({ transferencias }) => {
    await transferencias.abrir();
    await transferencias.monto.fill(String(monto));
    await transferencias.continuar.click();
    await expect(transferencias.mensaje).toHaveText(error);
  });
}
```
Los títulos deben ser únicos (incluye el dato en el título).

## 5. Organización

```ts
test.describe('Transferencias entre cuentas propias', { tag: '@transferencias' }, () => {
  test.beforeEach(async ({ transferencias }) => { await transferencias.abrir(); });

  test('[HU-245][CA-1] transfiere con saldo suficiente', {
    tag: ['@smoke', '@critico'],
    annotation: { type: 'req', description: 'HU-245/CA-1' },
  }, async ({ transferencias, cuentaConSaldo }) => { /* ... */ });

  test.fixme('[HU-250] programa transferencia futura', async () => {});   // pendiente conocido
});
```
- `test.skip(condición, motivo)` para skips condicionales (navegador no soportado); `test.fixme` para bugs conocidos (con enlace al ticket en una anotación); `test.fail()` cuando se espera que falle.
- Ejecutar por tag: `--grep @smoke`, excluir: `--grep-invert @lento` (`-G` en 1.61+).
- `test.step()` con `box: true` para que los errores apunten al paso y no al interior del helper; en 1.63+ admite `{ subtitle, params }`.

## 6. Paralelismo

- `fullyParallel: true` + tests independientes = máxima velocidad.
- **Locks (1.63+)**: tests que tocan un recurso compartido (configuración global de una cuenta, servicio externo con límite) declaran `{ lock: 'nombre' }`; los que comparten nombre nunca corren a la vez, el resto sigue en paralelo. También en `test.describe(..., { lock })` o `test.describe.configure({ lock })`.
- `test.describe.configure({ mode: 'serial' })` solo cuando los pasos son **un mismo flujo** que no se puede separar (y aun así, preferir un único test con `test.step`). Si uno falla, los siguientes se saltan.
- `workers: 1` global es un síntoma de dependencias ocultas, no una solución.

## 7. Convenciones

- TypeScript estricto; ESLint con `@typescript-eslint/no-floating-promises` y `eslint-plugin-playwright` (detecta `await` faltantes, `waitForTimeout`, `force`, `test.only`...).
- Timeouts como constantes con nombre (`TIMEOUT_PROCESO_BATCH = 60_000`) y un comentario del porqué; nunca números mágicos.
- Sin `console.log` de datos sensibles; usa `testInfo.attach()` para evidencia.
- Comentarios para el **porqué** (regla de negocio, bug conocido), no para el qué.
