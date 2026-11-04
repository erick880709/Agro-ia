# 04 — Patrones de pruebas de API

## Contenido
1. Request básico y construcción de URL
2. Autenticación (basic, bearer, OAuth2 client_credentials, token reutilizado)
3. Headers dinámicos y trazabilidad
4. Retry y polling (procesos asíncronos)
5. Multipart, form, archivos
6. GraphQL
7. SOAP
8. mTLS / SSL / proxy
9. Patrón CRUD completo
10. Pruebas negativas y de seguridad básicas
11. De especificación (OpenAPI / HU) a casos

---

## 1. Request básico

```gherkin
Background:
  * url baseUrl

Scenario: consulta con filtros
  Given path 'v1', 'clientes', clienteId, 'productos'     # segmentos se codifican individualmente
  And param estado = 'ACTIVO'
  And params { page: 1, size: 20 }
  And header Accept = 'application/json'
  When method get
  Then status 200
```
- `path` con varios argumentos evita concatenar `/` a mano. Para POST: `request` + `method post`. Valores de `status` múltiples: `* match [200, 201] contains responseStatus`.
- Después de `method`, `path`/`param`/`request` se **reinician**; `url` y `header`/`configure headers` persisten en el escenario.

## 2. Autenticación

### Basic / bearer declarativo (v2)
```gherkin
* configure auth = { type: 'basic', username: '#(usuario)', password: '#(clave)' }
* configure auth = { type: 'bearer', token: '#(accessToken)' }
* configure auth = { type: 'oauth2', grantType: 'client_credentials', tokenUrl: '#(authConfig.tokenUrl)', clientId: '#(authConfig.clientId)', clientSecret: '#(authConfig.clientSecret)' }
```

### Patrón portable v1/v2: token una vez por suite
`common/auth.feature`
```gherkin
@ignore
Feature: obtiene token OAuth2 client_credentials

  Scenario:
    * url tokenUrl
    * form field grant_type = 'client_credentials'
    * form field client_id = clientId
    * form field client_secret = clientSecret
    * form field scope = '##(scope)'
    * method post
    * status 200
    * def token = response.access_token
```
`karate-config.js`
```javascript
var auth = karate.callSingle('classpath:common/auth.feature', config.authConfig);
config.authHeader = { Authorization: 'Bearer ' + auth.token };
```
Feature:
```gherkin
Background:
  * url baseUrl
  * configure headers = authHeader
```
- `callSingle` en `karate-config.js` se ejecuta **una sola vez** aunque haya N hilos. Si hay varios perfiles (cliente, admin), usa claves distintas: `karate.callSingle('classpath:common/auth.feature?admin', adminConfig)` y `karate.callSingle('classpath:common/auth.feature?cliente', clienteConfig)`. La caché usa el primer argumento; cambiar solo el objeto de datos no separa perfiles.
- Tokens que expiran durante suites largas: usa `configure headers` con una **función** JS que revise expiración y renueve.

### Generación de headers con función (firmas, HMAC, timestamps)
```javascript
// common/headers.js
function fn() {
  var uuid = java.util.UUID.randomUUID() + '';
  var ts = java.time.Instant.now().toString();
  var out = { 'X-Request-Id': uuid, 'X-Timestamp': ts };
  var token = karate.get('accessToken');
  if (token) out['Authorization'] = 'Bearer ' + token;
  return out;
}
```
```gherkin
* configure headers = read('classpath:common/headers.js')   # se evalúa en cada request
```

## 3. Trazabilidad

Agrega siempre un `X-Request-Id`/`X-Correlation-Id` único por request (función de arriba) e imprímelo en fallos: facilita buscar en los logs del servicio (ELK, Dynatrace, CloudWatch) qué pasó con esa petición.

## 4. Retry y polling

Para recursos que se crean de forma asíncrona (colas, procesos batch, eventual consistency):
```gherkin
* configure retry = { count: 10, interval: 3000 }
Given path 'solicitudes', solicitudId
And retry until responseStatus == 200 && response.estado == 'APROBADA'
When method get
```
- `retry until` va **antes** de `method`; la expresión es JS puro (no `match`).
- Nunca `Thread.sleep` fijo como sustituto de polling. Si se necesita una pausa: `karate.pause(ms)`.

## 5. Multipart y archivos

```gherkin
Given path 'documentos'
And multipart file archivo = { read: 'data/cedula.pdf', filename: 'cedula.pdf', contentType: 'application/pdf' }
And multipart field tipo = 'CEDULA'
When method post
Then status 201

# descarga
Given path 'reportes', id, 'pdf'
When method get
Then status 200
And match header Content-Type == 'application/pdf'
* karate.write(responseBytes, 'reporte.pdf')   # queda en target/
```
Form URL-encoded: `form field x = 'y'` o `form fields { a: 1, b: 2 }`.

## 6. GraphQL

```gherkin
* text query =
  """
  query ($id: ID!) { cliente(id: $id) { id nombre productos { tipo saldo } } }
  """
Given path 'graphql'
And request { query: '#(query)', variables: { id: '#(clienteId)' } }
When method post
Then status 200
And match response.errors == '#notpresent'
And match each response.data.cliente.productos == { tipo: '#string', saldo: '#number' }
```
GraphQL devuelve 200 incluso con errores: siempre valida `errors`.

## 7. SOAP

```gherkin
Given url soapUrl
And request read('data/consulta-saldo-request.xml')   # puede tener #(variables)
And soap action 'ConsultarSaldo'
When method post
Then status 200
And match /Envelope/Body/ConsultarSaldoResponse/codigoRespuesta == '00'
```

## 8. SSL, mTLS, proxy, timeouts

