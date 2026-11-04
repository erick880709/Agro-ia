# 07 — Performance con karate-gatling

## Contenido
1. Idea central y límites
2. Dependencias y plugin
3. Simulación base
4. Agrupación de URLs y pausas
5. Variables de sesión (v1 vs v2)
6. Datos de prueba (feeders)
7. Métricas custom (BD, gRPC)
8. Buenas prácticas y logging

---

## 1. Idea central

Reutiliza las features funcionales como escenarios de carga: Gatling controla usuarios virtuales y tiempos; Karate ejecuta los pasos. Ventaja: una sola fuente de verdad. Límites: el overhead por request es mayor que Gatling puro; para pruebas de estrés extremo de un único endpoint, Gatling/JMeter/k6 nativos pueden ser más eficientes.

Las features de performance deben ser **subconjuntos ligeros**: sin `print` de payloads grandes, sin validaciones de esquema pesadas en cada iteración, con token obtenido por `callSingle`.

## 2. Dependencias

```xml
<dependency>
  <groupId>io.karatelabs</groupId>
  <artifactId>karate-gatling</artifactId>
  <version>${karate.version}</version>
  <scope>test</scope>
</dependency>

<!-- perfil maven para no correr carga en cada mvn test -->
<profile>
  <id>gatling</id>
  <build><plugins><plugin>
    <groupId>io.gatling</groupId>
    <artifactId>gatling-maven-plugin</artifactId>
    <version>4.7.0</version>
    <configuration>
      <simulationsFolder>src/test/java</simulationsFolder>
      <includes><include>perf.PagosSimulation</include></includes>
      <!-- requerido con Gatling 4.7+ en Java 17/21 -->
      <jvmArgs><jvmArg>--add-opens=java.base/java.lang=ALL-UNNAMED</jvmArg></jvmArgs>
    </configuration>
  </plugin></plugins></build>
</profile>
```
Ejecutar: `mvn clean test-compile gatling:test -Pgatling -Dkarate.env=perf`.

## 3. Simulación (Java DSL)

```java
package perf;

import io.gatling.javaapi.core.*;
import io.karatelabs.gatling.KarateProtocolBuilder;          // v1: com.intuit.karate.gatling.javaapi.*
import static io.gatling.javaapi.core.CoreDsl.*;
import static io.karatelabs.gatling.KarateDsl.*;

public class PagosSimulation extends Simulation {
  public PagosSimulation() {
    KarateProtocolBuilder protocol = karateProtocol(
        uri("/pagos/{id}").nil(),
        uri("/pagos").pauseFor(method("get", 15), method("post", 25))   // v1: .pauseFor("get", 15, "post", 25)
    );

    ScenarioBuilder consulta = scenario("consulta-pagos")
        .exec(karateFeature("classpath:perf/consultar-pago.feature"));
    ScenarioBuilder creacion = scenario("crear-pagos")
        .exec(karateFeature("classpath:perf/crear-pago.feature", "@perf"));

    setUp(
        consulta.injectOpen(rampUsersPerSec(1).to(20).during(60), constantUsersPerSec(20).during(300)),
        creacion.injectOpen(rampUsers(50).during(120))
    ).protocols(protocol)
     .assertions(
        global().responseTime().percentile(95).lt(800),
        global().failedRequests().percent().lt(1.0)
     );
  }
}
```
- `karateFeature(path, tags...)` selecciona escenarios por tag.
- `uri(...)` agrupa URLs con path params en una sola métrica (sin esto, `/pagos/1`, `/pagos/2`... aparecen como métricas separadas).
- Define **assertions** (SLA) para que la simulación falle el pipeline si no se cumplen.

## 4. Nombres y pausas

`pauseFor(method("get", 15), method("post", 25))` (v2; en v1 `pauseFor("get", 15, "post", 25)`) agrega pausa (ms) tras cada request del método en esa URL — simula think time sin ensuciar la feature. Dentro de features usa `karate.pause(ms)`, que se integra con el modelo no bloqueante de Gatling (nunca `Thread.sleep`).

`karateProtocol().nameResolver((req, vars) -> ...)` permite nombrar requests (útil en GraphQL, donde todo es `POST /graphql`).

## 5. Variables de sesión

```java
.exec(karateSet("documento", s -> "9" + s.userId()))
.exec(karateFeature("classpath:perf/crear-cliente.feature"))
.exec(karateFeature("classpath:perf/consultar-cliente.feature"))   // usa variables del anterior
```
| | v1 | v2 |
|---|---|---|
| Variable de Gatling | `documento` o `__gatling.documento` | **solo** `__gatling.documento` |
| Variable de feature anterior | `clienteId` o `__karate.clienteId` | **solo** `__karate.clienteId` |

En v2 las variables Gatling llegan después de `karate-config.js`: dentro del escenario usa `karate.get('__gatling.documento', 'default')`. Feature compatible con ejecución funcional y de carga:
```gherkin
* def documento = karate.get('__gatling.documento', '900000001')
```

## 6. Feeders

```java
Iterator<Map<String, Object>> feeder = Stream.generate(() ->
    Map.<String, Object>of("monto", ThreadLocalRandom.current().nextInt(1000, 500000))).iterator();
ScenarioBuilder s = scenario("crear").feed(feeder).exec(karateFeature("classpath:perf/crear-pago.feature"));
```
O `csv("data/clientes.csv").circular()` con el feeder estándar de Gatling. En la feature: `__gatling.monto`.

## 7. Métricas custom

Para medir operaciones no-HTTP (consultas JDBC, gRPC por interop) como métricas de Gatling:
```java
public static Map<String, Object> consultar(Map<String, Object> args, PerfContext ctx) {   // v2: io.karatelabs.core.PerfContext
  long ini = System.currentTimeMillis();
  // ... lógica ...
  ctx.capturePerfEvent("consulta-saldo-db", ini, System.currentTimeMillis());
  return Map.of("ok", true);
}
```
```gherkin
* def r = Java.type('perf.DbPerf').consultar({ cuenta: '001' }, karate)
```
Fuera de Gatling, `capturePerfEvent` es no-op: la misma feature sirve en funcional.

## 8. Buenas prácticas

- Ambiente dedicado y datos preparados; nunca carga contra producción ni contra ambientes compartidos sin coordinación.
- Escenarios con mezcla realista (ratio lectura/escritura del tráfico real).
- Logging mínimo: en `logback-test.xml` deja `karate` en `WARN`/`ERROR`. En v2, con `karateProtocol().logReplay(KarateLogReplay.FAILED)` el detalle solo se emite para features que fallan.
- Reporte: `target/gatling/<simulacion>-<timestamp>/index.html`. Publícalo como artefacto del pipeline.
- Prueba de humo de performance (pocos usuarios, 1–2 min) en cada release; carga/estrés completa en ventanas planificadas.
