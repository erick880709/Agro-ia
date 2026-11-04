# 06 — Red, mocks y tiempo

## Contenido
1. Cuándo mockear
2. `page.route` / `context.route`
3. Simular errores y latencia
4. Modificar respuestas reales
5. HAR: grabar y reproducir
6. WebSocket
7. Reloj (`page.clock`)
8. Otros: geolocalización, permisos, offline

---

## 1. Cuándo

| Mockear | No mockear |
|---|---|
| Servicios de terceros (pasarelas de pago, proveedores de identidad externos, mapas, analítica) | Tu propio backend en pruebas E2E: lo que se quiere probar es la integración |
| Estados difíciles de producir: 500, timeouts, respuestas vacías, límites | Contratos del backend (eso es API testing, ver 05) |
| Pruebas de componentes/frontend aisladas del backend | |

Una suite con todo mockeado es una prueba de frontend, no un E2E: decláralo así en su nombre o tags (`@frontend-aislado`).

## 2. `route`

```ts
await page.route('**/api/tasa-cambio*', route => route.fulfill({
  status: 200,
  contentType: 'application/json',
  json: { moneda: 'USD', tasa: 4100.5, fecha: '2026-10-05' },
}));
await page.goto('/divisas');
await expect(page.getByText('4.100,50')).toBeVisible();
```
- Registra la ruta **antes** de la navegación o acción que hace la petición.
- `context.route` aplica a todas las páginas del contexto (incluidos popups).
- Patrón glob o regex o predicado: `page.route(url => url.pathname.startsWith('/api/'), ...)`.
- Bloquear ruido (analítica, chat de soporte) para acelerar y estabilizar: `await context.route(/google-analytics|hotjar/, r => r.abort())`.
- `routeFromHAR`/`route.fallback()` para encadenar handlers.
- Verificar que el mock se usó: cuenta las llamadas en el handler o usa `page.waitForRequest`.

## 3. Errores y latencia

```ts
test('[HU-270] muestra mensaje amigable si el core bancario no responde', async ({ page }) => {
  await page.route('**/api/saldos', r => r.fulfill({ status: 503, json: { codigo: 'SERVICIO_NO_DISPONIBLE' } }));
  await page.goto('/inicio');
  await expect(page.getByRole('alert')).toHaveText(/no pudimos consultar tu saldo/i);
  await expect(page.getByRole('button', { name: 'Reintentar' })).toBeVisible();
});

test('muestra indicador de carga mientras responde el servicio', async ({ page }) => {
  await page.route('**/api/movimientos', async r => {
    await new Promise(res => setTimeout(res, 3_000));   // latencia simulada dentro del mock, no en el test
    await r.continue();
  });
  await page.goto('/movimientos');
  await expect(page.getByRole('progressbar')).toBeVisible();
  await expect(page.getByRole('progressbar')).toBeHidden({ timeout: 10_000 });
});

await page.route('**/api/pagos', r => r.abort('timedout'));   // fallo de red
```

## 4. Modificar respuestas reales

```ts
await page.route('**/api/perfil', async route => {
  const response = await route.fetch();
  const json = await response.json();
  json.segmento = 'PREFERENCIAL';
  await route.fulfill({ response, json });
});
```

## 5. HAR

Grabar tráfico real una vez y reproducirlo (útil para frontends con muchas llamadas o backends inestables):
```ts
// grabar (ejecución puntual con update: true)
await page.routeFromHAR('hars/catalogo.har', { url: '**/api/**', update: true, updateContent: 'embed' });
// reproducir (ejecución normal)
await page.routeFromHAR('hars/catalogo.har', { url: '**/api/**', notFound: 'fallback' });
```
Revisa el HAR antes de versionarlo: contiene cookies, tokens y datos. En 1.60+ el tracing puede incluir HAR bajo demanda.

## 6. WebSocket

```ts
await page.routeWebSocket('wss://ejemplo.com/cotizaciones', ws => {
  ws.onMessage(msg => { if (msg === 'subscribe:USD') ws.send(JSON.stringify({ par: 'USD/COP', valor: 4100 })); });
});
```
O `ws.connectToServer()` para interceptar y modificar mensajes del servidor real.

## 7. Reloj

Determinismo en fechas, expiraciones y temporizadores:
```ts
await page.clock.install({ time: new Date('2026-12-31T23:59:00-05:00') });
await page.goto('/pagos-programados');
await expect(page.getByText('31 dic 2026')).toBeVisible();

// expiración de sesión por inactividad sin esperar 15 minutos reales
await page.clock.fastForward('15:01');
await expect(page.getByRole('dialog', { name: 'Tu sesión expiró' })).toBeVisible();

await page.clock.setFixedTime(new Date('2026-10-05T10:00:00'));   // Date.now() fijo, timers corren
await page.clock.pauseAt(new Date('2026-10-05T10:00:00')); await page.clock.runFor(2_000);
```
Fija también `timezoneId` y `locale` en la config para que formatos de fecha y moneda sean estables entre máquinas.

## 8. Otros

```ts
test.use({ geolocation: { latitude: 6.2442, longitude: -75.5812 }, permissions: ['geolocation'] });
await context.setOffline(true);           // modo sin conexión
await context.grantPermissions(['notifications'], { origin: 'https://app.ejemplo.com' });
```
