# 03 — Arquitectura del framework (Java)

## Contenido
1. Estructura
2. Configuración
3. DriverFactory (local, Grid, paralelo)
4. BaseTest con evidencia al fallar
5. Page objects sin PageFactory
6. Componentes reutilizables
7. Tests
8. Datos de prueba
9. Screenplay / roles (alternativa para suites grandes)

---

## 1. Estructura

```
ui-tests/
├── pom.xml
├── Linea_Base_<Proyecto>.md
└── src/test/
    ├── java/co/empresa/qa/
    │   ├── config/Config.java            # ambientes, navegador, timeouts (System props > env > properties)
    │   ├── driver/DriverFactory.java     # crea/cierra WebDriver por hilo
    │   ├── support/BaseTest.java          # ciclo de vida + evidencia en fallos
    │   ├── support/Esperas.java           # condiciones propias
    │   ├── pages/LoginPage.java
    │   ├── pages/TransferenciaPage.java
    │   ├── pages/components/MenuPrincipal.java
    │   ├── api/                           # clientes para setup/limpieza de datos
    │   └── tests/transferencias/TransferenciaTest.java
    └── resources/
        ├── config/qa.properties           # URLs por ambiente (sin secretos)
        └── junit-platform.properties      # paralelismo (06)
```

## 2. Configuración

Orden de precedencia: `-Dpropiedad` > variable de entorno > `config/<env>.properties` > default.
```java
public final class Config {
  private static final Properties P = cargar(System.getProperty("env", System.getenv().getOrDefault("TEST_ENV", "qa")));

  public static String baseUrl()   { return valor("baseUrl", "BASE_URL", null); }
  public static String browser()   { return valor("browser", "BROWSER", "chrome"); }
  public static boolean headless() { return Boolean.parseBoolean(valor("headless", "HEADLESS", "true")); }
  public static String gridUrl()   { return valor("gridUrl", "GRID_URL", null); }   // null = local
  public static Duration espera()  { return Duration.ofSeconds(Long.parseLong(valor("esperaSeg", "ESPERA_SEG", "10"))); }

  /** Secretos: SOLO de variables de entorno. */
  public static String secreto(String env) {
    String v = System.getenv(env);
    if (v == null || v.isBlank()) throw new IllegalStateException("Falta la variable de entorno " + env);
    return v;
  }
  // ... valor(prop, env, def) y cargar(env) leen System props, env y el .properties del classpath
}
```

## 3. DriverFactory

```java
public final class DriverFactory {
  private static final ThreadLocal<WebDriver> DRIVER = new ThreadLocal<>();

  public static WebDriver iniciar() {
    MutableCapabilities opciones = switch (Config.browser()) {
      case "firefox" -> { var o = new FirefoxOptions(); if (Config.headless()) o.addArguments("-headless"); yield o; }
      case "edge"    -> { var o = new EdgeOptions(); if (Config.headless()) o.addArguments("--headless=new"); yield o; }
      default        -> { var o = new ChromeOptions(); if (Config.headless()) o.addArguments("--headless=new");
                          o.addArguments("--window-size=1920,1080"); yield o; }
    };
    WebDriver driver = Config.gridUrl() == null
        ? switch (Config.browser()) {
            case "firefox" -> new FirefoxDriver((FirefoxOptions) opciones);
            case "edge"    -> new EdgeDriver((EdgeOptions) opciones);
            default        -> new ChromeDriver((ChromeOptions) opciones);
          }
        : new RemoteWebDriver(URI.create(Config.gridUrl()).toURL(), opciones);   // toURL() lanza excepción verificada: envolver
    driver.manage().timeouts().implicitlyWait(Duration.ZERO);
    driver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(30));
    DRIVER.set(driver);
    return driver;
  }

  public static WebDriver actual() {
    WebDriver d = DRIVER.get();
    if (d == null) throw new IllegalStateException("No hay WebDriver iniciado en este hilo");
    return d;
  }

  public static void cerrar() {
    WebDriver d = DRIVER.get();
    if (d != null) { try { d.quit(); } finally { DRIVER.remove(); } }    // remove() evita fugas entre tests del mismo hilo
  }
}
```
- **Un driver por test** (no compartido entre tests): aislamiento de cookies/sesión. Reutilizar el navegador entre tests ahorra segundos y cuesta horas de depuración.
- `ThreadLocal` permite ejecución paralela; `remove()` es obligatorio.
- `RemoteWebDriver` + `RemoteWebDriver.builder()` para Grid/nube (06).

