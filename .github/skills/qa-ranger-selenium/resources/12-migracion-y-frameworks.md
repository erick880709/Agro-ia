# 12 — Migración y frameworks

## 1. Selenium 3 → 4
| Selenium 3 | Selenium 4 |
|---|---|
| `driver.findElementById("x")` / `find_element_by_id` | `driver.findElement(By.id("x"))` / `find_element(By.ID, "x")` |
| `new WebDriverWait(driver, 10)` (segundos `long`) | `new WebDriverWait(driver, Duration.ofSeconds(10))` |
| `implicitlyWait(10, TimeUnit.SECONDS)` | `implicitlyWait(Duration.ofSeconds(..))` (y mejor 0) |
| `DesiredCapabilities.chrome()` | `new ChromeOptions()` |
| `System.setProperty("webdriver.chrome.driver", ...)` / WebDriverManager | Selenium Manager (nada) |
| `new RemoteWebDriver(url, DesiredCapabilities)` | `new RemoteWebDriver(url, options)` / `RemoteWebDriver.builder()` |
| `getAttribute` para todo | `getDomProperty` / `getDomAttribute` |
| `executable_path=` (Python) | `Service(executable_path)` |
| `--headless` | `--headless=new` |
| Grid 3 (hub/node JSON) | Grid 4 (standalone, hub/node, distribuido, dinámico) |
| CDP vía `DevTools` | BiDi (05) |

Procedimiento: actualizar dependencias → compilar y corregir errores → buscar deprecaciones (`-Xlint:deprecation`) → quitar `Thread.sleep` y esperas implícitas en el camino → correr la suite completa y comparar resultados.

## 2. Serenity BDD
Frecuente en banca (reportes "documentación viva", Screenplay, integración con Cucumber/JUnit). Si el proyecto usa Serenity:
- Respeta su estructura: `Actor`, `Task`, `Interaction`, `Question`, `Target` (en lugar de `By` sueltos), `@Steps` / `@Managed WebDriver`.
- Esperas: Serenity tiene esperas propias (`WaitUntil.the(...)`, timeouts configurables en `serenity.conf`); no mezcles `Thread.sleep`.
- Configuración de navegador en `serenity.conf` (`webdriver.driver`, `headless.mode`, `webdriver.remote.url`).
- Las reglas de localizadores, independencia y datos de esta skill aplican igual.

## 3. Cucumber
- Steps delgados que llaman a page objects/tareas; sin lógica de Selenium en los step definitions.
- Un `Scenario Outline` por familia de validaciones.
- Tags de Cucumber para smoke/regresión e IDs de HU (`@HU-245`).
- Estado compartido entre steps con inyección de dependencias (PicoContainer/Spring), nunca `static`.

## 4. Selenide
Wrapper sobre Selenium con esperas automáticas (`$("#monto").shouldBe(visible)`). Si el proyecto lo usa, sigue su estilo (no mezclar `WebDriverWait` manuales con `should*`).

## 5. ¿Cuándo migrar a Playwright?
Señales: alta tasa de flakiness pese a buenas prácticas, depuración costosa, suite nueva en TypeScript, necesidad fuerte de mocking de red. Señales para quedarse: Grid/nube ya contratados, equipo Java consolidado con Serenity, Safari real o IE mode, gran inversión existente. Si se decide migrar: por módulos, priorizando flujos críticos, ejecutando ambas suites en paralelo un tiempo (skill `qa-ranger-playwright`, recurso 12).
