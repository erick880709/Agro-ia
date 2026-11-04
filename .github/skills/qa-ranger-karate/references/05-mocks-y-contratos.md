# 05 — Mocks y contract testing

## Contenido
1. Cuándo usar mocks Karate
2. Anatomía de un mock
3. Variables de request/response y funciones de matching
4. Mocks con estado
5. Proxy y respuestas híbridas
6. Arrancar el mock (Java, feature, CLI)
7. Contract testing consumidor/proveedor
8. Mocks en JS (v2)

---

## 1. Cuándo

- Desacoplar pruebas de dependencias inestables o costosas (core bancario, proveedores externos, servicios de terceros).
- Provocar errores difíciles de reproducir: timeouts (`responseDelay`), 500, respuestas malformadas.
- Desarrollo frontend/consumidor antes de que exista el proveedor.
- Contract testing: el mismo mock que usa el consumidor se valida contra el proveedor real.

## 2. Anatomía

Cada `Scenario` es una **ruta**; su "nombre" es una expresión JS booleana. Se evalúan **en orden** y gana el primero que da `true`. El `Background` se ejecuta **una vez** al arrancar (no por request) — por eso sirve para estado.

```gherkin
Feature: mock de cuentas

  Background:
    * configure cors = true
    * configure responseHeaders = { 'Content-Type': 'application/json' }
    * def cuentas = { '001': { id: '001', saldo: 150000, estado: 'ACTIVA' } }

  Scenario: pathMatches('/cuentas/{id}') && methodIs('get') && !headerContains('Authorization', 'Bearer')
    * def responseStatus = 401
    * def response = { codigo: 'UNAUTHORIZED' }

  Scenario: pathMatches('/cuentas/{id}') && methodIs('get')
    * def cuenta = cuentas[pathParams.id]
    * def responseStatus = cuenta ? 200 : 404
    * def response = cuenta ? cuenta : { codigo: 'NOT_FOUND' }

  Scenario: pathMatches('/cuentas/{id}/bloqueo') && methodIs('post')
    * def responseDelay = 4000          # simula lentitud para probar timeouts del consumidor
    * cuentas[pathParams.id].estado = 'BLOQUEADA'
    * def response = cuentas[pathParams.id]

  Scenario:
    # catch-all SIEMPRE al final
    * def responseStatus = 404
    * def response = { codigo: 'RUTA_NO_MOCKEADA', ruta: '#(requestPath)' }
```

## 3. Variables y funciones

Request (lectura): `request`, `requestBytes`, `requestPath`, `requestUri`, `requestUrlBase`, `requestMethod`, `requestHeaders`, `requestCookies`, `requestParams`, `requestParts`, `pathParams`.

Response (escritura): `response`, `responseStatus` (default 200), `responseHeaders`, `responseDelay` (ms).

Funciones de matching: `pathMatches('/x/{id}')`, `methodIs('post')`, `typeContains('json')`, `acceptContains('json')`, `headerContains(nombre, valor)`, `headerValue(nombre)` (v2), `paramValue(nombre)`, `paramExists(nombre)`, `bodyPath('$.campo')` (JsonPath o XPath si empieza por `/`).

Hooks: `configure beforeScenario` / `afterScenario` corren **por request**.

## 4. Con estado

Las variables del `Background` persisten entre requests; el handler sincroniza el acceso (thread-safe). Patrón CRUD en memoria:

```gherkin
Background:
  * def uuid = function(){ return java.util.UUID.randomUUID() + '' }
  * def items = {}

Scenario: pathMatches('/items') && methodIs('post')
  * def item = request
  * item.id = uuid()
  * items[item.id] = item
  * def responseStatus = 201
  * def response = item

Scenario: pathMatches('/items') && methodIs('get')
  * def response = $items.*

Scenario: pathMatches('/items/{id}') && methodIs('delete')
  * karate.remove('items', pathParams.id)
  * def responseStatus = 204
```

Datos de respuesta desde archivos: `* def response = read('respuestas/cuenta-' + pathParams.id + '.json')`.

## 5. Proxy

```gherkin
# pasa al backend real todo lo no mockeado y permite alterar la respuesta
Scenario: requestPath.startsWith('/api/clientes')
  * karate.proceed('https://api-qa.ejemplo.com')
  * if (responseStatus == 200) response.fuente = 'real'

Scenario: pathMatches('/api/riesgo/score')
  * def response = { score: 850 }       # solo esta dependencia se virtualiza
```

## 6. Arrancar

Java v2:
```java
MockServer mock = MockServer.feature("classpath:mocks/cuentas-mock.feature")
    .arg(Map.of("modo", "lento"))
    .pathPrefix("/api")     // opcional: quita prefijo antes del matching
    .start();               // puerto dinámico por defecto
String url = mock.getUrl();
// ... Runner.path(...).systemProperty("cuentasUrl", url).parallel(4)
mock.stopAndWait();
```
Java v1:
```java
MockServer mock = MockServer.feature("classpath:mocks/cuentas-mock.feature").http(0).build();
int port = mock.getPort();
mock.stop();
```
Desde una feature (o `karate-config.js` con `callSingle` para levantarlo una vez):
```gherkin
* def mock = karate.start({ mock: 'classpath:mocks/cuentas-mock.feature', port: 0 })
* def cuentasUrl = 'http://localhost:' + mock.port
```
CLI: `karate mock -m cuentas-mock.feature -p 8080 [-W hot-reload] [--ssl]` (v2) — útil para que frontend o QA manual usen el mock como servidor.

## 7. Contract testing (consumer-driven, sin Pact)

1. **Consumidor** define el mock (`payments-mock.feature`) con lo que espera del proveedor y prueba su servicio contra él.
2. **Contrato ejecutable**: una feature de pruebas (`payments-contract.feature`) con los esquemas que el consumidor necesita.
3. Esa misma feature se ejecuta **contra el mock** (debe pasar: el mock es fiel a lo que el consumidor asume) **y contra el proveedor real** (debe pasar: el proveedor cumple). Si ambas pasan, el mock es un sustituto válido.
4. El contrato vive en git (repo del consumidor o repo compartido); el proveedor lo corre en su pipeline.

```java
// mismo contrato, dos destinos
SuiteResult contraMock = Runner.path("classpath:contratos/payments-contract.feature")
    .systemProperty("paymentsUrl", mock.getUrl()).parallel(1);
SuiteResult contraReal = Runner.path("classpath:contratos/payments-contract.feature")
    .karateEnv("qa").parallel(1);
```
Diseña el contrato con `contains`/marcadores difusos sobre los campos que el consumidor **usa**, no con igualdad total: así el proveedor puede agregar campos sin romper el contrato.

## 8. Mocks en JS (v2)

v2 admite handlers en archivos JS con enrutamiento por archivo (`/api/todos` → `api/todos.js`, ver `karate-todo`). Para la mayoría de equipos de QA el mock en `.feature` es más legible; usa JS cuando la lógica del mock es extensa.
