# 07 — Regresión visual y accesibilidad

## Contenido
1. `toHaveScreenshot`: uso y estabilidad
2. Gestión de imágenes base (baselines)
3. Accesibilidad con axe-core
4. Aria snapshots como prueba estructural
5. Navegación por teclado

---

## 1. `toHaveScreenshot`

```ts
test('[UI] tarjeta de saldo — diseño estable', async ({ page }) => {
  await page.goto('/inicio');
  await expect(page.getByTestId('tarjeta-saldo')).toHaveScreenshot('tarjeta-saldo.png', {
    mask: [page.getByTestId('saldo-valor'), page.getByText(/Último acceso/)],   // datos dinámicos o sensibles
    maxDiffPixelRatio: 0.01,
    animations: 'disabled',
  });
});
```
Reglas para que no sea flaky:
- Capturar **componentes**, no páginas enteras con contenido variable.
- Enmascarar fechas, saldos, nombres, publicidad y cualquier dato personal (también por privacidad).
- Datos controlados (mocks o datos semilla), `clock` fijo, fuentes instaladas en la imagen de CI.
- Generar y comparar **en el mismo entorno**: las baselines dependen de SO, navegador y fuentes. Usa la imagen Docker oficial `mcr.microsoft.com/playwright:v1.63.0-noble` tanto para generar como en CI.
- `stylePath` para ocultar elementos con CSS durante la captura.
- 1.62+: baselines WebP (`'tarjeta.webp'`) ocupan menos en el repo.

## 2. Baselines

```bash
npx playwright test --grep @visual --update-snapshots          # regenerar tras un cambio de diseño aprobado
npx playwright test --update-snapshots=changed                  # solo las que cambiaron
```
- Las baselines se versionan junto a las specs (`*-snapshots/`); el PR que las cambia debe mostrar el diff visual al revisor (el reporte HTML lo muestra).
- `snapshotPathTemplate` en la config para ordenarlas por proyecto/plataforma.
- Ejecuta las pruebas visuales como un proyecto o tag separado (`@visual`): son más lentas y sensibles.

## 3. axe-core

```bash
npm i -D @axe-core/playwright
```
```ts
import AxeBuilder from '@axe-core/playwright';

test('[A11Y] formulario de transferencia sin violaciones WCAG 2.1 AA', async ({ page }) => {
  await page.goto('/transferencias/nueva');
  await expect(page.getByRole('form')).toBeVisible();
  const resultado = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .include('main')
    .exclude('#widget-chat-terceros')          // componentes que el equipo no controla, documentados
    .analyze();
  expect(resultado.violations.map(v => `${v.id}: ${v.nodes.length} nodo(s)`)).toEqual([]);
});
```
- Mapear el mensaje a `id` + cantidad deja el fallo legible; adjunta el detalle completo con `testInfo.attach('axe', { body: JSON.stringify(resultado.violations, null, 2), contentType: 'application/json' })`.
- Escanear **estados**, no solo la carga inicial: modal abierto, errores de validación visibles, menú desplegado.
- Deuda conocida: `.disableRules([...])` con un ticket asociado, nunca para silenciar sin registro.
- axe detecta ~30–50 % de los problemas: complementa con teclado (§5) y revisión manual.

## 4. Aria snapshots

Ver 02 §8. Útiles para fijar la estructura accesible (roles, nombres, jerarquía) de regiones clave; fallan si un botón pierde su nombre accesible aunque visualmente nada cambie.

## 5. Teclado

```ts
test('[A11Y] el flujo de pago se completa solo con teclado', async ({ page }) => {
  await page.goto('/pagos/nuevo');
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Convenio')).toBeFocused();
  await page.keyboard.type('Energía');
  await page.keyboard.press('Tab');
  await expect(page.getByLabel('Referencia')).toBeFocused();
  // ...
  await page.keyboard.press('Enter');
  await expect(page.getByRole('alert')).toBeVisible();
});
```
Verifica también: foco visible, foco atrapado en modales y devuelto al cerrarlos, `Escape` cierra diálogos.
