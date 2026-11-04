# 08 — Flakiness y depuración

## Contenido
1. Método de diagnóstico (no adivinar)
2. Trace CLI (1.59+): analizar trace.zip desde la terminal
3. Depuración interactiva: `--debug=cli`, UI mode, inspector
4. Causas de flakiness y su corrección
5. Reintentos, cuarentena y medición
6. Índice de errores frecuentes

---

## 1. Método

1. **Reproducir**: `npx playwright test ruta.spec.ts:LINEA --repeat-each=20 --workers=4`. Si solo falla en paralelo, el problema es aislamiento; si falla en solitario, es sincronización o datos.
2. **Obtener evidencia**: trace del fallo (`trace: 'retain-on-failure'` o `'retain-on-failure-and-retries'` para comparar el intento que pasó con el que falló).
3. **Leer el trace** (§2): acción fallida, snapshot DOM en ese momento, requests fallidas, errores de consola.
4. **Clasificar la causa** (§4) y corregir la causa, no el síntoma.
5. **Verificar** con `--repeat-each` de nuevo.

Nunca: subir timeouts globales, agregar `waitForTimeout`, agregar `force: true` o reintentos sin entender la causa.

## 2. Trace CLI

```bash
npx playwright trace open test-results/<carpeta-del-test>/trace.zip   # metadatos: navegador, viewport, duración, errores
npx playwright trace actions --errors-only                            # qué acción falló (con ID)
npx playwright trace action <id>                                      # parámetros, logs de espera, ubicación en el código
npx playwright trace snapshot <id>                                    # snapshot de accesibilidad del DOM en ese momento
npx playwright trace snapshot <id> --phase before                     # antes de la acción
npx playwright trace snapshot <id> -- eval "document.querySelector('[role=alert]')?.textContent"
npx playwright trace snapshot <id> -- screenshot --filename=fallo.png
npx playwright trace requests --failed                                # requests con status >= 400
npx playwright trace request <request-id>                             # headers y body
npx playwright trace console --errors-only
npx playwright trace errors
npx playwright trace close
```
El log de la acción muestra qué esperaba Playwright («waiting for getByRole('button', { name: 'Pagar' })… element is not enabled»): casi siempre revela la causa directamente.

**Ejemplo real** (validado al construir la skill): un test con `waitForTimeout(600)` + `expect(await alert.textContent())` fallaba 1 de cada 10 veces.
- `trace actions --errors-only` → la acción fallida era `Expect "toContain"`.
- `trace action 20` → `Received string: ""`: la alerta seguía vacía.
- `trace requests` → solo 2 peticiones; el `POST /api/transferencias` **aún no se había enviado**: la app tarda 400–1000 ms y la espera fija era de 600 ms.
- Corrección: `await expect(page.getByRole('alert')).toContainText('Transferencia exitosa')` → 30/30 en `--repeat-each=30 --workers=4`.

Visual: `npx playwright show-trace trace.zip` o el reporte HTML (`npx playwright show-report`).

## 3. Interactiva

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test ruta.spec.ts --debug=cli   # 1.59+: pausa y expone una sesión para playwright-cli
playwright-cli attach <sesion>                                           # explorar la página pausada (ver 10)
npx playwright test --ui                                                 # UI mode: watch, timeline, selector de locators
npx playwright test --debug                                              # inspector paso a paso
await page.pause();                                                      # punto de pausa en el código (quitar antes de commit)
```
Desde un agente: ejecuta `--debug=cli` en segundo plano, espera "Debugging Instructions", conéctate con `playwright-cli attach`, explora, corrige y detén el proceso.

## 4. Causas y correcciones

| Síntoma | Causa típica | Corrección |
|---|---|---|
| Falla «a veces» al hacer click | Overlay/spinner encima, animación, botón aún deshabilitado | Esperar a que desaparezca el overlay (`toBeHidden`), aserción `toBeEnabled` antes; nunca `force` |
| Aserción falla con el valor anterior | Aserción no web-first (`expect(await ...)`) | `await expect(locator).toHaveText(...)` |
| Pasa en local, falla en CI | CI más lento, otra zona horaria/locale, fuentes, resolución | `timezoneId`/`locale` en config, `expect.timeout` razonable, imagen Docker oficial |
| Solo falla en paralelo | Datos compartidos, misma cuenta modificada por varios tests, orden asumido | Datos únicos, cuenta por worker (04 §4), `lock` (1.63+) |
| Strict mode violation intermitente | Lista que se renderiza dos veces / duplicados transitorios | Acotar el locator; esperar el estado final (`toHaveCount`) |
| Navegación interrumpida | Redirecciones o recarga tras login | `await page.waitForURL(...)` tras la acción que navega |
| Respuesta llega después de la aserción | Carrera entre click y request | `waitForResponse` creado **antes** del click |
| Falla tras otro test | Estado del servidor que no se limpió | Limpieza en fixture, datos propios del test |
| Fechas/horas | Reloj real | `page.clock`, datos con fechas relativas controladas |
| Dependencia externa caída | Servicio de terceros real | Mock de ese servicio (06) |
| `Target page, context or browser has been closed` | Falta un `await`; el test terminó antes que la acción | ESLint `no-floating-promises`; revisar `await` |

## 5. Reintentos y cuarentena

- `retries: 2` en CI para no bloquear por ruido de infraestructura, pero **un test que solo pasa al reintento es flaky** y aparece como tal en el reporte: se trata como bug.
- `failOnFlakyTests: true` en pipelines estrictos (la ejecución falla si algún test fue flaky).
- `retryStrategy: 'isolated'` (1.62+): reintenta al final, de a uno, para no contaminar con la carga del resto de la suite.
- Cuarentena: `test.fixme()` con anotación del ticket, o tag `@cuarentena` excluido con `--grep-invert`; revisión semanal. Nunca borrar el test en silencio.
- Medir: tasa de flaky por test a partir del reporte JSON/JUnit histórico; priorizar los de mayor frecuencia.

## 6. Índice de errores

| Error | Significado | Acción |
|---|---|---|
| `strict mode violation: ... resolved to N elements` | Locator ambiguo | Acotar con filtros/contexto (02 §2) |
| `Timeout ... waiting for locator(...)` | Elemento nunca apareció/no fue accionable | Leer el log de la acción en el trace: ¿no existe, oculto, deshabilitado, otro texto? |
| `element is not visible` / `not enabled` / `intercepts pointer events` | Actionability | Esperar la condición real; buscar el overlay que intercepta |
| `expect(locator).toHaveText ... Received: ...` | Valor distinto tras reintentar | Verificar datos y si el texto cambió legítimamente |
| `net::ERR_CONNECTION_REFUSED` | App no levantada / `baseURL` errónea | `webServer`, variable `BASE_URL` |
| `browserType.launch: Executable doesn't exist` | Navegadores no instalados | `npx playwright install --with-deps` |
| `Test timeout of 30000ms exceeded` | El test completo excedió su tiempo | Ver qué acción consumió el tiempo en el trace; `test.slow()` solo si el flujo es legítimamente largo |
| `Error: page.goto: net::ERR_CERT_*` | Certificado no confiable en ambiente bajo | `ignoreHTTPSErrors: true` solo en ese proyecto/ambiente |
| `Cannot find module '@playwright/test'` en CI | Dependencias no instaladas o versión distinta | `npm ci`, versión fijada |
| Snapshot visual con diferencias mínimas | Entorno distinto al de la baseline | Generar y comparar en la misma imagen Docker |
