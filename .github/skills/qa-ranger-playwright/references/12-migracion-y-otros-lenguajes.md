# 12 — Migración y otros lenguajes

## Contenido
1. Desde Selenium / WebDriver (incluye Serenity BDD)
2. Desde Cypress
3. Actualizar versiones de Playwright
4. Playwright en Java
5. Playwright en Python

---

## 1. Desde Selenium

| Selenium | Playwright |
|---|---|
| `driver.findElement(By.xpath(...))` | `page.getByRole(...)` (rediseñar el locator, no traducirlo) |
| `WebDriverWait` + `ExpectedConditions` | Auto-wait de acciones + aserciones web-first |
| `Thread.sleep` | Eliminar; sincronizar por condición |
| `driver.switchTo().frame(...)` | `page.frameLocator(...)` |
| `driver.switchTo().window(...)` | `page.waitForEvent('popup')` / `context.pages()` |
| Grid para paralelismo | Workers locales y `--shard` en CI |
| Login por UI en cada clase | `storageState` |
| Page Factory (`@FindBy`) | Page object con locators `readonly` |

Estrategia: no migrar 1:1. Inventaria los flujos por valor de negocio, migra primero los `@smoke`, ejecuta ambas suites en paralelo un tiempo y retira la antigua por módulo. Aprovecha la migración para eliminar duplicados y tests que no aportan.

**Serenity BDD / Screenplay** (frecuente en banca): el valor está en los reportes y la trazabilidad con Gherkin. Equivalente en Playwright: títulos con IDs de HU, `test.step` legibles, anotaciones `req` y el reporte HTML + RTM (09 §6). Si el equipo exige Gherkin, existe `playwright-bdd` (terceros), pero evalúa si el costo de mantener `.feature` + steps compensa.

## 2. Desde Cypress

| Cypress | Playwright |
|---|---|
| `cy.get('[data-cy=x]')` | `page.getByTestId('x')` con `testIdAttribute: 'data-cy'` |
| `cy.contains('Guardar')` | `page.getByText('Guardar')` / `getByRole(..., { name })` |
| Encadenamiento implícito y asíncrono | `async/await` explícito |
| `cy.intercept` | `page.route` |
| `cy.session` | `storageState` |
| `cy.wait('@alias')` | `page.waitForResponse(...)` creado antes de la acción |
| `cy.clock` | `page.clock` |
| Un solo dominio/pestaña por test | Multi-pestaña, multi-origen y multi-contexto nativos |
| `beforeEach` con `cy.visit` | Fixtures + `goto` |

## 3. Actualizar Playwright

1. Lee las notas de versión desde la versión actual hasta la destino (`docs/src/release-notes-js.md` del repo o el sitio oficial), sección **Breaking Changes**.
2. `npm i -D @playwright/test@<versión> && npx playwright install --with-deps`.
3. Actualiza la imagen Docker de CI a la misma versión.
4. Ejecuta la suite completa; si hay pruebas visuales, espera diferencias por el nuevo navegador: revisa y regenera baselines en un PR aparte.
5. Si usas Test Agents, regenera las definiciones (`npx playwright init-agents`).
6. Adopta APIs nuevas en PRs separados (p. ej. `:visible` → `.visible()`, `mode: 'serial'` → `lock`).

Cambios relevantes recientes: ver tabla de 01 §7.

## 4. Java

```xml
<dependency>
  <groupId>com.microsoft.playwright</groupId>
  <artifactId>playwright</artifactId>
  <version>1.63.0</version>   <!-- alinear con la versión vigente -->
  <scope>test</scope>
</dependency>
```
```java
import com.microsoft.playwright.*;
import com.microsoft.playwright.junit.UsePlaywright;
import org.junit.jupiter.api.Test;
import static com.microsoft.playwright.assertions.PlaywrightAssertions.assertThat;
import com.microsoft.playwright.options.AriaRole;

@UsePlaywright
class TransferenciasTest {
  @Test
  void transfiereConSaldoSuficiente(Page page) {
    page.navigate(System.getenv("BASE_URL") + "/transferencias/nueva");
    page.getByLabel("Monto").fill("150000");
    page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName("Continuar")).click();
    assertThat(page.getByRole(AriaRole.ALERT)).hasText("Transferencia exitosa");
  }
}
```
- Misma filosofía de locators y aserciones web-first (`assertThat(...)`).
- Sin el test runner de Node: no hay fixtures, proyectos, sharding, reporter HTML ni Trace CLI integrados; el paralelismo y los reportes vienen de JUnit/Maven/Gradle (Allure, Surefire). Tracing manual con `context.tracing().start/stop` y `mvn exec:java -e -D exec.mainClass=com.microsoft.playwright.CLI -D exec.args="show-trace trace.zip"`.
- Recomendación: si el equipo puede trabajar en TypeScript para E2E, la experiencia (runner, reportes, agentes) es superior. Si la suite debe vivir en un repositorio Java, Playwright Java es una opción sólida.

## 5. Python

```bash
pip install pytest-playwright && playwright install --with-deps chromium
```
```python
import re
from playwright.sync_api import Page, expect

def test_transfiere_con_saldo_suficiente(page: Page):
    page.goto("/transferencias/nueva")          # base_url con --base-url o en pytest.ini
    page.get_by_label("Monto").fill("150000")
    page.get_by_role("button", name="Continuar").click()
    expect(page.get_by_role("alert")).to_have_text("Transferencia exitosa")
```
`pytest --base-url https://qa.app.ejemplo.com --browser chromium --tracing retain-on-failure -n 4` (con `pytest-xdist`). Fixtures de pytest en lugar de `test.extend`.
