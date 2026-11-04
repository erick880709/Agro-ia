# 09 — JMeter DSL (pruebas de rendimiento como código Java)

## 1. Qué es y cuándo usarlo
[JMeter DSL](https://abstracta.github.io/jmeter-java-dsl/) (Abstracta) define planes de JMeter en Java y los ejecuta con el motor de JMeter embebido desde JUnit. Versión estable: **2.2.1** (la rama principal prepara 2.3).

| Usar JMeter DSL | Usar `.jmx` |
|---|---|
| Equipo de desarrollo Java; pruebas en el mismo repo del servicio | Equipo QA de rendimiento con GUI y grabación |
| Pruebas de humo/regresión en cada PR | Pruebas grandes, distribuidas, con muchos flujos |
| Revisión de código, diffs legibles, refactor | Planes heredados |
| Criterios de aceptación como aserciones de JUnit | Gate con `analizar_jtl.py` |

Puede convertir un `.jmx` existente a código (`jmdsl jmx2dsl plan.jmx`, módulo CLI) y exportar un plan DSL a `.jmx` (`testPlan(...).saveAsJmx("plan.jmx")`).

## 2. Dependencia
```xml
<dependency>
  <groupId>us.abstracta.jmeter</groupId>
  <artifactId>jmeter-java-dsl</artifactId>
  <version>2.2.1</version>
  <scope>test</scope>
</dependency>
```
Más JUnit 5 y AssertJ. Módulos opcionales: `-jdbc`, `-websocket`, `-graphql`, `-prometheus`, `-dashboard`, `-blazemeter`/`-octoperf`/`-azure` (ejecución en la nube).

## 3. Prueba base (estructura de la skill oficial de Abstracta)
```java
package co.empresa.rendimiento;

import static org.assertj.core.api.Assertions.assertThat;
import static us.abstracta.jmeter.javadsl.JmeterDsl.*;

import java.time.Duration;
import org.junit.jupiter.api.Test;
import us.abstracta.jmeter.javadsl.core.TestPlanStats;
import us.abstracta.jmeter.javadsl.core.threadgroups.BaseThreadGroup.SampleErrorAction;

class SaldoPerformanceTest {
  private static final String BASE = System.getProperty("baseUrl", "http://localhost:3000");
  private static final int HILOS = 10;
  private static final int ITERACIONES = 20;
  private static final long P90_MS = 800;
  private static final double ERROR_MAX_PCT = 1.0;
  private static final double RPS_MIN = 5.0;

  @Test
  void consultaDeSaldoCumpleSla() throws Exception {
    TestPlanStats stats = testPlan(
        httpDefaults().url(BASE),
        threadGroup(HILOS, ITERACIONES,
            transaction("01_ConsultarSaldo",
                httpSampler("GET /api/saldo", "/api/saldo")
                    .children(responseAssertion().containsSubstrings("\"saldo\""))),
            uniformRandomTimer(Duration.ofSeconds(1), Duration.ofSeconds(3)))
            .sampleErrorAction(SampleErrorAction.START_NEXT_ITERATION),
        jtlWriter("target/jtls"),
        htmlReporter("target/reportes"))
        .run();

    assertThat(stats.overall().sampleTime().perc90()).isLessThan(Duration.ofMillis(P90_MS));
    double errorPct = stats.overall().samplesCount() == 0 ? 0
        : stats.overall().errorsCount() * 100.0 / stats.overall().samplesCount();
    assertThat(errorPct).isLessThan(ERROR_MAX_PCT);
    double rps = stats.overall().samplesCount() / (stats.duration().toMillis() / 1000.0);
    assertThat(rps).isGreaterThanOrEqualTo(RPS_MIN);
  }
}
```
Ajusta la firma exacta de los métodos a la versión del proyecto consultando la guía oficial; la skill de Abstracta recomienda leer la documentación viva antes de usar APIs que no estén en esta plantilla.

## 4. Piezas frecuentes (métodos verificados en el código de JMeter DSL)
| Necesidad | DSL |
|---|---|
| Carga por tasa (modelo abierto) | `rpsThreadGroup().maxThreads(50).rampToAndHold(20, Duration.ofMinutes(2), Duration.ofMinutes(10))` |
| Datos desde CSV | `csvDataSet("datos/usuarios.csv")` |
| Correlación | `jsonExtractor("token", "$.access_token")`, `regexExtractor(...)`, `boundaryExtractor(...)` |
| Encabezados y cookies | `httpHeaders().header("Authorization", "Bearer ${token}")`, `httpCookies()` |
| Aserción JSON | `jsonAssertion(...)` |
| Think time / ritmo | `uniformRandomTimer(...)`, `constantTimer(...)`, `throughputTimer(...)` |
| Pasos de negocio | `transaction("02_Transferir", ...)` |
| Condicional / preparación | `ifController(...)`, `setupThreadGroup(...)`, `jsr223PreProcessor(...)` |
| Resultados | `jtlWriter(...)` (para `analizar_jtl.py`), `htmlReporter(...)`, `influxDbListener(...)` |

## 5. En CI
`mvn test -Dtest=*PerformanceTest -DbaseUrl=https://qa.ejemplo.com`. Mantén estas pruebas cortas (1–3 min) y separadas de las unitarias (perfil Maven o tag de JUnit). El `jtlWriter` permite aplicar además `analizar_jtl.py --base` para detectar regresiones entre releases.
