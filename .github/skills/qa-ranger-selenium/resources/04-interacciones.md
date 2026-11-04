# 04 — Interacciones complejas

## Frames
```java
wait.until(ExpectedConditions.frameToBeAvailableAndSwitchToIt(By.id("pasarela")));
driver.findElement(By.name("numeroTarjeta")).sendKeys("4111111111111111");
driver.switchTo().defaultContent();          // volver SIEMPRE al documento principal
```
Frames anidados: `switchTo().frame(...)` sucesivos; `parentFrame()` sube un nivel.

## Ventanas y pestañas
```java
String original = driver.getWindowHandle();
driver.findElement(By.linkText("Ver comprobante")).click();
wait.until(ExpectedConditions.numberOfWindowsToBe(2));
for (String h : driver.getWindowHandles()) if (!h.equals(original)) driver.switchTo().window(h);
// ... validar
driver.close();
driver.switchTo().window(original);

driver.switchTo().newWindow(WindowType.TAB);   // abrir pestaña nueva (Selenium 4)
```

## Alertas nativas
```java
Alert alerta = wait.until(ExpectedConditions.alertIsPresent());
assertThat(alerta.getText()).contains("¿Confirmas");
alerta.accept();      // o dismiss(); sendKeys() para prompt
```

## Selects
```java
Select tipo = new Select(driver.findElement(By.id("tipoDocumento")));
tipo.selectByVisibleText("Cédula de ciudadanía");    // por texto visible (lo que ve el usuario)
assertThat(tipo.getFirstSelectedOption().getText()).isEqualTo("Cédula de ciudadanía");
```
Los "selects" de librerías (Angular Material, React Select) **no** son `<select>`: clic en el disparador, espera la lista (`[role='listbox']`) y clic en la opción (`[role='option']` con el texto).

## Actions (teclado y mouse)
```java
new Actions(driver).moveToElement(menu).pause(Duration.ofMillis(200)).click(submenu).perform();
new Actions(driver).dragAndDrop(origen, destino).perform();
new Actions(driver).keyDown(Keys.CONTROL).sendKeys("a").keyUp(Keys.CONTROL).sendKeys(Keys.DELETE).perform();
new Actions(driver).scrollToElement(elemento).perform();
```
`.pause()` dentro de una cadena de Actions es aceptable para gestos (hover que abre un menú); no es un sustituto de esperas.

## Archivos
Subir (con `<input type="file">`, aunque esté oculto detrás de un botón estilizado):
```java
driver.findElement(By.cssSelector("input[type='file']")).sendKeys(Path.of("src/test/resources/datos/soporte.pdf").toAbsolutePath().toString());
```
En Grid remoto: `((RemoteWebDriver) driver).setFileDetector(new LocalFileDetector());` para que el archivo viaje al nodo.

Descargar:
- Local: `download.default_directory` en las preferencias de Chrome (01 §5) y esperar a que el archivo exista y no termine en `.crdownload`.
- Grid: `options.setEnableDownloads(true)` y luego `((HasDownloads) driver).getDownloadableFiles()` / `downloadFile(nombre, destino)`.
- Mejor alternativa cuando aplica: validar la descarga por API (mismo endpoint, mismas cookies) en lugar de por navegador.

## JavascriptExecutor
Solo cuando no hay alternativa real (leer una propiedad, hacer scroll en contenedores con overflow raros):
```java
((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block: 'center'});", elemento);
```
**No** uses JS para hacer clic o escribir "porque el clic normal falla": eso salta la validación de interactuabilidad y oculta bugs reales (overlays, elementos deshabilitados). Si un clic falla con `ElementClickInterceptedException`, espera a que desaparezca lo que lo tapa.

Prefiere `getDomProperty("value")` / `getDomAttribute("data-x")` (Selenium 4) sobre `getAttribute` cuando necesites precisión.

## Cookies y almacenamiento
```java
driver.get(Config.baseUrl() + "/favicon.ico");             // hay que estar en el dominio para poner cookies
driver.manage().addCookie(new Cookie("sid", sesionObtenidaPorApi));
driver.get(Config.baseUrl() + "/inicio");                   // ya autenticado
driver.manage().deleteAllCookies();
((JavascriptExecutor) driver).executeScript("window.localStorage.clear();");
```

## Capturas de evidencia
```java
byte[] png = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BYTES);
byte[] elementoPng = elemento.getScreenshotAs(OutputType.BYTES);        // solo un componente
Pdf pdf = ((PrintsPage) driver).print(new PrintOptions());              // imprimir página a PDF (headless)
```
Enmascara o evita capturar pantallas con datos sensibles en artefactos compartidos.
