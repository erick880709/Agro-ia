# 11 — Revisión y antipatrones

## Contenido
1. Reglas P1–P25
2. Lo que el linter no ve (revisión manual)
3. Revisión de configuración
4. Checklist de PR
5. Formato del reporte de revisión

---

## 1. Reglas

`L` = detectada por `scripts/lint_specs.py`; `M` = revisión manual.

| # | Antipatrón | Sev. | Det. | Corrección |
|---|---|---|---|---|
| P1 | `page.waitForTimeout(n)` | Mayor | L | Aserción web-first / `waitForURL` / `waitForResponse` |
| P2 | `expect(await x.isVisible()/textContent()/...)` (aserción sin reintento) | Mayor | L | `await expect(locator).toBeVisible()/toHaveText()` |
| P3 | `expect(locator).toBe...` sin `await` (la aserción nunca se evalúa) | **Bloqueante** | L | Agregar `await`; ESLint `no-floating-promises` |
| P4 | Acción sin `await` (`page.click(...)` suelto) | **Bloqueante** | L | Agregar `await` |
| P5 | `waitForLoadState('networkidle')` | Mayor | L | Esperar el elemento o respuesta concreta |
| P6 | `{ force: true }` | Mayor | L | Esperar la condición real |
| P7 | XPath o CSS estructural (`nth-child`, `>` encadenados, clases generadas) | Mayor | L | `getByRole`/`getByLabel`/`getByTestId` |
| P8 | `.first()`/`.nth()`/`.last()` para esquivar strict mode | Menor | L (aviso) | Acotar con `filter`/contexto |
| P9 | API legacy: `page.$`, `$$`, `elementHandle`, `page.click('sel')`, `waitForSelector` | Mayor | L | Locators |
| P10 | `test.only` / `describe.only` | **Bloqueante** | L | Quitar; `forbidOnly` en CI |
| P11 | URL absoluta en `goto` | Mayor | L | `baseURL` + rutas relativas |
| P12 | Secretos en el código (claves, tokens, passwords literales) | **Bloqueante** | L | Variables de entorno / vault |
| P13 | Test sin ninguna aserción | **Bloqueante** | L | Aserción del resultado esperado |
| P14 | `page.pause()` olvidado | **Bloqueante** | L | Quitar |
| P15 | `test.describe.serial` / `mode: 'serial'` | Menor | L (aviso) | Tests independientes o un test con `test.step`; `lock` (1.63+) si es contención |
| P16 | Login por UI en `beforeEach` | Mayor | L | Proyecto `setup` + `storageState` (04) |
| P17 | `:visible` en selectores | Menor | L | `.visible()` (1.63+) |
| P18 | APIs eliminadas (`videosPath`, `videoSize`, `ariaRef`) | Mayor | L | `recordVideo`, `ariaSnapshot` |
| P19 | `try/catch` o `.catch(() => {})` alrededor de aserciones/acciones | Mayor | L | Dejar fallar; si el elemento es opcional, controlar los datos |
| P20 | `if (await locator.isVisible())` ramificando el test | Mayor | L | Estado determinista; dos tests |
| P21 | Tests dependientes del orden / estado compartido entre tests (variables de módulo mutadas) | **Bloqueante** | M (L detecta `let` a nivel de módulo) | Fixtures y datos propios |
| P22 | Datos fijos que colisionan en paralelo (mismo correo/documento) | Mayor | M | Datos únicos por test/worker |
| P23 | Aserciones de detalles de implementación (clases CSS, estado interno) | Menor | M | Comportamiento observable |
| P24 | Page objects con aserciones de negocio ocultas o micro-métodos | Menor | M | Métodos de intención; aserciones en el test |
| P25 | Título genérico o duplicado («test 1», «should work») | Menor | L | Comportamiento esperado + ID de requisito |

## 2. Revisión manual

El linter cubre lo mecánico. Revisa además:
- **Cobertura**: ¿validaciones, errores del backend, permisos, estados vacíos? ¿un test por comportamiento?
- **Aislamiento**: ¿cada test crea y limpia sus datos? ¿pasa con `--repeat-each=5 --workers=4`?
- **Mocks**: ¿se mockea el propio backend en un test que dice ser E2E?
- **Legibilidad**: ¿un analista entiende qué valida cada test leyendo el título y los `test.step`?
- **Esperas implícitas**: ¿hay `waitForResponse` creado después de la acción (carrera)?
- **Datos sensibles**: ¿capturas sin `mask`, `console.log` de tokens, datos reales?

## 3. Configuración

- `forbidOnly: !!process.env.CI`, `retries` 2 en CI y 0 local, `trace` en reintento o fallo, `screenshot: 'only-on-failure'`.
- `baseURL` definido; `timezoneId`/`locale` fijados.
- Reporter JUnit/blob en CI; HTML con `open: 'never'`.
- Timeouts globales razonables (sospecha de cualquier `timeout` > 60 s por test sin justificación).
- `playwright/.auth`, `.env`, reportes y resultados en `.gitignore`.
- Versión de `@playwright/test` fijada y coherente con la imagen Docker de CI.

## 4. Checklist de PR

- [ ] `lint_specs.py` sin bloqueantes ni mayores.
- [ ] `tsc --noEmit` y ESLint (`no-floating-promises`, `eslint-plugin-playwright`) limpios.
- [ ] Pasa con `--repeat-each=5` en paralelo.
- [ ] Locators accesibles y verificados contra la app.
- [ ] Datos propios y limpieza.
- [ ] Títulos con comportamiento y trazabilidad; tags según la taxonomía.
- [ ] Sin secretos ni datos reales; capturas enmascaradas.
- [ ] Línea Base actualizada si cambió config, ambientes o convenciones.

## 5. Formato del reporte

```markdown
## Revisión Playwright — <alcance>
Resumen: X bloqueantes, Y mayores, Z menores. <veredicto en una frase>

### Bloqueantes
1. **[P3] tests/pagos.spec.ts:42** — la aserción no tiene `await`; el test pasa aunque el mensaje no aparezca.
   ```ts
   await expect(page.getByRole('alert')).toHaveText('Pago exitoso');
   ```
### Mayores
...
### Menores
...
### Cobertura faltante
- Sin casos de error del backend (503/timeout) en el flujo de pagos.
```
Siempre con la corrección concreta en código.
