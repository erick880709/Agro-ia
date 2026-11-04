# 01 — Setup y versiones

## Contenido
1. Dependencias Java (Maven / Gradle)
2. Dependencias Python
3. Selenium Manager (drivers y navegadores)
4. Red corporativa: proxy, mirrors, sin internet
5. Opciones de navegador
6. Versiones y cambios recientes

---

## 1. Java

Selenium 4 requiere **Java 11+**; usa 17 o 21 (LTS).

```xml
<properties>
  <maven.compiler.release>17</maven.compiler.release>
  <selenium.version>4.50.0</selenium.version>
  <junit.version>5.13.4</junit.version>
  <assertj.version>3.27.3</assertj.version>
  <surefire.version>3.5.2</surefire.version>
</properties>
<dependencies>
  <dependency>
    <groupId>org.seleniumhq.selenium</groupId>
    <artifactId>selenium-java</artifactId>
    <version>${selenium.version}</version>
  </dependency>
  <dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>${junit.version}</version>
    <scope>test</scope>
  </dependency>
  <dependency>
    <groupId>org.assertj</groupId>
    <artifactId>assertj-core</artifactId>
    <version>${assertj.version}</version>
    <scope>test</scope>
  </dependency>
</dependencies>
```
- `selenium-java` incluye todos los drivers y `selenium-support` (esperas, `Select`, localizadores relativos). Para un solo navegador basta `selenium-chrome-driver` + `selenium-support`.
- TestNG: `org.testng:testng` en lugar de `junit-jupiter`.
- Gradle: `testImplementation("org.seleniumhq.selenium:selenium-java:4.50.0")` + `useJUnitPlatform()`.
- **No agregues WebDriverManager** (bonigarcia): Selenium Manager lo reemplaza (§3). Mantenerlo solo si una política corporativa lo exige.
- BOM opcional: `org.seleniumhq.selenium:selenium-bom` para alinear módulos.

Versiones verificadas al construir la skill: Selenium 4.50.0 (CDP 152–154). Confirma la última en Maven Central / PyPI.

## 2. Python

Python **3.10+**.
```bash
pip install "selenium==4.50.0" pytest pytest-xdist pytest-html
```
Fija versiones en `requirements.txt` (`selenium==4.50.0`).

## 3. Selenium Manager

Incluido en todos los bindings desde 4.6. Al crear `new ChromeDriver()` sin ruta de driver:
1. Detecta la versión del navegador instalado.
2. Descarga el driver compatible a `~/.cache/selenium` (si no está).
3. Si no hay navegador, puede descargar **Chrome for Testing** / Firefox / Edge.

```java
WebDriver driver = new ChromeDriver();           // nada más: ni setProperty ni WebDriverManager
ChromeOptions o = new ChromeOptions();
o.setBrowserVersion("stable");                   // o "beta", "dev", "153": Selenium Manager descarga esa versión
```
Variables útiles (equivalen a los flags `--offline`, `--proxy`, `--cache-path`, etc. del binario; verificado `SE_OFFLINE`): `SE_CACHE_PATH`, `SE_OFFLINE=true`, `SE_PROXY`, `SE_AVOID_BROWSER_DOWNLOAD=true`, `SE_DEBUG=true` (diagnóstico de resolución), `SE_DRIVER_MIRROR_URL` / `SE_BROWSER_MIRROR_URL`.

Ruta explícita (solo si la política lo exige o no hay red):
```java
ChromeDriverService svc = new ChromeDriverService.Builder()
    .usingDriverExecutable(new File(System.getenv("CHROMEDRIVER_PATH"))).build();
WebDriver driver = new ChromeDriver(svc, options);
```
Python: `Service(executable_path=os.environ["CHROMEDRIVER_PATH"])`.

## 4. Red corporativa

- **Proxy para descargas de drivers**: `SE_PROXY=http://proxy.corp:8080`.
- **Mirror interno** (Artifactory/Nexus): `SE_DRIVER_MIRROR_URL`, `SE_BROWSER_MIRROR_URL`.
- **Sin internet**: preinstala navegador y driver en la imagen del agente o usa docker-selenium (06); `SE_OFFLINE=true`.
- **Proxy para el tráfico del navegador** (distinto del anterior):
```java
Proxy p = new Proxy().setHttpProxy("proxy.corp:8080").setSslProxy("proxy.corp:8080").setNoProxy("*.corp.local");
options.setProxy(p);
```
- Certificados internos: importarlos en el sistema/imagen; `options.setAcceptInsecureCerts(true)` solo en ambientes bajos.

## 5. Opciones de navegador

```java
ChromeOptions o = new ChromeOptions();
o.addArguments("--headless=new", "--window-size=1920,1080");   // tamaño fijo: layouts deterministas
o.addArguments("--lang=es-CO");
o.setPageLoadStrategy(PageLoadStrategy.NORMAL);               // EAGER solo con justificación
o.setExperimentalOption("prefs", Map.of(
    "download.default_directory", descargas.toAbsolutePath().toString(),
    "credentials_enable_service", false,
    "profile.password_manager_enabled", false));
o.enableBiDi();                                                // para red/consola (05)
```
- Linux/CI sin `/dev/shm` grande: `--disable-dev-shm-usage` (o `--shm-size=2g` en Docker).
- `--no-sandbox` solo en contenedores que lo requieren, nunca en estaciones de trabajo.
- Edge con modo IE (aplicaciones heredadas): `InternetExplorerOptions` + `attachToEdgeChrome()` en Windows.

Timeouts del driver:
```java
driver.manage().timeouts().implicitlyWait(Duration.ZERO);           // siempre 0 (ver 02)
driver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(30));
driver.manage().timeouts().scriptTimeout(Duration.ofSeconds(10));
```

## 6. Versiones

| Versión | Cambios relevantes |
|---|---|
| 4.6 | Selenium Manager incluido |
| 4.11 | Selenium Manager descarga Chrome for Testing |
| 4.x recientes | BiDi (`LogInspector`, `Network`, `Script`) como vía estándar para red/consola; CDP queda atado a versiones concretas del navegador |
| 4.37 | Python 3.14 soportado; **se retira Python 3.9** |
| 4.47 | Corrección de escapado en `By.className()`/`By.id()`; elimina soporte de proxy FTP |
| 4.49 | Selenium Manager para Linux arm64; elimina endpoint antiguo de descarga de archivos de Grid |
| 4.50 | CDP 152–154; localizadores relativos desde elementos y shadow roots; elimina métodos deprecados de `HttpClient` y del perfil de Firefox |


Selenium 3 → 4: ver 12.
