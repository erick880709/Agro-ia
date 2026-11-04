# 08 — Protocolos, integraciones y extensiones

## Contenido
1. Mapa open source vs comercial
2. Java interop (la puerta a todo)
3. Base de datos (JDBC)
4. Kafka
5. gRPC
6. WebSocket
7. Procesos, CLI, SSH
8. `karate-boot.js` y extensiones (v2)
9. Ofertas enterprise y Karate Agent

---

## 1. Mapa

| Capacidad | Open source | Comercial (licencia Karate Labs) |
|---|---|---|
| HTTP/REST/SOAP/GraphQL, match, mocks, UI, Gatling | ✔ | |
| BD, colas, SDKs (AWS, etc.) vía Java interop | ✔ (código propio) | |
| Kafka nativo (`karate.channel('kafka')`, Avro, Protobuf, Schema Registry) | | ✔ |
| gRPC nativo (lee `.proto` en runtime, sin stubs) | | ✔ |
| WebSocket nativo | | ✔ |
| Karate Agent (trazabilidad requisitos→pruebas, cobertura, MCP), Xplorer, plugins IDE pagos | | ✔ |

Regla de la skill: cuando uses algo comercial, **dilo explícitamente** y ofrece la alternativa por Java interop.

## 2. Java interop

```gherkin
* def Util = Java.type('com.empresa.qa.Util')        # clase en src/test/java
* def r = Util.calcularDigito('900123456')            # método estático
* def inst = new Util('cfg')                          # instancia
* def lista = inst.consultar()                        # List<Map> => JSON nativo en Karate
* match lista contains { estado: 'OK' }
```
- `List`/`Map` de Java se comportan como arreglos/objetos JSON; se pueden validar con `match` directamente.
- En v2, funciones JS se convierten solas a interfaces funcionales Java (`Function`, `Predicate`, `Consumer`, `Supplier`); `karate.toJava()` es no-op deprecado.
- Cuándo escribir Java: drivers/SDKs (JDBC, Kafka client, AWS SDK), criptografía (firmas, cifrado JWE), lógica compleja reutilizable. Cuándo **no**: lógica que cabe en una función JS de 5 líneas.

## 3. Base de datos

Utilidad en `src/test/java`:
```java
public class DbUtils {
  private final JdbcTemplate jdbc;   // spring-jdbc; o JDBC puro con DriverManager
  public DbUtils(Map<String, Object> cfg) {
    DriverManagerDataSource ds = new DriverManagerDataSource();
    ds.setDriverClassName((String) cfg.get("driverClassName"));
    ds.setUrl((String) cfg.get("url"));
    ds.setUsername((String) cfg.get("username"));
    ds.setPassword((String) cfg.get("password"));
    jdbc = new JdbcTemplate(ds);
  }
  public Object readValue(String sql, Object... args) { return jdbc.queryForObject(sql, Object.class, args); }
  public Map<String, Object> readRow(String sql, Object... args) { return jdbc.queryForMap(sql, args); }
  public List<Map<String, Object>> readRows(String sql, Object... args) { return jdbc.queryForList(sql, args); }
  public int update(String sql, Object... args) { return jdbc.update(sql, args); }
}
```
`karate-config.js`:
```javascript
var DbUtils = Java.type('com.empresa.qa.DbUtils');
config.db = new DbUtils({ url: karate.properties['db.url'], username: karate.properties['db.user'],
                          password: karate.properties['db.password'], driverClassName: 'oracle.jdbc.OracleDriver' });
```
Feature:
```gherkin
* def fila = db.readRow('SELECT ESTADO, MONTO FROM PAGOS WHERE ID = ?', pagoId)
* match fila == { ESTADO: 'APLICADO', MONTO: '#? _ == 50000' }
```
- **Siempre consultas parametrizadas (`?`)**, nunca concatenar valores en el SQL.
- Oracle devuelve nombres de columna en MAYÚSCULAS y números como `BigDecimal` → compara con `#?` o convierte.
- Usuario de BD de solo lectura para validaciones; escrituras solo para setup/limpieza en ambientes de prueba.
- No retornar objetos Java desde `callSingle`: su resultado debe ser JSON puro. Para conexiones costosas, usa un pool Java con ciclo de vida y cierre explícitos, seguro entre hilos.

## 4. Kafka