## 4. BaseTest

JUnit 5 — extensión que captura evidencia **antes** de cerrar el driver:
```java
public class EvidenciaExtension implements TestWatcher, AfterEachCallback {
  @Override public void testFailed(ExtensionContext ctx, Throwable causa) {
    WebDriver d = DriverFactory.actual();
    String nombre = ctx.getRequiredTestClass().getSimpleName() + "_" + ctx.getRequiredTestMethod().getName();
    Path dir = Path.of("target", "evidencia");
    // Files.createDirectories + escribir screenshot (OutputType.BYTES), page source y URL actual
  }
  @Override public void afterEach(ExtensionContext ctx) { /* nada: el cierre lo hace BaseTest */ }
}
```
Orden importante en JUnit 5: `TestWatcher.testFailed` se ejecuta **después** de `@AfterEach`, cuando el driver ya está cerrado. Patrón probado en la plantilla (`templates/java-junit5`, `EvidenciaAlFallar`):
- `TestExecutionExceptionHandler` captura evidencia en el momento del fallo del test y relanza la excepción.
- **`LifecycleMethodExecutionExceptionHandler`** hace lo mismo para fallos en `@BeforeEach`. `TestExecutionExceptionHandler` **no** se invoca para métodos de ciclo de vida: sin esto, un login que falla en el `@BeforeEach` no deja evidencia (validado al construir la skill: 0 de 12 fallos con evidencia antes de la corrección, 12 de 12 después).
- `@AfterEach` cierra el driver.

```java
@ExtendWith(EvidenciaAlFallar.class)
public abstract class BaseTest {
  protected WebDriver driver;
  @BeforeEach void abrirNavegador() { driver = DriverFactory.iniciar(); }
  @AfterEach  void cerrarNavegador() { DriverFactory.cerrar(); }
}
```
TestNG: `ITestListener.onTestFailure` (se ejecuta antes de `@AfterMethod`), registrado con `@Listeners`.

## 5. Page objects

**Sin `PageFactory`/`@FindBy`**: los proxies perezosos de PageFactory ocultan cuándo se busca el elemento, favorecen `StaleElementReferenceException` y el propio equipo de Selenium desaconseja su uso. Usa campos `By` y búsqueda en el momento.

```java
public class TransferenciaPage {
  private static final By CUENTA_DESTINO = By.id("cuentaDestino");
  private static final By MONTO = By.cssSelector("input[name='monto']");
  private static final By CONTINUAR = By.xpath("//button[normalize-space()='Continuar']");
  private static final By CONFIRMAR = By.xpath("//button[normalize-space()='Confirmar transferencia']");
  private static final By MENSAJE = By.cssSelector("[role='alert']");

  private final WebDriver driver;
  private final WebDriverWait wait;

  public TransferenciaPage(WebDriver driver) {
    this.driver = driver;
    this.wait = new WebDriverWait(driver, Config.espera());
  }

  public TransferenciaPage abrir() {
    driver.get(Config.baseUrl() + "/transferencias/nueva");
    wait.until(ExpectedConditions.visibilityOfElementLocated(CUENTA_DESTINO));
    return this;
  }

  /** Intención del usuario: diligencia, continúa y confirma. Espera el resultado y lo devuelve. */
  public String transferir(String cuenta, String monto) {
    escribir(CUENTA_DESTINO, cuenta);
    escribir(MONTO, monto);
    driver.findElement(CONTINUAR).click();
    wait.until(ExpectedConditions.elementToBeClickable(CONFIRMAR)).click();
    return mensaje();
  }

  public String mensaje() {
    return wait.until(Esperas.textoNoVacio(MENSAJE));    // espera a que el mensaje tenga contenido
  }

  private void escribir(By campo, String valor) {
    WebElement e = wait.until(ExpectedConditions.elementToBeClickable(campo));
    e.clear();
    e.sendKeys(valor);
  }
}
```
Reglas:
- Métodos = intenciones (`transferir`), no micro-pasos (`clickBotonConfirmar`), salvo cuando el test necesita controlar el paso intermedio.
- Cada método espera el estado que produce (devuelve la página siguiente o el dato resultante).
- **Sin aserciones en los page objects** (salvo verificar que la página cargó); las aserciones van en el test.
- Nada de `driver.findElement` en los tests: todo pasa por page objects.
- Sin herencia profunda (`BasePage` delgada como mucho: driver, wait, helpers de escritura).

