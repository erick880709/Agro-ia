# Casos de API, seguridad y fraude con Playwright

Ejemplos para el runner Playwright ya elegido. Confirma reglas de negocio, datos, endpoints y resultados esperados antes de adaptarlos. Completa imports, fixtures y helpers según el proyecto; los fragmentos no constituyen una suite ejecutada. Para API usa [la guía request](05-api-testing.md) y resultados del runner; para navegador aplica [la evidencia browser](13-evidencia-video.md).

## Índice

- [API](#api)
- [Seguridad funcional](#seguridad-funcional)
- [Fraude e invariantes](#fraude-e-invariantes)

## API

Criterios de diseño: [api_testing_patterns.md](../../ranger/references/api_testing_patterns.md).

### Validación de Contrato/Schema

```typescript
import Ajv from 'ajv';
import orderSchema from '../schemas/order.schema.json';

test('API-01 [high] - GET /orders/:id respeta el schema documentado', async ({ request }) => {
  const res = await request.get(`/api/orders/${orderId}`);
  const body = await res.json();
  const ajv = new Ajv();
  const valid = ajv.validate(orderSchema, body);
  expect(valid, JSON.stringify(ajv.errors)).toBe(true);
});
```

### Idempotencia

```typescript
test('API-02 [critical] - POST con Idempotency-Key repetida no duplica el efecto', async ({ request }) => {
  const key = crypto.randomUUID();
  const res1 = await request.post('/api/payments', {
    data: paymentPayload,
    headers: { 'Idempotency-Key': key },
  });
  const res2 = await request.post('/api/payments', {
    data: paymentPayload,
    headers: { 'Idempotency-Key': key },
  });
  expect(res1.status()).toBe(201);
  expect(res2.status()).toBe(200); // o 201 con el mismo id de recurso, según el contrato
  expect((await res1.json()).id).toBe((await res2.json()).id);
});
```

### Códigos de Error y Consistencia

```typescript
test('API-03 [medium] - Errores 4xx tienen shape consistente', async ({ request }) => {
  const res = await request.post('/api/orders', { data: {} });
  const body = await res.json();
  expect(body).toMatchObject({ error: { code: expect.any(String), message: expect.any(String) } });
});
```


## Seguridad funcional

Criterios de diseño: [security_testing_patterns.md](../../ranger/references/security_testing_patterns.md).

### Autenticación

```typescript
test('SEC-01 [critical] - No enumera usuarios en recuperación de password', async ({ page }) => {
  await page.goto('/forgot-password');
  await page.getByLabel('Email').fill('usuario-que-no-existe@example.com');
  await page.getByRole('button', { name: 'Enviar' }).click();
  const registered = page.getByText(/hemos enviado un enlace/i);
  const notRegistered = page.getByText(/hemos enviado un enlace/i); // mismo mensaje
  await expect(registered).toBeVisible();
  // Repetir con un email real conocido (${QA_USER_EMAIL}) y comparar:
  // el mensaje debe ser idéntico en ambos casos.
});
```

### Autorización (Control de Acceso)

```typescript
test('SEC-02 [critical] - Usuario estándar no puede leer recurso de otro usuario (IDOR)', async ({ request }) => {
  const res = await request.get(`${process.env.QA_BASE_URL}/api/orders/${OTHER_USER_ORDER_ID}`, {
    headers: { Authorization: `Bearer ${process.env.QA_USER_TOKEN}` },
  });
  expect([403, 404]).toContain(res.status());
});
```

### Cabeceras de Seguridad

```typescript
test('SEC-03 [high] - Cabeceras de seguridad presentes', async ({ request }) => {
  const res = await request.get(process.env.QA_BASE_URL!);
  const headers = res.headers();
  expect(headers['x-content-type-options']).toBe('nosniff');
  expect(headers['x-frame-options'] ?? headers['content-security-policy']).toBeTruthy();
  expect(headers['strict-transport-security']).toBeTruthy();
});
```


## Fraude e invariantes

Criterios de diseño: [adversarial_fraud_testing.md](../../ranger/references/adversarial_fraud_testing.md).

### Patrones de Implementación en Playwright

```typescript
test('FRAUD-01 [critical] - Doble clic no duplica la transferencia', async ({ page }) => {
  await page.goto('/transfers/new');
  await fillTransferForm(page, { amount: '100', to: process.env.QA_TEST_ACCOUNT! });
  const confirmBtn = page.getByRole('button', { name: 'Confirmar' });
  await Promise.all([confirmBtn.click(), confirmBtn.click()]); // doble clic simulado
  await expect(page.getByText('Transferencia exitosa')).toBeVisible();
  const transfers = await getTransfersViaApi(page, process.env.QA_TEST_ACCOUNT!);
  expect(transfers.filter((t) => t.amount === 100)).toHaveLength(1);
});
```

### Patrones de Implementación en Playwright

```typescript
test('FRAUD-02 [critical] - Dos transferencias concurrentes no exceden el saldo', async ({ request }) => {
  const [res1, res2] = await Promise.all([
    request.post(`${process.env.QA_BASE_URL}/api/transfers`, { data: transferPayload }),
    request.post(`${process.env.QA_BASE_URL}/api/transfers`, { data: transferPayload }),
  ]);
  const successes = [res1, res2].filter((r) => r.ok());
  // Si el saldo solo alcanza para una, solo una debe haber tenido éxito.
  expect(successes.length).toBeLessThanOrEqual(1);
});
```

### Patrones de Implementación en Playwright

```typescript
test('FRAUD-03 [critical] - API rechaza monto que excede el límite diario', async ({ request }) => {
  const res = await request.post(`${process.env.QA_BASE_URL}/api/transfers`, {
    data: { ...transferPayload, amount: DAILY_LIMIT + 1 },
    headers: { Authorization: `Bearer ${process.env.QA_USER_TOKEN}` },
  });
  expect(res.status()).toBe(422);
});
```

### Patrones de Implementación en Playwright

```typescript
test('FRAUD-04 [critical] - No se puede confirmar un pago sin OTP validado', async ({ request }) => {
  const res = await request.post(`${process.env.QA_BASE_URL}/api/payments/${paymentId}/confirm`, {
    // Sin haber llamado antes a /api/payments/{id}/verify-otp
    headers: { Authorization: `Bearer ${process.env.QA_USER_TOKEN}` },
  });
  expect(res.status()).toBe(409); // o el código que el contrato defina para "estado previo faltante"
});
```
