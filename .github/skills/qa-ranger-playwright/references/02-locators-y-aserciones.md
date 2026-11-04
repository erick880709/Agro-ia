# 02 — Locators y aserciones

## Contenido
1. Escalera de locators
2. Strict mode y cómo desambiguar
3. Filtros, encadenamiento y listas
4. Frames, shadow DOM, visibilidad
5. Acciones: lo que Playwright ya espera por ti
6. Aserciones web-first
7. Soft, poll, toPass
8. Aria snapshots
9. Tabla de reemplazos (malo → bueno)

---

## 1. Escalera

Usa el primer nivel que identifique el elemento de forma única y estable:

1. `page.getByRole('button', { name: 'Transferir' })` — cómo lo percibe un usuario y un lector de pantalla. Opciones: `exact`, `checked`, `expanded`, `level` (headings), `description` (1.60+), `includeHidden`.
2. `page.getByLabel('Número de cuenta')` — campos de formulario con `<label>` o `aria-label`.
3. `page.getByPlaceholder('correo@ejemplo.com')`.
4. `page.getByText('Saldo disponible')` — contenido no interactivo; `{ exact: true }` o regex para precisión.
5. `page.getByAltText(...)`, `page.getByTitle(...)`.
6. `page.getByTestId('btn-confirmar')` — contrato explícito con desarrollo cuando lo anterior es ambiguo (íconos, listas repetidas, textos dinámicos o multi-idioma).
7. CSS **semántico** (`'form#transferencia'`) solo como último recurso. **Nunca** XPath ni CSS estructural (`div > div:nth-child(3)`).

Si la app no es accesible (botones sin nombre, inputs sin label), eso es un hallazgo de accesibilidad: repórtalo y pide `data-testid` o la corrección en vez de escribir selectores frágiles.

Para encontrar el locator correcto: `npx playwright codegen <url>`, el selector de locators de UI mode o `playwright-cli generate-locator <ref>` (ver 10).

## 2. Strict mode

Toda acción sobre un locator que resuelve a más de un elemento **falla** («strict mode violation»). Es una protección, no un estorbo. Corrígelo acotando el locator, no con `.first()`:
```ts
// ❌ esconde ambigüedad
await page.getByRole('button', { name: 'Eliminar' }).first().click();
// ✅ acota por contexto
const fila = page.getByRole('row').filter({ hasText: 'REF-00123' });
await fila.getByRole('button', { name: 'Eliminar' }).click();
```
`.first()`/`.nth()` son válidos solo cuando el orden **es** el comportamiento probado («el primer resultado es el más reciente»).

## 3. Filtros, encadenamiento y listas

```ts
const tarjeta = page.getByTestId('tarjeta-producto')
  .filter({ hasText: 'Cuenta de ahorros' })
  .filter({ has: page.getByRole('button', { name: 'Activar' }) });
await tarjeta.getByRole('button', { name: 'Activar' }).click();

page.getByRole('listitem').filter({ hasNotText: 'Inactivo' });
page.getByRole('button').and(page.getByTitle('Descargar'));       // ambos criterios
page.getByRole('button', { name: 'Nuevo' }).or(page.getByRole('button', { name: 'Crear' }));

// listas: aserción sobre el conjunto, no bucles con índices
await expect(page.getByRole('row')).toHaveCount(11);              // encabezado + 10
await expect(page.getByRole('cell', { name: /REF-/ })).toHaveText([/REF-001/, /REF-002/]);
for (const fila of await page.getByRole('row').all()) { /* solo tras asegurar la carga con una aserción */ }
```

## 4. Frames, shadow DOM, visibilidad

```ts
await page.frameLocator('#pasarela').getByLabel('Número de tarjeta').fill('4111111111111111');
await page.frameLocator().getByRole('button', { name: 'Pagar' }).click();   // 1.63+: busca en cualquier frame
await page.locator('button').visible().click();                             // 1.63+: reemplaza ':visible'
```
- El shadow DOM abierto se atraviesa automáticamente con todos los locators (excepto XPath).
- Popups y pestañas nuevas: `const popupPromise = page.waitForEvent('popup'); await click; const popup = await popupPromise;`.
- Diálogos nativos: `page.once('dialog', d => d.accept())` **antes** de la acción que los abre.
- Descargas: `const dl = page.waitForEvent('download'); await click; const file = await dl; await file.saveAs(...)`.

## 5. Acciones

`click`, `fill`, `check`, `selectOption`, `setInputFiles`, `press`, `hover`, `dragTo` esperan automáticamente a que el elemento sea **visible, estable, habilitado y reciba eventos** (actionability). Por eso:
- No pongas `waitForSelector` antes de un `click`.
- No uses `{ force: true }` para "arreglar" un click: oculta overlays, spinners o elementos deshabilitados que son bugs reales o condiciones que falta esperar.
- `fill` reemplaza el valor; `pressSequentially` solo cuando la app reacciona a cada tecla (autocompletar).
- `selectOption({ label: 'Cédula' })` por texto visible, no por `value` interno, salvo que el valor sea el contrato.