**Comercial (karate-kafka):**
```gherkin
Background:
  * configure kafka = { 'bootstrap.servers': '#(kafkaServers)', 'schema.registry.url': '#(registryUrl)' }

Scenario: publica evento y lo consume
  * def channel = karate.channel('kafka')
  * def consumer = channel.consumer()
  * consumer.topic = 'pagos-aplicados'
  * consumer.count = 1
  * consumer.timeout = 10000
  * consumer.start()                       # iniciar ANTES de producir
  * def producer = channel.producer()
  * producer.topic = 'pagos-solicitados'
  * producer.key = pagoId
  * producer.value = { id: '#(pagoId)', monto: 1000 }
  * producer.send()
  * def msg = consumer.pop()
  * match msg.value contains { id: '#(pagoId)', estado: 'APLICADO' }
```
Avro: `channel.register({ name: 'pago', path: 'classpath:schemas/pago.avsc' })`. Requiere `.karate/karate.lic`.

**Open source**: clase Java con `KafkaProducer`/`KafkaConsumer` (ver `karate-examples/kafka-custom`), expuesta con `Java.type`; el consumidor corre en un hilo y deja mensajes en una cola que la feature lee con timeout. Patrón API + evento: invocar el endpoint por HTTP y validar el evento publicado.

## 5. gRPC (comercial)

```gherkin
Background:
  * def session = karate.channel('grpc')
  * session.proto = 'classpath:proto/cuentas.proto'
  * session.service = 'CuentasService'

Scenario: unario
  * session.method = 'Consultar'
  * session.send({ numero: '001' })
  * match session.pop() == { numero: '001', saldo: '#number' }

Scenario: error de negocio
  * session.method = 'Consultar'
  * session.send({ numero: '' })
  * match session.collect() == []
  * match session.status == 'INVALID_ARGUMENT'
```
Streaming: `session.count = n` + `session.collect()`; client streaming: `session.stream = true`, varios `send`, `session.flush()`. Metadata: `session.metadata = { authorization: 'Bearer ...' }`. Open source: stubs generados + Java interop.

## 6. WebSocket

Comercial nativo vía `karate.channel('websocket')`; en v1 open source existía `karate.webSocket(url, handler)` (en v2 se retiró del core). Patrón: abrir, enviar, esperar mensaje con timeout, validar con `match`.

## 7. Procesos, CLI, SSH

```gherkin
* def r = karate.exec('kubectl get pods -n qa -o json')
* def pods = karate.fromString(r)
* def proc = karate.fork({ args: ['java', '-jar', 'stub.jar'], listener: function(l){ if (l.contains('Started')) karate.signal({ ok: true }) } })
* def ready = listen 30000
* match ready.ok == true
```
SSH: Java interop con JSch / sshj (ver `karate-examples/ssh`).

## 8. `karate-boot.js` (v2)

Archivo en la raíz de trabajo, evaluado **una vez por suite**, para activar extensiones (exts) declarativamente. No define variables de prueba (para eso está `karate-config.js`).
```javascript
// karate-boot.js
if (boot.has('openapi')) {
  const openapi = boot.ext('openapi');
  openapi.path = 'api/openapi.yaml';
  openapi.excludes = ['/health/**'];
}
boot.classpath('src/test/resources');   // declara otra raíz de recursos
```
API: `boot.env`, `boot.sysenv()`, `boot.sysprop()`, `boot.read()`, `boot.log()`, `boot.ext(nombre)` (falla la suite si no existe), `boot.has(nombre)`. Comparación de imágenes (regresión visual) en v2 vive en la extensión `karate-image` activada aquí.

## 9. Enterprise y Karate Agent

- **Karate Labs Enterprise**: extensiones comerciales (Kafka, gRPC, WebSocket y otras), soporte, licencias por runtime (`.karate/karate.lic`) y por asiento de IDE.
- **Karate Agent**: capa de gobierno para código generado por IA. Requisitos en markdown con criterios de aceptación EARS (`WHEN ... THE SYSTEM SHALL ...`), escenarios etiquetados `@req=<id>/<criterio>`, matriz de trazabilidad (RTM) y cobertura API/UI construidas desde evidencia de ejecución, y servidor MCP (`karate_eval`) para que agentes de IA lo operen. Se ejecuta como contenedor `public.ecr.aws/karatelabs/karate-agent` con licencia. Ejemplos: `github.com/karatelabs/karate-agent-examples`.
- Idea aprovechable **sin licencia**: etiquetar escenarios con el ID de requisito/criterio (`@req=HU-245/CA-3`) y generar la matriz de trazabilidad a partir de `karate-events.jsonl` (v2) o Cucumber JSON. Ver 09.