## 6. Componentes

Partes repetidas (menú, tabla, selector de cuenta, modal) como clases que reciben un `WebElement` raíz o un `By` de contenedor:
```java
public class TablaMovimientos {
  private final WebDriver driver;
  public TablaMovimientos(WebDriver driver) { this.driver = driver; }
  public Optional<List<String>> filaPorReferencia(String ref) {
    List<WebElement> filas = driver.findElements(By.xpath("//tbody/tr[td[normalize-space()='" + ref + "']]"));
    return filas.stream().findFirst().map(f -> f.findElements(By.tagName("td")).stream().map(WebElement::getText).toList());
  }
}
```

## 7. Tests

```java
class TransferenciaTest extends BaseTest {
  @Test
  @Tag("smoke")
  @DisplayName("[HU-245][CA-1] transfiere con saldo suficiente")
  void transfiereConSaldoSuficiente() {
    new LoginPage(driver).abrir().ingresar(Config.secreto("E2E_USER"), Config.secreto("E2E_PASSWORD"));
    String mensaje = new TransferenciaPage(driver).abrir().transferir("00998877665", "150000");
    assertThat(mensaje).matches("Transferencia exitosa\\. Referencia REF-[0-9A-F]{6}");
  }

  @ParameterizedTest(name = "[HU-245][CA-2] rechaza {0}")
  @CsvSource({
    "monto cero,           00998877665, 0,    El monto debe ser mayor a cero",
    "cuenta de 10 dígitos, 1234567890,  1000, La cuenta destino debe tener 11 dígitos",
  })
  void rechazaDatosInvalidos(String caso, String cuenta, String monto, String error) { /* ... */ }
}
```
AssertJ (`assertThat`) da mensajes de fallo más claros que `assertEquals`; `SoftAssertions` para validar varios campos de una pantalla en un solo test.

## 8. Datos de prueba

- Crear datos por API en el setup y limpiarlos en el teardown (clientes en `api/`, con `java.net.http.HttpClient` o RestAssured).
- Valores únicos por test (`UUID`, timestamp + hilo) para soportar paralelismo.
- Evitar el login por UI en cada test cuando no es lo que se prueba: obtener la sesión por API e inyectar la cookie (`driver.manage().addCookie(...)` tras navegar al dominio), conservando al menos un test de login por UI.
- Nunca datos reales de clientes.

## 9. Screenplay / roles

Para suites grandes con muchos actores (cliente, asesor, aprobador), el patrón **Screenplay** (Actor → Tarea → Interacción → Pregunta) o una capa de **roles/tareas** sobre los page objects mejora la legibilidad: `analista.realiza(CrearSolicitud.conMonto(100))`. Serenity BDD lo implementa de fábrica (ver 12). Para suites pequeñas o medianas, POM bien hecho es suficiente: no agregues capas sin necesidad.