## 6. Aserciones web-first

Reintentan hasta cumplirse o agotar `expect.timeout`. **Siempre con `await`**.

| Locator | Página / respuesta |
|---|---|
| `toBeVisible`, `toBeHidden`, `toBeAttached` | `toHaveURL(/\/inicio/)` |
| `toBeEnabled`, `toBeDisabled`, `toBeEditable` | `toHaveTitle('...')` |
| `toBeChecked`, `toBeFocused`, `toBeInViewport` | `expect(response).toBeOK()` |
| `toHaveText` (exacto/regex/array), `toContainText` | `toHaveScreenshot()` (ver 07) |
| `toHaveValue`, `toHaveValues`, `toHaveAttribute` | `toMatchAriaSnapshot()` |
| `toHaveCount`, `toHaveClass`, `toHaveCSS`, `toHaveId` | |
| `toHaveAccessibleName`, `toHaveAccessibleDescription`, `toHaveRole` | |

```ts
await expect(page.getByRole('alert')).toHaveText('Transferencia exitosa');
await expect(page.getByLabel('Monto')).toHaveValue('150000');
await expect(page.getByRole('button', { name: 'Confirmar' })).toBeDisabled();
await expect(page).toHaveURL(/\/comprobante\/\w+/);
await expect(page.getByText('Cargando')).toBeHidden();          // esperar fin de carga
await expect(page.getByRole('alert'), 'el banco debe confirmar la operación').toBeVisible();  // mensaje propio
```
Las aserciones genéricas (`expect(valor).toBe(...)`) **no reintentan**: úsalas solo con valores ya resueltos (cuerpo de una respuesta API, cálculos).

## 7. Soft, poll, toPass

```ts
// soft: continúa tras el fallo y reporta todos al final (formularios con muchos campos)
await expect.soft(page.getByLabel('Nombre')).toHaveValue('Ana');
await expect.soft(page.getByLabel('Ciudad')).toHaveValue('Medellín');

// poll: reintenta una función asíncrona (backend eventual, colas)
await expect.poll(async () => (await request.get(`/api/pagos/${id}`)).json().then(p => p.estado),
  { intervals: [1_000, 2_000, 5_000], timeout: 30_000 }).toBe('APLICADO');

// toPass: reintenta un bloque completo (último recurso; preferir poll o aserciones directas)
await expect(async () => {
  await page.getByRole('button', { name: 'Actualizar' }).click();
  await expect(page.getByText('APLICADO')).toBeVisible({ timeout: 1_000 });
}).toPass({ timeout: 20_000 });
```
Nunca bucles `while` con `waitForTimeout` para hacer polling a mano.

## 8. Aria snapshots

Validan la estructura accesible de una región completa en una sola aserción, resistentes a cambios de CSS:
```ts
await expect(page.getByRole('navigation')).toMatchAriaSnapshot(`
  - navigation:
    - link "Inicio"
    - link "Transferencias"
    - link /Pagos.*/
`);
```
Generación: `npx playwright test --update-snapshots` con `toMatchAriaSnapshot({ name: 'menu.aria.yml' })`, o copiarlo desde el trace viewer / `playwright-cli snapshot`. Útiles para menús, formularios y páginas de resultados; no para contenido muy dinámico.

## 9. Reemplazos

| ❌ | ✅ |
|---|---|
| `await page.waitForTimeout(3000)` | `await expect(locator).toBeVisible()` / `waitForURL` / `waitForResponse` |
| `expect(await el.isVisible()).toBe(true)` | `await expect(el).toBeVisible()` |
| `expect(await el.textContent()).toBe('x')` | `await expect(el).toHaveText('x')` |
| `await page.waitForLoadState('networkidle')` | Esperar el elemento o la respuesta concreta |
| `page.$('.btn')`, `page.$$`, `elementHandle` | `page.locator()` / `getBy*` |
| `page.click('text=Guardar')` (API de strings) | `page.getByRole('button', { name: 'Guardar' }).click()` |
| `locator('xpath=//div[2]/span')` | `getByRole` / `getByTestId` |
| `locator('button:visible')` | `locator('button').visible()` (1.63+) |
| `click({ force: true })` | Esperar la condición real (overlay oculto, botón habilitado) |
| `.first()` para evitar strict mode | Acotar con `filter` o contexto |
| `if (await el.isVisible()) { ... }` | Determinar el estado con datos controlados; un test no debe ramificarse según la UI |
