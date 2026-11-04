# 05 — API testing con Playwright

## Contenido
1. Cuándo usar Playwright para API (y cuándo no)
2. Fixture `request` y contexto propio
3. Aserciones y validación de esquemas
4. Clientes API para setup y limpieza
5. Pruebas híbridas API + UI
6. Escuchar el tráfico de la UI

---

## 1. Cuándo

- **Sí**: setup/limpieza de datos para E2E, verificar el efecto de una acción de UI en el backend, smoke de API en el mismo pipeline que la UI, equipos que ya trabajan en TypeScript.
- **Considera otra herramienta** (p. ej. Karate — skill `qa-ranger-karate`) si la suite es mayoritariamente de API con contratos extensos, mocks de servicios, performance reutilizando las mismas pruebas o equipos Java.

## 2. `request`

```ts
import { test, expect } from '@playwright/test';

test.use({
  baseURL: process.env.API_URL,
  extraHTTPHeaders: { Accept: 'application/json', Authorization: `Bearer ${process.env.API_TOKEN}` },
});

test('[HU-301][CA-1] consulta un pago existente', async ({ request }) => {
  const r = await request.get<Pago>('/v1/pagos/123');          // 1.63+: json() tipado
  await expect(r).toBeOK();
  const pago = await r.json();
  expect(pago).toMatchObject({ id: '123', estado: expect.stringMatching(/APLICADO|PENDIENTE/) });
});
```
Contexto propio (otra base URL, otro token, mTLS):
```ts
const api = await playwright.request.newContext({
  baseURL: process.env.API_URL,
  clientCertificates: [{ origin: process.env.API_URL!, pfxPath: 'certs/cliente.p12', passphrase: process.env.P12_PASS }],
  ignoreHTTPSErrors: false,
});
// ...
await api.dispose();
```
Los métodos `get/post/put/patch/delete/fetch` aceptan `params`, `data` (JSON), `form`, `multipart`, `headers`, `timeout`, `failOnStatusCode`, `maxRetries` (errores de red).

## 3. Aserciones y esquemas

```ts
expect(r.status()).toBe(201);
expect(r.headers()['content-type']).toContain('application/json');
const body = await r.json();
expect(body).toEqual({
  id: expect.any(String),
  monto: 150000,
  fechaCreacion: expect.stringMatching(/^\d{4}-\d{2}-\d{2}T/),
  detalles: expect.arrayContaining([expect.objectContaining({ tipo: 'COMISION' })]),
});
```
Para contratos completos, valida con un esquema (zod o ajv) en lugar de decenas de `expect`:
```ts
import { z } from 'zod';
const Pago = z.object({
  id: z.string().uuid(),
  estado: z.enum(['PENDIENTE', 'APLICADO', 'RECHAZADO']),
  monto: z.number().positive(),
  descripcion: z.string().max(40).optional(),
});
const resultado = Pago.safeParse(await r.json());
expect(resultado.success, JSON.stringify(resultado.error?.issues)).toBe(true);
```
Los esquemas pueden generarse desde el OpenAPI (p. ej. `openapi-zod-client`) para no mantenerlos a mano.

Cobertura mínima por endpoint: igual que en la skill Karate (camino feliz, 400/422 por validación, 401/403, 404, idempotencia en operaciones monetarias, errores sin stack traces).

## 4. Clientes API

```ts
// api/pagos.client.ts
import { type APIRequestContext, expect } from '@playwright/test';

export class PagosClient {
  constructor(private readonly request: APIRequestContext) {}

  async crearPago(datos: { monto: number; cuentaOrigen: string }) {
    const r = await this.request.post('/api/pagos', { data: datos });
    await expect(r, `crear pago: ${await r.text()}`).toBeOK();
    return r.json() as Promise<{ id: string; referencia: string }>;
  }

  async eliminarPago(id: string) {
    const r = await this.request.delete(`/api/pagos/${id}`);
    expect([200, 204, 404]).toContain(r.status());   // idempotente: ya borrado también vale
  }
}
```
Se exponen como fixtures (ver 03 §3), con limpieza en el teardown de la fixture.

## 5. Híbridas

El patrón de mayor valor por costo: **arrange por API, act/assert en UI, verificación de backend por API**.
```ts
test('[HU-260] el pago creado aparece en el historial', async ({ page, pagosApi }) => {
  const pago = await pagosApi.crearPago({ monto: 50_000, cuentaOrigen: '00112233445' });
  await page.goto('/historial');
  await expect(page.getByRole('row').filter({ hasText: pago.referencia })).toBeVisible();
});
```
`page.request` comparte cookies con el contexto del navegador (sesión del usuario); la fixture `request` usa su propio contexto.

## 6. Escuchar el tráfico de la UI

Validar que la UI envió lo correcto (sin mockear):
```ts
const reqPromise = page.waitForRequest(r => r.url().includes('/api/transferencias') && r.method() === 'POST');
const resPromise = page.waitForResponse(r => r.url().includes('/api/transferencias') && r.request().method() === 'POST');
await page.getByRole('button', { name: 'Confirmar' }).click();
const req = await reqPromise;
expect(req.postDataJSON()).toMatchObject({ monto: 150000, cuentaDestino: '00998877665' });
const res = await resPromise;
expect(res.status()).toBe(201);
```
Crea las promesas **antes** de la acción que dispara la petición; si no, se pierde la carrera.
