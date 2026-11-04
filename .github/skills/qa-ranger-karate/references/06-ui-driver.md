# 06 — Automatización UI (driver)

## Contenido
1. Configuración del driver
2. Localizadores
3. Acciones y lecturas
4. Esperas (la causa #1 de pruebas inestables)
5. Page objects en Karate
6. Pruebas híbridas API + UI
7. Ejecución en contenedor / grid / nube
8. Intercept y mocks de red (CDP)
9. Diferencias v1 → v2 en UI

---

## 1. Configuración

```javascript
// karate-config.js
karate.configure('driver', { type: 'chrome', headless: karate.env != 'local' });
```
| `type` | Backend |
|---|---|
| `chrome` | CDP (DevTools) — recomendado; más rápido y con intercept |
| `chromedriver`, `geckodriver`, `msedgedriver`, `safaridriver` | W3C WebDriver |
| `chrome` con `start: false` + `webDriverUrl` / remoto | Grid, Selenoid, BrowserStack, Sauce, LambdaTest (W3C) |

v2 hace pooling automático de navegadores según `parallel(n)`. En v1, la UI se suele correr con `parallel(1)` o con el contenedor `karate-chrome`.

## 2. Localizadores

| Forma | Ejemplo |
|---|---|
| CSS | `'#usuario'`, `'button[type=submit]'`, `'[data-testid=btn-pagar]'` |
| XPath | `'//button[text()="Pagar"]'` |
| Texto exacto (wildcard) | `'{button}Pagar'`, `'{a}Cerrar sesión'` |
| Texto parcial | `'{^button}Pag'`, `'{^}Total a pagar'` |
| Índice | `'{div:2}Detalle'` |
| Amigables (relativos) | `rightOf('{}Monto').input('300')`, `below('{}Cuenta').click()`, `near(...)`, `leftOf(...)`, `above(...)` |

Orden de preferencia: `data-testid` (acordado con desarrollo) > id estable > texto visible > CSS estructural > XPath posicional. Pide a desarrollo atributos `data-testid` en lugar de pelear con selectores frágiles.

## 3. Acciones y lecturas

```gherkin
* driver baseUrlWeb + '/login'
* input('#usuario', usuario)
* input('#clave', [clave, Key.ENTER])
* click('{button}Ingresar')
* select('#tipoDocumento', 'CC')                # por texto; '{}CC' o '#valor' según variante
* inputFile('#adjunto', 'classpath:data/soporte.pdf')
* def saldo = text('[data-testid=saldo]')
* match saldo == '$ 1.500.000'
* match driver.title == 'Inicio'
* match driver.url contains '/inicio'
* match attribute('#btnPagar', 'disabled') == null
* assert exists('{}Bienvenido')
* screenshot()                                  # se adjunta al reporte
* switchFrame('#iframePago')
* switchFrame(null)
* switchPage('Comprobante')                     # pestaña por título o url parcial
* dialog(true)                                   # acepta alert/confirm
* def filas = locateAll('table#movimientos tbody tr')
* match filas.length == 10
* def celda = locate('//td[text()="REF-001"]').closest('tr').locate('td.estado')   # v2
* match celda.text == 'APLICADO'
```

## 4. Esperas

Karate **no** espera implícitamente en todas las acciones. Usa siempre esperas explícitas basadas en condición:

```gherkin
* waitFor('#dashboard')
* waitForUrl('/inicio')
* waitForText('#estado', 'APROBADO')
* waitForEnabled('#btnPagar').click()
* waitForAny('#exito', '#error')
* waitForResultCount('table tbody tr', 10)
* waitUntil("document.readyState == 'complete'")
* waitUntil('#spinner', '!_.offsetParent')       # hasta que el spinner no sea visible
* retry(5, 1000).click('#btnConfirmar')           # reintenta la acción
* configure retry = { count: 10, interval: 1000 } # aplica a waitFor*/retry()
```
Prohibido `delay(5000)` como sincronización; solo para depuración. `karate.pause(ms)` si no hay driver activo.

## 5. Page objects en Karate

En lugar de clases, usa **features `@ignore` por flujo** y **archivos JS de localizadores**:

`pages/locators.json`
```json
{ "login": { "usuario": "#usuario", "clave": "#clave", "ingresar": "{button}Ingresar" } }
```
`pages/login.feature`
```gherkin
@ignore
Feature: flujo de login
  Scenario:
    * def L = read('classpath:pages/locators.json').login
    * driver baseUrlWeb + '/login'
    * input(L.usuario, usuario)
    * input(L.clave, clave)
    * click(L.ingresar)
    * waitForUrl('/inicio')
```
Feature de prueba:
```gherkin
Scenario: transferencia entre cuentas propias
  * call read('classpath:pages/login.feature') { usuario: '#(usuarioQa)', clave: '#(claveQa)' }
  # el driver creado en el call se propaga al llamador (shared scope)
  * click('{a}Transferir')
```

## 6. Híbridas API + UI (alto valor, bajo costo)

Prepara datos por API (rápido, estable), valida en UI solo lo que es UI, y verifica el efecto final por API:
```gherkin
Scenario: pago visible en historial
  # arrange por API
  * def pago = call read('classpath:common/crear-pago.feature') { monto: 50000 }
  # act/assert en UI
  * call read('classpath:pages/login.feature') { usuario: '#(usuarioQa)', clave: '#(claveQa)' }
  * click('{a}Historial')
  * waitForText('table#pagos', pago.referencia)
  # verificación de backend
  * url baseUrl
  * path 'pagos', pago.id
  * method get
  * status 200
```
Otra táctica: inyectar la sesión (cookie/token obtenido por API) para saltar el login en UI en todas las pruebas excepto las del login mismo.

## 7. Contenedor / grid

- v2 + Testcontainers: `chromedp/headless-shell` y un `DriverProvider` que conecta por CDP (`ContainerDriverProvider` en `karate-todo`). Pasa `serverUrl` (visto desde el contenedor, p. ej. `host.docker.internal`) y `apiUrl` (visto desde el host) por separado.
- WebDriver remoto (Selenium Grid / nube):
```javascript
karate.configure('driver', {
  type: 'chromedriver', start: false,
  webDriverUrl: 'https://hub.ejemplo.com/wd/hub',
  webDriverSession: { capabilities: { alwaysMatch: { browserName: 'chrome', 'goog:chromeOptions': { args: ['--headless=new'] } } } }
});
```

## 8. Intercept (solo CDP)

```gherkin
* driver.intercept({ patterns: [{ urlPattern: '*/api/riesgo/*' }], mock: 'classpath:mocks/riesgo-mock.feature' })
* driver baseUrlWeb
```
Permite virtualizar llamadas del frontend a backends sin tocar el ambiente.

## 9. v1 → v2 en UI

- La sintaxis Gherkin del driver es compatible.
- Eliminados: `element.parent`, `.children`, `.firstChild`, `.nextSibling`, etc. → `closest(selector)`, `locate`/`locateAll` con alcance, o `element.script('_.nextElementSibling.id')`.
- `delay()` requiere driver activo; sin driver usa `karate.pause()`.
- API Java del driver rediseñada (`DriverProvider` reemplaza `Target`).
- `showDriverLog` no tiene efecto aún en v2.
- `karate-robot` (desktop Windows) no existe en v2.
