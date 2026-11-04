# 05 — Web con SeleniumLibrary

Para suites que ya importan `SeleniumLibrary` o necesitan Selenium Grid. Diferencia clave con Browser: **las keywords de elemento no esperan** y las aserciones `… Should …` no reintentan.

## 1. Importación y apertura

```robotframework
Library    SeleniumLibrary    timeout=10s    implicit_wait=0s
...
Open Browser    ${BASE_URL}    ${BROWSER}    options=${OPCIONES}    remote_url=${GRID_URL}
```

- Pasa siempre el navegador: `Open Browser` sin él abre Firefox. Nombres headless: `headlesschrome`, `headlessfirefox` (sin guion bajo); Edge headless con `options=add_argument("--headless=new")`.
- `implicit_wait=0s`: las implícitas se suman a cada sondeo de `Wait Until …` y desbordan los tiempos.
- Selenium Manager resuelve el driver; sin internet, driver interno por `executable_path` en `Create Webdriver` y regístralo en la Línea Base.

## 2. Esperas

| Situación | Keyword |
|---|---|
| Aparece tras navegación/AJAX | `Wait Until Element Is Visible` / `Wait Until Page Contains Element` |
| Spinner u overlay se va | `Wait Until Element Is Not Visible` |
| Botón habilitado | `Wait Until Element Is Enabled` |
| Texto que carga tarde | `Wait Until Element Contains` / `Wait Until Page Contains` |
| Condición propia | `Wait Until Keyword Succeeds    10s    500ms    <verificación>` (solo verificaciones, nunca un clic o envío) |

## 3. Localizadores

Sin prefijo: `id` o `name`. Con estrategia: `css:[data-testid="guardar"]`, `xpath://button[normalize-space()="Guardar"]`. Nunca XPath absolutos ni por índice. Guarda localizadores en variables, no `WebElement` (se vuelven *stale*).

## 4. Frames, ventanas, alertas

`Select Frame` es pegajoso hasta `Unselect Frame`; `Page Should Contain` vuelve al frame principal. Ventanas: `Switch Window    NEW` / `MAIN`. Alertas: `Handle Alert`.

## 5. Evidencia disponible

| Tipo | Cómo | Nota |
|---|---|---|
| Screenshot | `Capture Page Screenshot    ${carpeta}/screenshot.png` en teardown | también en exitosos |
| Traza diagnóstica | `Guardar Traza Selenium` (QaEvidencia): page source, URL y consola en `trace.zip` | no es un trace de Playwright |
| Video | solo si la infraestructura graba (docker-selenium con video, nube) | sin ella, pendiente o excepción explícita |

Si la política del encargo exige video y la infraestructura no lo produce, no cierres como `completed`: declara el faltante (ver `../../qa-ranger-selenium/resources/06-grid-paralelismo-nube.md` para Grid con video).
