# 04 — Web con Browser Library (Playwright)

Librería por defecto para web nueva en Robot Framework: acciones con espera automática, aserciones con operador que reintentan y un contexto aislado por sesión. Firmas: `python -m robot.libdoc Browser show "<Keyword>"`.

## 1. Ciclo de vida con evidencia por caso

Navegador por suite; **contexto y página nuevos por test** (cookies y storage aislados). La plantilla `web-browser` lo implementa:

```robotframework
Iniciar Caso Con Evidencia
    ${carpeta}=    Carpeta De Evidencia Del Caso
    New Context    viewport={'width': 1280, 'height': 800}
    ...    recordVideo={'dir': '${carpeta}/_video'}    tracing=${carpeta}/trace.zip
    ${pagina}=    New Page    ${BASE_URL}
    VAR    ${VIDEO_DEL_CASO}    ${pagina}[video_path]    scope=TEST

Cerrar Caso Con Evidencia
    ${carpeta}=    Carpeta De Evidencia Del Caso
    Take Screenshot    ${carpeta}/screenshot      # ruta absoluta: guarda screenshot.png
    Close Context                                 # escribe video y trace
    Mover Video Al Caso    ${VIDEO_DEL_CASO}
```

- Video y trace existen **después** de `Close Context`. `recordVideo` no funciona con navegadores remotos: ese faltante se declara.
- El trace se abre con `rfbrowser show-trace <ruta>/trace.zip`.
- `run_on_failure` ya toma screenshot al fallar; el teardown añade el de los casos exitosos que exige la política.

## 2. Selectores

Orden: `data-testid` → rol accesible (`role=button[name="Guardar"]`) → CSS corto → `text=` → XPath al final. Encadena con `>>` (`.carrito >> text=Quitar`), iframes con `>>>`. `#` al inicio de una celda es comentario: escribe `id=login`. Modo estricto (por defecto): un selector que coincide con varios elementos falla; hazlo único.

## 3. Aserciones y esperas

| Necesidad | Keyword |
|---|---|
| Texto/URL/cantidad/estado | Getter con operador: `Get Text    h1    ==    Bienvenido`, `Get Url    contains    /inicio`, `Get Element Count    li    ==    3` |
| Aparece / desaparece | `Wait For Elements State    .spinner    hidden` |
| Respuesta de API tras un clic | `${p}=    Promise To    Wait For Response    **/api/pagos` → `Click` → `Wait For    ${p}` |
| Condición arbitraria | `Wait For Condition    Text    h1    ==    Listo` |

Un getter **sin** operador no reintenta. Dos tiempos distintos: `timeout` (acciones, 10 s) y `retry_assertions_for` (aserciones, 1 s); sube el segundo para aserciones lentas, nunca agregues `Sleep`.

## 4. Formularios y sesiones

`Fill Text` llena de una vez; `Type Text` cuando importan los eventos de tecla; `Fill Secret    ${sel}    %CLAVE_ENV` para claves (no se registra). Reutiliza login con `Save Storage State` y `New Context    storageState=${archivo}`; el archivo contiene cookies: trátalo como secreto.

## 5. Gotchas

- `New Page` sin `New Browser`/`New Context` crea ambos con valores por defecto y pierde viewport, video y trace.
- `auto_closing_level=TEST` cierra lo abierto en el test; lo de Suite Setup vive hasta el teardown de la suite.
- `Wait Until Network Is Idle` está deprecado: espera el elemento o la respuesta concreta.
