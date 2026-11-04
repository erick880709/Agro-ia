# 05 — BiDi y CDP

## Contenido
1. Qué es y cuándo usarlo
2. Habilitar
3. Consola y errores JavaScript
4. Red: interceptar, bloquear, autenticación básica
5. Python
6. CDP: solo como último recurso

---

## 1. Qué y cuándo

**WebDriver BiDi** es el protocolo bidireccional estándar (W3C) que Selenium 4 usa para escuchar eventos del navegador: consola, errores JS, red. Reemplaza al uso directo de **CDP** (Chrome DevTools Protocol), que solo funciona en navegadores Chromium y está atado a la versión exacta del navegador (cada release de Selenium soporta solo 3 versiones de CDP).

Usos en pruebas:
- Fallar el test si la página lanza errores JavaScript no controlados.
- Adjuntar los logs de consola a la evidencia de un fallo.
- Simular errores del backend o bloquear servicios de terceros (analítica, chat).
- Autenticación HTTP básica sin poner credenciales en la URL.

La API de BiDi sigue evolucionando: **verifica los nombres en la versión del proyecto** (javadoc de `org.openqa.selenium.bidi.module` / `help(driver.network)` en Python). Lo de abajo está verificado en 4.50.

## 2. Habilitar

```java
ChromeOptions o = new ChromeOptions();
o.enableBiDi();                                  // también FirefoxOptions / EdgeOptions
```
Python: `options.enable_bidi = True`.
En Grid: el nodo debe tener BiDi habilitado (docker-selenium lo soporta); la URL de WebSocket se negocia automáticamente.

## 3. Consola y errores JS (Java)

```java
try (LogInspector inspector = new LogInspector(driver)) {
  List<String> errores = new CopyOnWriteArrayList<>();
  inspector.onJavaScriptException(e -> errores.add(e.getText()));
  inspector.onConsoleEntry(e -> { if (e.getLevel() == LogLevel.ERROR) errores.add(e.getText()); });

  driver.get(Config.baseUrl() + "/transferencias/nueva");
  // ... flujo
  assertThat(errores).as("errores JavaScript en la página").isEmpty();
}
```
Patrón recomendado: registrar el `LogInspector` en el `BaseTest` y adjuntar lo capturado a la evidencia si el test falla.

## 4. Red (Java)

```java
try (Network network = new Network(driver)) {
  // bloquear un servicio de terceros
  network.addIntercept(new AddInterceptParameters(InterceptPhase.BEFORE_REQUEST_SENT));
  network.onBeforeRequestSent(evento -> {
    String url = evento.getRequest().getUrl();
    if (url.contains("analytics")) network.failRequest(evento.getRequest().getRequestId());
    else network.continueRequest(new ContinueRequestParameters(evento.getRequest().getRequestId()));
  });
  driver.get(Config.baseUrl());
}
```
Autenticación básica (API de alto nivel, Chromium):
```java
((HasAuthentication) driver).register(() -> new UsernameAndPassword(Config.secreto("BASIC_USER"), Config.secreto("BASIC_PASS")));
```
Para **respuestas simuladas completas** de un backend (devolver un JSON de error), Selenium es menos cómodo que Playwright: considera un mock de servidor (WireMock, Karate mock — skill `qa-ranger-karate`) configurado en el ambiente de pruebas.

## 5. Python

```python
options = webdriver.ChromeOptions()
options.enable_bidi = True
driver = webdriver.Chrome(options=options)

mensajes = []
driver.script.add_console_message_handler(mensajes.append)
errores = []
driver.script.add_javascript_error_handler(errores.append)

driver.network.add_auth_handler(os.environ["BASIC_USER"], os.environ["BASIC_PASS"])
```
Otros: `driver.network.add_request_handler(...)`, `driver.browsing_context`, `driver.storage`, `driver.emulation` (verificar firmas con `help()`).

## 6. CDP

`((HasDevTools) driver).getDevTools()` con el paquete `org.openqa.selenium.devtools.vNNN` correspondiente a la versión del navegador. Úsalo solo para capacidades sin equivalente BiDi y acepta que se rompe con cada actualización de Chrome. Nunca en tests que deban correr en Firefox o Safari.
