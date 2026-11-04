# 02 — Localizadores y esperas

## Contenido
1. Jerarquía de localizadores
2. XPath y CSS bien escritos
3. Localizadores relativos
4. Shadow DOM
5. Esperas: reglas
6. WebDriverWait y ExpectedConditions
7. FluentWait y condiciones propias
8. StaleElementReferenceException

---

## 1. Jerarquía

1. `By.id("monto")` — si es estable (no autogenerado como `ember123`, `mat-input-7`).
2. Atributo de prueba acordado con desarrollo: `By.cssSelector("[data-testid='btn-confirmar']")`.
3. `By.name("cuentaDestino")` en formularios.
4. CSS semántico: `By.cssSelector("form#transferencia button[type='submit']")`.
5. XPath por **texto visible o etiqueta** cuando no hay alternativa: `//button[normalize-space()='Confirmar']`, `//label[normalize-space()='Monto']/following::input[1]` o, mejor, `//input[@id=//label[normalize-space()='Monto']/@for]`.
6. **Nunca**: XPath absoluto (`/html/body/div[2]/...`), índices posicionales (`(//div)[7]`), clases de CSS-in-JS (`.css-1x2y3z`, `.sc-bdVaJa`), `By.linkText` con textos que cambian por idioma sin justificación.

Si la app no tiene identificadores estables, pide a desarrollo `data-testid` (acuerdo barato que elimina gran parte del mantenimiento) y registra la decisión en la Línea Base.

## 2. XPath y CSS

| Necesidad | CSS | XPath |
|---|---|---|
| Atributo exacto | `input[name='monto']` | `//input[@name='monto']` |
| Atributo parcial | `[class*='alerta']`, `[id^='fila-']` | `contains(@class,'alerta')` |
| Por texto | — (CSS no puede) | `//button[normalize-space()='Pagar']` |
| Hijo directo | `ul > li` | `//ul/li` |
| Fila que contiene un texto | — | `//tr[td[normalize-space()='REF-001']]` |
| Ancestro | — | `./ancestor::tr` |

Prefiere CSS por velocidad y legibilidad; XPath cuando necesites texto o navegar hacia arriba. `normalize-space()` evita fallos por espacios.

Elementos dentro de un contenedor (evita ambigüedad):
```java
WebElement fila = driver.findElement(By.xpath("//tr[td[normalize-space()='" + referencia + "']]"));
fila.findElement(By.cssSelector("button.eliminar")).click();
```
Cuidado con comillas en datos dinámicos dentro de XPath; si el texto puede contener `'`, usa `concat()` o localiza por otro atributo.

## 3. Relativos

```java
import static org.openqa.selenium.support.locators.RelativeLocator.with;

WebElement monto = driver.findElement(with(By.tagName("input")).below(By.xpath("//label[normalize-space()='Monto']")));
WebElement cancelar = driver.findElement(with(By.tagName("button")).toLeftOf(By.id("confirmar")));
```
`above`, `below`, `toLeftOf`, `toRightOf`, `near`. Útiles en formularios sin `label for`; dependen del layout (frágiles con responsive). Desde 4.50 se pueden anclar en elementos y shadow roots.

## 4. Shadow DOM

```java
SearchContext raiz = driver.findElement(By.cssSelector("banco-selector-cuenta")).getShadowRoot();
raiz.findElement(By.cssSelector("input[name='cuenta']")).sendKeys("00998877665");
```
Dentro de un shadow root solo funciona CSS (no XPath). Shadow roots anidados: encadenar `getShadowRoot()`.

## 5. Reglas de espera

1. `implicitlyWait` **en 0**. Mezclar implícitas y explícitas produce tiempos impredecibles (se suman o se bloquean entre sí).
2. **Esperas explícitas** antes de interactuar con algo que depende de una acción asíncrona.
3. **Nunca** `Thread.sleep` / `time.sleep` como sincronización.
4. Espera la **condición de negocio** (el mensaje de éxito, la fila en la tabla), no un proxy (un spinner que a veces no aparece).
5. Timeouts como constantes con nombre y justificación.

## 6. WebDriverWait

```java
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
WebElement boton = wait.until(ExpectedConditions.elementToBeClickable(By.id("confirmar")));
wait.until(ExpectedConditions.invisibilityOfElementLocated(By.id("cargando")));
wait.until(ExpectedConditions.textToBePresentInElementLocated(By.cssSelector("[role='alert']"), "Transferencia exitosa"));
wait.until(ExpectedConditions.urlContains("/comprobante"));
wait.until(ExpectedConditions.numberOfElementsToBe(By.cssSelector("tbody tr"), 10));
wait.until(ExpectedConditions.frameToBeAvailableAndSwitchToIt(By.id("pasarela")));
wait.until(ExpectedConditions.alertIsPresent());
wait.until(ExpectedConditions.stalenessOf(elementoAnterior));   // la página se recargó
```
Python:
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "confirmar"))).click()
```

Esperar y luego afirmar: la espera **es** la sincronización; la aserción valida el contenido.
```java
String texto = wait.until(ExpectedConditions.visibilityOfElementLocated(MENSAJE)).getText();
assertThat(texto).isEqualTo("Saldo insuficiente");
```
Si el texto cambia de vacío a lleno, espera el texto (`textToBePresentInElementLocated` o una lambda), no solo la visibilidad.

## 7. FluentWait y condiciones propias

```java
Wait<WebDriver> wait = new FluentWait<>(driver)
    .withTimeout(Duration.ofSeconds(30))
    .pollingEvery(Duration.ofMillis(500))
    .ignoring(NoSuchElementException.class, StaleElementReferenceException.class)
    .withMessage("el estado de la transferencia nunca llegó a APLICADA");

String estado = wait.until(d -> {
  String t = d.findElement(By.cssSelector("[data-testid='estado']")).getText();
  return t.equals("APLICADA") ? t : null;          // null/false = seguir esperando
});
```
Condición reutilizable:
```java
public static ExpectedCondition<Boolean> textoNoVacio(By locator) {
  return d -> !d.findElement(locator).getText().isBlank();
}
```

## 8. StaleElementReferenceException

Ocurre cuando el elemento guardado ya no está en el DOM (re-render de frameworks SPA, recarga, paginación).
- Guarda **`By`**, no `WebElement`, en los page objects; vuelve a buscar el elemento al usarlo.
- Tras una acción que re-renderiza, espera el nuevo estado (`stalenessOf` + `visibilityOf...`).
- No envuelvas en `try/catch` con reintento ciego: oculta problemas de sincronización. `FluentWait.ignoring(StaleElementReferenceException.class)` es aceptable dentro de una espera con condición clara.
