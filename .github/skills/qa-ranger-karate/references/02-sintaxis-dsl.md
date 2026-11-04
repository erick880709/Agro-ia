# 02 — Sintaxis del DSL

## Contenido
1. Anatomía de una feature
2. Keywords
3. JSON de Karate vs JavaScript (regla del RHS)
4. Expresiones embebidas `#()` y `##()`
5. Leer archivos: `read()`
6. `karate-config.js`
7. Reutilización: `call`, `callonce`, `karate.callSingle`
8. Data-driven: Scenario Outline, CSV, JSON, `@setup`
9. Tags integrados
10. Hooks y control de flujo
11. API `karate.*` más usada

---

## 1. Anatomía

```gherkin
@pagos @regresion
Feature: Consulta de pagos

  Background:
    * url baseUrl
    * def auth = karate.callSingle('classpath:common/auth.feature', authConfig)
    * header Authorization = 'Bearer ' + auth.token

  @smoke
  Scenario: [HU-101][CA-1] consulta un pago existente
    Given path 'pagos', pagoId
    When method get
    Then status 200
    And match response == read('classpath:pagos/schemas/pago.json')
```
`Given/When/Then/And/But` y `*` son equivalentes para Karate; úsalos para legibilidad, no tienen semántica. `Background` se ejecuta antes de **cada** escenario.

## 2. Keywords

- Variables: `def`, `set`, `remove`, `copy`, `text`, `json`, `xml`, `xmlstring`, `string`, `csv`, `yaml`, `table`, `replace`
- Aserciones: `match` (todos los operadores, ver 03), `assert`, `print`
- HTTP: `url`, `path`, `param`, `params`, `header`, `headers`, `cookie`, `cookies`, `form field(s)`, `request`, `method`, `status`, `retry until`, `multipart file/field/fields/files/entity`, `soap action`
- Control: `call`, `callonce`, `eval`
- Config: `configure` (ssl, proxy, timeouts, headers, cookies, auth, retry, logging, report, etc.)

Variables HTTP disponibles tras `method`: `response`, `responseStatus`, `responseHeaders`, `responseCookies`, `responseTime`, `responseBytes`, `responseType`.

```gherkin
* def id = 123
* def body = { nombre: 'Ana', monto: 1000 }
* set body.monto = 2000
* set body.direccion.ciudad = 'Medellín'      # crea rutas intermedias
* remove body.nombre
* def copia = copy body                        # clon profundo (def solo copia referencia)
* table casos
  | monto | esperado |
  | 0     | 400      |
  | 100   | 201      |
* text plantilla =
  """
  hola <nombre>
  """
* replace plantilla.nombre = 'Ana'
```

## 3. Regla del lado derecho (RHS)

Todo RHS de `def`, `set`, `configure`, `match` **o argumento inline de `call`** que empieza por `{` o `[` se parsea como **JSON relajado de Karate**: claves con guion válidas, `#(expr)` se sustituye, y un identificador suelto en posición de valor se lee como **string**.

```gherkin
* def id = 123
* def a = { id: '#(id)' }            # a.id == 123 (número, tipo preservado)
* def b = { id: id }                 # OJO: b.id == 'id' (string literal)
* def c = ({ id: id })               # paréntesis => JavaScript: c.id == 123
* def d = ({ id })                   # shorthand ES6, solo con paréntesis
* def headers = { Content-Type: 'application/json', X-Request-Id: 'abc' }  # guiones OK

* def r1 = call read('x.feature') { id: id }        # __arg.id == 'id'  (error común)
* def r2 = call read('x.feature') { id: '#(id)' }   # __arg.id == 123
```
Este es el error #1 de quienes vienen de JS. Para valores dinámicos usa `'#(var)'` o envuelve en paréntesis.

## 4. Expresiones embebidas

- `#(expr)` — sustituye conservando el tipo. Funciona en JSON, XML y en archivos leídos con `read()`.
- `##(expr)` — al **construir** datos: si es `null` elimina la clave. Al **validar**: campo opcional.

```gherkin
* def segundoNombre = null
* def body = { nombre: 'Ana', segundo: '##(segundoNombre)' }
* match body == { nombre: 'Ana' }
```
Plantillas: un `.json` con `#(variable)` se rellena al hacer `read()` con las variables del contexto actual.

## 5. `read()`

