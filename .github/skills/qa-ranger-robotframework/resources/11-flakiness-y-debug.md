# 11 — Inestabilidad y diagnóstico

## 1. Método

1. **Reproduce**: ejecuta el caso aislado varias veces (`for i in $(seq 10); do python -m robot --include TC-07 --output NONE ... ; done`) y en paralelo (pabot `--testlevelsplit`). Cuenta fallos: «7/10» es un dato, «a veces» no.
2. **Lee la evidencia** antes de cambiar código: `log.html` (mensaje, keyword exacta, argumentos), screenshot/trace/video del caso, filas consultadas, respuesta HTTP.
3. **Clasifica**: espera insuficiente · dependencia entre tests · datos compartidos o no deterministas · ambiente (red, BD, versión) · defecto real del sistema.
4. **Corrige la causa** y repite la medición (p. ej. 7/12 fallos → 12/12 pasan). Un reintento automático no es una corrección.

Leer resultados sin abrir el HTML: `robotcode results summary --failed` o `python -c "from robot.api import ExecutionResult as E; r=E('output.xml'); [print(t.name, t.message) for t in r.suite.all_tests if t.failed]"`.

## 2. Índice de errores

| Mensaje | Causa típica | Acción |
|---|---|---|
| `No keyword with name 'X' found` | resource no importado, nombre distinto, keyword de una versión más nueva | libdoc; imports; puerta de versión |
| `Multiple keywords with name 'X' found` | mismo nombre en dos resources | renombrar o calificar |
| `Variable '${X}' not found` / `'%{X}' not found` | variable fuera de alcance, archivo de variables no pasado, env en minúscula | `--variablefile`; MAYÚSCULA en Linux |
| `Keyword 'X' expected N arguments, got M` | celdas separadas por un solo espacio, `=` con espacio | 4 espacios; `nombre=valor` |
| `Parent suite setup failed` | falló la conexión/apertura del Suite Setup | revisar el primer error de la suite |
| `password authentication failed for user "<agente>"` | `%{USER}` tomó el usuario del sistema | 08 §4 |
| `Wrong query result: 'X' (str) should be 'Y' (int)` | aserción sensible al tipo | `assert_as_string=True` o `${valor}` tipado |
| `TimeoutError: locator.click` (Browser) | overlay, selector que no es único o elemento fuera de la página | `Wait For Elements State`; selector único |
| `strict mode violation` | selector coincide con varios elementos | hacerlo único o `>> nth=0` justificado |
| `ElementClickInterceptedException` / `StaleElementReferenceException` (Selenium) | overlay / WebElement guardado | esperar invisibilidad; pasar el localizador |
| `HTTPError: 4xx/5xx` (Requests) | negativo sin `expected_status` o defecto real | `expected_status=` en negativos |
| `contains no tests` | archivo sin `*** Test Cases ***` o ruta equivocada | encabezado plural; ruta de la tarea |

## 3. Herramientas

- `robotcode debug` / `robot-debug` para depurar paso a paso; `robotcode repl` para probar keywords contra el ambiente.
- `--loglevel DEBUG` (o `TRACE`) para ver argumentos y retornos: cuidado, también registra secretos.
- `--exitonfailure` para cortar en el primer fallo al reproducir; `--randomize tests` para destapar dependencias de orden.