```gherkin
* configure ssl = true                                        # confía en cualquier certificado (solo ambientes bajos)
* configure ssl = { keyStore: 'classpath:certs/cliente.p12', keyStorePassword: '#(ksPass)', keyStoreType: 'pkcs12' }   # mTLS
* configure ssl = { trustStore: 'classpath:certs/trust.jks', trustStorePassword: '#(tsPass)', trustStoreType: 'jks' }
* configure proxy = 'http://proxy.corp:8080'
* configure proxy = { uri: 'http://proxy.corp:8080', username: 'u', password: 'p', nonProxyHosts: ['localhost'] }
* configure connectTimeout = 10000
* configure readTimeout = 60000
```

## 9. Patrón CRUD (independiente y autolimpiante)

```gherkin
Feature: ciclo de vida de beneficiario

  Background:
    * url baseUrl
    * def esquema = read('classpath:beneficiarios/schemas/beneficiario.json')

  Scenario: crear, consultar, actualizar y eliminar
    # dato único por ejecución: evita colisiones en paralelo y re-ejecuciones
    * def documento = '9' + Math.floor(10000000 + Math.random() * 89999999)
    * def payload = read('data/beneficiario.json')        # la plantilla usa #(documento)

    Given path 'beneficiarios'
    And request payload
    When method post
    Then status 201
    And match response == esquema
    * def id = response.id
    * configure afterScenario = function(){ karate.call('classpath:common/eliminar-beneficiario.feature', { id: id }) }

    Given path 'beneficiarios', id
    When method get
    Then status 200
    And match response contains { documento: '#(documento)' }

    Given path 'beneficiarios', id
    And request { alias: 'nuevo-alias' }
    When method patch
    Then status 200
    And match response.alias == 'nuevo-alias'
```
`afterScenario` garantiza limpieza aunque un paso intermedio falle.

## 10. Negativas y seguridad básica

Cubre como mínimo, por endpoint:
| Caso | Esperado típico |
|---|---|
| Sin token / token inválido / token expirado | 401 |
| Token válido sin el scope/rol | 403 |
| Acceso a recurso de otro cliente (BOLA/IDOR) | 403 o 404, nunca 200 |
| Campo obligatorio ausente, tipo incorrecto, formato inválido | 400 (o 422) con cuerpo de error consistente |
| Valores límite (0, negativo, máximo+1, cadena vacía, longitud máxima+1) | 400 |
| Recurso inexistente | 404 |
| Método no soportado | 405 |
| Duplicado / idempotencia (misma `Idempotency-Key`) | 409 o misma respuesta |
| Respuesta de error no filtra stack traces ni datos internos | `match response !contains { stackTrace: '#notnull' }` |

Valida también el **formato del error** con un esquema común (`schemas/error.json`) para todas las respuestas 4xx/5xx.

```gherkin
Scenario Outline: [SEG] rechaza autenticación inválida: <caso>
  * configure headers = null
  Given path 'pagos'
  And header Authorization = <auth>
  When method get
  Then status 401
  And match response == read('classpath:common/schemas/error.json')

  Examples:
    | caso      | auth                       |
    | sin token | null                       |
    | malformado| 'Bearer abc'               |
    | expirado  | 'Bearer ' + tokenExpirado  |
```

## 11. De especificación a casos

**Desde OpenAPI/Swagger** — por cada operación:
1. Feature por recurso (`/clientes` → `clientes.feature`), tag con el `operationId`.
2. Esquema `schemas/<Entidad>.json` traducido del `components/schemas` (ver 03 §5).
3. Camino feliz con payload mínimo válido y otro con payload completo.
4. Validaciones en **dos** `Scenario Outline` separados (más legibles y robustos que uno que hace todo):
   - *Valores inválidos* (de `minimum/maximum`, `minLength/maxLength`, `pattern`, `enum`, tipo): payload base válido + columna `cambio!` aplicada con `karate.merge(body, cambio)`. Valores calculados (p. ej. cadenas de longitud máxima+1) se definen en el `Background` (`* def desc41 = 'a'.repeat(41)`) y se referencian en la celda con `'#(desc41)'`.
   - *Campos obligatorios* (de `required`): payload base + `* remove body.<campo>` (sustitución textual de la columna).
   ```gherkin
   Scenario Outline: [op][400] rechaza la solicitud sin el campo obligatorio <campo>
     * def body = { cuentaOrigen: '#(cuentaOrigen)', cuentaDestino: '#(cuentaDestino)', monto: 1000 }
     * remove body.<campo>
     Given path 'v1', 'transferencias'
     And request body
     When method post
     Then status 400
     And match response == esquemaError
     Examples:
       | campo         |
       | cuentaOrigen  |
       | monto         |
   ```
   Si el spec no documenta el código de error de un caso (p. ej. id con formato inválido), acepta el conjunto razonable (`* match [400, 404] contains responseStatus`) y déjalo comentado: nunca 200 ni 500.
5. Casos de seguridad de la tabla §10 según `securitySchemes`.
6. Datos de ambiente que el spec no da (cuentas con/sin saldo, usuarios con roles) van en `karate-config.js` por ambiente y se declaran como supuesto en el comentario de la feature.
7. Cada código de respuesta documentado (`responses`) debe tener al menos un escenario que lo provoque, o quedar listado como no cubierto con su motivo.

**Desde una HU con criterios de aceptación** — un escenario (o fila de outline) por criterio, con el ID en el nombre: `Scenario: [HU-245][CA-3] ...`. Si un criterio no es automatizable vía API, decláralo explícitamente en la entrega. Esto permite construir una matriz de trazabilidad HU → criterio → escenario → resultado a partir del reporte.