```gherkin
* def payload = read('data/pago-valido.json')          # relativo a la feature
* def esquema = read('classpath:pagos/schemas/pago.json')
* def casos = read('data/casos.csv')                   # lista de objetos (cabecera = claves)
* def cfg = read('data/config.yaml')
* def fn = read('utils/fechas.js')                     # función JS
* def otra = read('common/crear-pago.feature')         # para call
* def bytes = karate.readAsBytes('data/firma.pdf')
* def texto = karate.readAsString('data/plantilla.json')  # sin procesar #()
```
Prefijos: `classpath:` (recomendado para recursos compartidos), relativo a la feature (sin prefijo), `this:` (relativo explícito), `file:` (ruta de sistema). En v2, una ruta que empieza por `/` en `read()` es relativa a la **raíz del proyecto** (donde está `karate-config.js`), no del sistema de archivos.

## 6. `karate-config.js`

Se ejecuta antes de **cada** escenario; lo que retorna queda como variables globales. Debe ser rápido: nada de llamadas HTTP aquí salvo vía `karate.callSingle()` (que se cachea).

```javascript
function fn() {
  var env = karate.env || 'dev';
  karate.log('karate.env =', env);

  var config = {
    env: env,
    baseUrl: 'https://api-dev.ejemplo.com',
    authConfig: {
      tokenUrl: 'https://auth-dev.ejemplo.com/oauth2/token',
      clientId: karate.properties['client.id'] || java.lang.System.getenv('CLIENT_ID'),
      clientSecret: karate.properties['client.secret'] || java.lang.System.getenv('CLIENT_SECRET')
    }
  };

  if (env == 'qa') {
    config.baseUrl = 'https://api-qa.ejemplo.com';
    config.authConfig.tokenUrl = 'https://auth-qa.ejemplo.com/oauth2/token';
  } else if (env == 'stg') {
    config.baseUrl = 'https://api-stg.ejemplo.com';
  }

  karate.configure('connectTimeout', 10000);
  karate.configure('readTimeout', 30000);
  karate.configure('ssl', true);   // solo si hay certificados autofirmados en ambientes bajos
  return config;
}
```
- Secretos: siempre por variable de entorno o `-D`; nunca en el repo. En v2 también `karate.sysenv('CLIENT_ID', 'default')` y `karate.sysprop(...)`.
- `karate-config-<env>.js` se ejecuta después del principal y puede sobrescribir valores.
- `karate-base.js` (opcional) corre antes que `karate-config.js` — útil para config compartida entre repos vía JAR.

## 7. Reutilización

| Mecanismo | Alcance de caché | Uso típico |
|---|---|---|
| `call read('x.feature')` | ninguno | Paso reutilizable con parámetros (crear entidad, login de UI) |
| `callonce read('x.feature')` | por feature | Setup compartido entre escenarios de una feature |
| `karate.callSingle('x.feature', arg)` | **por suite** (todos los hilos) | Token de autenticación, datos maestros |
| `call fn` / `call fn arg` | — | Función JS |

```gherkin
# feature reutilizable — common/crear-cliente.feature
@ignore
Feature: helper crear cliente
  Scenario:
    * url baseUrl
    * path 'clientes'
    * request { documento: '#(documento)', nombre: '#(nombre)' }
    * method post
    * status 201
    * def clienteId = response.id

# invocación: el resultado es un mapa con TODAS las variables definidas en la llamada
* def cliente = call read('classpath:common/crear-cliente.feature') { documento: '#(doc)', nombre: 'Ana' }
* def id = cliente.clienteId

# llamada en bucle: si el argumento es una lista, se invoca una vez por elemento
* def creados = call read('classpath:common/crear-cliente.feature') listaDeClientes
* def ids = $creados[*].clienteId
```
- **Shared scope**: `* call read('x.feature')` sin asignar resultado comparte variables y configuración (headers, cookies) con el llamador. Útil para "aplicar" un login; peligroso si se abusa.
- Dentro de la feature llamada: `__arg` (argumento completo) y `__loop` (índice cuando se llama con lista).
- `callSingle` con caché en disco entre ejecuciones locales: `karate.configure('callSingleCache', { minutes: 15 })` en `karate-config.js` (no en CI).

## 8. Data-driven

```gherkin
Scenario Outline: [CA-3] valida monto <monto> -> <codigo>
  Given path 'pagos'
  And request { monto: <monto>, moneda: 'COP' }
  When method post
  Then status <codigo>

  Examples:
    | monto  | codigo |
    | -1     | 400    |
    | 0      | 400    |
    | 1      | 201    |
    | 999999 | 201    |
```
- `<monto>` es sustitución **textual** antes de ejecutar el paso (por eso `{ monto: <monto> }` produce un número). Además, cada columna existe como variable (`monto`), pero **como string**; para que la variable se evalúe con su tipo (número, booleano, JSON) termina la cabecera en `!`: `| monto! | codigo |`. `__row` (fila completa) y `__num` (índice) disponibles.
- Fuente externa: `Examples:` seguido de `| read('data/casos.csv') |` o `| read('data/casos.json') |`.
- **Dynamic outline con `@setup`** (datos calculados o traídos de una API/BD):

