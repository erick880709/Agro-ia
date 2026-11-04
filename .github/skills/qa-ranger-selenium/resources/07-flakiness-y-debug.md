# 07 — Flakiness y depuración

## 1. Método
1. **Reproducir**: correr el test aislado 20 veces y en paralelo (JUnit: `mvn test -Dtest=Clase#metodo -Dsurefire.rerunFailingTestsCount=0` en un bucle; pytest: `pytest -k nombre --count=20 -n 4` con `pytest-repeat` + `pytest-xdist`). Si solo falla en paralelo → aislamiento; si falla solo → sincronización o datos.
2. **Evidencia**: screenshot + page source + URL + logs de consola (BiDi) del momento exacto del fallo (03 §4).
3. **Clasificar** con la tabla de §3 y corregir la causa.
4. **Verificar** repitiendo la ejecución.

Nunca: subir timeouts globales, agregar `Thread.sleep`, reintentos automáticos sin investigar, `executeScript` para forzar clics.

## 2. Evidencia mínima al fallar
- Screenshot de la página completa.
- `driver.getPageSource()` → muestra el DOM real (¿existía el elemento? ¿con qué atributos?).
- `driver.getCurrentUrl()` → ¿hubo redirección inesperada (sesión expirada, error)?
- Consola y errores JS (05).
- En Grid: video de la sesión (docker-selenium dinámico).

### Ejemplo real (validado al construir la skill)
Un test con `sleep(0.6)` + `find_element(MENSAJE).text` falló **7 de 12** veces contra una app con latencia de 400–1000 ms.
- Error: `assert 'Transferencia exitosa' in ''` → el mensaje estaba vacío.
- Page source capturado en el fallo: `#mensaje` vacío, overlay `#cargando` con `display: block`, botón `confirmar` `disabled` → la petición seguía en curso.
- Corrección: `WebDriverWait(driver, 10).until(lambda d: d.find_element(By.ID, "mensaje").text.strip() or False)` → **12/12**.
- Lección adicional: `visibility_of_element_located` sobre un contenedor vacío "funcionó" solo porque el div vacío medía 0 px (Selenium considera invisible un elemento sin tamaño). Es un éxito accidental que depende del CSS: espera siempre **la condición de negocio** (el texto), no un efecto lateral del layout.

## 3. Índice de excepciones

| Excepción | Causa típica | Corrección |
|---|---|---|
| `NoSuchElementException` | Elemento aún no renderizado; localizador incorrecto; está en un iframe o shadow DOM | Espera explícita; verificar el localizador contra el page source; `switchTo().frame` / `getShadowRoot()` |
| `TimeoutException` | La condición esperada nunca se cumplió | Leer qué condición era; mirar screenshot/page source del fallo: ¿otro texto, error del backend, página distinta? |
| `StaleElementReferenceException` | El DOM se re-renderizó | Guardar `By`, volver a buscar; esperar el nuevo estado (02 §8) |
| `ElementClickInterceptedException` | Overlay, spinner, banner de cookies o modal tapa el elemento | Esperar `invisibilityOfElementLocated` del overlay; cerrar el banner en el setup |
| `ElementNotInteractableException` | Elemento oculto, deshabilitado o de tamaño cero | Esperar `elementToBeClickable`; verificar que no hay duplicados ocultos (localizador ambiguo) |
| `InvalidSelectorException` | Sintaxis de XPath/CSS inválida | Probar el selector en DevTools (`$x()` / `$$()`) |
| `SessionNotCreatedException` | Versión navegador/driver incompatible, Grid sin capacidad, opciones inválidas | Selenium Manager (01 §3), `SE_DEBUG=true`, revisar `/status` del Grid |
| `NoSuchWindowException` / `NoSuchFrameException` | Se cerró o cambió la ventana/frame | Esperar `numberOfWindowsToBe`; volver a `defaultContent()` |
| `UnhandledAlertException` | Alerta nativa abierta inesperadamente | Manejar la alerta (04); revisar por qué apareció |
| `WebDriverException: unknown error: DevToolsActivePort file doesn't exist` | Chrome no arranca en contenedor | `--headless=new`, `--disable-dev-shm-usage`, `shm_size` |

## 4. Patrones de inestabilidad

| Síntoma | Causa | Corrección |
|---|---|---|
| Lee el texto anterior/vacío | Espera de visibilidad cuando el contenido llega después | Esperar el texto o una condición sobre el contenido |
| Pasa local, falla en CI | Ventana más pequeña, más lento, otra zona horaria | `--window-size` fijo, esperas por condición, zona horaria fija en datos |
| Falla tras otro test | Datos compartidos, sesión reutilizada | Datos propios, driver por test |
| Falla a horas puntuales | Datos dependientes de fecha/hora, procesos batch del ambiente | Fechas relativas controladas; coordinar ventanas |
| Clic "no hace nada" | Clic antes de que el JS del framework enganche el evento | Esperar un indicador de que la vista está lista (botón habilitado, dato cargado) |

## 5. Reintentos y cuarentena
- `surefire.rerunFailingTestsCount=1` o el `IRetryAnalyzer` de TestNG **solo** como red de seguridad en CI, con reporte de los tests que pasaron al reintento: son flaky y se tratan como bugs.
- Cuarentena con `@Tag("cuarentena")` / grupo excluido, ticket asociado y revisión periódica.
