# 10 — Revisión y antipatrones

`L` = detectada por `scripts/lint_selenium.py` (Java y Python); `M` = revisión manual.

| # | Antipatrón | Sev. | Det. | Corrección |
|---|---|---|---|---|
| S1 | `Thread.sleep` / `time.sleep` | Mayor | L | Espera explícita por condición |
| S2 | `implicitlyWait` > 0 (sobre todo combinado con explícitas) | Mayor | L | `implicitlyWait(Duration.ZERO)` + `WebDriverWait` |
| S3 | XPath absoluto o con índices posicionales | Mayor | L | id / data-testid / CSS semántico / XPath por texto |
| S4 | Clases generadas (`css-1x2y3`, `sc-…`, `jss12`, `ng-tns-…`) | Mayor | L | Atributos estables |
| S5 | `PageFactory` / `@FindBy` | Menor | L | Campos `By` (03 §5) |
| S6 | `static WebDriver` / driver compartido | **Bloqueante** | L | Driver por test, `ThreadLocal` |
| S7 | Falta `quit()` (solo `close()` o nada) | Mayor | L (aviso) | `quit()` en teardown |
| S8 | Clic/escritura con `executeScript` | Mayor | L | Esperar interactuabilidad; resolver el overlay |
| S9 | Secretos literales en el código | **Bloqueante** | L | Variables de entorno / vault |
| S10 | URL absoluta en `driver.get` | Mayor | L | Base URL desde configuración |
| S11 | API de Selenium 3 (`findElementBy*`, `DesiredCapabilities`, `new WebDriverWait(driver, 10)` con long, `find_element_by_*`) | **Bloqueante** | L | API Selenium 4 (12 §1) |
| S12 | `System.setProperty("webdriver.chrome.driver", …)` / WebDriverManager sin necesidad | Menor | L | Selenium Manager |
| S13 | `catch (Exception e) {}` / `except: pass` que traga fallos | Mayor | L | Dejar fallar o manejar con intención |
| S14 | Test sin aserción | **Bloqueante** | L | Aserción del resultado esperado |
| S15 | `assertTrue(x.equals(y))` / `assert x == y` sin mensaje | Menor | L | `assertThat(x).isEqualTo(y)` / mensaje |
| S16 | `driver.findElement` dentro de clases de test | Menor | L | Encapsular en page objects |
| S17 | Aserciones dentro de page objects | Menor | L (aviso) | Mover al test |
| S18 | `isDisplayed()` inmediatamente después de una acción, sin espera | Mayor | M | `visibilityOfElementLocated` |
| S19 | Orden de ejecución requerido (`@Order`, `dependsOnMethods`, `priority`) | Mayor | L | Tests independientes |
| S20 | `@Disabled`/`enabled=false`/`@pytest.mark.skip` sin motivo | Menor | L | Motivo + ticket |
| S21 | Reintentos (`rerunFailingTestsCount`, `IRetryAnalyzer`, `@flaky`) ocultando inestabilidad | Mayor | M | Investigar la causa (07) |
| S22 | Datos fijos que colisionan en paralelo | Mayor | M | Datos únicos por test |
| S23 | Login por UI en cada test cuando no es lo probado | Menor | M | Sesión por API + cookie |
| S24 | Page objects con micro-métodos o herencia profunda | Menor | M | Métodos de intención, composición |
| S25 | Nombres genéricos (`test1`, `testLogin2`) sin trazabilidad | Menor | L | `@DisplayName("[HU-x][CA-y] ...")` |

## Revisión manual
- ¿Cada test es independiente y pasa en paralelo (07 §1)?
- ¿Las esperas esperan la condición de negocio correcta?
- ¿La capa es la adecuada? (validaciones combinatorias → API, 09 §5)
- ¿Evidencia en fallos sin datos sensibles?
- ¿Configuración por ambiente sin secretos en el repo?

## Checklist de PR
- [ ] `lint_selenium.py` sin bloqueantes ni mayores.
- [ ] Compila sin warnings de APIs deprecadas.
- [ ] Ejecutado contra la app; repetido en paralelo sin fallos.
- [ ] Localizadores estables y verificados contra el DOM real.
- [ ] Nombres con trazabilidad; tags/grupos según convención.
- [ ] Línea Base actualizada si cambió configuración, ambientes o convenciones.

## Formato del reporte
```markdown
## Revisión Selenium — <alcance>
Resumen: X bloqueantes, Y mayores, Z menores. <veredicto>

### Bloqueantes
1. **[S6] DriverManager.java:12** — `static WebDriver driver` compartido: con ejecución paralela los tests se pisan la sesión.
   ```java
   private static final ThreadLocal<WebDriver> DRIVER = new ThreadLocal<>();
   ```
### Mayores / Menores / Cobertura faltante
```
Siempre con el código corregido.
