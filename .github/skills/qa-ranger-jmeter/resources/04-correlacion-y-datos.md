# 04 — Correlación, datos y scripting

## 1. Correlación
Todo valor dinámico que el servidor genera y luego espera recibir (token JWT, ID de sesión, ID de recurso creado, CSRF, ViewState) debe **extraerse** y reenviarse. Un script grabado sin correlacionar "funciona" con 1 usuario durante 5 minutos y luego falla.

Método: ejecutar 2 veces con 1 usuario y comparar las peticiones (View Results Tree en la GUI): lo que cambia entre ejecuciones y viene de una respuesta previa se correlaciona.

| Extractor | Para | Propiedades clave |
|---|---|---|
| **JSON Extractor** (`JSONPostProcessor`) | Respuestas JSON | `JSONPostProcessor.referenceNames`, `.jsonPathExprs`, `.match_numbers`, `.defaultValues` |
| **Boundary Extractor** | Texto entre delimitadores (rápido) | `BoundaryExtractor.refname`, `.lboundary`, `.rboundary`, `.match_number`, `.default` |
| Regular Expression Extractor | Patrones complejos | `RegexExtractor.refname`, `.regex`, `.template`, `.match_number`, `.default` |
| CSS Selector Extractor (`HtmlExtractor`) | HTML | |
| XPath2 Extractor | XML/SOAP | |

Reglas:
- **Siempre un valor por defecto distinguible** (`NO_ENCONTRADO_token`) y una aserción posterior o un If Controller: si la extracción falla, el siguiente request debe fallar de forma evidente, no enviar `${token}` literal.
- `match_number`: `1` = primera coincidencia, `0` = aleatoria, `-1` = todas (`var_1..var_N` + `var_matchNr`, para ForEach).
- Extrae del alcance mínimo (hijo del sampler que produce el valor).

Uso:
```
Header:  Authorization: Bearer ${token}
Path:    /api/transferencias/${transferenciaId}
```

## 2. Datos de prueba: CSV Data Set Config
```
usuario,clave,cuentaOrigen
qa.0001,${__env(CLAVE_QA)},00112233445
```
| Propiedad | Recomendado | Por qué |
|---|---|---|
| `filename` | Ruta relativa al `.jmx` (o `${__P(datos,datos/usuarios.csv)}`) | Portable entre máquinas |
| `variableNames` | Vacío si el CSV tiene encabezado + `ignoreFirstLine=false`; o nombres explícitos + `ignoreFirstLine=true` | |
| `shareMode` | `shareMode.all` | Cada línea la toma un hilo distinto |
| `recycle` / `stopThread` | `false`/`true` para datos de un solo uso (crear usuarios); `true`/`false` para datos reutilizables | Evitar colisiones |
| `fileEncoding` | `UTF-8` | Tildes y ñ |

Datos suficientes: mínimo un registro por hilo concurrente (y para datos de un solo uso, uno por iteración total). En pruebas distribuidas, **cada generador necesita su propio subconjunto** de datos (archivos distintos por nodo).

## 3. Funciones útiles
| Función | Uso |
|---|---|
| `${__P(nombre,defecto)}` | Propiedad con valor por defecto |
| `${__UUID()}` | Identificador único (idempotency keys, referencias) |
| `${__Random(1000,500000,)}` | Número aleatorio |
| `${__RandomString(8,abcdef0123456789,)}` | Texto aleatorio |
| `${__time(yyyy-MM-dd'T'HH:mm:ss,)}` | Fecha/hora actual |
| `${__timeShift(yyyy-MM-dd,,P1D,,)}` | Fecha relativa |
| `${__threadNum}` | Número de hilo |
| `${__counter(FALSE,)}` | Contador global |
| `${__jexl3(...)}` / `${__groovy(...)}` | Expresiones (If Controller) |

## 4. Scripting: JSR223 + Groovy
- **Siempre Groovy** (`scriptLanguage=groovy`) con **`cacheKey=true`** (compilación en caché). **Nunca BeanShell** (lento, sin caché, se elimina progresivamente).
- **No uses `${variable}` dentro del script**: rompe la caché (cada valor genera un script distinto). Usa `vars.get("variable")`, `props.get("propiedad")`.
- Objetos disponibles: `vars`, `props`, `prev` (resultado previo), `sampler`, `log`, `ctx`.

```groovy
// JSR223 PostProcessor: validar y normalizar el token extraído
def token = vars.get("token")
if (!token || token.startsWith("NO_ENCONTRADO")) {
    prev.setSuccessful(false)
    prev.setResponseMessage("No se obtuvo token de autenticación")
    return
}
vars.put("authHeader", "Bearer " + token)
```
Mantén el scripting mínimo: lógica pesada en el generador consume CPU y distorsiona los tiempos medidos.

## 5. Grabación
HTTP(S) Test Script Recorder (o BlazeMeter Chrome extension) → limpiar: eliminar recursos estáticos innecesarios (o dejarlos con `Retrieve All Embedded Resources` si el objetivo es medir carga de página), agrupar en Transaction Controllers, parametrizar, correlacionar, añadir think time. Un script grabado **nunca** está listo para carga sin este trabajo.