```gherkin
@setup
Scenario:
  * def data = karate.call('classpath:common/listar-productos.feature').productos

Scenario Outline: producto ${nombre} tiene precio positivo
  * match precio == '#? _ > 0'

  Examples:
    | karate.setup().data |
```
Los nombres de escenario aceptan placeholders `${var}` (o `<var>`).

## 9. Tags integrados

| Tag | Efecto |
|---|---|
| `@ignore` | No se ejecuta en la suite, pero se puede invocar con `call` |
| `@env=qa` / `@envnot=prod` | Ejecuta solo (o excepto) en ese `karate.env` |
| `@setup` | Proveedor de datos para dynamic outlines |
| `@fail` | Espera que el escenario falle (invierte el resultado) — v2 |
| `@lock=nombre` / `@lock=*` | Exclusión mutua — v2 (en v1: `@parallel=false`) |
| `@report=false` | Ejecuta pero oculta el detalle del reporte (secretos) — v2 |

Expresiones de tags: `--tags @smoke` (incluye), `--tags ~@wip` (excluye), varios `--tags` = AND, `@a,@b` en un mismo argumento = OR. Tags con valor: `@req=HU-101` y en código `karate.tagValues`.

## 10. Hooks y control de flujo

```gherkin
* configure afterScenario = function(){ karate.call('classpath:common/limpiar.feature', { id: pagoId }) }
* configure afterFeature = function(){ karate.log('fin feature') }
* if (responseStatus == 404) karate.abort()       # termina el escenario como saltado
* if (!habilitado) karate.fail('feature flag apagado en ' + karate.env)
* def resultado = responseStatus == 200 ? response.data : []
* eval for (var i = 0; i < 3; i++) karate.log('intento', i)
```
`beforeScenario` en v2 debe definirse en `karate-config.js` para aplicar al escenario actual. Mantén la lógica condicional al mínimo: un escenario con muchos `if` suele ser varios escenarios.

`configure continueOnStepFailure = true` (soft assertions): sigue ejecutando tras un `match` fallido y reporta todos los fallos al final; desactivar con `configure continueOnStepFailure = false`. En v2, además, un único `match` ya reporta **todas** las rutas que difieren, no solo la primera.

## 11. API `karate.*` más usada

| Categoría | Métodos |
|---|---|
| Flujo | `call`, `callonce`, `callSingle`, `abort`, `fail`, `eval`, `get(name, default)`, `set` |
| Datos | `read`, `readAsString`, `readAsBytes`, `write`, `fromString`, `toJson`, `toCsv`, `jsonPath(obj, '$..x')`, `xmlPath` |
| Colecciones | `filter`, `map`, `forEach`, `sort`, `distinct`, `merge`, `append`, `keysOf`, `valuesOf`, `sizeOf`, `range`, `repeat`, `mapWithKey`, `filterKeys` |
| Aserción | `match(actual, expected)` → `{ pass, message }` (no falla el paso), `expect()` estilo Chai (v2) |
| Datos de prueba | `java.util.UUID.randomUUID().toString()` (v1/v2), `karate.uuid()` (v2); en v2 `karate.faker.*` (`fullName`, `email`, `randomInt(a,b)`, `isoTimestamp`…) |
| Info | `env`, `os`, `properties`, `scenario`, `feature`, `tags`, `tagValues`, `info` |
| Log/reporte | `log`, `embed(bytes, mime)`, `logger.*` (v2) |
| Procesos | `exec`, `fork`, `signal` + `listen`, `waitForHttp`, `waitForPort` |
| Mocks | `start`, `proceed` |
| Pausa | `karate.pause(ms)` (respeta Gatling; preferir sobre `java.lang.Thread.sleep`) |

```gherkin
* def activos = karate.filter(response.items, function(x){ return x.estado == 'ACTIVO' })
* def ids = karate.map(activos, x => x.id)
* def r = karate.match(response, { id: '#number' })
* if (!r.pass) karate.log('diferencias:', r.message)
* def LocalDate = Java.type('java.time.LocalDate')
* def hoy = LocalDate.now().toString()
```
