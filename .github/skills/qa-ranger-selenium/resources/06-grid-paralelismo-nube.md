# 06 — Paralelismo, Grid y nube

## Contenido
1. Requisitos para paralelizar
2. JUnit 5
3. TestNG
4. Selenium Grid 4
5. docker-selenium (CI)
6. Nubes (BrowserStack, Sauce Labs, TestMu/LambdaTest)
7. Dimensionamiento

---

## 1. Requisitos

Paralelizar sin estos requisitos convierte una suite estable en una inestable:
- Un `WebDriver` por test/hilo (`ThreadLocal`, 03 §3), nunca `static WebDriver`.
- Datos propios por test (usuarios/cuentas distintos o creados por API).
- Nada de estado estático mutable en page objects o utilidades.

## 2. JUnit 5

`src/test/resources/junit-platform.properties`:
```properties
junit.jupiter.execution.parallel.enabled=true
junit.jupiter.execution.parallel.mode.default=concurrent
junit.jupiter.execution.parallel.mode.classes.default=concurrent
junit.jupiter.execution.parallel.config.strategy=fixed
junit.jupiter.execution.parallel.config.fixed.parallelism=4
```
Tests que tocan un recurso compartido: `@ResourceLock("configuracion-cuenta")` o `@Execution(ExecutionMode.SAME_THREAD)`.

## 3. TestNG

```xml
<suite name="Regresion" parallel="methods" thread-count="4" data-provider-thread-count="4">
  <test name="UI">
    <groups><run><include name="smoke"/></run></groups>
    <packages><package name="co.empresa.qa.tests.*"/></packages>
  </test>
</suite>
```
`parallel="classes"` es más seguro si hay estado por clase; `methods` da más paralelismo.

## 4. Grid 4

Modos:
- **Standalone** (un proceso, para pruebas locales de Grid): `java -jar selenium-server-4.50.0.jar standalone`.
- **Hub + Nodes**: `hub` en una máquina, `node --hub http://hub:4444` en cada nodo.
- **Distribuido** (router, distributor, session map, queue) para escala grande.
- **Dinámico** con Docker/Kubernetes: un contenedor por sesión, con video por sesión.

Conexión:
```java
WebDriver driver = RemoteWebDriver.builder()
    .oneOf(new ChromeOptions().addArguments("--headless=new"))
    .address(URI.create(Config.gridUrl()))
    .build();
```
Útil: `options.setCapability("se:name", nombreDelTest)` (aparece en la UI del Grid y en el video), `options.setEnableDownloads(true)`, `LocalFileDetector` para subir archivos (04).

## 5. docker-selenium

`docker-compose.yml` mínimo para CI:
```yaml
services:
  chrome:
    image: selenium/standalone-chrome:latest     # fijar la etiqueta exacta (versión de navegador + Selenium) en CI
    shm_size: 2gb
    ports: ["4444:4444", "7900:7900"]            # 7900: noVNC para ver la sesión (contraseña por defecto 'secret')
    environment:
      - SE_NODE_MAX_SESSIONS=4
      - SE_NODE_OVERRIDE_MAX_SESSIONS=true
```
Esperar a que el Grid esté listo antes de correr las pruebas:
```bash
until curl -sf http://localhost:4444/status | grep -q '"ready": true'; do sleep 2; done
mvn test -DgridUrl=http://localhost:4444 -Dbrowser=chrome
```
Si la app bajo prueba corre en el host, el navegador del contenedor la alcanza con `host.docker.internal` (agregar `extra_hosts: ["host.docker.internal:host-gateway"]` en Linux).

## 6. Nubes

Todas aceptan W3C capabilities con un bloque propio. Ejemplo genérico:
```java
ChromeOptions o = new ChromeOptions();
o.setPlatformName("Windows 11");
o.setBrowserVersion("latest");
o.setCapability("bstack:options", Map.of(          // BrowserStack; Sauce: "sauce:options"; TestMu/LambdaTest: "LT:Options"
    "projectName", "Banca Web",
    "buildName", System.getenv().getOrDefault("BUILD_ID", "local"),
    "sessionName", nombreDelTest));
WebDriver driver = new RemoteWebDriver(URI.create(System.getenv("CLOUD_GRID_URL")).toURL(), o);
```
- Credenciales en la URL o en el bloque de opciones, **siempre desde variables de entorno**.
- Reporta el estado del test al proveedor al finalizar (cada uno tiene su script/endpoint) para que el tablero refleje pasa/falla.
- Apps internas: túnel del proveedor (BrowserStack Local, Sauce Connect, LambdaTest Tunnel) aprobado por seguridad.
- TestMu AI (antes LambdaTest) ofrece además "agent skills" para Selenium; las reglas de esta skill aplican igual al código que generen.

## 7. Dimensionamiento

- Hilos ≈ sesiones disponibles en el Grid; más hilos que sesiones solo encola.
- Chrome headless ≈ 1 CPU y 1–2 GB por sesión; empieza con 4 y mide.
- Si la duración no baja al subir hilos, el cuello de botella es la app o el ambiente, no la suite.
